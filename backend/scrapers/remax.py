import re
import logging
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..models import SearchCriteria, FlatListing
from ..benchmarks import normalize_string, normalize_disposition

logger = logging.getLogger(__name__)


class RemaxScraper(BaseScraper):
    portal_name = "remax"
    BASE_URL = "https://www.remax-czech.cz"

    # Remax subcategory mapping for flats: types[4][sub_id]=on
    DISP_MAP = {
        "1+kk": "1",
        "1+1": "2",
        "2+kk": "9",
        "2+1": "3",
        "3+kk": "10",
        "3+1": "4",
        "4+kk": "11",
        "4+1": "5",
        "5+kk": "12",
        "5+1": "6",
        "6+": "13",
        "atypicky": "16",
    }

    async def search(self, criteria: SearchCriteria) -> List[FlatListing]:
        listings: List[FlatListing] = []

        url = f"{self.BASE_URL}/reality/vyhledavani/"
        params: List[tuple] = [
            ("types[4]", "on"),  # Flats category
        ]

        if criteria.location:
            params.append(("text", criteria.location.strip()))

        # Dispositions
        if criteria.dispositions:
            for d in criteria.dispositions:
                norm_d = normalize_disposition(d)
                if norm_d in self.DISP_MAP:
                    params.append((f"types[4][{self.DISP_MAP[norm_d]}]", "on"))

        if criteria.min_price:
            params.append(("price_from", str(criteria.min_price)))
        if criteria.max_price:
            params.append(("price_to", str(criteria.max_price)))

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Remax returned HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.find_all("div", class_="pl-items__item")

                norm_search_loc = normalize_string(criteria.location)

                for item in items:
                    flat = self._parse_item(item, criteria.location, norm_search_loc)
                    if flat:
                        listings.append(flat)

        except Exception as e:
            logger.error(f"Error scraping Remax: {e}", exc_info=True)

        return listings

    def _parse_item(self, item, fallback_location: str, norm_search_loc: str) -> Optional[FlatListing]:
        try:
            title = item.get("data-title", "").strip()
            if not title or "pronájem" in title.lower():
                return None  # We only want sales (prodej)

            url_suffix = item.get("data-url", "")
            if not url_suffix:
                return None

            # ID
            id_match = re.search(r'/detail/(\d+)/', url_suffix)
            estate_id = id_match.group(1) if id_match else url_suffix.replace("/", "_")

            # Price
            raw_price = item.get("data-price", "")
            # Filter out "za měsíc" (rentals)
            if "měsíc" in raw_price.lower():
                return None
            price_digits = re.sub(r'[^\d]', '', raw_price.split("<")[0])
            if not price_digits:
                return None
            price = float(price_digits)
            if price <= 300000:
                return None

            # Area from title: e.g. "Prodej bytu 2+kk v osobním vlastnictví 52 m²"
            area_m2 = 0.0
            area_match = re.search(r'(\d+[\.,]?\d*)\s*m²', title)
            if area_match:
                area_m2 = float(area_match.group(1).replace(",", "."))

            if area_m2 < 12 or area_m2 > 800:
                return None

            price_per_m2 = round(price / area_m2, 0)
            if price_per_m2 < 12000 or price_per_m2 > 500000:
                return None

            # Address / Locality
            display_addr = item.get("data-display-address", "").strip()
            if display_addr:
                display_addr = re.sub(r'\s+', ' ', display_addr)
            
            locality = display_addr or fallback_location
            
            # City extraction
            city = fallback_location or "Česká republika"
            if display_addr:
                parts = [p.strip() for p in display_addr.split(",") if p.strip()]
                if parts:
                    city = parts[0].split("-")[0].strip()

            # Locality filter: verify searched city is in title or address
            if norm_search_loc and norm_search_loc not in ["ceska republika", "cr", "cesko"]:
                norm_full = normalize_string(f"{title} {display_addr} {url_suffix}")
                search_words = [w for w in norm_search_loc.split() if len(w) > 2]
                if search_words and not any(w in norm_full for w in search_words):
                    return None

            # Disposition
            disp = normalize_disposition(title)

            # Image
            img_url = item.get("data-img", "")
            if img_url and not img_url.startswith("http"):
                img_url = "https:" + img_url

            # GPS
            raw_gps = item.get("data-gps", "")
            lat, lng = None, None
            if raw_gps:
                gps_match = re.search(r'([\d\.]+).*?N.*?([\d\.]+).*?E', raw_gps)
                if gps_match:
                    try:
                        lat = float(gps_match.group(1))
                        lng = float(gps_match.group(2))
                    except ValueError:
                        pass

            full_url = f"{self.BASE_URL}{url_suffix}" if url_suffix.startswith("/") else url_suffix

            return FlatListing(
                id=f"remax_{estate_id}",
                title=title,
                portal=self.portal_name,
                url=full_url,
                image_url=img_url,
                additional_images=[],
                locality=locality,
                city=city,
                disposition=disp,
                area_m2=area_m2,
                price_czk=price,
                price_per_m2=price_per_m2,
                latitude=lat,
                longitude=lng,
                extra_details={
                    "agency": "RE/MAX Czech Republic",
                }
            )
        except Exception as e:
            logger.debug(f"Failed to parse Remax item: {e}")
            return None
