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
        """Build enhanced prompt with medical safety layers.

        Args:
            medications: Medication information
            patient_info: Patient information
            pubmed_context: Research context
            medex_context: Drug database context

        Returns:
            Formatted prompt
        """
        # Analyze medication risk profile
        risk_analysis = self._analyze_medication_risks(medications, patient_info)

        # Prioritize context based on risk level
        prioritized_context = self._prioritize_medical_context(
            pubmed_context, medex_context, risk_analysis
        )

        # Dynamic instruction adaptation
        safety_instructions = self._generate_safety_instructions(risk_analysis)

        # Format medications with risk assessment
        med_list = []
        for med in medications:
            med_info = f"- **{med['name']}** (Schedule: {med['schedule']})"
            if med.get("url"):
                med_info += " - Database Entry Available"
            med_list.append(med_info)

        # Gender mapping for better readability
        gender_map = {"M": "Male", "F": "Female", "O": "Other"}
        gender_display = gender_map.get(patient_info.get("gender", "O"), "Other")

        # Build enhanced prompt
        prompt = f"""You are an expert clinical pharmacist providing evidence-based medication guidance.

**RISK ASSESSMENT:**
{risk_analysis["summary"]}

**PATIENT INFORMATION:**
- Age: {patient_info.get("age", "Not specified")} years
- Gender: {gender_display}
- Risk Level: {risk_analysis["level"]}

**PRESCRIBED MEDICATIONS & SCHEDULE:**
{chr(10).join(med_list)}

**PRIORITIZED MEDICAL EVIDENCE:**
{prioritized_context}

**SAFETY INSTRUCTIONS:**
{safety_instructions}

**RESPONSE STRUCTURE:**
{self._get_response_structure(risk_analysis["level"])}

Please provide comprehensive, evidence-based advice following this structure."""

        return prompt

    def _analyze_medication_risks(
        self, medications: List[Dict], patient_info: Dict
    ) -> Dict:
        """Analyze risk profile of medication combination."""
        risk_level = "low"
        risk_factors = []

        # High-risk medications
        high_risk_meds = ["warfarin", "insulin", "digoxin", "lithium"]
        moderate_risk_meds = ["metformin", "lisinopril", "atorvastatin"]

        for med in medications:
            med_name = med.get("name", "").lower()
            if any(high_risk in med_name for high_risk in high_risk_meds):
                risk_level = "high"
                risk_factors.append(f"High-risk medication: {med['name']}")
            elif any(mod_risk in med_name for mod_risk in moderate_risk_meds):
                if risk_level == "low":
                    risk_level = "moderate"
                risk_factors.append(f"Moderate-risk medication: {med['name']}")

        # Age-based risk factors
        age = patient_info.get("age", 0)
        if age > 65:
            risk_factors.append("Elderly patient (>65 years)")
            if risk_level == "low":
                risk_level = "moderate"
        elif age < 18:
            risk_factors.append("Pediatric patient (<18 years)")
            if risk_level == "low":
                risk_level = "moderate"

        # Multiple medication risk
        if len(medications) > 3:
            risk_factors.append("Polypharmacy (>3 medications)")
            if risk_level == "low":
                risk_level = "moderate"

        summary = (
            f"Risk Level: {risk_level.upper()}. " + "; ".join(risk_factors)
            if risk_factors
            else "No significant risk factors identified."
        )

        return {"level": risk_level, "factors": risk_factors, "summary": summary}

    def _prioritize_medical_context(
        self, pubmed_context: List[Dict], medex_context: List[str], risk_analysis: Dict
    ) -> str:
        """Prioritize context based on risk analysis."""
        context_parts = []

        # Format PubMed context with risk-based prioritization
        if pubmed_context:
            context_parts.append("**RESEARCH EVIDENCE (PubMed):**")

            # Sort by relevance score and prioritize safety-related content for high-risk cases
            sorted_context = sorted(
                pubmed_context, key=lambda x: x.get("relevance_score", 0), reverse=True
            )

            for i, doc in enumerate(sorted_context[:3]):  # Limit to top 3
                title = doc.get("title", "N/A")
                content = doc.get("content", "")[:400]
                relevance = doc.get("relevance_score", 0)

                context_parts.append(
                    f"""
**Article {i + 1}:**
Title: {title}
Content: {content}...
Relevance Score: {relevance:.3f}
""".strip()
                )

        # Format MedEx context
        if medex_context:
            context_parts.append("\n**DRUG DATABASE INFORMATION (MedEx):**")
            combined_medex = "\n".join(medex_context[:2])  # Limit to first 2 entries
            if len(combined_medex) > 1000:
                combined_medex = combined_medex[:1000] + "..."
            context_parts.append(combined_medex)

        return (
            "\n".join(context_parts)
            if context_parts
            else "No relevant medical literature found"
        )

    def _generate_safety_instructions(self, risk_analysis: Dict) -> str:
        """Generate safety instructions based on risk level."""
        risk_level = risk_analysis["level"]

        base_instructions = [
            "- Prioritize patient safety in all recommendations",
            "- Base advice on provided evidence",
            "- Include appropriate medical disclaimers",
        ]

        if risk_level == "high":
            safety_instructions = base_instructions + [
                "- EMPHASIZE monitoring requirements for high-risk medications",
                "- Highlight potential serious adverse effects",
                "- Recommend close healthcare provider communication",
                "- Include emergency contact recommendations",
            ]
        elif risk_level == "moderate":
            safety_instructions = base_instructions + [
                "- Include monitoring recommendations",
                "- Mention common side effects to watch for",
                "- Suggest regular healthcare provider follow-up",
            ]
        else:
            safety_instructions = base_instructions + [
                "- Provide general monitoring guidance",
                "- Include standard safety precautions",
            ]

        return "\n".join(safety_instructions)

    def _get_response_structure(self, risk_level: str) -> str:
        """Get response structure based on risk level."""
        base_structure = """
## 1. Probable Indications
## 2. Do's and Don'ts  
## 3. Warnings & Safety Alerts
## 4. Lifestyle Guidelines
## 5. Drug Interactions & Monitoring
"""

        if risk_level == "high":
            return (
                base_structure
                + """
## 6. URGENT MONITORING REQUIREMENTS
## 7. Emergency Contact Guidelines
"""
            )
        elif risk_level == "moderate":
            return (
                base_structure
                + """
## 6. Monitoring Recommendations
"""
            )
        else:
            return base_structure

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
