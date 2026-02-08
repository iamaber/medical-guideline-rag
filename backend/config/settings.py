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


# Module-level path constants (for imports)
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DRUG_DB_PATH = DATA_DIR / "drug_db" / "medex_URL.json"
RAW_DATA_DIR = DATA_DIR / "raw"
FAISS_INDEX_PATH = DATA_DIR / "vector_index.faiss"
DOCUMENTS_METADATA_PATH = DATA_DIR / "documents_metadata.json"


# Legacy module-level exports (for backwards compatibility)
DRUG_DB_NAME = "medex_URL.json"
VECTOR_SEARCH_TOP_K = 5
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
JINA_BASE_URL = "https://r.jina.ai/"
REQUEST_TIMEOUT = 30
SCRAPING_DELAY = 1.0


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


def _init_legacy_exports() -> None:
    """Initialize legacy module-level exports."""
    global NCBI_EMAIL, NCBI_API_KEY, JINA_API_KEY
    global MAX_MEDICATIONS, DEFAULT_SEARCH_RESULTS, CACHE_EXPIRY_HOURS
    global API_PORT, UI_PORT, LOG_LEVEL, LOG_FORMAT

    # Use direct constants
    NCBI_EMAIL = None
    NCBI_API_KEY = None
    JINA_API_KEY = None
    MAX_MEDICATIONS = 10
    DEFAULT_SEARCH_RESULTS = 5
    CACHE_EXPIRY_HOURS = 24
    API_PORT = 8000
    UI_PORT = 8501
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


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
