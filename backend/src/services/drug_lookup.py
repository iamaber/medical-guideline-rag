import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import Paths

logger = logging.getLogger(__name__)


class DrugLookup:
    """Service for looking up drug information from a local database."""

    MIN_MATCH_SCORE = 0.6
    AMBIGUITY_MARGIN = 0.05

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the drug lookup service.

        Args:
            db_path: Optional path to the drug database JSON file.
        """
        self.db_path = Path(db_path) if db_path else Paths.DRUG_DB_PATH
        self.drug_db: Dict[str, str] = self._load_drug_db()
        self._normalized_db: Dict[str, str] = {
            self._normalize(name): url for name, url in self.drug_db.items()
        }

    def _load_drug_db(self) -> Dict[str, str]:
        """Load the drug database from JSON file.

        Returns:
            Dictionary mapping drug names to their URLs.
        """
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            brands = data["brands"] if isinstance(data, dict) and "brands" in data else data
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

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalize a drug name for comparison (case, separators, whitespace)."""
        return " ".join(name.casefold().replace("-", " ").replace("/", " ").split())

    @classmethod
    def _match_score(cls, query: str, candidate: str) -> float:
        """Score a normalized query against a normalized database name."""
        if query == candidate:
            return 1.0
        if candidate.startswith(query):
            return 0.7 + 0.3 * (len(query) / len(candidate))
        if query in candidate:
            return 0.6 + 0.2 * (len(query) / len(candidate))
        query_tokens = set(query.split())
        candidate_tokens = set(candidate.split())
        if query_tokens and query_tokens.issubset(candidate_tokens):
            return 0.5 + 0.2 * (len(query_tokens) / len(candidate_tokens))
        return 0.0

    def find_drug_url(self, drug_name: str) -> Optional[str]:
        """Find the URL for a drug by name.

        Resolution order is exact normalized match, then the highest scoring
        fuzzy match. If two different brands share the top score the lookup is
        treated as ambiguous and returns ``None`` rather than attaching the
        wrong monograph to the advice.

        Args:
            drug_name: Name of the drug to look up.

        Returns:
            URL string if unambiguously found, None otherwise.
        """
        if not drug_name:
            return None

        query = self._normalize(drug_name)
        if not query:
            return None

        exact = self._normalized_db.get(query)
        if exact:
            return exact

        scored = [
            (self._match_score(query, candidate), candidate, url)
            for candidate, url in self._normalized_db.items()
        ]
        scored = [entry for entry in scored if entry[0] >= self.MIN_MATCH_SCORE]
        if not scored:
            logger.warning(f"Drug not found in database: {drug_name}")
            return None

        scored.sort(key=lambda entry: entry[0], reverse=True)
        best_score, best_name, best_url = scored[0]
        rivals = {
            url for score, _, url in scored[1:] if best_score - score < self.AMBIGUITY_MARGIN
        } - {best_url}
        if rivals:
            logger.warning(
                f"Ambiguous drug lookup for '{drug_name}': '{best_name}' matches "
                f"{len(rivals) + 1} different brands"
            )
            return None

        return best_url

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
        matches = [drug_name for drug_name in self.drug_db.keys() if query_lower in drug_name]
        matches.sort(key=lambda name: (not name.startswith(query_lower), len(name), name))
        return [" ".join(word.capitalize() for word in name.split()) for name in matches[:limit]]

    def get_all_drugs(self) -> List[str]:
        """Get all drug names in the database.

        Returns:
            List of all drug names.
        """
        return [
            " ".join(word.capitalize() for word in name.split()) for name in self.drug_db.keys()
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
