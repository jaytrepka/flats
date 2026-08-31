# 🏠 Czech Real Estate Bargain Finder (BytyBargain)

Inteligentní aplikace a cenový srovnávač pro vyhledávání výhodných nabídek bytů na českém realitním trhu pod průměrnou tržní cenou za $m^2$.

---

## ⚡ Hlavní funkce

1. **Agregace z hlavních českých portálů:**
   - **Sreality.cz** (Největší český realitní portál, detailní parametry a $m^2$)
   - **Bezrealitky.cz** (Přímé nabídky od majitelů bez 3–5% provize RK)
   - **RE/MAX Czech** (Ověřené makléřské nabídky)
   - **Bazoš.cz Reality** (Soukromé inzeráty a rychlé prodeje)

2. **Výpočet průměrné ceny za $m^2$ a hledání výhodných nabídek:**
   - **Dynamický tržní průměr**: V reálném čase spočítá oříznutý průměr a medián ceny za $m^2$ pro hledanou lokalitu a dispozici.
   - **Regionální cenová mapa ČR**: Vestavěná benchmarková databáze pro všech 14 krajů a 76 okresů ČR.
   - **Výpočet úspory**:
     $$\text{Očekávaná tržní cena} = \text{Plocha } (m^2) \times \text{Průměrná cena za } m^2$$
     $$\text{Úspora (Kč)} = \text{Očekávaná tržní cena} - \text{Nabídková cena}$$
     $$\text{Sleva (\%)} = \frac{\text{Úspora}}{\text{Očekávaná tržní cena}} \times 100\%$$
   - **Filtrování**: Automatické zobrazení pouze těch nabídek, které jsou levnější než průměr (nebo s volitelnou minimální slevou např. 10%, 20%+).

3. **Interaktivní uživatelské rozhraní:**
   - Hledání dle lokality (Praha, Brno, Plzeň, Ostrava, Praha 4...) s rychlými tlačítky.
   - Výběr dispozic (1+kk, 1+1, 2+kk, 2+1, 3+kk, 3+1, 4+kk, 5+kk+).
   - Rozpětí celkové ceny (Kč) a plochy ($m^2$).
   - Posuvník minimální požadované slevy.
   - Možnost zadat vlastní cílovou cenu za $m^2$.
   - Zobrazení ve formě **karet s fotografiemi** nebo **přehledné srovnávací tabulky**.
   - Řazení dle největší slevy %, nejvíce ušetřených Kč, nejnižší ceny za $m^2$, nejnižší ceny celkem.
   - Přímé odkazy na původní inzerát na daném portálu.
   - **Export výsledků do CSV**.

---

## 🚀 Spuštění aplikace

### 1. Aktivace virtuálního prostředí a spuštění:
```bash
cd /Users/jtrepka/Documents/jay/flats
./venv/bin/python run.py
```

### 2. Otevření v prohlížeči:
Otevřete v internetovém prohlížeči adresu:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🏗️ Architektura projektu

```
flats/
├── backend/
│   ├── app.py              # FastAPI server, REST API, statické soubory
│   ├── models.py           # Pydantic datové modely (SearchCriteria, FlatListing, PriceStats)
│   ├── benchmarks.py       # Regionální cenová mapa ČR a normalizace
│   ├── pricing_engine.py   # Algoritmus výpočtu slev, tržních průměrů a úspor
│   └── scrapers/
│       ├── base.py         # Abstraktní třída BaseScraper
│       ├── sreality.py     # Scraper pro Sreality.cz
│       ├── bezrealitky.py  # Scraper pro Bezrealitky.cz
│       ├── remax.py        # Scraper pro Remax-czech.cz
│       └── bazos.py        # Scraper pro Bazoš Reality
├── frontend/
│   ├── index.html          # Responzivní HTML rozhraní s Tailwind CSS
│   ├── style.css           # Vlastní animace a badge
│   └── app.js              # Klientská logika, filtry, dynamické vykreslování
├── run.py                  # Jednoduchý spouštěcí skript
├── requirements.txt        # Python závislosti
└── README.md
```
