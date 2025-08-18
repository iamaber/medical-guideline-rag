import requests
import logging
import time
from typing import Optional, Dict, List
from config.settings import JINA_BASE_URL, JINA_API_KEY, REQUEST_TIMEOUT, SCRAPING_DELAY

logger = logging.getLogger(__name__)


class JinaScraper:
    def __init__(self, api_key: Optional[str] = JINA_API_KEY):
        self.base_url = JINA_BASE_URL
        self.session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; MedicalAdvisor/1.0)",
            "Accept": "text/plain, application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.session.headers.update(headers)

    def scrape_medex_page(self, medex_url: str) -> Optional[str]:
        if not medex_url:
            return None

        try:
            jina_url = f"{self.base_url}{medex_url}"
            logger.info(f"Scraping URL: {medex_url}")

            response = self.session.get(jina_url, timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                content = response.text
                logger.info(f"Successfully scraped: {medex_url}")
                return content
            else:
                logger.warning(
                    f"Failed to scrape {medex_url}: HTTP {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Unexpected error scraping {medex_url}: {e}")
            return None

    def batch_scrape(self, urls: List[str], delay: float = None) -> Dict[str, str]:
        if delay is None:
            delay = SCRAPING_DELAY

        results = {}

        for i, url in enumerate(urls):
            if i > 0:
                time.sleep(delay)

            content = self.scrape_medex_page(url)
            results[url] = content

            logger.info(f"Scraped {i + 1}/{len(urls)} URLs")

        return results

    def test_connection(self) -> bool:
        try:
            test_url = f"{self.base_url}https://example.com"
            response = self.session.get(test_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Jina Reader connection test failed: {e}")
            return False
