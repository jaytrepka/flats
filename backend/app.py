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

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.post("/api/search", response_model=SearchResponse)
async def search_flats(criteria: SearchCriteria) -> SearchResponse:
    """Execute concurrent search across all selected Czech real estate portals."""
    logger.info(f"Received search request for location='{criteria.location}', dispositions={criteria.dispositions}, portals={criteria.portals}")
    
    selected_scrapers = []
    for p in criteria.portals:
        p_lower = p.lower()
        if p_lower in SCRAPERS:
            selected_scrapers.append(SCRAPERS[p_lower])

    if not selected_scrapers:
        selected_scrapers = list(SCRAPERS.values())

    # Execute all scraper tasks concurrently
    tasks = [scraper.search(criteria) for scraper in selected_scrapers]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_listings: List[FlatListing] = []
    for idx, res in enumerate(results_nested):
        scraper_name = selected_scrapers[idx].portal_name
        if isinstance(res, Exception):
            logger.error(f"Scraper '{scraper_name}' failed with error: {res}")
        elif isinstance(res, list):
            logger.info(f"Scraper '{scraper_name}' returned {len(res)} listings")
            all_listings.extend(res)

    # Process pricing and apply bargain filtering
    response = calculate_pricing_and_filter(all_listings, criteria)
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
    # Perform search
    resp = await search_flats(criteria)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
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


# Serve frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
