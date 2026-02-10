"""Pydantic models for API request and response schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenderEnum(str, Enum):
    """Patient gender options."""

    MALE = "M"
    FEMALE = "F"


class UserInput(BaseModel):
    """User input for medication advice request."""

    meds: List[str] = Field(..., description="List of medication names")
    schedule: List[str] = Field(
        ..., description="Dosing schedule for each medication (e.g., '1+0+1')"
    )
    age: int = Field(..., ge=1, le=120, description="Patient age")
    gender: GenderEnum = Field(..., description="Patient gender")
    conditions: Optional[List[str]] = Field(
        default=None, description="List of patient medical conditions"
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


class MedicationInfo(BaseModel):
    """Information about a single medication."""

    name: str
    url: Optional[str] = None
    medex_data: Optional[str] = None
    schedule: str


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
    url: str
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
