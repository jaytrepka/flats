import asyncio
import io
import csv
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from .models import SearchCriteria, SearchResponse, FlatListing
from .benchmarks import REGIONAL_BENCHMARKS, get_benchmark_price_per_m2
from .pricing_engine import calculate_pricing_and_filter
from .scrapers import SrealityScraper, BezrealitkyScraper, RemaxScraper, BazosScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flats_app")

app = FastAPI(
    title="Czech Real Estate Bargain Finder",
    description="Find flats below average market price across major Czech portals (Sreality, Bezrealitky, Remax, Bazos)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registry of active scrapers
SCRAPERS = {
    "sreality": SrealityScraper(),
    "bezrealitky": BezrealitkyScraper(),
    "remax": RemaxScraper(),
    "bazos": BazosScraper(),
}

ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "public"
FRONTEND_DIR = ROOT_DIR / "frontend"
STATIC_DIR = PUBLIC_DIR if PUBLIC_DIR.exists() else FRONTEND_DIR


async def run_scraper_safe(scraper, criteria: SearchCriteria) -> List[FlatListing]:
    """Execute scraper with strict timeout so slow portals don't block the search."""
    try:
        return await asyncio.wait_for(scraper.search(criteria), timeout=8.0)
    except asyncio.TimeoutError:
        logger.warning(f"Scraper '{scraper.portal_name}' timed out after 8s")
        return []
    except Exception as e:
        logger.error(f"Scraper '{scraper.portal_name}' error: {e}")
        return []


@app.post("/api/search", response_model=SearchResponse)
async def search_flats(criteria: SearchCriteria) -> SearchResponse:
    """Execute concurrent search across all selected Czech real estate portals and locations."""
    loc_list = criteria.locations if (criteria.locations and len(criteria.locations) > 0) else [criteria.location]
    loc_list = [l.strip() for l in loc_list if l and l.strip()]
    if not loc_list:
        loc_list = ["Praha"]

    logger.info(f"Received search request for locations={loc_list}, dispositions={criteria.dispositions}, portals={criteria.portals}")
    
    selected_scrapers = []
    for p in criteria.portals:
        p_lower = p.lower()
        if p_lower in SCRAPERS:
            selected_scrapers.append(SCRAPERS[p_lower])

    if not selected_scrapers:
        selected_scrapers = list(SCRAPERS.values())

    # Execute all scraper tasks for all locations concurrently with timeout guard
    tasks = []
    for loc in loc_list:
        loc_criteria = criteria.model_copy(update={"location": loc})
        for scraper in selected_scrapers:
            tasks.append(run_scraper_safe(scraper, loc_criteria))

    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_listings: List[FlatListing] = []
    seen_ids = set()
    for res in results_nested:
        if isinstance(res, list):
            for flat in res:
                if flat.id not in seen_ids and flat.url not in seen_ids:
                    seen_ids.add(flat.id)
                    seen_ids.add(flat.url)
                    all_listings.append(flat)

    # Process pricing and apply bargain filtering
    response = calculate_pricing_and_filter(all_listings, criteria)
    if len(loc_list) > 1:
        response.stats.locality_name = ", ".join(loc_list[:3]) + (f" (+{len(loc_list)-3})" if len(loc_list) > 3 else "")
    logger.info(f"Found {len(response.listings)} matching bargain flats out of {response.stats.total_scanned} scanned")
    return response


@app.get("/api/benchmarks")
async def get_benchmarks():
    """Return regional price baseline dataset and popular city recommendations."""
    popular_cities = [
        {"name": "Praha", "avg_m2": 158000, "region": "Praha"},
        {"name": "Brno", "avg_m2": 128000, "region": "Jihomoravský"},
        {"name": "Plzeň", "avg_m2": 84000, "region": "Plzeňský"},
        {"name": "Olomouc", "avg_m2": 82000, "region": "Olomoucký"},
        {"name": "Hradec Králové", "avg_m2": 86000, "region": "Královéhradecký"},
        {"name": "Pardubice", "avg_m2": 79000, "region": "Pardubický"},
        {"name": "České Budějovice", "avg_m2": 81000, "region": "Jihočeský"},
        {"name": "Liberec", "avg_m2": 74000, "region": "Liberecký"},
        {"name": "Ostrava", "avg_m2": 52000, "region": "Moravskoslezský"},
        {"name": "Kladno", "avg_m2": 78000, "region": "Středočeský"},
        {"name": "Zlín", "avg_m2": 76000, "region": "Zlínský"},
        {"name": "Ústí nad Labem", "avg_m2": 42000, "region": "Ústecký"},
    ]
    return {
        "benchmarks": REGIONAL_BENCHMARKS,
        "popular_cities": popular_cities,
    }


@app.post("/api/export/csv")
async def export_csv(criteria: SearchCriteria):
    """Export search results to CSV format."""
    resp = await search_flats(criteria)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID", "Název", "Portál", "Dispozice", "Plocha (m²)", "Cena (Kč)",
        "Cena za m² (Kč/m²)", "Tržní průměr m² (Kč/m²)", "Očekávaná cena (Kč)",
        "Úspora (Kč)", "Sleva (%)", "Lokalita", "Odkaz"
    ])
    
    for item in resp.listings:
        writer.writerow([
            item.id,
            item.title,
            item.portal.upper(),
            item.disposition,
            item.area_m2,
            item.price_czk,
            item.price_per_m2,
            item.market_avg_price_per_m2,
            item.expected_price_czk,
            item.difference_czk,
            item.discount_percentage,
            item.locality,
            item.url
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=vyhodne_byty_{criteria.location}.csv"}
    )


# Serve frontend static assets locally
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(STATIC_DIR / "index.html"))

    @app.get("/app.js")
    async def serve_app_js():
        return FileResponse(str(STATIC_DIR / "app.js"))

    @app.get("/style.css")
    async def serve_style_css():
        return FileResponse(str(STATIC_DIR / "style.css"))
