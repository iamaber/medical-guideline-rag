import logging
from typing import List, Dict
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
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
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini client: {self.model_name}")
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
        if not self.model:
            return self._fallback_advice()

        try:
            # Use the improved structured prompt
            prompt = self._build_structured_prompt(
                medications, patient_info, pubmed_context, medex_context
            )

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
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

    def _build_structured_prompt(
        self,
        medications: List[Dict],
        patient_info: Dict,
        pubmed_context: List[Dict],
        medex_context: List[str],
    ) -> str:
        """Build prompt for structured output."""
        # Analyze medication risk profile
        risk_analysis = self._analyze_medication_risks(medications, patient_info)

        # Prioritize context based on risk level
        prioritized_context = self._prioritize_medical_context(
            pubmed_context, medex_context, risk_analysis
        )

        # Format medications with risk assessment and combination analysis
        med_list = []
        for med in medications:
            med_info = f"- **{med['name']}** (Schedule: {med['schedule']})"
            if med.get("url"):
                med_info += " - Database Entry Available"
            med_list.append(med_info)

        # Generate medication combination context
        combination_context = self._generate_combination_context(
            medications, patient_info
        )

        # Gender mapping for better readability
        gender_map = {"M": "Male", "F": "Female", "O": "Other"}
        gender_display = gender_map.get(patient_info.get("gender", "O"), "Other")

        prompt = f"""You are an expert clinical pharmacist providing evidence-based medication guidance for a complete medication regimen.

**CRITICAL FORMATTING INSTRUCTIONS:**
- Start each section with proper markdown headers (##)
- For MEDICATION REGIMEN ANALYSIS section: Use EXACTLY 3 bullet points (•)
- Each bullet point must be under 20 words
- Focus only on: therapeutic purpose, key interactions, timing benefits
- Add blank line after MEDICATION REGIMEN ANALYSIS section before next section
- Use professional medical language without conversational phrases
- Do NOT use phrases like "Okay, here's..." or "Let me provide..."
- Create a DO'S AND DON'TS table with exactly this format:

| ❌ DON'T | ✅ DO |
|----------|-------|
| [specific don't action] | [specific do action] |
| [specific don't action] | [specific do action] |
| [specific don't action] | [specific do action] |
| [specific don't action] | [specific do action] |

**CONTENT INSTRUCTIONS:**
- Analyze ALL medications as a COMBINED REGIMEN, not individually
- Focus on synergistic effects, drug interactions, and overall therapeutic strategy
- Provide unified timing recommendations and lifestyle modifications
- Address the patient's complete treatment plan holistically

**PATIENT PROFILE:**
- Age: {patient_info.get("age", "Not specified")} years
- Gender: {gender_display}
- Medication Risk Level: {risk_analysis["level"]}

**COMPLETE MEDICATION REGIMEN:**
{chr(10).join(med_list)}

**MEDICATION COMBINATION ANALYSIS:**
{combination_context}

**CLINICAL EVIDENCE BASE:**
{prioritized_context}

**RISK ASSESSMENT:**
{risk_analysis["summary"]}

**REQUIRED RESPONSE FORMAT:**
## MEDICATION REGIMEN ANALYSIS
• [First bullet: therapeutic purpose/indication - max 20 words]
• [Second bullet: key interaction or safety concern - max 20 words]  
• [Third bullet: timing/administration benefit - max 20 words]

## THERAPEUTIC INDICATIONS & RATIONALE

## INTEGRATED DOSING STRATEGY
### Timing Coordination
### Administration Guidelines

## SAFETY MONITORING PROTOCOL
### Key Parameters to Monitor
### Warning Signs

## DRUG INTERACTION MANAGEMENT
### Identified Interactions
### Mitigation Strategies

## DO'S AND DON'TS REFERENCE TABLE
[Create the table exactly as specified above with 4-6 rows of specific, actionable advice]

## LIFESTYLE & DIETARY CONSIDERATIONS
### Coordinated Recommendations
### Timing with Meals

Provide a comprehensive, professional medication management plan that addresses this specific combination of medications. Focus on integration, not individual drug analysis."""

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

    def _generate_combination_context(
        self, medications: List[Dict], patient_info: Dict
    ) -> str:
        """Generate context for medication combination analysis."""
        if len(medications) <= 1:
            return f"Single medication regimen: {medications[0]['name'] if medications else 'No medications'}"

        medication_names = [med["name"] for med in medications]
        schedules = [med["schedule"] for med in medications]

        # Analyze therapeutic categories
        therapeutic_analysis = self._analyze_therapeutic_categories(medications)

        # Timing analysis
        timing_analysis = self._analyze_medication_timing(medications)

        # Drug interaction potential
        interaction_analysis = self._analyze_interaction_potential(medication_names)

        combination_context = f"""
**REGIMEN OVERVIEW:**
- Total medications: {len(medications)}
- Medication names: {", ".join(medication_names)}
- Dosing schedules: {", ".join(set(schedules))}

**THERAPEUTIC CATEGORY ANALYSIS:**
{therapeutic_analysis}

**TIMING COORDINATION:**
{timing_analysis}

**INTERACTION ASSESSMENT:**
{interaction_analysis}
""".strip()

        return combination_context

    def _analyze_therapeutic_categories(self, medications: List[Dict]) -> str:
        """Analyze therapeutic categories of medications."""
        # Common therapeutic categories mapping
        category_mapping = {
            "metformin": "Antidiabetic (Biguanide)",
            "insulin": "Antidiabetic (Hormone)",
            "lisinopril": "Antihypertensive (ACE Inhibitor)",
            "atorvastatin": "Lipid-lowering (Statin)",
            "warfarin": "Anticoagulant",
            "aspirin": "Antiplatelet/Analgesic",
            "omeprazole": "Proton Pump Inhibitor",
            "levothyroxine": "Thyroid Hormone",
            "amlodipine": "Antihypertensive (Calcium Channel Blocker)",
            "hydrochlorothiazide": "Diuretic (Thiazide)",
        }

        categories = []
        for med in medications:
            med_name = med["name"].lower()
            category = "Unknown category"
            for drug, cat in category_mapping.items():
                if drug in med_name:
                    category = cat
                    break
            categories.append(f"- {med['name']}: {category}")

        if len(set(cat.split(":")[1].strip() for cat in categories)) > 1:
            analysis = "Multi-system therapeutic approach detected. Requires coordinated management."
        else:
            analysis = "Single therapeutic category. Monitor for cumulative effects."

        return f"{chr(10).join(categories)}\n{analysis}"

    def _analyze_medication_timing(self, medications: List[Dict]) -> str:
        """Analyze medication timing for optimal coordination."""
        schedules = [med["schedule"] for med in medications]
        unique_schedules = set(schedules)

        if len(unique_schedules) == 1:
            timing_note = f"All medications on {list(unique_schedules)[0]} schedule. Simplifies adherence but may require staggered timing."
        else:
            timing_note = f"Multiple dosing schedules ({', '.join(unique_schedules)}). Requires careful timing coordination."

        # Identify potential timing conflicts
        conflicts = []
        for i, med1 in enumerate(medications):
            for j, med2 in enumerate(medications[i + 1 :], i + 1):
                if self._has_timing_conflict(med1["name"], med2["name"]):
                    conflicts.append(f"{med1['name']} and {med2['name']}")

        if conflicts:
            timing_note += f"\nPotential timing conflicts: {'; '.join(conflicts)}"
        else:
            timing_note += "\nNo significant timing conflicts identified."

        return timing_note

    def _has_timing_conflict(self, drug1: str, drug2: str) -> bool:
        """Check if two drugs have potential timing conflicts."""
        # Common timing conflicts
        timing_conflicts = [
            ("levothyroxine", "calcium"),
            ("levothyroxine", "iron"),
            ("warfarin", "vitamin k"),
            ("tetracycline", "dairy"),
        ]

        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()

        for conflict_pair in timing_conflicts:
            if (
                conflict_pair[0] in drug1_lower and conflict_pair[1] in drug2_lower
            ) or (conflict_pair[1] in drug1_lower and conflict_pair[0] in drug2_lower):
                return True
        return False

    def _analyze_interaction_potential(self, medication_names: List[str]) -> str:
        """Analyze potential drug-drug interactions."""
        high_risk_combinations = [
            ("warfarin", "aspirin"),
            ("warfarin", "clopidogrel"),
            ("digoxin", "amiodarone"),
            ("lithium", "lisinopril"),
            ("metformin", "contrast"),
        ]

        moderate_risk_combinations = [
            ("atorvastatin", "diltiazem"),
            ("omeprazole", "clopidogrel"),
            ("lisinopril", "spironolactone"),
        ]

        found_interactions = []
        risk_level = "low"

        for i, med1 in enumerate(medication_names):
            for j, med2 in enumerate(medication_names[i + 1 :], i + 1):
                med1_lower = med1.lower()
                med2_lower = med2.lower()

                # Check high-risk combinations
                for combo in high_risk_combinations:
                    if (combo[0] in med1_lower and combo[1] in med2_lower) or (
                        combo[1] in med1_lower and combo[0] in med2_lower
                    ):
                        found_interactions.append(f"HIGH RISK: {med1} + {med2}")
                        risk_level = "high"

                # Check moderate-risk combinations
                for combo in moderate_risk_combinations:
                    if (combo[0] in med1_lower and combo[1] in med2_lower) or (
                        combo[1] in med1_lower and combo[0] in med2_lower
                    ):
                        found_interactions.append(f"MODERATE RISK: {med1} + {med2}")
                        if risk_level == "low":
                            risk_level = "moderate"

        if found_interactions:
            return (
                f"Interaction risk level: {risk_level.upper()}\nIdentified interactions:\n"
                + "\n".join([f"- {interaction}" for interaction in found_interactions])
            )
        else:
            return (
                "No significant drug-drug interactions identified in current database."
            )

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

    def _fallback_advice(self) -> str:
        """Provide fallback advice when Gemini is not available."""
        return """## MEDICATION REGIMEN ANALYSIS

**Service Temporarily Unavailable**

The AI-powered medication analysis service is currently experiencing technical difficulties. Please refer to the general safety guidelines below and consult your healthcare provider for specific medication advice.

## STANDARD MEDICATION SAFETY PROTOCOL

### Essential Safety Measures:
- Administer all medications exactly as prescribed by your healthcare provider
- Maintain consistent timing for all doses within your regimen
- Store medications according to manufacturer specifications
- Maintain an updated medication list including dosages and schedules

### Critical Precautions:
- Do not discontinue any medication without physician consultation
- Avoid sharing medications between individuals
- Restrict alcohol consumption unless specifically approved by healthcare provider
- Do not consume expired medications

### Immediate Healthcare Provider Contact Required For:
- Any unexpected adverse reactions or side effects
- Multiple missed doses across your medication regimen
- Questions regarding medication interactions or timing
- Before initiating any new medications, supplements, or treatments

### Emergency Protocol:
For acute medical concerns, severe adverse reactions, or medication-related emergencies, contact your healthcare provider immediately or seek emergency medical care.

## MEDICAL DISCLAIMER

This information serves educational purposes exclusively and does not constitute professional medical advice, diagnosis, or treatment recommendations. Individual medication management requires personalized clinical assessment and ongoing healthcare provider supervision.

**Immediate medical attention should be sought for any urgent health concerns.**"""

    def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        if not self.model:
            return False

        try:
            test_response = self.model.generate_content("Test message")
            return bool(test_response.text)
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False

    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "api_key_configured": bool(self.api_key),
            "client_initialized": bool(self.model),
            "connection_test": self.test_connection(),
        }
