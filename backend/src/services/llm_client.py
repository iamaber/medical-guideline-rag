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
from src.models.medication_advice import StructuredMedicationAdvice

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """Unified async LLM client supporting multiple providers via Pydantic AI.

    Provider selection is done through environment variables. The client
    automatically initializes the appropriate model based on the configured
    provider.

    Attributes:
        settings: LLM configuration settings loaded from environment.
        is_available: Whether the LLM client is properly initialized.
        model: The underlying Pydantic AI model instance.
    """

    def __init__(self, settings: Optional[LLMSettings] = None):
        """Initialize the unified LLM client.

        Args:
            settings: Optional LLM settings. If not provided, settings are
                loaded from environment variables.
        """
        self.settings = settings or LLMSettings()
        self._model = None
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

    def _create_model_for_provider(self, provider: LLMProvider, model_name: str):
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
    def model(self):
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
            return self._fallback_response()

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
            return self._fallback_response()

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
            return self._fallback_response()

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
            return self._fallback_response()

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
            return self._fallback_response()

        # Build system prompt for medical advice
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

        # Build user prompt with all context
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
                user_prompt += f"   Database: Available\n"
            if med.get('medex_data'):
                user_prompt += f"   Detailed Info: Available\n"

        # Add drug interactions if present
        drug_interactions = patient_info.get('drug_interactions', [])
        if drug_interactions:
            user_prompt += f"\nDrug Interactions Detected: {len(drug_interactions)}\n"
            for interaction in drug_interactions:
                user_prompt += f"- {interaction.get('description', 'Unknown interaction')}\n"

        # Add PubMed context
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


# Medical RAG System Prompt with drug interaction focus
MEDICAL_RAG_SYSTEM_PROMPT = """
You are an expert clinical pharmacist and medical advisor providing evidence-based medication guidance.

CRITICAL PRIORITY: Drug Interaction Safety

When analyzing medications, ALWAYS:

1. FIRST: Identify ALL potential drug interactions
   - Class-based interactions (e.g., NSAID + ACE inhibitor)
   - Direct drug-drug interactions
   - Disease-drug interactions
   - Food-drug interactions

2. SECOND: Classify interaction severity
   - MINOR: Monitor, usually manageable
   - MODERATE: Clinical monitoring, dose adjustment
   - MAJOR: Close monitoring, consider alternative
   - SEVERE: Avoid combination, medical attention may be needed
   - CONTRAINDICATED: Do not use together

3. THIRD: Provide actionable management
   - How to mitigate interaction
   - What to monitor
   - When to seek medical help

4. FOURTH: Provide patient-friendly guidance
   - Clear do's and don'ts
   - Warning signs to watch for
   - Lifestyle considerations

STRUCTURED OUTPUT REQUIRED:
- Therapeutic Indications: What each medication treats and mechanism
- Drug Interactions: ALL potential interactions with risk level, description, mitigation
- Dosing Strategy: How to coordinate timing between medications
- Safety Monitoring: Parameters to monitor, warning signs
- Do's and Don'ts: Pairs for easy patient understanding (4-8 pairs)
- Lifestyle Recommendations: Diet, exercise, activity considerations
- Emergency Protocols: When to seek immediate help

FORMATTING REQUIREMENTS:
- Use markdown-style formatting for dos/donts tables
- Bold interaction warnings with severity indicators
- Include clinical references from provided articles
- Use clear, non-technical language for patients
- Include medical terminology for healthcare professionals
- Always include disclaimer: "Consult your healthcare provider"

SAFETY DISCLAIMER (always include at end):
"This information is for educational purposes only. It is not a substitute
for professional medical advice, diagnosis, or treatment. Always consult your
healthcare provider before making any changes to your medication regimen."
"""


class MedicalRAGAgent:
    """Medical RAG agent using Pydantic AI for structured responses.

    This agent focuses on drug interaction safety while providing comprehensive
    medication guidance.
    """

    def __init__(self, model: Any):
        """Initialize the medical RAG agent.

        Args:
            model: The underlying Pydantic AI model.
        """
        self.agent = Agent(
            model,
            result_type=StructuredMedicationAdvice,
            instructions=MEDICAL_RAG_SYSTEM_PROMPT
        )
        logger.info("MedicalRAGAgent initialized with structured output type")

    def generate_advice(
        self,
        medications: List[Dict],
        patient_info: Dict,
        pubmed_context: List[Dict],
        medex_context: List[str],
        interactions: Optional[List[Dict]] = None
    ) -> StructuredMedicationAdvice:
        """Generate structured medication advice with drug interaction focus.

        Args:
            medications: List of medication dictionaries with name, schedule, url.
            patient_info: Patient information (age, gender, conditions).
            pubmed_context: Retrieved medical literature.
            medex_context: Drug information from medical databases.
            interactions: Optional list of pre-detected drug interactions.

        Returns:
            StructuredMedicationAdvice with all sections.
        """
        prompt = self._build_enhanced_prompt(
            medications, patient_info, pubmed_context, medex_context, interactions
        )

        try:
            result = self.agent.run_sync(prompt)
            logger.info("Successfully generated structured medication advice")
            return result.output
        except Exception as e:
            logger.error(f"Failed to generate structured advice: {e}", exc_info=True)
            raise

    def _build_enhanced_prompt(
        self,
        medications: List[Dict],
        patient_info: Dict,
        pubmed_context: List[Dict],
        medex_context: List[str],
        interactions: Optional[List[Dict]]
    ) -> str:
        """Build enhanced prompt with all context and interaction data.

        Args:
            medications: List of medication dictionaries.
            patient_info: Patient information.
            pubmed_context: Retrieved medical literature.
            medex_context: Drug information.
            interactions: Optional drug interactions.

        Returns:
            Complete prompt string for LLM.
        """
        prompt_parts = []

        # Patient information
        prompt_parts.append(f"""
PATIENT INFORMATION:
- Age: {patient_info.get('age', 'Unknown')}
- Gender: {patient_info.get('gender', 'Unknown')}
- Conditions: {', '.join(patient_info.get('medical_conditions', ['None']))}
        """)

        # Medications
        prompt_parts.append("\nMEDICATIONS:")
        for i, med in enumerate(medications, 1):
            prompt_parts.append(f"""
{i}. {med.get('name', 'Unknown')}
   - Schedule: {med.get('schedule', 'Unknown')}
   - In Database: {'Yes' if med.get('url') else 'No'}
   - Has Detailed Info: {'Yes' if med.get('medex_data') else 'No'}
            """)

        # Drug Interactions (PROMINENT)
        if interactions:
            prompt_parts.append("\n" + "=" * 60)
            prompt_parts.append("DRUG INTERACTIONS - CRITICAL SAFETY INFORMATION")
            prompt_parts.append("=" * 60)

            for i, interaction in enumerate(interactions, 1):
                risk_level = interaction.get('severity', 'Unknown')
                prompt_parts.append(f"""
{i}. {', '.join(interaction.get('medications', []))}
   Severity: {risk_level.upper()}
   Category: {interaction.get('category', 'Unknown')}
   Description: {interaction.get('description', 'No description')}
   Mechanism: {interaction.get('mechanism', 'Unknown')}
   Clinical Significance: {interaction.get('clinical_significance', 'Unknown')}
   Risk Factors: {', '.join(interaction.get('risk_factors', []))}
   Monitoring Required: {', '.join(interaction.get('monitoring_required', []))}
   Management Strategy: {interaction.get('management_strategy', 'Consult provider')}
                """)

            prompt_parts.append("\nIMPORTANT: These interactions MUST be addressed prominently in your response!")
        else:
            prompt_parts.append("\nDRUG INTERACTIONS: No known interactions detected based on our current knowledge.")

        # PubMed Context
        prompt_parts.append("\n" + "-" * 60)
        prompt_parts.append("RELEVANT MEDICAL LITERATURE")
        prompt_parts.append("-" * 60)

        for i, article in enumerate(pubmed_context[:10], 1):
            prompt_parts.append(f"""
{i}. {article.get('title', 'Untitled')}
   Source: {article.get('source', 'Unknown')}
   Year: {article.get('publication_year', 'Unknown')}
   Section: {article.get('section_type', 'General')}
   {article.get('abstract', '')[:300]}...
            """)

        # MedEx Drug Information
        if medex_context:
            prompt_parts.append("\n" + "-" * 60)
            prompt_parts.append("DRUG INFORMATION FROM MEDICAL DATABASES")
            prompt_parts.append("-" * 60)

            for i, medex in enumerate(medex_context, 1):
                truncated = medex[:500] + "..." if len(medex) > 500 else medex
                prompt_parts.append(f"""
{i}. {truncated}
                """)

        # Instructions
        prompt_parts.append("\n" + "=" * 60)
        prompt_parts.append("YOUR TASK")
        prompt_parts.append("=" * 60)
        prompt_parts.append("""
Generate comprehensive medication guidance addressing:

1. ALL drug interactions listed above (make them PROMINENT with severity indicators)
2. How to safely take these medications together
3. What to monitor and warning signs
4. Clear do's and don'ts (4-8 pairs in markdown table format)
5. Lifestyle and dietary recommendations
6. When to seek emergency medical help

CRITICAL: If ANY severe or contraindicated interactions are present,
make them the FIRST and MOST PROMINENT part of your response.
Use ALERT formatting (⚠️, ❌, ✅) to highlight important safety information.

ALWAYS include this disclaimer at the end:
"This information is for educational purposes only. It is not a substitute
for professional medical advice, diagnosis, or treatment. Always consult your
healthcare provider before making any changes to your medication regimen."
        """)

        return "\n".join(prompt_parts)


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


def get_medical_rag_agent() -> MedicalRAGAgent:
    """Get medical RAG agent for structured responses.

    Returns:
        MedicalRAGAgent instance initialized with current LLM model.
    """
    client = get_llm_client()
    if not client.is_available:
        logger.error("Cannot create RAG agent: LLM client not available")
        raise RuntimeError("LLM client not available")

    return MedicalRAGAgent(client.model)
