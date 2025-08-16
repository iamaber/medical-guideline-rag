"""LLM service using Google Gemini for generating medication advice."""

import logging
from typing import List, Dict
from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API to generate medication advice."""

    def __init__(self):
        """Initialize the Gemini client."""
        self.api_key = GEMINI_API_KEY
        self.model_name = GEMINI_MODEL_NAME
        self.model = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Gemini API client."""
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini client with model: {self.model_name}")
        except ImportError:
            logger.error(
                "google-generativeai not installed. Install with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    def generate_advice(
        self,
        medications: List[Dict],
        patient_info: Dict,
        pubmed_context: List[Dict],
        medex_context: List[str],
    ) -> str:
        """Generate medication advice using Gemini.

        Args:
            medications: List of medication information
            patient_info: Patient demographic information
            pubmed_context: Relevant PubMed articles
            medex_context: Scraped MedEx information

        Returns:
            Generated medication advice
        """
        if not self.model:
            return self._fallback_advice()

        try:
            prompt = self._build_prompt(
                medications, patient_info, pubmed_context, medex_context
            )

            # Generate response with safety settings
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temperature for more consistent medical advice
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                },
            )

            if response.text:
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return self._fallback_advice()

        except Exception as e:
            logger.error(f"Error generating advice with Gemini: {e}")
            return self._fallback_advice()

    def _build_prompt(
        self,
        medications: List[Dict],
        patient_info: Dict,
        pubmed_context: List[Dict],
        medex_context: List[str],
    ) -> str:
        """Build the prompt for Gemini.

        Args:
            medications: Medication information
            patient_info: Patient information
            pubmed_context: Research context
            medex_context: Drug database context

        Returns:
            Formatted prompt
        """
        # Format medications
        med_list = []
        for med in medications:
            med_info = f"- **{med['name']}** (Schedule: {med['schedule']})"
            if med.get("url"):
                med_info += f" [Database Entry Available]"
            med_list.append(med_info)

        # Format PubMed context (limit to most relevant)
        pubmed_snippets = []
        for i, doc in enumerate(pubmed_context[:3]):  # Limit to top 3 articles
            snippet = f"""
**Research Article {i + 1}:**
Title: {doc.get("title", "N/A")}
Content: {doc.get("content", "")[:400]}...
Relevance Score: {doc.get("relevance_score", 0):.3f}
"""
            pubmed_snippets.append(snippet.strip())

        # Format MedEx context
        medex_info = (
            "\n".join(medex_context[:3]) if medex_context else "No MedEx data available"
        )
        if medex_info and len(medex_info) > 1500:
            medex_info = medex_info[:1500] + "..."

        # Gender mapping for better readability
        gender_map = {"M": "Male", "F": "Female", "O": "Other"}
        gender_display = gender_map.get(patient_info.get("gender", "O"), "Other")

        prompt = f"""You are an expert clinical pharmacist providing evidence-based medication guidance. Your role is to analyze the provided information and give comprehensive, safe, and practical advice.

**PATIENT INFORMATION:**
- Age: {patient_info.get("age", "Not specified")} years
- Gender: {gender_display}

**PRESCRIBED MEDICATIONS & SCHEDULE:**
{chr(10).join(med_list)}

**DRUG DATABASE INFORMATION (MedEx):**
{medex_info}

**RELEVANT MEDICAL LITERATURE (PubMed):**
{chr(10).join(pubmed_snippets) if pubmed_snippets else "No relevant research articles found"}

**INSTRUCTIONS:**
Please provide comprehensive medication advice in the following structured format:

## 1. Probable Indications
List the likely medical conditions being treated by these medications, based on the provided information.

## 2. Do's and Don'ts
**Do's:**
- Provide specific recommendations for proper medication use
- Include timing, food interactions, and administration guidelines

**Don'ts:**
- List important warnings and contraindications
- Highlight potential risks and what to avoid

## 3. Warnings & Safety Alerts
- Critical safety information specific to these medications
- Potential side effects to monitor
- When to contact healthcare provider immediately

## 4. Lifestyle Guidelines
- Dietary recommendations and restrictions
- Activity modifications if needed
- General health optimization tips relevant to the medications

## 5. Drug Interactions & Monitoring
- Potential interactions between the prescribed medications
- Important monitoring parameters
- Laboratory tests that may be needed

**IMPORTANT GUIDELINES:**
- Base your advice on the provided research evidence
- Consider the patient's age and gender in your recommendations
- Use clear, patient-friendly language
- Prioritize safety and evidence-based practices
- Include a medical disclaimer

**MEDICAL DISCLAIMER:**
Always include that this is educational information only and not a substitute for professional medical advice. Patients should consult with their healthcare provider for personalized medical decisions.

Please provide comprehensive, evidence-based advice following this structure."""

        return prompt

    def _fallback_advice(self) -> str:
        """Provide fallback advice when Gemini is not available.

        Returns:
            Basic safety advice
        """
        return """## Important Notice

I apologize, but I'm currently unable to generate personalized medication advice due to a technical issue with the AI service. 

## General Medication Safety Guidelines

### Do's:
- Take medications exactly as prescribed by your healthcare provider
- Take medications at the same time each day
- Store medications in a cool, dry place
- Keep a list of all your medications

### Don'ts:
- Never stop taking medications without consulting your doctor
- Don't share medications with others
- Avoid alcohol unless approved by your healthcare provider
- Don't take expired medications

### When to Contact Your Healthcare Provider:
- If you experience any unusual side effects
- If you miss multiple doses
- If you have questions about your medications
- Before starting any new medications or supplements

## Medical Disclaimer
This information is for educational purposes only and is not a substitute for professional medical advice. Please consult with your healthcare provider for personalized medical guidance and before making any changes to your medication regimen.

**For immediate medical concerns, contact your healthcare provider or emergency services.**"""

    def test_connection(self) -> bool:
        """Test connection to Gemini API.

        Returns:
            True if connection is successful
        """
        if not self.model:
            return False

        try:
            test_response = self.model.generate_content("Test message")
            return bool(test_response.text)
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False

    def get_model_info(self) -> Dict:
        """Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "api_key_configured": bool(self.api_key),
            "client_initialized": bool(self.model),
            "connection_test": self.test_connection(),
        }
