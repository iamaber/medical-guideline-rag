"""Unified async LLM client supporting multiple providers via Pydantic AI.

This module provides a unified interface for interacting with various LLM providers.
Provider selection is done through environment variables:
- LLM_PROVIDER: groq (default), openai, anthropic, google, zai, ollama, azure, deepseek
- LLM_MODEL: model name for the selected provider
- <PROVIDER>_API_KEY: API key for the selected provider

Example usage:
    from src.services.llm_client import get_llm_client

    client = get_llm_client()
    generation = await client.generate_text("Hello, world!")
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

from groq import APITimeoutError, AsyncGroq
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from src.models.llm_config import LLMProvider, LLMSettings

logger = logging.getLogger(__name__)

MAX_EVIDENCE_CHARS = 6000
MAX_MEDEX_CHARS = 4000
MAX_ARTICLE_CHARS = 700
MAX_PROMPT_CHARS = 16000
MAX_OUTPUT_TOKENS = 2048
LLM_TIMEOUT_SECONDS = 30
PUBMED_ID_PATTERN = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)")

FALLBACK_RESPONSE = """I apologize, but I'm currently unable to process your request
due to a service configuration issue.

Please ensure that:
1. A valid API key is configured in your environment variables
2. The LLM_PROVIDER setting matches your API key
3. You have sufficient API credits/quota

For medical emergencies, please contact your healthcare provider immediately."""


@dataclass(frozen=True)
class Generation:
    text: str
    from_llm: bool


class UnifiedLLMClient:
    def __init__(self, settings: Optional[LLMSettings] = None) -> None:
        """Initialize the unified LLM client.

        Args:
            settings: Optional LLM settings. If not provided, settings are
                loaded from environment variables.
        """
        self.settings = settings or LLMSettings()
        self._model: Optional[Any] = None
        self._fallback_model: Optional[Any] = None
        self._initialize_model()

    @property
    def fallback_advice(self) -> str:
        missing_key = (
            self.settings.llm_provider != LLMProvider.OLLAMA
            and not self.settings.get_api_key_for_provider()
        )
        return self._failure_response("missing_key" if missing_key else "error")

    def _initialize_model(self) -> None:
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
            logger.error("Failed to initialize LLM client (%s)", type(e).__name__)
            self._model = None
            return
        fallback_model = self.settings.effective_fallback_model
        if fallback_model:
            self._fallback_model = self._create_model_for_provider(
                self.settings.llm_provider, fallback_model
            )

    def _create_model_for_provider(self, provider: LLMProvider, model_name: str) -> Any:
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

        if provider == LLMProvider.GROQ:
            if not api_key:
                raise ValueError("GROQ_API_KEY or LLM_API_KEY is required for Groq provider")
            groq_client = AsyncGroq(api_key=api_key, max_retries=0, timeout=LLM_TIMEOUT_SECONDS)
            return GroqModel(model_name, provider=GroqProvider(groq_client=groq_client))

        if provider == LLMProvider.OPENAI:
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return OpenAIChatModel(model_name, provider=OpenAIProvider(api_key=api_key))

        if provider == LLMProvider.ZAI:
            if not api_key:
                raise ValueError("LLM_API_KEY is required for z.ai provider")
            return OpenAIChatModel(
                model_name,
                provider=OpenAIProvider(
                    base_url="https://open.bigmodel.cn/api/paas/v4", api_key=api_key
                ),
            )

        if provider == LLMProvider.ANTHROPIC:
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            return AnthropicModel(model_name, provider=AnthropicProvider(api_key=api_key))

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
            return OpenAIChatModel(model_name, provider=DeepSeekProvider(api_key=api_key))

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
        return self._model

    def missing_configuration(self) -> List[str]:
        if self._model is not None:
            return []
        provider = self.settings.llm_provider
        if provider == LLMProvider.OLLAMA:
            return ["LLM_MODEL (no local Ollama model reachable)"]
        return [f"LLM_API_KEY or {provider.value.upper()}_API_KEY"]

    async def generate_text(self, prompt: str) -> Generation:
        return await self.generate("", prompt)

    def generate_text_sync(self, prompt: str) -> Generation:
        return self.generate_sync("", prompt)

    async def generate(self, system_prompt: str, user_prompt: str) -> Generation:
        if self._model is None:
            return Generation(self.fallback_advice, from_llm=False)
        if len(system_prompt) + len(user_prompt) > MAX_PROMPT_CHARS:
            logger.warning("Prompt exceeds %d characters", MAX_PROMPT_CHARS)
            return Generation(self._failure_response("error"), from_llm=False)
        try:
            return await self._run(
                self._model, self.settings.groq_reasoning_effort, system_prompt, user_prompt
            )
        except Exception as exc:
            if self._fallback_model is None or not self._is_rate_limited(exc):
                return Generation(self._failure_from_exception(exc), from_llm=False)
        logger.warning(
            "Primary model rate limited; trying %s", self.settings.effective_fallback_model
        )
        try:
            return await self._run(
                self._fallback_model,
                self.settings.groq_fallback_reasoning_effort,
                system_prompt,
                user_prompt,
            )
        except Exception as exc:
            return Generation(self._failure_from_exception(exc), from_llm=False)

    async def _run(
        self, model: Any, reasoning_effort: str, system_prompt: str, user_prompt: str
    ) -> Generation:
        agent = self._create_agent(model, reasoning_effort, system_prompt)
        async with asyncio.timeout(LLM_TIMEOUT_SECONDS):
            result = await agent.run(user_prompt, usage_limits=UsageLimits(request_limit=1))
        if result.response.finish_reason == "length":
            logger.warning("LLM response truncated at the output token limit")
        if not result.output.strip():
            raise ValueError("Empty model output")
        return Generation(result.output, from_llm=True)

    def generate_sync(self, system_prompt: str, user_prompt: str) -> Generation:
        # Reuse the event loop, as Agent.run_sync does, so pooled HTTP clients
        # remain usable across repeated synchronous calls.
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.generate(system_prompt, user_prompt))

    def _create_agent(
        self, model: Any, reasoning_effort: str, system_prompt: str
    ) -> Agent[None, str]:
        settings = ModelSettings(
            temperature=self.settings.llm_temperature,
            max_tokens=min(self.settings.llm_max_tokens, MAX_OUTPUT_TOKENS),
            top_p=self.settings.llm_top_p,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if self.settings.llm_provider == LLMProvider.GROQ and reasoning_effort:
            # Pydantic AI 1.30.1 forwards Groq-specific settings through extra_body.
            settings["extra_body"] = {"reasoning_effort": reasoning_effort}
        return Agent(model, instructions=system_prompt, model_settings=settings, retries=0)

    @staticmethod
    def _causes(exc: BaseException) -> List[BaseException]:
        causes = []
        cause: Optional[BaseException] = exc
        while cause is not None:
            causes.append(cause)
            cause = cause.__cause__
        return causes

    @classmethod
    def _is_rate_limited(cls, exc: BaseException) -> bool:
        return any(getattr(cause, "status_code", None) == 429 for cause in cls._causes(exc))

    @staticmethod
    def _retry_after(exc: BaseException) -> Optional[str]:
        headers = getattr(getattr(exc, "response", None), "headers", {})
        value = headers.get("retry-after", "").strip()
        if re.fullmatch(r"\d+(?:\.\d+)?", value):
            return f"{value} seconds"
        if value:
            try:
                return parsedate_to_datetime(value).isoformat()
            except (ValueError, TypeError, OverflowError):
                pass
        match = re.search(r"try again in (?:\d+(?:\.\d+)?(?:ms|s|m|h|d))+\b", str(exc))
        return match.group(0).removeprefix("try again in ") if match else None

    def _failure_response(self, reason: str, retry_after: Optional[str] = None) -> str:
        notes = {
            "rate_limit": "The provider rate limit or quota has been reached.",
            "timeout": "The AI request timed out after 30 seconds.",
            "error": "The AI service could not complete the request.",
        }
        if reason == "missing_key":
            note = f"API key is missing; configure {' or '.join(self.missing_configuration())}."
        else:
            note = notes[reason]
        if reason == "rate_limit" and retry_after:
            note += f" Retry after {retry_after}."
        return f"{FALLBACK_RESPONSE}\n\nService note: {note}"

    def _failure_from_exception(self, exc: Exception) -> str:
        reason = "error"
        retry_after = None
        for cause in self._causes(exc):
            if isinstance(cause, (TimeoutError, APITimeoutError)):
                reason = "timeout"
            if getattr(cause, "status_code", None) == 429:
                reason = "rate_limit"
                retry_after = self._retry_after(cause)
        logger.warning("LLM request failed (%s)", reason)
        return self._failure_response(reason, retry_after)

    async def generate_medication_advice(
        self,
        medications: List[Dict[str, Any]],
        patient_info: Dict[str, Any],
        pubmed_context: List[Dict[str, Any]],
        medex_context: List[str],
    ) -> Generation:
        system_prompt = """You are a medical AI assistant specializing in medication
guidance and drug interactions.

Provide evidence-based medication advice following these guidelines:
1. Ground every clinical claim in the supplied EVIDENCE BASE and DRUG MONOGRAPH excerpts
2. Focus on drug safety, proper dosing, and potential interactions
3. Consider patient-specific factors (age, gender, medical conditions)
4. Use clear, professional medical terminology
5. Include practical management strategies and monitoring recommendations
6. Highlight any warnings or contraindications clearly
7. Cite the supporting document ids in square brackets (e.g. [PMID:12345678]) next to
   claims that come from the evidence base. Never invent a citation.

If the supplied context does not cover a question, say so explicitly instead of guessing.

Use concise bullets and keep the full response to 700 words or fewer, including headings.
Format your response as a structured medical consultation with:
- Medication-specific guidance
- Interaction warnings (if applicable)
- Monitoring parameters
- Lifestyle recommendations
- Emergency protocols (if needed)"""

        user_prompt = f"""Patient Information:
- Age: {patient_info.get("age", "N/A")}
- Gender: {patient_info.get("gender", "N/A")}
- Medical Conditions: {", ".join(patient_info.get("medical_conditions", []))}
- Regimen Type: {patient_info.get("regimen_type", "Unknown")}

Medications ({len(medications)}):
"""
        for i, medication in enumerate(medications, 1):
            medication_name = medication.get("name", "Unknown")
            generic_name = medication.get("generic_name")
            if generic_name:
                medication_name = f"{medication_name} ({generic_name})"
            schedule = medication.get("schedule", "N/A")
            user_prompt += f"{i}. {medication_name} - Schedule: {schedule}\n"

        drug_interactions = patient_info.get("drug_interactions", [])
        if drug_interactions:
            user_prompt += f"\nDrug Interactions Detected: {len(drug_interactions)}\n"
            for interaction in drug_interactions:
                user_prompt += f"- {interaction.get('description', 'Unknown interaction')}\n"

        evidence = self._format_evidence(pubmed_context[:5])
        if evidence:
            shown = min(len(pubmed_context), 5)
            user_prompt += (
                f"\nEVIDENCE BASE ({len(pubmed_context)} retrieved articles, "
                f"top {shown} shown):\n"
            )
            user_prompt += evidence
        else:
            user_prompt += "\nEVIDENCE BASE: no matching literature was retrieved.\n"

        monographs = self._format_medex(medex_context)
        if monographs:
            user_prompt += f"\nDRUG MONOGRAPH EXCERPTS (scraped):\n{monographs}"
        else:
            user_prompt += "\nDRUG MONOGRAPH EXCERPTS: none available.\n"

        user_prompt += (
            "\n\nBased only on the patient profile, detected interactions and the "
            "supplied context above, provide concise medication guidance focusing on "
            "safety, efficacy, and patient-specific considerations. Cite evidence-backed "
            "claims with the bracketed labels shown above, such as [PMID:12345678]."
        )

        return await self.generate(system_prompt, user_prompt)

    @staticmethod
    def _citation_label(article: Dict[str, Any]) -> str:
        match = PUBMED_ID_PATTERN.search(str(article.get("source", "")))
        if match:
            return f"PMID:{match.group(1)}"
        return f"WHO: {article.get('title', 'Unknown')}"

    @classmethod
    def _format_evidence(cls, pubmed_context: List[Dict[str, Any]]) -> str:
        """Format retrieved articles with their actual text, truncated to a token budget."""
        if not pubmed_context:
            return ""

        blocks: List[str] = []
        remaining = MAX_EVIDENCE_CHARS

        for article in pubmed_context:
            if remaining <= 0:
                break

            title = article.get("title", "Unknown")
            year = article.get("publication_year", "N/A")
            body = article.get("abstract") or article.get("content") or ""
            body = " ".join(str(body).split())[:MAX_ARTICLE_CHARS]
            if not body:
                continue

            block = f"[{cls._citation_label(article)}] {title} ({year})\n{body}"
            block = block[:remaining]
            blocks.append(block)
            remaining -= len(block) + 2  # account for the "\n\n" separator

        return "\n\n".join(blocks)[:MAX_EVIDENCE_CHARS]

    @staticmethod
    def _format_medex(medex_context: List[str]) -> str:
        """Format scraped drug monographs, truncated to a token budget."""
        if not medex_context:
            return ""

        combined = "\n\n".join(" ".join(str(entry).split()) for entry in medex_context if entry)
        return combined[:MAX_MEDEX_CHARS]

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
