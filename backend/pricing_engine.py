import statistics
import logging
from typing import List, Tuple, Dict
from .models import SearchCriteria, FlatListing, PriceStats, SearchResponse
from .benchmarks import get_benchmark_price_per_m2

logger = logging.getLogger(__name__)


def calculate_pricing_and_filter(
    listings: List[FlatListing], criteria: SearchCriteria
) -> SearchResponse:
    total_scanned = len(listings)
    
    # 1. Determine baseline price per m2
    regional_benchmark = get_benchmark_price_per_m2(criteria.location)
    benchmark_source = "Regionální cenová mapa ČR"
    
    # Collect valid price_per_m2 values
    valid_prices_m2 = [f.price_per_m2 for f in listings if f.price_per_m2 > 10000 and f.price_per_m2 < 500000]
    
    disposition_stats: Dict[str, List[float]] = {}
    for f in listings:
        if f.price_per_m2 > 10000 and f.price_per_m2 < 500000:
            disposition_stats.setdefault(f.disposition, []).append(f.price_per_m2)

    disp_averages: Dict[str, float] = {}
    for disp, prices in disposition_stats.items():
        if prices:
            disp_averages[disp] = round(statistics.median(prices), 0)

    if criteria.custom_benchmark_czk_m2 and criteria.custom_benchmark_czk_m2 > 0:
        base_price_m2 = criteria.custom_benchmark_czk_m2
        benchmark_source = f"Uživatelská cílová cena ({int(base_price_m2):,} Kč/m²)"
    elif len(valid_prices_m2) >= 4:
        # Calculate trimmed mean & median
        sorted_p = sorted(valid_prices_m2)
        # Trim top and bottom 10%
        trim_count = max(1, int(len(sorted_p) * 0.1))
        trimmed = sorted_p[trim_count:-trim_count] if len(sorted_p) > 4 else sorted_p
        
        dynamic_median = statistics.median(trimmed)
        dynamic_mean = statistics.mean(trimmed)
        
        # Weighted combination: 80% dynamic median + 20% regional benchmark for stability
        base_price_m2 = round(0.8 * dynamic_median + 0.2 * regional_benchmark, 0)
        benchmark_source = f"Dynamický tržní průměr ({len(valid_prices_m2)} nabídek v lokalitě)"
    elif len(valid_prices_m2) > 0:
        dynamic_median = statistics.median(valid_prices_m2)
        base_price_m2 = round(0.5 * dynamic_median + 0.5 * regional_benchmark, 0)
        benchmark_source = f"Kombinovaný průměr trhu a cenové mapy ({len(valid_prices_m2)} nabídek)"
    else:
        base_price_m2 = regional_benchmark
        benchmark_source = f"Cenová mapa pro lokalitu '{criteria.location}'"

    # 2. Score and calculate savings for every flat
    enriched_listings: List[FlatListing] = []
    portal_counts: Dict[str, int] = {}
    
    for flat in listings:
        portal_counts[flat.portal] = portal_counts.get(flat.portal, 0) + 1
        
        # Use disposition-specific baseline if we have enough samples for it
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

    # 3. Filtering
    filtered_listings: List[FlatListing] = []
    for flat in enriched_listings:
        if criteria.only_below_average and not flat.is_bargain:
            continue
        if criteria.min_discount_percent > 0 and flat.discount_percentage < criteria.min_discount_percent:
            continue
        filtered_listings.append(flat)

    # 4. Sorting
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

    # 5. Summary Statistics
    total_bargains = sum(1 for f in enriched_listings if f.is_bargain)
    max_savings = max([f.difference_czk for f in enriched_listings], default=0.0)
    
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
