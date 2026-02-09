"""Application settings loaded from environment variables.

This module provides centralized configuration management using pydantic-settings.
Settings are loaded from environment variables and .env files.

Usage:
    from config.settings import get_settings, Settings

    settings = get_settings()
    print(settings.api_port)
    
    # Access path constants
    from config.settings import Paths
    print(Paths.PROCESSED_DIR)
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Paths:
    """Path constants for the application."""

    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    PROCESSED_DIR = DATA_DIR / "processed"
    DRUG_DB_PATH = DATA_DIR / "drug_db" / "medex_URL.json"
    RAW_DATA_DIR = DATA_DIR / "raw"
    FAISS_INDEX_PATH = DATA_DIR / "vector_index.faiss"
    DOCUMENTS_METADATA_PATH = DATA_DIR / "documents_metadata.json"
    TEMPLATES_DIR = BASE_DIR / "templates"


class Defaults:
    """Default values for settings."""

    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_SEARCH_TOP_K = 5
    MAX_MEDICATIONS = 10
    DEFAULT_SEARCH_RESULTS = 5
    CACHE_EXPIRY_HOURS = 24
    API_PORT = 8000
    UI_PORT = 8501
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    max_medications: int = Field(default=Defaults.MAX_MEDICATIONS)
    default_search_results: int = Field(default=Defaults.DEFAULT_SEARCH_RESULTS)
    cache_expiry_hours: int = Field(default=Defaults.CACHE_EXPIRY_HOURS)
    api_port: int = Field(default=Defaults.API_PORT)
    ui_port: int = Field(default=Defaults.UI_PORT)

    # Logging
    log_level: str = Field(default=Defaults.LOG_LEVEL)
    log_format: str = Field(default=Defaults.LOG_FORMAT)

    # Vector Search
    embedding_model: str = Field(default=Defaults.EMBEDDING_MODEL)
    vector_search_top_k: int = Field(default=Defaults.VECTOR_SEARCH_TOP_K)

    # Scraping
    jina_base_url: str = Field(default=Defaults.JINA_BASE_URL)
    request_timeout: int = Field(default=Defaults.REQUEST_TIMEOUT)
    scraping_delay: float = Field(default=Defaults.SCRAPING_DELAY)


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
