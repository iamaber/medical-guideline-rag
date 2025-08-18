import json
import logging
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
import os

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("medex")


class MedexScraper:
    BASE_URL = "https://medex.com.bd/brands"
    JINA_BASE = "https://r.jina.ai/"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    )
    DOSAGE_UNITS = ("mg", "ml", "iu", "mcg", "%")

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self.existing_brands = set()
        self.existing_data = None

    def fetch_markdown(self, url: str) -> Optional[str]:
        # Fetch markdown content from Jina reader
        try:
            response = self.session.get(self.JINA_BASE + url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            log.error("Failed to fetch %s: %s", url, exc)
            return None

    def discover_total_pages(self, markdown: str) -> int:
        # Extract highest page number from pagination links in markdown
        pattern = re.compile(r"\[(\d+)\]\([^)]*\bpage=(\d+)\)")
        pages = [int(page) for _, page in pattern.findall(markdown)]
        if pages:
            return max(pages)
        log.warning("Could not detect pagination; defaulting to 1 page")
        return 1

    def extract_brands(self, markdown: str) -> List[Dict[str, str]]:
        link_pattern = re.compile(r"!\[.*?\]\([^)]+\)\s*(.*?)\]\(([^)]+)\)")
        brands = []

        for text, href in link_pattern.findall(markdown):
            brand_name = self._parse_brand_name(text)
            if not brand_name:
                continue
            brand_url = self._make_absolute_url(href.strip())
            brands.append({"brand_name": brand_name, "brand_url": brand_url})

        return brands

    def _parse_brand_name(self, text: str) -> str:
        tokens = text.strip().split()
        idx = next(
            (
                i
                for i, tok in enumerate(tokens)
                if any(u in tok.lower() for u in self.DOSAGE_UNITS)
            ),
            None,
        )
        brand_name = " ".join(tokens[:idx]) if idx is not None else " ".join(tokens[:3])
        brand_name = re.sub(r"[^\w\s\-]", "", brand_name).strip()
        return brand_name

    def _make_absolute_url(self, href: str) -> str:
        # Convert relative URLs to absolute.
        if href.startswith("/"):
            return urljoin("https://medex.com.bd", href)
        if not href.startswith("http"):
            return urljoin("https://medex.com.bd/", href)
        return href

    def load_existing_data(self, filename: str = "medex_URL.json") -> Dict:
        """Load existing data from JSON file if it exists."""
        out_dir = "./data/drug_db"
        out_path = os.path.join(out_dir, filename)

        if os.path.exists(out_path):
            try:
                with open(out_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    # Create a set of existing brand URLs for fast lookup
                    self.existing_brands = {
                        brand["brand_url"] for brand in data.get("brands", [])
                    }
                    log.info(
                        f"Loaded {len(self.existing_brands)} existing brands from {filename}"
                    )
                    return data
            except Exception as exc:
                log.warning(f"Failed to load existing data: {exc}")

        return {"total_brands": 0, "brands": []}

    def get_last_scraped_page(self, existing_brands: List[Dict[str, str]]) -> int:
        """Determine the last successfully scraped page based on existing data."""
        if not existing_brands:
            return 0

        # Estimate pages based on brands count (assuming ~30 brands per page)
        estimated_page = len(existing_brands) // 30
        return max(1, estimated_page)

    def is_brand_exists(self, brand_url: str) -> bool:
        """Check if a brand URL already exists in the dataset."""
        return brand_url in self.existing_brands

    def scrape_all_pages(
        self, max_pages: Optional[int] = None, delay: float = 1.0
    ) -> List[Dict[str, str]]:
        # Load existing data first
        self.existing_data = self.load_existing_data()
        existing_brands_list = self.existing_data.get("brands", [])

        # Start with existing brands
        brands = existing_brands_list.copy()

        # Determine starting page
        start_page = self.get_last_scraped_page(existing_brands_list)
        log.info(
            f"Resuming from page {start_page + 1} (already have {len(brands)} brands)"
        )

        # Get first page to determine total pages
        first_md = self.fetch_markdown(self.BASE_URL)
        if not first_md:
            log.error("Cannot fetch first page – aborting")
            return brands

        total_pages = self.discover_total_pages(first_md)
        if max_pages:
            total_pages = min(total_pages, max_pages)
        log.info(f"Discovered {total_pages} total pages")

        # If we haven't scraped page 1 yet, do it now
        if start_page == 0:
            new_brands = self.extract_brands(first_md)
            # Filter out brands that already exist
            filtered_brands = [
                b for b in new_brands if not self.is_brand_exists(b["brand_url"])
            ]
            brands.extend(filtered_brands)
            # Update existing brands set
            self.existing_brands.update(b["brand_url"] for b in filtered_brands)
            log.info(f"Added {len(filtered_brands)} new brands from page 1")
            start_page = 1

        # Scrape remaining pages
        for page in range(start_page + 1, total_pages + 1):
            url = f"{self.BASE_URL}?page={page}"
            md = self.fetch_markdown(url)
            if md:
                new_brands = self.extract_brands(md)
                # Filter out brands that already exist
                filtered_brands = [
                    b for b in new_brands if not self.is_brand_exists(b["brand_url"])
                ]
                brands.extend(filtered_brands)
                # Update existing brands set
                self.existing_brands.update(b["brand_url"] for b in filtered_brands)

                if filtered_brands:
                    log.info(f"Page {page}: Added {len(filtered_brands)} new brands")
                else:
                    log.info(f"Page {page}: No new brands (all already exist)")

            if page % 50 == 0 or page == total_pages:
                log.info(
                    "Progress: page %d/%d | total brands: %d",
                    page,
                    total_pages,
                    len(brands),
                )
            time.sleep(delay)

        return brands

    @staticmethod
    def save_json(data: List[Dict[str, str]], filename: str = "medex_URL.json"):
        out_dir = "./data/drug_db"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)

        # Remove duplicates based on brand_url
        seen_urls = set()
        unique_brands = []
        for brand in data:
            if brand["brand_url"] not in seen_urls:
                unique_brands.append(brand)
                seen_urls.add(brand["brand_url"])

        payload = {
            "total_brands": len(unique_brands),
            "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "brands": unique_brands,
        }
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        log.info("Saved %d unique brands", len(unique_brands))


def main():
    scraper = MedexScraper()

    # Check existing data
    existing_data = scraper.load_existing_data()
    existing_count = len(existing_data.get("brands", []))

    if existing_count > 0:
        log.info(f"Found existing data with {existing_count} brands")

    # Scrape with resume capability
    # brands = scraper.scrape_all_pages(max_pages=350, delay=0.5)
    brands = scraper.scrape_all_pages(delay=1.0)  # Uncomment for full run

    if brands:
        scraper.save_json(brands)
        print(f"Total brands: {len(brands)}")
        new_brands_count = len(brands) - existing_count
        if new_brands_count > 0:
            print(f"Added {new_brands_count} new brands")
        else:
            print("No new brands found - all data is up to date")
    else:
        print("Nothing scraped – check logs above")


if __name__ == "__main__":
    main()
