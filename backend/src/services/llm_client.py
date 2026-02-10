"""Unified async LLM client supporting multiple providers via Pydantic AI.

This module provides a unified interface for interacting with various LLM providers.
Provider selection is done through environment variables:
- LLM_PROVIDER: openai, anthropic, google, ollama, azure, deepseek
- LLM_MODEL: model name for the selected provider
- <PROVIDER>_API_KEY: API key for the selected provider

Example usage:
    from src.services.llm_client import get_llm_client

    client = get_llm_client()
    response = await client.generate_text("Hello, world!")
"""

import logging
from typing import Any, Dict, List, Optional

from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

from src.models.llm_config import LLMProvider, LLMSettings

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = """I apologize, but I'm currently unable to process your request due to a service configuration issue. 

Please ensure that:
1. A valid API key is configured in your environment variables
2. The LLM_PROVIDER setting matches your API key
3. You have sufficient API credits/quota

For medical emergencies, please contact your healthcare provider immediately."""


class UnifiedLLMClient:
    """Unified async LLM client supporting multiple providers via Pydantic AI.

    Provider selection is done through environment variables. The client
    automatically initializes the appropriate model based on the configured
    provider.
    """

    def __init__(self, settings: Optional[LLMSettings] = None) -> None:
        """Initialize the unified LLM client.

        Args:
            settings: Optional LLM settings. If not provided, settings are
                loaded from environment variables.
        """
        self.settings = settings or LLMSettings()
        self._model: Optional[Any] = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the model based on provider settings."""
        try:
            self._model = self._create_model_for_provider(
                self.settings.llm_provider, self.settings.llm_model
            )
            logger.info(
                "Initialized LLM client: %s/%s",
                self.settings.llm_provider.value,
                self.settings.llm_model,
            )
        except Exception as e:
            logger.error("Failed to initialize LLM client: %s", e)
            self._model = None

    def _create_model_for_provider(
        self, provider: LLMProvider, model_name: str
    ) -> Any:
        """Create a model instance for the specified provider.

        Args:
            provider: The LLM provider to use.
            model_name: The model name for the provider.

        Returns:
            A Pydantic AI model instance.

        Raises:
            ValueError: If the provider is not supported or API key is missing.
        """
        api_key = self.settings.get_api_key_for_provider(provider)

        if provider == LLMProvider.OPENAI:
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return OpenAIChatModel(
                model_name, provider=OpenAIProvider(api_key=api_key)
            )

        if provider == LLMProvider.ZAI:
            if not api_key:
                raise ValueError("LLM_API_KEY is required for z.ai provider")
            return OpenAIChatModel(
                model_name,
                provider=OpenAIProvider(
                    base_url="https://open.bigmodel.cn/api/paas/v4",
                    api_key=api_key
                )
            )

        if provider == LLMProvider.ANTHROPIC:
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            return AnthropicModel(
                model_name, provider=AnthropicProvider(api_key=api_key)
            )

        if provider == LLMProvider.GOOGLE:
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY (or GEMINI_API_KEY) is required for Google provider"
                )
            return GoogleModel(model_name, provider=GoogleProvider(api_key=api_key))

        if provider == LLMProvider.OLLAMA:
            return OpenAIChatModel(
                model_name,
                provider=OpenAIProvider(
                    base_url=self.settings.ollama_base_url,
                    api_key="ollama",
                ),
            )

        if provider == LLMProvider.DEEPSEEK:
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek provider")
            return OpenAIChatModel(
                model_name, provider=DeepSeekProvider(api_key=api_key)
            )

        if provider == LLMProvider.AZURE:
            if not api_key:
                raise ValueError("AZURE_OPENAI_API_KEY is required for Azure provider")
            if not self.settings.azure_openai_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure provider")
            azure_client = AsyncAzureOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_version=self.settings.azure_openai_api_version,
                api_key=api_key,
            )
            return OpenAIChatModel(
                model_name,
                provider=OpenAIProvider(openai_client=azure_client),
            )

        raise ValueError(f"Unsupported provider: {provider}")

    @property
    def is_available(self) -> bool:
        """Check if the LLM client is available."""
        return self._model is not None

    @property
    def model(self) -> Optional[Any]:
        """Get the underlying model for direct use with Pydantic AI Agent."""
        return self._model

    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt (async).

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The generated text response.
        """
        if not self._model:
            return FALLBACK_RESPONSE

        agent: Agent[None, str] = Agent(self._model)
        result = await agent.run(prompt)
        return result.output

    def generate_text_sync(self, prompt: str) -> str:
        """Generate text from a prompt (synchronous).

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The generated text response.
        """
        if not self._model:
            return FALLBACK_RESPONSE

        agent: Agent[None, str] = Agent(self._model)
        result = agent.run_sync(prompt)
        return result.output

    async def generate_with_system_prompt(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Generate text with a system prompt (async).

        Args:
            system_prompt: The system instructions for the LLM.
            user_prompt: The user message to respond to.

        Returns:
            The generated text response.
        """
        if not self._model:
            return FALLBACK_RESPONSE

        agent: Agent[None, str] = Agent(self._model, instructions=system_prompt)
        result = await agent.run(user_prompt)
        return result.output

    def generate_with_system_prompt_sync(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Generate text with a system prompt (synchronous).

        Args:
            system_prompt: The system instructions for the LLM.
            user_prompt: The user message to respond to.

        Returns:
            The generated text response.
        """
        if not self._model:
            return FALLBACK_RESPONSE

        agent: Agent[None, str] = Agent(self._model, instructions=system_prompt)
        result = agent.run_sync(user_prompt)
        return result.output

    def generate_medication_advice(
        self,
        medications: List[Dict[str, Any]],
        patient_info: Dict[str, Any],
        pubmed_context: List[Dict[str, Any]],
        medex_context: List[str],
    ) -> str:
        """Generate medication advice with comprehensive context.

        Args:
            medications: List of medications with names, URLs, schedules.
            patient_info: Patient demographics and clinical context.
            pubmed_context: Relevant medical literature from vector search.
            medex_context: Scraped drug information from MedEx.

        Returns:
            Generated medication advice.
        """
        if not self._model:
            return FALLBACK_RESPONSE

        system_prompt = """You are a medical AI assistant specializing in medication guidance and drug interactions.

Provide evidence-based medication advice following these guidelines:
1. Focus on drug safety, proper dosing, and potential interactions
2. Consider patient-specific factors (age, gender, medical conditions)
3. Use clear, professional medical terminology
4. Include practical management strategies and monitoring recommendations
5. Highlight any warnings or contraindications clearly

Format your response as a structured medical consultation with:
- Medication-specific guidance
- Interaction warnings (if applicable)
- Monitoring parameters
- Lifestyle recommendations
- Emergency protocols (if needed)"""

        user_prompt = f"""Patient Information:
- Age: {patient_info.get('age', 'N/A')}
- Gender: {patient_info.get('gender', 'N/A')}
- Medical Conditions: {', '.join(patient_info.get('medical_conditions', []))}
- Regimen Type: {patient_info.get('regimen_type', 'Unknown')}

Medications ({len(medications)}):
"""
        for i, med in enumerate(medications, 1):
            user_prompt += f"{i}. {med.get('name', 'Unknown')} - Schedule: {med.get('schedule', 'N/A')}\n"
            if med.get('url'):
                user_prompt += "   Database: Available\n"
            if med.get('medex_data'):
                user_prompt += "   Detailed Info: Available\n"

        drug_interactions = patient_info.get('drug_interactions', [])
        if drug_interactions:
            user_prompt += f"\nDrug Interactions Detected: {len(drug_interactions)}\n"
            for interaction in drug_interactions:
                user_prompt += f"- {interaction.get('description', 'Unknown interaction')}\n"

        if pubmed_context:
            user_prompt += f"\nEvidence Base: {len(pubmed_context)} relevant articles\n"
            for i, article in enumerate(pubmed_context[:5], 1):
                user_prompt += f"{i}. {article.get('title', 'Unknown')} ({article.get('publication_year', 'N/A')})\n"

        user_prompt += "\n\nBased on this comprehensive analysis, provide detailed medication guidance focusing on safety, efficacy, and patient-specific considerations."

        return self.generate_with_system_prompt_sync(system_prompt, user_prompt)

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration.

        Returns:
            A dictionary containing model configuration details.
        """
        return {
            "provider": self.settings.llm_provider.value,
            "model": self.settings.llm_model,
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
            "is_available": self.is_available,
        }


_llm_client: Optional[UnifiedLLMClient] = None


def get_llm_client() -> UnifiedLLMClient:
    """Get the shared LLM client instance.

    Returns:
        The singleton UnifiedLLMClient instance.
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = UnifiedLLMClient()
    return _llm_client


def reset_llm_client() -> None:
    """Reset the LLM client (useful for testing or reconfiguration)."""
    global _llm_client
    _llm_client = None
