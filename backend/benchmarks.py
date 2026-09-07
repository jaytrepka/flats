"""
Czech Real Estate Baseline Benchmarks (Kč/m²)
Based on regional statistical data (ČSÚ, Sreality price index, Deloite Real Index, Cenová Mapa)
"""

import unicodedata
import re
from typing import Optional, Dict

# Regional benchmark average prices per m2 (in CZK/m²)
REGIONAL_BENCHMARKS: Dict[str, float] = {
    # Prague and districts
    "praha": 158000,
    "praha 1": 210000,
    "praha 2": 185000,
    "praha 3": 165000,
    "praha 4": 142000,
    "praha 5": 155000,
    "praha 6": 160000,
    "praha 7": 162000,
    "praha 8": 148000,
    "praha 9": 138000,
    "praha 10": 140000,
    
    # Major regional capitals
    "brno": 128000,
    "brno-mesto": 128000,
    "brno-venkov": 98000,
    "plzen": 84000,
    "olomouc": 82000,
    "hradec kralove": 86000,
    "pardubice": 79000,
    "ceske budejovice": 81000,
    "liberec": 74000,
    "zlin": 76000,
    "jihlava": 72000,
    "karlovy vary": 62000,
    "usti nad labem": 42000,
    "ostrava": 52000,
    
    # Central Bohemian Region (Středočeský kraj)
    "stredocesky": 88000,
    "praha-vychod": 108000,
    "praha-zapad": 112000,
    "kladno": 78000,
    "beroun": 86000,
    "ricany": 115000,
    "kolin": 74000,
    "kutna hora": 69000,
    "mlada boleslav": 81000,
    "melnik": 86000,
    "nymburk": 75000,
    "pribram": 68000,
    "rakovnik": 64000,
    "benesov": 78000,
    "podebrady": 86000,
    "kralupy nad vltavou": 82000,
    
    # South Moravian Region (Jihomoravský kraj)
    "jihomoravsky": 95000,
    "blansko": 75000,
    "breclav": 72000,
    "hodonin": 64000,
    "vyskov": 74000,
    "znojmo": 69000,
    
    # Moravian-Silesian Region (Moravskoslezský kraj)
    "moravskoslezsky": 48000,
    "frydek-mistek": 54000,
    "opava": 51000,
    "karvina": 36000,
    "havirov": 38000,
    "novy jicin": 49000,
    "bruntal": 39000,
    "trinec": 52000,
    
    # Olomouc Region (Olomoucký kraj)
    "olomoucky": 71000,
    "prostejov": 65000,
    "prerov": 54000,
    "sumperk": 56000,
    "jesenik": 48000,
    
    # Zlín Region (Zlínský kraj)
    "zlinsky": 70000,
    "kromeriz": 64000,
    "uherske hradiste": 72000,
    "vsetin": 58000,
    
    # Vysočina Region
    "vysocina": 68000,
    "trebic": 62000,
    "havlickuv brod": 64000,
    "pelhrimov": 65000,
    "zdar nad sazavou": 66000,
    
    # South Bohemian Region (Jihočeský kraj)
    "jihocesky": 73000,
    "tabor": 68000,
    "pisek": 69000,
    "strakonice": 61000,
    "jindrichuv hradec": 64000,
    "cesky krumlov": 68000,
    "prachatice": 58000,
    
    # Plzeň Region (Plzeňský kraj)
    "plzensky": 74000,
    "klatovy": 63000,
    "domazlice": 59000,
    "tachov": 55000,
    "rokycany": 68000,
    
    # Karlovy Vary Region (Karlovarský kraj)
    "karlovarsky": 54000,
    "cheb": 52000,
    "sokolov": 38000,
    "marianske lazne": 68000,
    
    # Ústí nad Labem Region (Ústecký kraj)
    "ustecky": 39000,
    "decin": 39000,
    "chomutov": 37000,
    "litomerice": 62000,
    "louny": 48000,
    "most": 34000,
    "teplice": 41000,
    
    # Liberec Region (Liberecký kraj)
    "liberecky": 68000,
    "ceska lipa": 52000,
    "jablonec nad nisou": 63000,
    "semily": 55000,
    "turnov": 72000,
    
    # Hradec Králové Region (Královéhradecký kraj)
    "kralovehradecky": 78000,
    "jicin": 69000,
    "nachod": 58000,
    "rychnov nad kneznou": 66000,
    "trutnov": 57000,
    
    # Pardubice Region (Pardubický kraj)
    "pardubicky": 72000,
    "chrudim": 68000,
    "svitavy": 58000,
    "usti nad orlici": 61000,
}

# National baseline fallback
NATIONAL_AVERAGE_PRICE_PER_M2 = 78000.0


def normalize_string(text: str) -> str:
    """Normalize text: strip accents, convert to lowercase, remove extra spaces."""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_benchmark_price_per_m2(location: str) -> float:
    """Find the best matching benchmark price per m² for a given location."""
    norm_loc = normalize_string(location)
    
    # Direct match
    if norm_loc in REGIONAL_BENCHMARKS:
        return REGIONAL_BENCHMARKS[norm_loc]
        
    # Check if any benchmark key is contained within the search query
    # Prioritize longest matching keys (e.g. 'praha 4' over 'praha')
    sorted_keys = sorted(REGIONAL_BENCHMARKS.keys(), key=lambda k: len(k), reverse=True)
    
    for key in sorted_keys:
        if key in norm_loc:
            return REGIONAL_BENCHMARKS[key]
            
    # Check words
    words = norm_loc.split()
    for word in words:
        if word in REGIONAL_BENCHMARKS:
            return REGIONAL_BENCHMARKS[word]
            
    return NATIONAL_AVERAGE_PRICE_PER_M2


# Regional benchmark rental prices per m2 per month (in CZK/m²/month)
RENTAL_BENCHMARKS_M2_MONTH: Dict[str, float] = {
    # Prague and districts
    "praha": 420.0,
    "praha 1": 520.0,
    "praha 2": 480.0,
    "praha 3": 450.0,
    "praha 4": 390.0,
    "praha 5": 430.0,
    "praha 6": 420.0,
    "praha 7": 460.0,
    "praha 8": 430.0,
    "praha 9": 380.0,
    "praha 10": 390.0,

    # Major regional capitals
    "brno": 350.0,
    "brno-mesto": 350.0,
    "brno-venkov": 280.0,
    "plzen": 280.0,
    "olomouc": 275.0,
    "hradec kralove": 280.0,
    "pardubice": 270.0,
    "ceske budejovice": 270.0,
    "liberec": 250.0,
    "zlin": 250.0,
    "jihlava": 240.0,
    "karlovy vary": 220.0,
    "usti nad labem": 190.0,
    "ostrava": 220.0,

    # Central Bohemian Region (Středočeský kraj)
    "stredocesky": 280.0,
    "praha-vychod": 330.0,
    "praha-zapad": 340.0,
    "ricany": 340.0,
    "kladno": 260.0,
    "beroun": 280.0,
    "kolin": 245.0,
    "kutna hora": 235.0,
    "mlada boleslav": 275.0,
    "melnik": 255.0,
    "kralupy nad vltavou": 265.0,
    "nymburk": 250.0,
    "pribram": 230.0,
    "rakovnik": 220.0,
    "benesov": 260.0,
    "podebrady": 280.0,

    # South Moravian Region (Jihomoravský kraj)
    "jihomoravsky": 290.0,
    "blansko": 240.0,
    "breclav": 230.0,
    "hodonin": 210.0,
    "vyskov": 230.0,
    "znojmo": 220.0,

    # Moravian-Silesian Region (Moravskoslezský kraj)
    "moravskoslezsky": 200.0,
    "frydek-mistek": 215.0,
    "opava": 210.0,
    "karvina": 170.0,
    "havirov": 180.0,
    "novy jicin": 205.0,
    "bruntal": 175.0,
    "trinec": 210.0,

    # Olomouc Region (Olomoucký kraj)
    "olomoucky": 235.0,
    "prostejov": 220.0,
    "prerov": 195.0,
    "sumperk": 195.0,
    "jesenik": 175.0,

    # Zlín Region (Zlínský kraj)
    "zlinsky": 235.0,
    "kromeriz": 215.0,
    "uherske hradiste": 240.0,
    "vsetin": 205.0,

    # Vysočina Region
    "vysocina": 225.0,
    "trebic": 210.0,
    "havlickuv brod": 215.0,
    "pelhrimov": 220.0,
    "zdar nad sazavou": 220.0,

    # South Bohemian Region (Jihočeský kraj)
    "jihocesky": 245.0,
    "tabor": 230.0,
    "pisek": 235.0,
    "strakonice": 210.0,
    "jindrichuv hradec": 215.0,
    "cesky krumlov": 240.0,
    "prachatice": 200.0,

    # Plzeň Region (Plzeňský kraj)
    "plzensky": 255.0,
    "klatovy": 220.0,
    "rokycany": 235.0,
    "domazlice": 215.0,
    "tachov": 205.0,

    # Karlovy Vary Region (Karlovarský kraj)
    "karlovarsky": 205.0,
    "cheb": 210.0,
    "sokolov": 185.0,

    # Ústí nad Labem Region (Ústecký kraj)
    "ustecky": 190.0,
    "teplice": 210.0,
    "most": 180.0,
    "chomutov": 185.0,
    "decin": 185.0,
    "litomerice": 225.0,
    "louny": 195.0,

    # Liberec Region (Liberecký kraj)
    "liberecky": 235.0,
    "jablonec nad nisou": 220.0,
    "ceska lipa": 210.0,
    "semily": 200.0,
    "turnov": 240.0,

    # Hradec Králové Region (Královéhradecký kraj)
    "kralovehradecky": 250.0,
    "trutnov": 215.0,
    "nachod": 210.0,
    "jicin": 230.0,
    "rychnov nad kneznou": 225.0,

    # Pardubice Region (Pardubický kraj)
    "pardubicky": 245.0,
    "chrudim": 230.0,
    "svitavy": 210.0,
    "usti nad orlici": 215.0,
}

NATIONAL_AVERAGE_RENT_PER_M2_MONTH = 260.0

DISPOSITION_RENT_MULTIPLIERS: Dict[str, float] = {
    "1+kk": 1.15,
    "1+1": 1.12,
    "2+kk": 1.00,
    "2+1": 0.98,
    "3+kk": 0.90,
    "3+1": 0.88,
    "4+kk": 0.82,
    "4+1": 0.80,
    "5+kk": 0.78,
    "5+1": 0.76,
    "6+": 0.75,
    "atypicky": 1.00,
    "jiny": 1.00,
}


def get_rental_benchmark_per_m2(location: str, disposition: str = "2+kk") -> float:
    """Find the estimated monthly rental rate (CZK/m²/month) for a given location and disposition."""
    norm_loc = normalize_string(location)
    base_rent_m2 = NATIONAL_AVERAGE_RENT_PER_M2_MONTH

    # 1. Direct match
    if norm_loc in RENTAL_BENCHMARKS_M2_MONTH:
        base_rent_m2 = RENTAL_BENCHMARKS_M2_MONTH[norm_loc]
    else:
        # 2. Check sorted keys (longest first)
        sorted_keys = sorted(RENTAL_BENCHMARKS_M2_MONTH.keys(), key=lambda k: len(k), reverse=True)
        matched = False
        for key in sorted_keys:
            if key in norm_loc:
                base_rent_m2 = RENTAL_BENCHMARKS_M2_MONTH[key]
                matched = True
                break

        if not matched:
            words = norm_loc.split()
            for word in words:
                if word in RENTAL_BENCHMARKS_M2_MONTH:
                    base_rent_m2 = RENTAL_BENCHMARKS_M2_MONTH[word]
                    break

    # 3. Apply disposition multiplier
    norm_disp = normalize_disposition(disposition)
    multiplier = DISPOSITION_RENT_MULTIPLIERS.get(norm_disp, 1.00)

    return round(base_rent_m2 * multiplier, 1)


def normalize_disposition(disp_text: str) -> str:
    """Normalize dispositions like '2+kk', '2+1', 'GARSONIERA', '1+kk'."""
    if not disp_text:
        return "atypicky"
    disp = disp_text.lower().strip()
    
    # Look for patterns like 1+kk, 2+1, 3+kk, 4+1, 5+kk, etc.
    match = re.search(r'([1-6])\s*(\+|\/)\s*(kk|1)', disp)
    if match:
        num = match.group(1)
        suffix = match.group(3)
        return f"{num}+{suffix}"
        
    if "garson" in disp or "1+0" in disp or "garsoniera" in disp or "garsonka" in disp:
        return "1+kk"
    if "atyp" in disp:
        return "atypicky"
    if "pokoj" in disp:
        return "1+kk"
        
    return "jiny"
