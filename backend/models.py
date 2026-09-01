from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    location: str = Field(default="Praha", description="Primary location name, e.g., 'Praha'")
    locations: Optional[List[str]] = Field(default=None, description="List of multiple selected locations/regions, e.g. ['Praha', 'Brno', 'Středočeský kraj']")
    dispositions: List[str] = Field(default_factory=lambda: ["1+kk", "2+kk", "3+kk"], description="Dispositions to search for")
    min_price: Optional[int] = Field(default=None, description="Minimum total price in CZK")
    max_price: Optional[int] = Field(default=None, description="Maximum total price in CZK")
    min_area: Optional[int] = Field(default=None, description="Minimum floor area in m2")
    max_area: Optional[int] = Field(default=None, description="Maximum floor area in m2")
    portals: List[str] = Field(default_factory=lambda: ["sreality", "bezrealitky", "remax", "bazos"], description="Portals to scrape")
    only_below_average: bool = Field(default=True, description="Filter to show only below-average priced flats")
    min_discount_percent: float = Field(default=0.0, description="Minimum discount percentage vs market average (e.g. 5 for 5%)")
    custom_benchmark_czk_m2: Optional[float] = Field(default=None, description="Optional manual override for average CZK/m2")

    # Smart real-price evaluation & caveat filters
    include_annuity_in_price: bool = Field(default=True, description="Automatically detect unpaid annuity (anuita) and add to total price")
    filter_partial_shares: bool = Field(default=True, description="Filter out fractional share listings (1/2, 1/4 apod.)")
    filter_auctions: bool = Field(default=True, description="Filter out auction and execution starting bids (dražby)")

    sort_by: str = Field(default="discount_desc", description="Sort order: discount_desc, savings_desc, price_m2_asc, price_asc, newest")
    limit: int = Field(default=150, description="Maximum number of listings to return")


class FlatListing(BaseModel):
    id: str
    title: str
    portal: str  # sreality, bezrealitky, remax, bazos
    url: str
    image_url: Optional[str] = None
    additional_images: List[str] = Field(default_factory=list)
    locality: str
    city: str
    district: Optional[str] = None
    region: Optional[str] = None
    disposition: str  # 1+kk, 2+1, etc.
    area_m2: float
    price_czk: float
    price_per_m2: float
    
    # Annuity & Caveat metadata
    advertised_price_czk: Optional[float] = None
    unpaid_annuity_czk: float = 0.0
    caveat_flags: List[str] = Field(default_factory=list)
    is_partial_share: bool = False
    is_auction: bool = False

    # Calculated metrics vs market
    market_avg_price_per_m2: float = 0.0
    expected_price_czk: float = 0.0
    difference_czk: float = 0.0  # Positive = saved CZK (bargain), Negative = over market
    discount_percentage: float = 0.0  # Positive = discount %, Negative = premium %
    is_bargain: bool = False
    bargain_tier: str = "FAIR_DEAL"  # SUPER_BARGAIN, GOOD_DEAL, FAIR_DEAL, ABOVE_MARKET
    
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    extra_details: Dict[str, Any] = Field(default_factory=dict)


class PriceStats(BaseModel):
    locality_name: str
    total_scanned: int
    total_bargains: int
    average_price_per_m2: float
    median_price_per_m2: float
    min_price_per_m2: float
    max_price_per_m2: float
    max_savings_czk: float
    benchmark_source: str
    disposition_averages: Dict[str, float] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    stats: PriceStats
    listings: List[FlatListing]
    criteria: SearchCriteria
    portal_counts: Dict[str, int] = Field(default_factory=dict)
