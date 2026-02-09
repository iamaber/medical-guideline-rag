"""Service container for dependency injection.

This module provides a centralized container for managing service instances
with lazy initialization and caching.
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from src.services.drug_lookup import DrugLookup
from src.services.jina_scraper import JinaScraper
from src.services.vector_search import VectorSearch
from src.services.llm_client import get_llm_client, UnifiedLLMClient
from src.services.medical_knowledge_graph import MedicalKnowledgeGraph

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Container for managing service instances with lazy initialization.
    
    Services are initialized on first access and cached for subsequent calls.
    This provides a cleaner alternative to global variables while maintaining
    singleton behavior.
    
    Example:
        services = ServiceContainer()
        drug_lookup = services.drug_lookup()
        results = drug_lookup.search_drugs("aspirin")
    """

    def __init__(self) -> None:
        self._instances: Dict[str, Any] = {}

    def drug_lookup(self) -> DrugLookup:
        """Get or create DrugLookup service instance."""
        if "drug_lookup" not in self._instances:
            logger.info("Initializing DrugLookup service")
            self._instances["drug_lookup"] = DrugLookup()
        return self._instances["drug_lookup"]

    def jina_scraper(self) -> JinaScraper:
        """Get or create JinaScraper service instance."""
        if "jina_scraper" not in self._instances:
            logger.info("Initializing JinaScraper service")
            self._instances["jina_scraper"] = JinaScraper()
        return self._instances["jina_scraper"]

    def vector_search(self) -> VectorSearch:
        """Get or create VectorSearch service instance."""
        if "vector_search" not in self._instances:
            logger.info("Initializing VectorSearch service")
            instance = VectorSearch()
            if not instance._load_index():
                logger.info("Creating new vector search index")
                instance.load_processed_data()
            self._instances["vector_search"] = instance
        return self._instances["vector_search"]

    def llm_client(self) -> UnifiedLLMClient:
        """Get or create LLM client instance."""
        if "llm_client" not in self._instances:
            logger.info("Initializing LLM client")
            self._instances["llm_client"] = get_llm_client()
        return self._instances["llm_client"]

    def knowledge_graph(self) -> MedicalKnowledgeGraph:
        """Get or create MedicalKnowledgeGraph service instance."""
        if "knowledge_graph" not in self._instances:
            logger.info("Initializing MedicalKnowledgeGraph service")
            self._instances["knowledge_graph"] = MedicalKnowledgeGraph()
        return self._instances["knowledge_graph"]

    def is_available(self, service_name: str) -> bool:
        """Check if a service is available and initialized.
        
        Args:
            service_name: Name of the service to check.
            
        Returns:
            True if the service is available, False otherwise.
        """
        return service_name in self._instances

    def all_available(self) -> bool:
        """Check if all core services are available.
        
        Returns:
            True if all required services are initialized.
        """
        required = ["drug_lookup", "jina_scraper", "vector_search", "llm_client", "knowledge_graph"]
        return all(name in self._instances for name in required)

    def get_health_status(self) -> Dict[str, bool]:
        """Get health status of all services.
        
        Returns:
            Dictionary mapping service names to their availability status.
        """
        status = {}
        
        if "drug_lookup" in self._instances:
            status["drug_lookup"] = len(self._instances["drug_lookup"].drug_db) > 0
        
        if "vector_search" in self._instances:
            status["vector_search"] = self._instances["vector_search"].index is not None
        
        if "llm_client" in self._instances:
            status["llm_client"] = self._instances["llm_client"].is_available
        
        if "jina_scraper" in self._instances:
            status["jina_scraper"] = True
        
        if "knowledge_graph" in self._instances:
            status["knowledge_graph"] = True
        
        return status

    def clear(self) -> None:
        """Clear all cached service instances."""
        self._instances.clear()
        logger.info("All service instances cleared")


_container: Optional[ServiceContainer] = None


def get_services() -> ServiceContainer:
    """Get the global service container instance.
    
    Returns:
        The singleton ServiceContainer instance.
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_services() -> None:
    """Reset the service container (useful for testing)."""
    global _container
    if _container is not None:
        _container.clear()
    _container = None
