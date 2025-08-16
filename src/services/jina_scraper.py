"""Web scraping service using Jina Reader."""

import requests
import logging
import time
from typing import Optional, Dict, List
from config.settings import JINA_BASE_URL, REQUEST_TIMEOUT, SCRAPING_DELAY

logger = logging.getLogger(__name__)


class JinaScraper:
    """Web scraper using Jina Reader API for extracting content from web pages."""

    def __init__(self):
        """Initialize the Jina scraper."""
        self.base_url = JINA_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; MedicalAdvisor/1.0)",
                "Accept": "text/plain, application/json",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def scrape_medex_page(self, medex_url: str) -> Optional[str]:
        """Scrape MedEx page using Jina Reader.

        Args:
            medex_url: URL of the MedEx page to scrape

        Returns:
            Cleaned content from the page or None if failed
        """
        if not medex_url:
            return None

        try:
            jina_url = f"{self.base_url}{medex_url}"
            logger.info(f"Scraping URL: {medex_url}")

            response = self.session.get(jina_url, timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                content = response.text

                # Clean and extract relevant sections
                cleaned_content = self._extract_drug_info(content)
                logger.info(f"Successfully scraped: {medex_url}")
                return cleaned_content
            else:
                logger.warning(
                    f"Failed to scrape {medex_url}: HTTP {response.status_code}"
                )
                return None

        except requests.RequestException as e:
            logger.error(f"Network error scraping {medex_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {medex_url}: {e}")
            return None

    def _extract_drug_info(self, content: str) -> str:
        """Extract relevant drug information from scraped content.

        Args:
            content: Raw scraped content

        Returns:
            Extracted and formatted drug information
        """
        if not content:
            return ""

        # Key sections to look for in MedEx pages
        sections_to_extract = [
            "indication",
            "composition",
            "dosage",
            "side effect",
            "contraindication",
            "precaution",
            "interaction",
            "description",
            "mechanism of action",
            "pharmacokinetics",
            "adverse effect",
        ]

        extracted_info = []
        content_lower = content.lower()

        for section in sections_to_extract:
            # Look for section headers
            section_patterns = [
                f"{section}:",
                f"{section}s:",
                f"# {section}",
                f"## {section}",
                f"**{section}**",
            ]

            for pattern in section_patterns:
                start_idx = content_lower.find(pattern.lower())
                if start_idx != -1:
                    # Find the end of this section (next section or reasonable limit)
                    section_content = self._extract_section_content(content, start_idx)
                    if section_content:
                        extracted_info.append(f"{section.title()}: {section_content}")
                    break

        # If no specific sections found, return a truncated version
        if not extracted_info:
            return content[:1500] if len(content) > 1500 else content

        return "\n\n".join(extracted_info)

    def _extract_section_content(
        self, content: str, start_idx: int, max_length: int = 800
    ) -> str:
        """Extract content from a specific section.

        Args:
            content: Full content
            start_idx: Starting index of the section
            max_length: Maximum length of extracted content

        Returns:
            Extracted section content
        """
        # Find the actual start of content (after the header)
        section_start = content.find(":", start_idx)
        if section_start == -1:
            section_start = start_idx
        else:
            section_start += 1

        # Look for natural end points
        next_section_indicators = [
            "\n#",
            "\n##",
            "\n**",
            "\nIndication",
            "\nDosage",
            "\nSide Effect",
            "\nContraindication",
            "\nPrecaution",
        ]

        end_idx = len(content)
        for indicator in next_section_indicators:
            next_section = content.find(
                indicator, section_start + 50
            )  # Skip immediate matches
            if next_section != -1 and next_section < end_idx:
                end_idx = next_section

        # Limit the extraction length
        end_idx = min(end_idx, section_start + max_length)

        section_content = content[section_start:end_idx].strip()

        # Clean up the content
        lines = section_content.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("*"):
                cleaned_lines.append(line)

        return " ".join(cleaned_lines)

    def batch_scrape(self, urls: List[str], delay: float = None) -> Dict[str, str]:
        """Scrape multiple URLs with rate limiting.

        Args:
            urls: List of URLs to scrape
            delay: Delay between requests (uses default if None)

        Returns:
            Dictionary mapping URLs to scraped content
        """
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
        """Test connection to Jina Reader service.

        Returns:
            True if connection is successful
        """
        try:
            test_url = f"{self.base_url}https://example.com"
            response = self.session.get(test_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Jina Reader connection test failed: {e}")
            return False
