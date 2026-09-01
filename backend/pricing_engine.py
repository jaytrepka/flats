import re
import statistics
import logging
from typing import List, Tuple, Dict, Optional
from .models import SearchCriteria, FlatListing, PriceStats, SearchResponse
from .benchmarks import get_benchmark_price_per_m2
from .geo_resolver import is_listing_in_target_location

logger = logging.getLogger(__name__)


def parse_czk_amount(val: str) -> float:
    """Extract numeric CZK digits from formatted text (e.g. '11.275.385 Kč' -> 11275385.0)."""
    digits = re.sub(r'[^\d]', '', val)
    return float(digits) if digits else 0.0


def detect_hidden_costs_and_caveats(flat: FlatListing) -> Tuple[float, List[str], bool, bool]:
    """
    Detect unpaid annuities ('anuita'), partial shares ('podíl 1/2'), 
    auctions ('dražba'), and lifetime rights ('věcné břemeno dožití').
    """
    title = flat.title or ""
    desc = flat.description or ""
    extra = flat.extra_details or {}
    
    full_text = f"{title} {desc}".lower()
    caveats: List[str] = []
    annuity = 0.0
    is_partial_share = False
    is_auction = False

    # Check structured extra_details first (e.g. Sreality API annuity field)
    raw_annuity = extra.get("annuity") or extra.get("raw_annuity")
    if raw_annuity and isinstance(raw_annuity, (int, float)) and raw_annuity >= 100000:
        annuity = float(raw_annuity)

    # 1. Unpaid Annuity (Družstevní byty / Finep / Skanska / převod podílu s doplatkem anuity)
    if annuity == 0.0:
        # Pattern 1: (anuita): 3 979 000 or anuita: 3 979 000 or anuita ve výši 3 979 000 Kč
        annuity_matches_1 = re.findall(
            r'(?:zbývající\s+anuit[au]|nesplacen[áa]\s+anuita|nesplacen[áa]\s+část\s*\(anuita\)|\(?\s*anuita\s*\)?)\s*(?:ve\s+výši|činí|je|:|\-)?\s*([0-9\s\.\,]{4,18})',
            full_text,
        )
        for m in annuity_matches_1:
            amt = parse_czk_amount(m)
            if 150000 <= amt <= 35000000:
                annuity = max(annuity, amt)

    if annuity == 0.0:
        # Pattern 2: nedoplacená část novostavby ... (anuita): 3 979 000
        annuity_matches_2 = re.findall(
            r'(?:nedoplacen[áa]|nesplacen[áa]|zbývající|doplatek)[^\n\r\.\,]*?(?:anuita|anuitu|anuitou|\(anuita\))\s*(?:ve\s+výši|činí|je|:|\-)?\s*([0-9\s\.\,]{4,18})',
            full_text,
        )
        for m in annuity_matches_2:
            amt = parse_czk_amount(m)
            if 150000 <= amt <= 35000000:
                annuity = max(annuity, amt)

    if annuity == 0.0:
        # Pattern 3: general mention of doplatek or odstupné + doplatek
        doplatek_match = re.search(
            r'(?:doplatek\s+družstvu|doplatek\s+anuit[ay]|doplatit\s+anuitu)\s*(?:ve\s+výši|činí|je|:|\-)?\s*([0-9\s\.\,]{4,18})',
            full_text,
        )
        if doplatek_match:
            amt = parse_czk_amount(doplatek_match.group(1))
            if 150000 <= amt <= 35000000:
                annuity = max(annuity, amt)

    if annuity > 0:
        caveats.append(f"Anuita +{int(annuity):,} Kč".replace(",", " "))

    # 2. Fractional Spoluvlastnický Podíl (1/2, 1/3, 1/4, etc.)
    if re.search(r'(?:podíl\s+[1-9]\/[1-9]|ideální\s+polovin|ideální\s+podíl|spoluvlastnick[ýé]\s+podíl|prodej\s+podílu|1\/[2-8]\s+bytu|poloviční\s+podíl)', full_text):
        is_partial_share = True
        caveats.append("Spoluvlastnický podíl")

    # 3. Auctions & Execution starting bids (Dražba, Vyvolávací cena)
    if re.search(r'(?:dražb[ay]|vyvolávací\s+cena|nedobrovoln[áé]\s+dražb|exekuční\s+dražb|dražební\s+jednání)', full_text):
        is_auction = True
        caveats.append("Dražba / Vyvolávací cena")

    # 4. Lifetime Encumbrance (Věcné břemeno dožití)
    if re.search(r'(?:břemen[oa-z]*\s+dožití|doživotní\s+užívání|břemeno\s+bydlení|právo\s+dožití|věcné\s+břemeno)', full_text):
        caveats.append("Věcné břemeno dožití")

    return annuity, caveats, is_partial_share, is_auction


def calculate_pricing_and_filter(
    listings: List[FlatListing], criteria: SearchCriteria
) -> SearchResponse:
    # 0. Enforce geographic boundary matching for all selected locations
    loc_targets = criteria.locations if (criteria.locations and len(criteria.locations) > 0) else [criteria.location]
    loc_targets = [l.strip() for l in loc_targets if l and l.strip()]

    if loc_targets and not any(l.lower() in ["ceska republika", "cr", "čr", "cesko", "česko"] for l in loc_targets):
        valid_geo_listings = []
        for f in listings:
            if any(
                is_listing_in_target_location(
                    target_location=loc,
                    listing_locality=f.locality,
                    listing_city=f.city,
                    listing_region=f.region or "",
                    listing_district=f.district or "",
                    listing_title=f.title,
                )
                for loc in loc_targets
            ):
                valid_geo_listings.append(f)
        listings = valid_geo_listings

    total_scanned = len(listings)
    
    # 1. Pre-process listings: Detect Annuities and Caveats, recalculate Real Total Price
    for flat in listings:
        annuity, caveats, is_share, is_auc = detect_hidden_costs_and_caveats(flat)
        flat.unpaid_annuity_czk = annuity
        flat.caveat_flags = caveats
        flat.is_partial_share = is_share
        flat.is_auction = is_auc

        if criteria.include_annuity_in_price and annuity > 0:
            flat.advertised_price_czk = flat.price_czk
            flat.price_czk = flat.price_czk + annuity
            if flat.area_m2 > 0:
                flat.price_per_m2 = round(flat.price_czk / flat.area_m2, 0)

    # 2. Determine baseline price per m2
    regional_benchmark = get_benchmark_price_per_m2(criteria.location)
    benchmark_source = "Regionální cenová mapa ČR"
    
    # Collect valid price_per_m2 values (excluding partial share distortions)
    valid_prices_m2 = [
        f.price_per_m2 for f in listings 
        if f.price_per_m2 > 10000 and f.price_per_m2 < 500000 and not f.is_partial_share
    ]
    
    disposition_stats: Dict[str, List[float]] = {}
    for f in listings:
        if f.price_per_m2 > 10000 and f.price_per_m2 < 500000 and not f.is_partial_share:
            disposition_stats.setdefault(f.disposition, []).append(f.price_per_m2)

    disp_averages: Dict[str, float] = {}
    for disp, prices in disposition_stats.items():
        if prices:
            disp_averages[disp] = round(statistics.median(prices), 0)

    if criteria.custom_benchmark_czk_m2 and criteria.custom_benchmark_czk_m2 > 0:
        base_price_m2 = criteria.custom_benchmark_czk_m2
        benchmark_source = f"Uživatelská cílová cena ({int(base_price_m2):,} Kč/m²)"
    elif len(valid_prices_m2) >= 4:
        sorted_p = sorted(valid_prices_m2)
        trim_count = max(1, int(len(sorted_p) * 0.1))
        trimmed = sorted_p[trim_count:-trim_count] if len(sorted_p) > 4 else sorted_p
        
        dynamic_median = statistics.median(trimmed)
        base_price_m2 = round(0.5 * dynamic_median + 0.5 * regional_benchmark, 0)
        benchmark_source = f"Tržní průměr inzerátů a cenové mapy ({len(valid_prices_m2)} nabídek v lokalitě)"
    elif len(valid_prices_m2) > 0:
        dynamic_median = statistics.median(valid_prices_m2)
        base_price_m2 = round(0.5 * dynamic_median + 0.5 * regional_benchmark, 0)
        benchmark_source = f"Kombinovaný průměr trhu a cenové mapy ({len(valid_prices_m2)} nabídek)"
    else:
        base_price_m2 = regional_benchmark
        benchmark_source = f"Cenová mapa pro vybranou lokalitu"

    # 3. Score and calculate savings for every flat
    enriched_listings: List[FlatListing] = []
    portal_counts: Dict[str, int] = {}
    
    for flat in listings:
        portal_counts[flat.portal] = portal_counts.get(flat.portal, 0) + 1
        
        # Use disposition-specific baseline if available
        if flat.disposition in disp_averages and len(disposition_stats.get(flat.disposition, [])) >= 3:
            loc_baseline = round(0.7 * disp_averages[flat.disposition] + 0.3 * base_price_m2, 0)
        else:
            loc_baseline = base_price_m2

        flat.market_avg_price_per_m2 = loc_baseline
        flat.expected_price_czk = round(flat.area_m2 * loc_baseline, 0)
        flat.difference_czk = round(flat.expected_price_czk - flat.price_czk, 0)
        
        if flat.expected_price_czk > 0:
            flat.discount_percentage = round((flat.difference_czk / flat.expected_price_czk) * 100.0, 1)
        else:
            flat.discount_percentage = 0.0

        flat.is_bargain = flat.difference_czk > 0

        # Bargain tiers
        if flat.discount_percentage >= 20.0:
            flat.bargain_tier = "SUPER_BARGAIN"
        elif flat.discount_percentage >= 10.0:
            flat.bargain_tier = "GOOD_DEAL"
        elif flat.discount_percentage > 0.0:
            flat.bargain_tier = "FAIR_DEAL"
        else:
            flat.bargain_tier = "ABOVE_MARKET"

        enriched_listings.append(flat)

    # 4. Filtering (including caveat filters)
    filtered_listings: List[FlatListing] = []
    for flat in enriched_listings:
        # Filter out partial shares if requested
        if criteria.filter_partial_shares and flat.is_partial_share:
            continue
            
        # Filter out auctions / execution starting bids if requested
        if criteria.filter_auctions and flat.is_auction:
            continue

        if criteria.only_below_average and not flat.is_bargain:
            continue
            
        if criteria.min_discount_percent > 0 and flat.discount_percentage < criteria.min_discount_percent:
            continue

        filtered_listings.append(flat)

    # 5. Sorting
    if criteria.sort_by == "discount_desc":
        filtered_listings.sort(key=lambda x: x.discount_percentage, reverse=True)
    elif criteria.sort_by == "savings_desc":
        filtered_listings.sort(key=lambda x: x.difference_czk, reverse=True)
    elif criteria.sort_by == "price_m2_asc":
        filtered_listings.sort(key=lambda x: x.price_per_m2)
    elif criteria.sort_by == "price_asc":
        filtered_listings.sort(key=lambda x: x.price_czk)
    elif criteria.sort_by == "price_desc":
        filtered_listings.sort(key=lambda x: x.price_czk, reverse=True)

    # Limit results
    final_listings = filtered_listings[: criteria.limit]

    # 6. Summary Statistics
    total_bargains = sum(1 for f in filtered_listings if f.is_bargain)
    max_savings = max([f.difference_czk for f in filtered_listings], default=0.0)
    
    avg_price_m2 = round(statistics.mean(valid_prices_m2), 0) if valid_prices_m2 else base_price_m2
    median_price_m2 = round(statistics.median(valid_prices_m2), 0) if valid_prices_m2 else base_price_m2
    min_p_m2 = min(valid_prices_m2) if valid_prices_m2 else base_price_m2
    max_p_m2 = max(valid_prices_m2) if valid_prices_m2 else base_price_m2

    stats = PriceStats(
        locality_name=criteria.location.title(),
        total_scanned=total_scanned,
        total_bargains=total_bargains,
        average_price_per_m2=avg_price_m2,
        median_price_per_m2=median_price_m2,
        min_price_per_m2=min_p_m2,
        max_price_per_m2=max_p_m2,
        max_savings_czk=max(0.0, max_savings),
        benchmark_source=benchmark_source,
        disposition_averages=disp_averages,
    )

    return SearchResponse(
        stats=stats,
        listings=final_listings,
        criteria=criteria,
        portal_counts=portal_counts,
    )
