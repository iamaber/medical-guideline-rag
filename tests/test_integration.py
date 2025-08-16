"""Integration tests for the Medical Advisor system."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pytest
import json
from unittest.mock import Mock, patch


def test_full_integration():
    """Test full system integration without external API calls."""
    from src.models.schemas import UserInput, GenderEnum
    from src.services.drug_lookup import DrugLookup
    from src.utils.text_processor import TextProcessor

    # Test data
    test_input = UserInput(
        meds=["Test Medicine"], schedule=["1+0+1"], age=30, gender=GenderEnum.MALE
    )

    # Test drug lookup
    drug_lookup = DrugLookup()
    assert isinstance(drug_lookup.drug_db, dict)

    # Test text processor
    processor = TextProcessor()
    clean_text = processor.clean_text("Test <b>medication</b> content [1]")
    assert "<b>" not in clean_text
    assert "[1]" not in clean_text


def test_vector_search_initialization():
    """Test vector search can be initialized."""
    from src.services.vector_search import VectorSearch

    # This should not fail even without data
    vector_search = VectorSearch()
    assert vector_search.model_name == "sentence-transformers/all-MiniLM-L6-v2"


def test_gemini_client_initialization():
    """Test Gemini client initialization."""
    from src.services.gemini_client import GeminiClient

    client = GeminiClient()
    model_info = client.get_model_info()

    assert "model_name" in model_info
    assert "api_key_configured" in model_info


def test_jina_scraper_initialization():
    """Test Jina scraper initialization."""
    from src.services.jina_scraper import JinaScraper

    scraper = JinaScraper()
    assert scraper.base_url == "https://r.jina.ai/"


@pytest.mark.asyncio
async def test_api_endpoints_mock():
    """Test API endpoints with mocked dependencies."""
    from fastapi.testclient import TestClient
    from app.main import app

    # Mock the services to avoid external dependencies
    with (
        patch("app.main.drug_lookup") as mock_drug_lookup,
        patch("app.main.vector_search") as mock_vector_search,
        patch("app.main.gemini_client") as mock_gemini_client,
        patch("app.main.jina_scraper") as mock_jina_scraper,
    ):
        # Setup mocks
        mock_drug_lookup.drug_db = {"test": "url"}
        mock_drug_lookup.search_drugs.return_value = ["Test Drug"]
        mock_vector_search.search_by_medications.return_value = []
        mock_gemini_client.generate_advice.return_value = "Test advice"

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "Medical Guideline RAG API" in response.json()["message"]

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "degraded"]


def test_data_availability():
    """Test if required data files are available."""
    from config.settings import DRUG_DB_PATH, PROCESSED_DIR

    # Check if drug database exists
    drug_db_exists = DRUG_DB_PATH.exists()

    # Check if processed data directory exists
    processed_dir_exists = PROCESSED_DIR.exists()

    print(f"Drug database available: {drug_db_exists}")
    print(f"Processed data directory available: {processed_dir_exists}")

    # At least one should be available for the system to work
    assert drug_db_exists or processed_dir_exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
