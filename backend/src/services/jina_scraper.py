"""Jina Reader scraper for medical content.

This module provides web scraping capabilities using the Jina Reader API
to extract content from medical websites like MedEx.
"""

import logging
import time
from typing import Dict, List, Optional

import requests

from config.settings import get_settings

logger = logging.getLogger(__name__)


class JinaScraper:
    """Web scraper using Jina Reader API.

    Fetches and extracts text content from web pages, particularly
    medical information from drug databases.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the Jina scraper.

        Args:
            api_key: Optional Jina API key for authenticated requests.
        """
        settings = get_settings()
        self.base_url = settings.jina_base_url
        self.timeout = settings.request_timeout
        self.delay = settings.scraping_delay
        self.session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; MedicalAdvisor/1.0)",
            "Accept": "text/plain, application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }

        effective_key = api_key or (settings.jina_api_key.get_secret_value() if settings.jina_api_key else None)
        if effective_key:
            headers["Authorization"] = f"Bearer {effective_key}"

        self.session.headers.update(headers)

    def scrape_medex_page(self, medex_url: str) -> Optional[str]:
        """Scrape content from a MedEx page.

        Args:
            medex_url: URL of the MedEx page to scrape.

        Returns:
            Extracted text content or None if failed.
        """
        if not medex_url:
            return None

        try:
            jina_url = f"{self.base_url}{medex_url}"
            logger.info(f"Scraping URL: {medex_url}")

            response = self.session.get(jina_url, timeout=self.timeout)

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

    def batch_scrape(
        self, urls: List[str], delay: Optional[float] = None
    ) -> Dict[str, Optional[str]]:
        """Scrape multiple URLs with rate limiting.

        Args:
            urls: List of URLs to scrape.
            delay: Optional delay between requests in seconds.

        Returns:
            Dictionary mapping URLs to their scraped content.
        """
        if delay is None:
            delay = self.delay

        results: Dict[str, Optional[str]] = {}

        for i, url in enumerate(urls):
            if i > 0:
                time.sleep(delay)

            content = self.scrape_medex_page(url)
            results[url] = content

            logger.info(f"Scraped {i + 1}/{len(urls)} URLs")

        return results

    def test_connection(self) -> bool:
        """Test the connection to Jina Reader API.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            test_url = f"{self.base_url}https://example.com"
            response = self.session.get(test_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Jina Reader connection test failed: {e}")
            return False
