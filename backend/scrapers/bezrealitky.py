import re
import json
import logging
from typing import List, Optional, Dict, Any
import httpx

from .base import BaseScraper
from ..models import SearchCriteria, FlatListing
from ..benchmarks import normalize_string, normalize_disposition

logger = logging.getLogger(__name__)


class BezrealitkyScraper(BaseScraper):
    portal_name = "bezrealitky"
    BASE_URL = "https://www.bezrealitky.cz"

    DISPOSITION_MAP = {
        "1+kk": "DISP_1_KK",
        "1+1": "DISP_1_1",
        "2+kk": "DISP_2_KK",
        "2+1": "DISP_2_1",
        "3+kk": "DISP_3_KK",
        "3+1": "DISP_3_1",
        "4+kk": "DISP_4_KK",
        "4+1": "DISP_4_1",
        "5+kk": "DISP_5_KK",
        "5+1": "DISP_5_1",
        "6+": "DISP_6_KK",
        "atypicky": "DISP_OTHERS",
    }

    DISP_REVERSE_MAP = {
        "DISP_1_KK": "1+kk",
        "DISP_1_1": "1+1",
        "DISP_2_KK": "2+kk",
        "DISP_2_1": "2+1",
        "DISP_3_KK": "3+kk",
        "DISP_3_1": "3+1",
        "DISP_4_KK": "4+kk",
        "DISP_4_1": "4+1",
        "DISP_5_KK": "5+kk",
        "DISP_5_1": "5+1",
        "DISP_6_KK": "6+",
        "DISP_6_1": "6+",
        "DISP_OTHERS": "atypicky",
        "GARSONIERA": "1+kk",
    }

    async def search(self, criteria: SearchCriteria) -> List[FlatListing]:
        listings: List[FlatListing] = []

        url = f"{self.BASE_URL}/vyhledat"
        params: List[tuple] = [
            ("offerType", "PRODEJ"),
            ("estateType", "BYT"),
        ]

        if criteria.location:
            params.append(("location", criteria.location.strip()))

        if criteria.dispositions:
            for d in criteria.dispositions:
                norm_d = normalize_disposition(d)
                if norm_d in self.DISPOSITION_MAP:
                    params.append(("disposition", self.DISPOSITION_MAP[norm_d]))
                elif d in self.DISPOSITION_MAP:
                    params.append(("disposition", self.DISPOSITION_MAP[d]))

        if criteria.min_price:
            params.append(("priceFrom", str(criteria.min_price)))
        if criteria.max_price:
            params.append(("priceTo", str(criteria.max_price)))
        if criteria.min_area:
            params.append(("surfaceFrom", str(criteria.min_area)))
        if criteria.max_area:
            params.append(("surfaceTo", str(criteria.max_area)))

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Bezrealitky returned HTTP {resp.status_code}")
                    return []

                html = resp.text
                match = re.search(r'<script id="__NEXT_DATA__\" type=\"application/json\">(.*?)</script>', html)
                if not match:
                    logger.warning("Bezrealitky: __NEXT_DATA__ script tag not found")
                    return []

                data = json.loads(match.group(1))
                apollo_cache = data.get("props", {}).get("pageProps", {}).get("apolloCache", {})

                # Build image lookup table
                image_lookup = {}
                for k, v in apollo_cache.items():
                    if isinstance(v, dict) and v.get("__typename") == "Image":
                        for url_key in ["url({\"filter\":\"RECORD_MAIN\"})", "url({\"filter\":\"RECORD_THUMB\"})", "url"]:
                            if url_key in v and v[url_key]:
                                image_lookup[k] = v[url_key]
                                break

                # Extract adverts
                norm_search_loc = normalize_string(criteria.location)
                for k, v in apollo_cache.items():
                    if isinstance(v, dict) and v.get("__typename") == "Advert":
                        flat = self._parse_advert(v, image_lookup, criteria.location, norm_search_loc)
                        if flat:
                            listings.append(flat)

        except Exception as e:
            logger.error(f"Error scraping Bezrealitky: {e}", exc_info=True)

        return listings

    def _parse_advert(self, adv: dict, image_lookup: Dict[str, str], fallback_location: str, norm_search_loc: str) -> Optional[FlatListing]:
        try:
            adv_id = str(adv.get("id", ""))
            uri = adv.get("uri", "")
            if not adv_id or not uri:
                return None

            price = float(adv.get("price") or 0)
            # Filter out foreign listings priced in EUR (e.g. 50k EUR) or auction shares < 350k CZK
            if price < 350000:
                return None

            area_m2 = float(adv.get("surface") or adv.get("surfaceTotal") or 0)
            if area_m2 < 12 or area_m2 > 800:
                return None

            price_per_m2 = round(price / area_m2, 0)
            if price_per_m2 < 12000 or price_per_m2 > 500000:
                return None

            # Address & Locality
            address_cs = adv.get('address({"locale":"CS"})') or adv.get("address") or fallback_location
            
            # Check locality match if specific location requested
            if norm_search_loc and norm_search_loc not in ["ceska republika", "cr", "cesko"]:
                norm_addr = normalize_string(address_cs + " " + uri)
                # Ensure the searched city/district name appears in address or slug
                search_words = [w for w in norm_search_loc.split() if len(w) > 2]
                if search_words and not any(w in norm_addr for w in search_words):
                    return None

            # Disposition
            raw_disp = adv.get("disposition", "")
            disp = self.DISP_REVERSE_MAP.get(raw_disp, normalize_disposition(raw_disp))

            title = adv.get('imageAltText({"locale":"CS"})') or f"Prodej bytu {disp} {int(area_m2)} m²"

            # Parse city from address
            city = fallback_location or "Česká republika"
            if address_cs:
                parts = [p.strip() for p in address_cs.split(",") if p.strip()]
                if len(parts) >= 2:
                    city = parts[-2] if len(parts) > 2 else parts[-1]

            # Image resolution
            main_image = None
            main_image_ref = adv.get("mainImage", {}).get("__ref") if isinstance(adv.get("mainImage"), dict) else None
            if main_image_ref and main_image_ref in image_lookup:
                main_image = image_lookup[main_image_ref]

            additional_images = []
            public_images = adv.get('publicImages({"limit":3})', []) or adv.get("publicImages", [])
            for p_img in public_images:
                if isinstance(p_img, dict):
                    ref = p_img.get("__ref")
                    if ref and ref in image_lookup and image_lookup[ref] != main_image:
                        additional_images.append(image_lookup[ref])

            # GPS coordinates
            gps = adv.get("gps", {})
            lat = gps.get("lat") if isinstance(gps, dict) else None
            lng = gps.get("lng") if isinstance(gps, dict) else None

            url = f"{self.BASE_URL}/nemovitosti-byty-domy/{uri}"

            return FlatListing(
                id=f"bezrealitky_{adv_id}",
                title=title,
                portal=self.portal_name,
                url=url,
                image_url=main_image,
                additional_images=additional_images,
                locality=address_cs or city,
                city=city,
                disposition=disp,
                area_m2=area_m2,
                price_czk=price,
                price_per_m2=price_per_m2,
                latitude=lat,
                longitude=lng,
                extra_details={
                    "no_commission": True,
                    "landType": adv.get("landType"),
                }
            )
        except Exception as e:
            logger.debug(f"Failed to parse Bezrealitky item: {e}")
            return None
