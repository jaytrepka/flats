import re
import logging
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..models import SearchCriteria, FlatListing
from ..benchmarks import normalize_string, normalize_disposition

logger = logging.getLogger(__name__)


class BazosScraper(BaseScraper):
    portal_name = "bazos"
    BASE_URL = "https://reality.bazos.cz"

    async def search(self, criteria: SearchCriteria) -> List[FlatListing]:
        listings: List[FlatListing] = []

        url = f"{self.BASE_URL}/prodam/byt/"
        
        # Build search query keywords
        keywords = []
        if criteria.location:
            keywords.append(criteria.location.strip())
        
        # If specific single disposition requested, add to search query
        if criteria.dispositions and len(criteria.dispositions) == 1:
            keywords.append(criteria.dispositions[0])

        params: dict = {}
        if keywords:
            params["hledat"] = " ".join(keywords)

        if criteria.min_price:
            params["cenaod"] = str(criteria.min_price)
        if criteria.max_price:
            params["cenado"] = str(criteria.max_price)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Bazos returned HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.find_all("div", class_="inzeraty")

                norm_search_loc = normalize_string(criteria.location)

                for item in items:
                    flat = self._parse_item(item, criteria.location, norm_search_loc)
                    if flat:
                        # Filter by disposition if multiple requested
                        if criteria.dispositions:
                            allowed_disps = [normalize_disposition(d) for d in criteria.dispositions]
                            if flat.disposition not in allowed_disps and "jiny" not in allowed_disps and "atypicky" not in allowed_disps:
                                continue

                        # Filter by area if specified
                        if criteria.min_area and flat.area_m2 < criteria.min_area:
                            continue
                        if criteria.max_area and flat.area_m2 > criteria.max_area:
                            continue

                        listings.append(flat)

        except Exception as e:
            logger.error(f"Error scraping Bazos: {e}", exc_info=True)

        return listings

    def _parse_item(self, item, fallback_location: str, norm_search_loc: str) -> Optional[FlatListing]:
        try:
            title_el = item.find("h2", class_="nadpis")
            if not title_el:
                return None

            title = title_el.text.strip()
            link_el = title_el.find("a")
            url_path = link_el["href"] if link_el and "href" in link_el.attrs else ""
            if not url_path:
                return None

            # ID
            id_match = re.search(r'/inzerat/(\d+)/', url_path)
            estate_id = id_match.group(1) if id_match else url_path.replace("/", "_")

            # Price
            price_el = item.find("div", class_="inzeratycena")
            if not price_el:
                return None
            price_text = price_el.text.strip()
            price_digits = re.sub(r'[^\d]', '', price_text)
            if not price_digits:
                return None
            price = float(price_digits)
            if price < 300000:  # Skip rentals or fractional deposits
                return None

            # Description
            desc_el = item.find("div", class_="popis")
            desc = desc_el.text.strip() if desc_el else ""

            # Area from title or description
            full_text = f"{title} {desc}"
            area_m2 = 0.0
            area_match = re.search(r'(\d+[\.,]?\d*)\s*(?:m2|m²)', full_text)
            if area_match:
                area_m2 = float(area_match.group(1).replace(",", "."))

            if area_m2 < 12 or area_m2 > 800:
                return None

            price_per_m2 = round(price / area_m2, 0)
            if price_per_m2 < 10000 or price_per_m2 > 500000:
                return None

            # Disposition
            disp = normalize_disposition(full_text)

            # Locality
            loc_el = item.find("div", class_="inzeratylok")
            locality = loc_el.text.strip().replace("\n", ", ") if loc_el else fallback_location
            locality = re.sub(r'\s+', ' ', locality)

            # Locality verification
            if norm_search_loc and norm_search_loc not in ["ceska republika", "cr", "cesko"]:
                norm_full = normalize_string(f"{title} {desc} {locality} {url_path}")
                search_words = [w for w in norm_search_loc.split() if len(w) > 2]
                if search_words and not any(w in norm_full for w in search_words):
                    return None

            # City
            city = fallback_location or "Česká republika"
            if locality:
                city = locality.split(",")[0].strip()

            # Image
            img_el = item.find("img", class_="obrazek")
            img_url = img_el["src"] if img_el and "src" in img_el.attrs else None

            full_url = f"{self.BASE_URL}{url_path}" if url_path.startswith("/") else url_path

            return FlatListing(
                id=f"bazos_{estate_id}",
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
                description=desc[:250] if desc else None,
                extra_details={
                    "source": "Bazoš.cz - Reality",
                    "direct_seller": True,
                }
            )
        except Exception as e:
            logger.debug(f"Failed to parse Bazos item: {e}")
            return None
