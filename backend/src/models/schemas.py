"""Pydantic models for API request and response schemas."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from config.settings import Defaults

MAX_MEDICATIONS = Defaults.MAX_MEDICATIONS
MAX_MEDICATION_NAME_LENGTH = 100


class GenderEnum(str, Enum):
    """Patient gender options."""

    MALE = "M"
    FEMALE = "F"


class UserInput(BaseModel):
    """User input for medication advice request."""

    meds: List[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_MEDICATIONS,
        description="List of medication names",
    )
    schedule: List[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_MEDICATIONS,
        description="Dosing schedule for each medication (e.g., '1+0+1')",
    )
    age: int = Field(..., ge=1, le=120, description="Patient age")
    gender: GenderEnum = Field(..., description="Patient gender")
    conditions: Optional[List[str]] = Field(
        default=None,
        max_length=MAX_MEDICATIONS,
        description="List of patient medical conditions",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "meds": ["Adol 500", "Napa Extra"],
                "schedule": ["1+0+1", "0+1+0"],
                "age": 35,
                "gender": "M",
                "conditions": ["diabetes", "hypertension"],
            }
        }
    }

    @field_validator("meds", "schedule")
    @classmethod
    def _reject_blank_or_oversized_entries(cls, values: List[str]) -> List[str]:
        """Reject blank entries and names that would bloat the LLM prompt."""
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("medication names and schedules must not be blank")
        if any(len(value) > MAX_MEDICATION_NAME_LENGTH for value in cleaned):
            raise ValueError(
                "medication names and schedules must be at most "
                f"{MAX_MEDICATION_NAME_LENGTH} characters"
            )
        return cleaned


class PatientInfo(BaseModel):
    """Patient context for an interaction check."""

    age: Optional[int] = Field(default=None, ge=1, le=120)
    gender: Optional[GenderEnum] = None
    medical_conditions: Optional[List[str]] = Field(default=None, max_length=MAX_MEDICATIONS)


class DrugInteractionRequest(BaseModel):
    """Request body for the drug interaction endpoint."""

    medications: List[str] = Field(
        ...,
        min_length=2,
        max_length=MAX_MEDICATIONS,
        description="At least two medication names",
    )
    patient_info: Optional[PatientInfo] = None


def active_ingredients(name: str) -> List[str]:
    """Lowercased first word of each '+'-separated component, e.g. 'Metformin Hydrochloride'."""
    return [component.split()[0].lower() for component in name.split("+") if component.strip()]


class MedicationInfo(BaseModel):
    """Information about a single medication."""

    name: str
    generic_name: Optional[str] = None
    url: Optional[str] = None
    medex_data: Optional[str] = None
    schedule: str

    @property
    def active_ingredients(self) -> List[str]:
        return active_ingredients(self.generic_name or self.name)


class AdviceResponse(BaseModel):
    """Response containing medication advice."""

    advice: str
    medications_found: int
    pubmed_articles: int
    context_sources: List[str]


class DrugSearchResult(BaseModel):
    """Result of a drug search query."""

    query: str
    results: List[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    services: str
    timestamp: Optional[str] = None
    services_detail: Optional[Dict[str, bool]] = None
    missing_configuration: List[str] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Metadata for a searchable document."""

    id: str
    title: str
    content: str
    source: str
    source_type: str
    mesh_terms: List[str] = Field(default_factory=list)
    relevance_score: Optional[float] = None


class ContextSource(BaseModel):
    """Source document used for generating advice."""

    title: str
    source: str
    url: Optional[str] = None
    section_type: str
    publication_year: str


class MedicationDetail(BaseModel):
    """Detailed information about a processed medication."""

    name: str
    schedule: str
    found_in_database: bool
    has_detailed_info: bool


class MedicationAdviceResponse(BaseModel):
    """Full response from medication advice endpoint."""

    advice: str
    advice_source: str
    missing_configuration: List[str] = Field(default_factory=list)
    medications_processed: int
    medications_found: int
    successful_scrapes: int
    pubmed_articles: int
    context_sources: List[ContextSource]
    drug_interactions_found: int
    interaction_warnings: int
    processing_time: str
    patient_age: int
    patient_gender: str
    medications_detail: List[MedicationDetail]
    advice_format: str


class DrugInteractionInfo(BaseModel):
    """Information about a drug-drug interaction."""

    medications: List[str]
    severity: str
    category: str
    description: str
    mechanism: Optional[str] = None
    clinical_significance: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    monitoring_required: List[str] = Field(default_factory=list)
    management_strategy: str


class DrugInteractionsResponse(BaseModel):
    """Response from drug interactions check."""

    data: List[DrugInteractionInfo]


class SystemStats(BaseModel):
    """System statistics response."""

    timestamp: str
    api_version: str
    services: Dict[str, Any]
