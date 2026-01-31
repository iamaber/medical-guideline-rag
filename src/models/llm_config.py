"""LLM provider configuration models.

This module provides configuration classes for multi-provider LLM support.
Users can select their provider, model, and API key through environment variables.

Supported providers:
- OpenAI (GPT-4, GPT-4o, etc.)
- Anthropic (Claude 3.5, Claude 3, etc.)
- Google (Gemini 2.0, Gemini Pro, etc.)
- Ollama (local models)
- Azure OpenAI
- DeepSeek
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE = "azure"
    DEEPSEEK = "deepseek"


class LLMSettings(BaseSettings):
    """LLM configuration loaded from environment variables.

    Universal provider selection - user specifies provider, model, and API key.

    Example .env configuration:
        LLM_PROVIDER=openai
        LLM_MODEL=gpt-4o
        OPENAI_API_KEY=sk-...
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider selection
    llm_provider: LLMProvider = Field(
        default=LLMProvider.GOOGLE, description="LLM provider to use"
    )
    llm_model: str = Field(
        default="gemini-2.0-flash", description="Model name for the selected provider"
    )

    # Provider API Keys (user configures the one they need)
    openai_api_key: Optional[SecretStr] = Field(default=None)
    anthropic_api_key: Optional[SecretStr] = Field(default=None)
    google_api_key: Optional[SecretStr] = Field(default=None)
    deepseek_api_key: Optional[SecretStr] = Field(default=None)

    # Azure OpenAI specific
    azure_openai_api_key: Optional[SecretStr] = Field(default=None)
    azure_openai_endpoint: Optional[str] = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-02-01")

    # Ollama (local)
    ollama_base_url: str = Field(default="http://localhost:11434/v1")

    # Legacy support for backwards compatibility
    gemini_api_key: Optional[SecretStr] = Field(default=None)

    # Generation settings
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, ge=1)
    llm_top_p: float = Field(default=0.8, ge=0.0, le=1.0)

    def get_api_key_for_provider(
        self, provider: Optional[LLMProvider] = None
    ) -> Optional[str]:
        """Get the API key for the specified or current provider.

        Args:
            provider: The provider to get the API key for. If None, uses the
                configured llm_provider.

        Returns:
            The API key string or None if not configured.
        """
        provider = provider or self.llm_provider

        key_map = {
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.GOOGLE: self.google_api_key or self.gemini_api_key,
            LLMProvider.DEEPSEEK: self.deepseek_api_key,
            LLMProvider.AZURE: self.azure_openai_api_key,
            LLMProvider.OLLAMA: None,
        }

        secret = key_map.get(provider)
        return secret.get_secret_value() if secret else None


class MedicationAdviceOutput(BaseModel):
    """Structured output for medication advice from the LLM."""

    regimen_analysis: str = Field(
        description="Analysis of the medication regimen"
    )
    therapeutic_indications: str = Field(
        description="Therapeutic indications and rationale"
    )
    dosing_strategy: str = Field(
        description="Integrated dosing strategy and timing"
    )
    safety_monitoring: str = Field(
        description="Safety monitoring protocol"
    )
    drug_interactions: str = Field(
        description="Drug interaction management"
    )
    dos_and_donts: str = Field(
        description="Do's and don'ts reference"
    )
    lifestyle_considerations: str = Field(
        description="Lifestyle and dietary considerations"
    )
