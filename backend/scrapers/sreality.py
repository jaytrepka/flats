import re
import json
import logging
from typing import List, Optional
import httpx

from .base import BaseScraper
from ..models import SearchCriteria, FlatListing
from ..benchmarks import normalize_string, normalize_disposition

logger = logging.getLogger(__name__)


class SrealityScraper(BaseScraper):
    portal_name = "sreality"
    BASE_URL = "https://www.sreality.cz"

    DISPOSITION_MAP = {
        "1+kk": "1-kk",
        "1+1": "1-1",
        "2+kk": "2-kk",
        "2+1": "2-1",
        "3+kk": "3-kk",
        "3+1": "3-1",
        "4+kk": "4-kk",
        "4+1": "4-1",
        "5+kk": "5-kk",
        "5+1": "5-1",
        "6+": "6-a-vice",
        "atypicky": "atypicky",
    }

    async def search(self, criteria: SearchCriteria) -> List[FlatListing]:
        listings: List[FlatListing] = []
        
        # Build search URL
        loc_slug = normalize_string(criteria.location).replace(" ", "-")
        if not loc_slug:
            loc_slug = "ceska-republika"

        url = f"{self.BASE_URL}/hledani/prodej/byty/{loc_slug}"
        params = {}

        # Dispositions
        if criteria.dispositions:
            disp_slugs = []
            for d in criteria.dispositions:
                norm_d = normalize_disposition(d)
                if norm_d in self.DISPOSITION_MAP:
                    disp_slugs.append(self.DISPOSITION_MAP[norm_d])
                elif d.lower() in self.DISPOSITION_MAP:
                    disp_slugs.append(self.DISPOSITION_MAP[d.lower()])
            if disp_slugs:
                params["velikost"] = ",".join(disp_slugs)

        if criteria.min_price:
            params["cena-od"] = str(criteria.min_price)
        if criteria.max_price:
            params["cena-do"] = str(criteria.max_price)
        if criteria.min_area:
            params["plocha-od"] = str(criteria.min_area)
        if criteria.max_area:
            params["plocha-do"] = str(criteria.max_area)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Sreality returned HTTP {resp.status_code} for {resp.url}")
                    return []

                html = resp.text
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
                if not match:
                    logger.warning("Sreality: __NEXT_DATA__ script tag not found")
                    return []

                data = json.loads(match.group(1))
                page_props = data.get("props", {}).get("pageProps", {})
                queries = page_props.get("dehydratedState", {}).get("queries", [])

                for q in queries:
                    q_key = q.get("queryKey", [])
                    if q_key and q_key[0] == "estatesSearch":
                        results = q.get("state", {}).get("data", {}).get("results", [])
                        for item in results:
                            flat = self._parse_item(item)
                            if flat:
                                listings.append(flat)
                        break

        except Exception as e:
            logger.error(f"Error scraping Sreality: {e}", exc_info=True)

        return listings

    def _parse_item(self, item: dict) -> Optional[FlatListing]:
        try:
            estate_id = str(item.get("id", ""))
            if not estate_id:
                return None

            name = item.get("name", "Byt na prodej")
            price = float(item.get("priceCzk") or item.get("priceSummaryCzk") or 0)
            if price <= 300000:  # Skip unrealistic / auction deposits
                return None

            price_per_m2 = float(item.get("priceCzkPerSqM") or 0)

            # Area in m2
            area_m2 = 0.0
            if price_per_m2 > 0 and price > 0:
                area_m2 = round(price / price_per_m2, 1)
            else:
                match = re.search(r'(\d+[\.,]?\d*)\s*m²', name)
                if match:
                    area_m2 = float(match.group(1).replace(",", "."))
                if area_m2 > 0 and price > 0:
                    price_per_m2 = round(price / area_m2, 0)

            if area_m2 < 12 or area_m2 > 800:
                return None

            # Disposition
            raw_disp = item.get("categorySubCb", {}).get("name", "")
            disp = normalize_disposition(raw_disp or name)

            # Locality
            loc_data = item.get("locality", {})
            city = loc_data.get("city") or loc_data.get("cityPart") or "Česká republika"
            city_part = loc_data.get("cityPart")
            district = loc_data.get("district")
            region = loc_data.get("region")
            street = loc_data.get("street")

            locality_parts = [p for p in [street, city_part, city, district] if p]
            locality_str = ", ".join(dict.fromkeys(locality_parts))

            # Images
            images = []
            for img in item.get("images", []):
                u = img.get("url", "")
                if u:
                    if u.startswith("//"):
                        u = "https:" + u
                    images.append(u)
            
            main_image = images[0] if images else None

            # Detail URL construction
            city_seo = loc_data.get("citySeoName") or "praha"
            city_part_seo = loc_data.get("cityPartSeoName") or city_seo
            disp_seo = disp.replace("+", "-")
            url = f"{self.BASE_URL}/detail/prodej/byt/{disp_seo}/{city_seo}/{city_part_seo}/{estate_id}"

            return FlatListing(
                id=f"sreality_{estate_id}",
                title=name,
                portal=self.portal_name,
                url=url,
                image_url=main_image,
                additional_images=images[1:6],
                locality=locality_str,
                city=city,
                district=district,
                region=region,
                disposition=disp,
                area_m2=area_m2,
                price_czk=price,
                price_per_m2=price_per_m2,
                latitude=loc_data.get("latitude"),
                longitude=loc_data.get("longitude"),
                extra_details={
                    "hasMatterport": item.get("hasMatterport", False),
                    "hasVideo": item.get("hasVideo", False),
                    "premiseLogo": item.get("premiseLogo"),
                }
            )
        except Exception as e:
            logger.debug(f"Failed to parse Sreality item: {e}")
            return None
