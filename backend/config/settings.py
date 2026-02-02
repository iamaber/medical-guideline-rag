"""Application settings loaded from environment variables.

This module provides centralized configuration management using pydantic-settings.
Settings are loaded from environment variables and .env files.

Usage:
    from config.settings import get_settings

    settings = get_settings()
    print(settings.api_port)
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables. The class
    automatically loads from a .env file if present.

    LLM configuration is handled separately in src.models.llm_config.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # External API Keys (non-LLM)
    ncbi_email: Optional[str] = None
    ncbi_api_key: Optional[SecretStr] = None
    jina_api_key: Optional[SecretStr] = None

    # Application Settings
    max_medications: int = Field(default=10)
    default_search_results: int = Field(default=5)
    cache_expiry_hours: int = Field(default=24)
    api_port: int = Field(default=8000)
    ui_port: int = Field(default=8501)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Vector Search
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    vector_search_top_k: int = Field(default=5)

    # Scraping
    jina_base_url: str = Field(default="https://r.jina.ai/")
    request_timeout: int = Field(default=30)
    scraping_delay: float = Field(default=1.0)


# File paths (derived from module location)
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DRUG_DB_PATH = DATA_DIR / "drug_db" / "medex_URL.json"
RAW_DATA_DIR = DATA_DIR / "raw"
FAISS_INDEX_PATH = DATA_DIR / "vector_index.faiss"
DOCUMENTS_METADATA_PATH = DATA_DIR / "documents_metadata.json"

# Legacy exports for backwards compatibility (non-LLM)
NCBI_EMAIL = None
NCBI_API_KEY = None
JINA_API_KEY = None
MAX_MEDICATIONS = 10
DEFAULT_SEARCH_RESULTS = 5
CACHE_EXPIRY_HOURS = 24
API_PORT = 8000
UI_PORT = 8501
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SEARCH_TOP_K = 5
JINA_BASE_URL = "https://r.jina.ai/"
REQUEST_TIMEOUT = 30
SCRAPING_DELAY = 1.0
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _init_legacy_exports() -> None:
    """Initialize legacy module-level exports from settings."""
    global NCBI_EMAIL, NCBI_API_KEY, JINA_API_KEY
    global MAX_MEDICATIONS, DEFAULT_SEARCH_RESULTS, CACHE_EXPIRY_HOURS
    global API_PORT, UI_PORT, EMBEDDING_MODEL, VECTOR_SEARCH_TOP_K
    global JINA_BASE_URL, REQUEST_TIMEOUT, SCRAPING_DELAY, LOG_LEVEL, LOG_FORMAT

    settings = get_settings()
    NCBI_EMAIL = settings.ncbi_email
    NCBI_API_KEY = settings.effective_ncbi_api_key
    JINA_API_KEY = settings.effective_jina_api_key
    MAX_MEDICATIONS = settings.max_medications
    DEFAULT_SEARCH_RESULTS = settings.default_search_results
    CACHE_EXPIRY_HOURS = settings.cache_expiry_hours
    API_PORT = settings.api_port
    UI_PORT = settings.ui_port
    EMBEDDING_MODEL = settings.embedding_model
    VECTOR_SEARCH_TOP_K = settings.vector_search_top_k
    JINA_BASE_URL = settings.jina_base_url
    REQUEST_TIMEOUT = settings.request_timeout
    SCRAPING_DELAY = settings.scraping_delay
    LOG_LEVEL = settings.log_level
    LOG_FORMAT = settings.log_format


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the shared settings instance.

    Returns:
        The singleton Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None


def setup_logging() -> None:
    """Configure application logging based on settings."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=settings.log_format,
    )


# Initialize legacy exports on module load
_init_legacy_exports()
