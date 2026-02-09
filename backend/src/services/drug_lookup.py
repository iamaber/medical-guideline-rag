import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import Paths

logger = logging.getLogger(__name__)


class DrugLookup:
    """Service for looking up drug information from a local database."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the drug lookup service.

        Args:
            db_path: Optional path to the drug database JSON file.
        """
        self.db_path = Path(db_path) if db_path else Paths.DRUG_DB_PATH
        self.drug_db: Dict[str, str] = self._load_drug_db()

    def _load_drug_db(self) -> Dict[str, str]:
        """Load the drug database from JSON file.

        Returns:
            Dictionary mapping drug names to their URLs.
        """
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            brands = (
                data["brands"] if isinstance(data, dict) and "brands" in data else data
            )
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
        """Find the URL for a drug by name.

        Args:
            drug_name: Name of the drug to look up.

        Returns:
            URL string if found, None otherwise.
        """
        if not drug_name:
            return None
        drug_name_clean = drug_name.lower().strip()
        if drug_name_clean in self.drug_db:
            return self.drug_db[drug_name_clean]
        for db_name, url in self.drug_db.items():
            if drug_name_clean in db_name:
                return url
        for db_name, url in self.drug_db.items():
            if db_name in drug_name_clean:
                return url
        logger.warning(f"Drug not found in database: {drug_name}")
        return None

    def search_drugs(self, query: str, limit: int = 10) -> List[str]:
        """Search for drugs matching a query.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of matching drug names.
        """
        if not query or len(query) < 2:
            return []
        query_lower = query.lower()
        matches = []
        for drug_name in self.drug_db.keys():
            if query_lower in drug_name:
                display_name = " ".join(word.capitalize() for word in drug_name.split())
                matches.append(display_name)
                if len(matches) >= limit:
                    break
        return sorted(matches)

    def get_all_drugs(self) -> List[str]:
        """Get all drug names in the database.

        Returns:
            List of all drug names.
        """
        return [
            " ".join(word.capitalize() for word in name.split())
            for name in self.drug_db.keys()
        ]

    def reload_database(self) -> bool:
        """Reload the drug database from disk.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.drug_db = self._load_drug_db()
            return True
        except Exception as e:
            logger.error(f"Failed to reload drug database: {e}")
            return False
