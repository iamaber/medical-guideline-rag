from typing import List, Optional
from pydantic import BaseModel, Field


class DosDontsItem(BaseModel):
  text: str = Field(description="The specific recommendation text")
  category: str = Field(description="Category like 'timing', 'food', 'monitoring', 'safety'")


class DosDontsPair(BaseModel):
  do: DosDontsItem = Field(description="What the patient should do")
  dont: DosDontsItem = Field(description="What the patient should not do")


class MedicationRegimenSummary(BaseModel):
  therapeutic_purpose: str = Field(
    max_length=100, 
    description="Brief therapeutic purpose of the combination"
  )
  key_interaction: str = Field(
    max_length=100, 
    description="Primary interaction or safety concern"
  )
  timing_benefit: str = Field(
    max_length=100, 
    description="Main timing or administration advantage"
  )


class TherapeuticIndication(BaseModel):
  medication_name: str = Field(description="Name of the medication")
  indication: str = Field(description="Primary therapeutic indication")
  mechanism: str = Field(description="Brief mechanism of action")


class DosingStrategy(BaseModel):
  timing_coordination: str = Field(description="How to coordinate timing between medications")
  administration_guidelines: str = Field(description="Specific administration instructions")
  food_interactions: Optional[str] = Field(description="Food-related considerations")


class MonitoringParameter(BaseModel):
  parameter: str = Field(description="What to monitor")
  frequency: str = Field(description="How often to monitor")
  normal_range: Optional[str] = Field(description="Normal range or target values")


class SafetyMonitoring(BaseModel):
  key_parameters: List[MonitoringParameter] = Field(description="Key parameters to monitor")
  warning_signs: List[str] = Field(description="Warning signs to watch for")


class DrugInteraction(BaseModel):
  medications: str = Field(description="Medications involved in interaction")
  risk_level: str = Field(description="Risk level: low, moderate, high")
  description: str = Field(description="Description of the interaction")
  mitigation: str = Field(description="How to mitigate the interaction")


class LifestyleRecommendation(BaseModel):
  category: str = Field(description="Category like 'diet', 'exercise', 'sleep'")
  recommendation: str = Field(description="Specific recommendation")
  rationale: str = Field(description="Why this recommendation is important")


class StructuredMedicationAdvice(BaseModel):
  regimen_analysis: MedicationRegimenSummary = Field(
    description="Concise 3-point analysis of the medication regimen"
  )
  therapeutic_indications: List[TherapeuticIndication] = Field(
    description="Therapeutic indications for each medication"
  )
  dosing_strategy: DosingStrategy = Field(
    description="Integrated dosing and administration strategy"
  )
  safety_monitoring: SafetyMonitoring = Field(
    description="Safety monitoring protocol"
  )
  drug_interactions: List[DrugInteraction] = Field(
    description="Identified drug interactions and management"
  )
  dos_and_donts: List[DosDontsPair] = Field(
    description="Paired do's and don'ts for easy comparison",
    min_items=4,
    max_items=8
  )
  lifestyle_recommendations: List[LifestyleRecommendation] = Field(
    description="Coordinated lifestyle and dietary recommendations"
  )
  emergency_protocols: Optional[List[str]] = Field(
    description="Emergency protocols if applicable"
  )


class FormattedAdviceResponse(BaseModel):
  structured_advice: StructuredMedicationAdvice
  dos_donts_table: str = Field(description="Formatted markdown table of do's and don'ts")
  summary_html: Optional[str] = Field(description="HTML formatted summary for web display")
