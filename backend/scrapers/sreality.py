import re
import json
import asyncio
import logging
from typing import List, Optional
import httpx

from .base import BaseScraper
from ..models import SearchCriteria, FlatListing
from ..benchmarks import normalize_string, normalize_disposition
from ..geo_resolver import is_listing_in_target_location, find_region_key, get_region_slug

logger = logging.getLogger(__name__)


class SrealityScraper(BaseScraper):
    portal_name = "sreality"
    BASE_URL = "https://www.sreality.cz"

    DISPOSITION_MAP = {
        "1+kk": "1+kk",
        "1+1": "1+1",
        "2+kk": "2+kk",
        "2+1": "2+1",
        "3+kk": "3+kk",
        "3+1": "3+1",
        "4+kk": "4+kk",
        "4+1": "4+1",
        "5+kk": "5+kk",
        "5+1": "5+1",
        "6+": "6-a-vice",
        "atypicky": "atypicky",
    }

    async def search(self, criteria: SearchCriteria) -> List[FlatListing]:
        listings: List[FlatListing] = []
        
        # Build search URL: use region slug for Kraje (e.g. /hledani/prodej/byty/stredocesky-kraj)
        # or region parameter for specific cities
        params = {}
        is_reg = find_region_key(criteria.location) is not None
        if is_reg:
            reg_slug = get_region_slug(criteria.location)
            url = f"{self.BASE_URL}/hledani/prodej/byty/{reg_slug}"
        else:
            url = f"{self.BASE_URL}/hledani/prodej/byty"
            if criteria.location and criteria.location.lower() not in ["ceska republika", "cr", "čr", "cesko", "česko"]:
                params["region"] = criteria.location

        # Dispositions
        if criteria.dispositions:
            disp_slugs = []
            for d in criteria.dispositions:
                norm_d = normalize_disposition(d)
                if norm_d:
                    disp_slugs.append(norm_d)
                elif d.lower():
                    disp_slugs.append(d.lower())
            if disp_slugs:
                params["velikost"] = ",".join(dict.fromkeys(disp_slugs))

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

                raw_items = []
                for q in queries:
                    q_key = q.get("queryKey", [])
                    if q_key and q_key[0] == "estatesSearch":
                        results = q.get("state", {}).get("data", {}).get("results", [])
                        for item in results:
                            flat = self._parse_item(item, criteria.location)
                            if flat:
                                listings.append(flat)
                                raw_items.append(item)
                        break

                # Concurrently enrich candidate listings with detail API (description & annuity)
                async def enrich_sreality(flat_item: FlatListing, est_id: str):
                    try:
                        det_resp = await client.get(f"https://www.sreality.cz/api/v1/estates/{est_id}", timeout=3.0)
                        if det_resp.status_code == 200:
                            d_json = det_resp.json()
                            text_val = d_json.get("text", {}).get("value", "") if isinstance(d_json.get("text"), dict) else d_json.get("description", "")
                            if text_val:
                                flat_item.description = text_val
                            raw_ann = d_json.get("annuity")
                            if raw_ann and isinstance(raw_ann, (int, float)) and raw_ann > 0:
                                flat_item.extra_details["annuity"] = float(raw_ann)
                    except Exception:
                        pass

                if listings:
                    enrich_tasks = []
                    for f in listings:
                        est_id = f.id.replace("sreality_", "")
                        enrich_tasks.append(enrich_sreality(f, est_id))
                    await asyncio.gather(*enrich_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error scraping Sreality: {e}", exc_info=True)

        return listings

    def _parse_item(self, item: dict, target_location: str = "") -> Optional[FlatListing]:
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

            # Strict spatial verification
            if target_location and target_location.lower() not in ["ceska republika", "cr", "čr", "cesko", "česko"]:
                if not is_listing_in_target_location(
                    target_location=target_location,
                    listing_locality=locality_str,
                    listing_city=city,
                    listing_region=region or "",
                    listing_district=district or "",
                    listing_title=name,
                ):
                    return None

            # Images
            images = []
            for img in item.get("images", []):
                u = img.get("url", "")
                if u:
                    if u.startswith("//"):
                        u = "https:" + u
                    images.append(u)
            
            main_image = images[0] if images else None

            # Detail URL construction (Sreality requires '+' in disposition e.g. '3+kk' and joined SEO locality slug)
            city_seo = loc_data.get("citySeoName") or loc_data.get("municipalitySeoName") or "ceska-republika"
            city_part_seo = loc_data.get("cityPartSeoName")
            street_seo = loc_data.get("streetSeoName")

            seo_parts = [p for p in [city_seo, city_part_seo, street_seo] if p]
            locality_seo_slug = "-".join(dict.fromkeys(seo_parts)) or city_seo
            disp_seo = disp if disp else "1+kk"
            url = f"{self.BASE_URL}/detail/prodej/byt/{disp_seo}/{locality_seo_slug}/{estate_id}"

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
