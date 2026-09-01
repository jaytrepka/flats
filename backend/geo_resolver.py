"""
Comprehensive Czech Geography & Region Resolver.
Provides accurate spatial matching and region resolution for all 14 Kraje of the Czech Republic,
preventing cross-region contamination (e.g. Karlovarský, Ústecký, or Moravskoslezský flats appearing in Středočeský kraj).
"""

import unicodedata
import re
from typing import Dict, List, Optional, Set, Any


def normalize_name(text: str) -> str:
    """Normalize text by stripping diacritics, lowercase, removing special punctuation."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


CZECH_REGIONS_DATA: Dict[str, Dict[str, Any]] = {
    "praha": {
        "name": "Hlavní město Praha",
        "short": "Praha",
        "slug": "praha",
        "sreality_slug": "praha",
        "bezrealitky_slug": "praha",
        "keywords": ["praha", "prague", "hlavni mesto praha"],
        "districts": [
            "praha 1", "praha 2", "praha 3", "praha 4", "praha 5", "praha 6",
            "praha 7", "praha 8", "praha 9", "praha 10", "praha 11", "praha 12",
            "praha 13", "praha 14", "praha 15", "praha 16", "praha 17", "praha 18",
            "praha 19", "praha 20", "praha 21", "praha 22"
        ],
        "cities": [
            "vinohrady", "zizkov", "smichov", "dejvice", "nusle", "karlin", "vrsovice",
            "holesovice", "liben", "branik", "modrany", "stodulky", "chodov", "vysocany",
            "libus", "prosek", "kobylisy", "hlubocepy", "jinonice", "brevnov", "repy",
            "letnany", "cakovice", "troja", "stresovice", "kosire", "radlice", "radotin",
            "zbraslav", "uhrineves", "krc", "michle", "malesice", "strasnice", "hostivar",
            "zabehlice", "cerny most", "kyje", "sterboholy", "hrdlorezy", "vokovice",
            "bubenec", "josefov", "stare mesto", "nove mesto", "mala strana", "hradcany"
        ],
    },
    "stredocesky": {
        "name": "Středočeský kraj",
        "short": "Středočeský",
        "slug": "stredocesky-kraj",
        "sreality_slug": "stredocesky-kraj",
        "bezrealitky_slug": "stredocesky-kraj",
        "keywords": ["stredocesky", "stredocesky kraj", "stredni cechy", "central bohemia"],
        "districts": [
            "benesov", "beroun", "kladno", "kolin", "kutna hora", "melnik",
            "mlada boleslav", "nymburk", "praha vychod", "praha zapad", "pribram", "rakovnik"
        ],
        "cities": [
            "kladno", "mlada boleslav", "pribram", "kolin", "kutna hora", "beroun",
            "melnik", "brandys nad labem", "stara boleslav", "kralupy nad vltavou",
            "benesov", "nymburk", "podebrady", "ricany", "celakovice", "slany",
            "neratovice", "rakovnik", "lysa nad labem", "milovice", "mnichovo hradiste",
            "dobris", "vlasim", "sedlcany", "roztoky", "jesenice", "hostivice",
            "caslav", "unhost", "uvaly", "horomerice", "pruhonice", "cernosice",
            "dobrichovice", "revnice", "mnisek pod brdy", "sadska", "pecky",
            "veltrusy", "zdiby", "klecany", "odolena voda", "kostelec nad cernymi lesy",
            "cesky brod", "tynec nad sazavou", "votice", "neveklov", "bystrice",
            "kosmonosy", "bakov nad jizerou", "bela pod bezdezem", "benatky nad jizerou",
            "zasmuky", "kourim", "uhlirske janovice", "zruc nad sazavou", "zebrak",
            "horovice", "kraluv dvur", "zdice", "zlonice", "stochov", "libusin",
            "bustehrad", "nove straseci", "rozmital pod tremsinem", "breznice",
            "vsetaty", "hostoun", "kostelec nad labem", "kropacova vrutice", "stribrna skalice",
            "davle", "stepanov", "zelivec", "lochovice", "lany", "jilove u prahy"
        ],
    },
    "jihocesky": {
        "name": "Jihočeský kraj",
        "short": "Jihočeský",
        "slug": "jihocesky-kraj",
        "sreality_slug": "jihocesky-kraj",
        "bezrealitky_slug": "jihocesky-kraj",
        "keywords": ["jihocesky", "jihocesky kraj", "jizni cechy"],
        "districts": [
            "ceske budejovice", "cesky krumlov", "jindrichuv hradec", "pisek",
            "prachatice", "strakonice", "tabor"
        ],
        "cities": [
            "ceske budejovice", "tabor", "pisek", "strakonice", "jindrichuv hradec",
            "cesky krumlov", "prachatice", "milevsko", "trebon", "tyn nad vltavou",
            "vimperk", "dacice", "kaplice", "sobeslav", "sezimovo usti", "vodnany",
            "hluboka nad vltavou", "blatna", "veseli nad luznici", "trhove sviny",
            "lisov", "netolice", "protivin", "volary", "chvalsiny", "suchdol nad luznici"
        ],
    },
    "plzensky": {
        "name": "Plzeňský kraj",
        "short": "Plzeňský",
        "slug": "plzensky-kraj",
        "sreality_slug": "plzensky-kraj",
        "bezrealitky_slug": "plzensky-kraj",
        "keywords": ["plzensky", "plzensky kraj", "zapadni cechy"],
        "districts": [
            "domazlice", "klatovy", "plzen mesto", "plzen jih", "plzen sever",
            "rokycany", "tachov"
        ],
        "cities": [
            "plzen", "klatovy", "rokycany", "tachov", "domazlice", "susice",
            "stribro", "prestice", "nyrany", "holysov", "dobrany", "horazdovice",
            "kdyne", "horsovsky tyn", "plana", "kralovice", "kaznejov", "nepomuk",
            "tremosna", "zbiroh", "spalene porici", "blovice", "nyrsko", "zelezna ruda"
        ],
    },
    "karlovarsky": {
        "name": "Karlovarský kraj",
        "short": "Karlovarský",
        "slug": "karlovarsky-kraj",
        "sreality_slug": "karlovarsky-kraj",
        "bezrealitky_slug": "karlovarsky-kraj",
        "keywords": ["karlovarsky", "karlovarsky kraj"],
        "districts": ["cheb", "karlovy vary", "sokolov"],
        "cities": [
            "karlovy vary", "cheb", "sokolov", "ostrov", "as", "chodov",
            "marianske lazne", "nejdek", "kraslice", "frantiskovy lazne", "habartov",
            "kynsperk nad ohri", "horni slavkov", "loket", "jachymov", "zlutice",
            "bochov", "hroznetin", "touzim", "nova role", "rotava", "luby",
            "skalna", "plesna", "abertamy", "bozi dar", "brezova"
        ],
    },
    "ustecky": {
        "name": "Ústecký kraj",
        "short": "Ústecký",
        "slug": "ustecky-kraj",
        "sreality_slug": "ustecky-kraj",
        "bezrealitky_slug": "ustecky-kraj",
        "keywords": ["ustecky", "ustecky kraj", "severni cechy"],
        "districts": ["decin", "chomutov", "litomerice", "louny", "most", "teplice", "usti nad labem"],
        "cities": [
            "usti nad labem", "most", "teplice", "decin", "chomutov", "litomerice",
            "litvinov", "jirkov", "zatec", "louny", "kadan", "varnsdorf",
            "klasterec nad ohri", "bilina", "roudnice nad labem", "rumburk", "krupka",
            "lovosice", "steti", "duchcov", "dubi", "podborany", "sluknov",
            "jilove", "postoloprty", "ceska kamenice", "libochovice", "terezin",
            "trmice", "chabarovice", "mezibori", "vejprty"
        ],
    },
    "liberecky": {
        "name": "Liberecký kraj",
        "short": "Liberecký",
        "slug": "liberecky-kraj",
        "sreality_slug": "liberecky-kraj",
        "bezrealitky_slug": "liberecky-kraj",
        "keywords": ["liberecky", "liberecky kraj"],
        "districts": ["ceska lipa", "jablonec nad nisou", "liberec", "semily"],
        "cities": [
            "liberec", "jablonec nad nisou", "ceska lipa", "turnov", "novy bor",
            "semily", "hradek nad nisou", "frydlant", "zelezny brod", "mimon",
            "tanvald", "chrastava", "lomnice nad popelkou", "jilemnice", "doksy",
            "cvikov", "straz pod ralskem", "rokytnice nad jizerou", "raspenava",
            "hejnice", "velke hamry", "smrzovka", "desna", "lucany nad nisou",
            "hodkovice nad mohelkou", "cesky dub", "zakupy", "jablonne v podjestedi", "harrachov"
        ],
    },
    "kralovehradecky": {
        "name": "Královéhradecký kraj",
        "short": "Královéhradecký",
        "slug": "kralovehradecky-kraj",
        "sreality_slug": "kralovehradecky-kraj",
        "bezrealitky_slug": "kralovehradecky-kraj",
        "keywords": ["kralovehradecky", "kralovehradecky kraj", "vychodni cechy"],
        "districts": ["hradec kralove", "jicin", "nachod", "rychnov nad kneznou", "trutnov"],
        "cities": [
            "hradec kralove", "trutnov", "nachod", "jicin", "dvur kralove nad labem",
            "vrchlabi", "jaromer", "rychnov nad kneznou", "nove mesto nad metuji",
            "novy bydzov", "horice", "dobruska", "broumov", "kostelec nad orlici",
            "cerveny kostelec", "tyniste nad orlici", "hronov", "chlumec nad cidlinou",
            "trebechovice pod orebem", "upice", "ceska skalice", "opocno", "vamberk",
            "smirice", "nechanice", "zacler", "hostinne", "sobotka", "nova paka",
            "lazne belohrad", "police nad metuji", "rokytnice v orlickych horach",
            "pec pod snezkou", "spindleruv mlyn", "janske lazne"
        ],
    },
    "pardubicky": {
        "name": "Pardubický kraj",
        "short": "Pardubický",
        "slug": "pardubicky-kraj",
        "sreality_slug": "pardubicky-kraj",
        "bezrealitky_slug": "pardubicky-kraj",
        "keywords": ["pardubicky", "pardubicky kraj"],
        "districts": ["chrudim", "pardubice", "svitavy", "usti nad orlici"],
        "cities": [
            "pardubice", "chrudim", "svitavy", "ceska trebova", "usti nad orlici",
            "vysoke myto", "litomysl", "moravska trebova", "lanskroun", "hlinsko",
            "prelouc", "policka", "chocen", "holice", "letohrad", "zamberk",
            "skutec", "hermanuv mestec", "slatinany", "kraliky", "jablonne nad orlici"
        ],
    },
    "vysocina": {
        "name": "Kraj Vysočina",
        "short": "Vysočina",
        "slug": "kraj-vysocina",
        "sreality_slug": "kraj-vysocina",
        "bezrealitky_slug": "kraj-vysocina",
        "keywords": ["vysocina", "kraj vysocina"],
        "districts": ["havlickuv brod", "jihlava", "pelhrimov", "trebic", "zdar nad sazavou"],
        "cities": [
            "jihlava", "trebic", "havlickuv brod", "zdar nad sazavou", "pelhrimov",
            "velke mezirici", "humpolec", "nove mesto na morave", "chotebor",
            "bystrice nad pernstejnem", "moravske budejovice", "svetla nad sazavou",
            "trest", "ledec nad sazavou", "telc", "namest nad oslavou", "pacov",
            "polna", "jaromerice nad rokytnou", "jemnice", "pribyslav", "brtnice",
            "zirovnice", "pocatky"
        ],
    },
    "jihomoravsky": {
        "name": "Jihomoravský kraj",
        "short": "Jihomoravský",
        "slug": "jihomoravsky-kraj",
        "sreality_slug": "jihomoravsky-kraj",
        "bezrealitky_slug": "jihomoravsky-kraj",
        "keywords": ["jihomoravsky", "jihomoravsky kraj", "jizni morava"],
        "districts": [
            "blansko", "brno mesto", "brno venkov", "breclav", "hodonin", "vyskov", "znojmo", "brno"
        ],
        "cities": [
            "brno", "znojmo", "hodonin", "breclav", "vyskov", "blansko", "kyjov",
            "boskovice", "kurim", "ivancice", "tisnov", "slavkov u brna", "mikulov",
            "bucovice", "rosice", "hustopece", "moravsky krumlov", "slapanice",
            "dubnany", "veseli nad moravou", "straznice", "pohorelice", "letovice",
            "rajhrad", "modrice", "velke bilovice", "valtice", "zidlochovice",
            "adamov", "zbysov", "rousinov", "jedovnice", "popice"
        ],
    },
    "olomoucky": {
        "name": "Olomoucký kraj",
        "short": "Olomoucký",
        "slug": "olomoucky-kraj",
        "sreality_slug": "olomoucky-kraj",
        "bezrealitky_slug": "olomoucky-kraj",
        "keywords": ["olomoucky", "olomoucky kraj", "stredni morava"],
        "districts": ["jesenik", "olomouc", "prostejov", "prerov", "sumperk"],
        "cities": [
            "olomouc", "prostejov", "prerov", "sumperk", "hranice", "zabreh",
            "sternberk", "jesenik", "unicov", "litovel", "mohelnice",
            "lipnik nad becvou", "kojetin", "zlate hory", "javornik", "hanusovice",
            "konice", "kostelec na hane", "plumlov", "tovacov", "nemcice nad hanou",
            "velka bystrice", "moravsky beroun"
        ],
    },
    "zlinsky": {
        "name": "Zlínský kraj",
        "short": "Zlínský",
        "slug": "zlinsky-kraj",
        "sreality_slug": "zlinsky-kraj",
        "bezrealitky_slug": "zlinsky-kraj",
        "keywords": ["zlinsky", "zlinsky kraj", "vychodni morava"],
        "districts": ["kromeriz", "uherske hradiste", "vsetin", "zlin"],
        "cities": [
            "zlin", "uherske hradiste", "kromeriz", "vsetin", "valasske mezirici",
            "otrokovice", "uhersky brod", "roznov pod radhostem", "holesov",
            "bystrice pod hostynem", "slavicin", "hulin", "stare mesto",
            "chropyne", "napajedla", "luhacovice", "brumov bylnice", "zubri",
            "frystak", "kunovice", "valasske klobouky", "bojkovice",
            "uhersky ostroh", "morkovice slizany", "korycany", "kelc"
        ],
    },
    "moravskoslezsky": {
        "name": "Moravskoslezský kraj",
        "short": "Moravskoslezský",
        "slug": "moravskoslezsky-kraj",
        "sreality_slug": "moravskoslezsky-kraj",
        "bezrealitky_slug": "moravskoslezsky-kraj",
        "keywords": ["moravskoslezsky", "moravskoslezsky kraj", "severni morava", "slezsko"],
        "districts": ["bruntal", "frydek mistek", "karvina", "novy jicin", "opava", "ostrava mesto", "ostrava"],
        "cities": [
            "ostrava", "havirov", "karvina", "frydek mistek", "opava", "trinec",
            "orlova", "cesky tesin", "krnov", "novy jicin", "koprivnice",
            "bohumin", "bruntal", "hlucin", "frenstat pod radhostem",
            "frydlant nad ostravici", "studenka", "rymarov", "pribor", "bilovec",
            "odry", "petrvald", "rychvald", "vratimov", "kravare", "vitkov",
            "jablunkov", "fulnek", "klimkovice", "bridlicna", "vrbno pod pradedem"
        ],
    },
}


def find_region_key(location_name: str) -> Optional[str]:
    """Check if location_name corresponds to any of the 14 Czech Kraje."""
    if not location_name:
        return None
    norm = normalize_name(location_name)
    for key, data in CZECH_REGIONS_DATA.items():
        if any(normalize_name(kw) == norm for kw in data["keywords"]) or norm == key:
            return key
        if normalize_name(data["name"]) == norm or normalize_name(data["short"]) == norm:
            return key
    return None


def get_region_slug(location_name: str) -> str:
    """Return canonical SEO slug for portals, e.g. 'stredocesky-kraj'."""
    reg_key = find_region_key(location_name)
    if reg_key:
        return CZECH_REGIONS_DATA[reg_key]["slug"]
    return normalize_name(location_name).replace(" ", "-")


def is_listing_in_target_location(
    target_location: str,
    listing_locality: str,
    listing_city: str = "",
    listing_region: str = "",
    listing_district: str = "",
    listing_title: str = "",
) -> bool:
    """
    Strictly verify whether a scraped listing belongs to the user-selected location.
    Eliminates cross-region contamination (e.g. Karlovarský or Ústecký flats in Středočeský kraj).
    """
    if not target_location or target_location.lower() in [
        "ceska republika", "cr", "čr", "cesko", "česko", "czech republic"
    ]:
        return True

    reg_key = find_region_key(target_location)
    combined_listing_text = f"{listing_locality} {listing_city} {listing_region} {listing_district} {listing_title}"
    norm_listing = normalize_name(combined_listing_text)
    padded_listing = f" {norm_listing} "

    # 1. Target is one of the 14 Kraje
    if reg_key:
        target_reg = CZECH_REGIONS_DATA[reg_key]

        # REJECT if the listing explicitly declares a DIFFERENT Kraj name or foreign country
        for other_key, other_reg in CZECH_REGIONS_DATA.items():
            if other_key != reg_key:
                for other_kw in other_reg["keywords"]:
                    norm_kw = normalize_name(other_kw)
                    # e.g. "karlovarsky kraj", "moravskoslezsky kraj", "ustecky kraj"
                    if f" {norm_kw} " in padded_listing:
                        return False

        # REJECT foreign locations
        if any(f" {foreign} " in padded_listing for foreign in ["slovensko", "germany", "nemecko", "berlin", "leipzig", "badensko", "zilinsky", "presovsky", "rakousko"]):
            return False

        # ACCEPT if listing matches target region name, districts, or cities
        match_candidates = (
            target_reg["keywords"]
            + target_reg.get("districts", [])
            + target_reg.get("cities", [])
        )
        for cand in match_candidates:
            norm_cand = normalize_name(cand)
            if f" {norm_cand} " in padded_listing or norm_listing.startswith(norm_cand) or norm_listing.endswith(norm_cand):
                return True

        return False

    # 2. Target is a specific city, district, or municipality (e.g. 'Kralupy nad Vltavou', 'Praha 4', 'Olomouc')
    norm_target = normalize_name(target_location)
    if f" {norm_target} " in padded_listing or norm_listing.startswith(norm_target) or norm_listing.endswith(norm_target):
        return True

    # Word-based containment for multi-word city names (e.g. 'Kralupy nad Vltavou' -> 'kralupy')
    target_words = [w for w in norm_target.split() if len(w) > 3 and w not in ["kraj", "okres", "mesto", "obec", "cast", "ulice"]]
    if target_words:
        return all(f" {w} " in padded_listing for w in target_words)

    return False
