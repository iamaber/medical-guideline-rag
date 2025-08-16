"""Drug lookup service for finding medication URLs and information."""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from config.settings import DRUG_DB_PATH

logger = logging.getLogger(__name__)


class DrugLookup:
    """Service for looking up drug information from the medex database."""

    def __init__(self, db_path: str = None):
        """Initialize the drug lookup service.

        Args:
            db_path: Path to the drug database JSON file
        """
        self.db_path = Path(db_path) if db_path else DRUG_DB_PATH
        self.drug_db = self._load_drug_db()

    def _load_drug_db(self) -> Dict[str, str]:
        """Load drug database from JSON file.

        Returns:
            Dictionary mapping drug names to URLs
        """
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle both old and new format
            if isinstance(data, dict) and "brands" in data:
                brands = data["brands"]
            else:
                brands = data

            # Create lookup dictionary
            drug_lookup = {}
            for brand in brands:
                if isinstance(brand, dict):
                    name = brand.get("brand_name", brand.get("name", ""))
                    url = brand.get("brand_url", brand.get("url", ""))
                    if name and url:
                        drug_lookup[name.lower()] = url

            logger.info(f"Loaded {len(drug_lookup)} drugs from database")
            return drug_lookup

        except FileNotFoundError:
            logger.error(f"Drug database not found at {self.db_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in drug database: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading drug database: {e}")
            return {}

    def find_drug_url(self, drug_name: str) -> Optional[str]:
        """Find URL for a drug name with fuzzy matching.

        Args:
            drug_name: Name of the drug to search for

        Returns:
            URL of the drug page or None if not found
        """
        if not drug_name:
            return None

        drug_name_clean = drug_name.lower().strip()

        # Exact match first
        if drug_name_clean in self.drug_db:
            return self.drug_db[drug_name_clean]

        # Partial match - check if query is contained in database name
        for db_name, url in self.drug_db.items():
            if drug_name_clean in db_name:
                return url

        # Reverse partial match - check if database name is contained in query
        for db_name, url in self.drug_db.items():
            if db_name in drug_name_clean:
                return url

        logger.warning(f"Drug not found in database: {drug_name}")
        return None

    def search_drugs(self, query: str, limit: int = 10) -> List[str]:
        """Search for drugs matching query.

        Args:
            query: Search query
            limit: Maximum number of results to return

        Returns:
            List of matching drug names
        """
        if not query or len(query) < 2:
            return []

        query_lower = query.lower()
        matches = []

        # Find matches
        for drug_name in self.drug_db.keys():
            if query_lower in drug_name:
                # Convert back to title case for display
                display_name = " ".join(word.capitalize() for word in drug_name.split())
                matches.append(display_name)
                if len(matches) >= limit:
                    break

        return sorted(matches)

    def get_all_drugs(self) -> List[str]:
        """Get all drug names from the database.

        Returns:
            List of all drug names
        """
        return [
            " ".join(word.capitalize() for word in name.split())
            for name in self.drug_db.keys()
        ]

    def reload_database(self) -> bool:
        """Reload the drug database.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.drug_db = self._load_drug_db()
            return True
        except Exception as e:
            logger.error(f"Failed to reload drug database: {e}")
            return False
