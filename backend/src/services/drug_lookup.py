import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from config.settings import DRUG_DB_PATH

logger = logging.getLogger(__name__)


class DrugLookup:
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DRUG_DB_PATH
        self.drug_db = self._load_drug_db()

    def _load_drug_db(self) -> Dict[str, str]:
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
        return [
            " ".join(word.capitalize() for word in name.split())
            for name in self.drug_db.keys()
        ]

    def reload_database(self) -> bool:
        try:
            self.drug_db = self._load_drug_db()
            return True
        except Exception as e:
            logger.error(f"Failed to reload drug database: {e}")
            return False
