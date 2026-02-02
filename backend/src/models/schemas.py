from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class GenderEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"


class UserInput(BaseModel):
    meds: List[str] = Field(
        ..., description="List of medication names", min_items=1, max_items=10
    )
    schedule: List[str] = Field(
        ..., description="Dosing schedule for each medication (e.g., '1+0+1')"
    )
    age: int = Field(..., ge=1, le=120, description="Patient age")
    gender: GenderEnum = Field(..., description="Patient gender")

    class Config:
        json_schema_extra = {
            "example": {
                "meds": ["Adol 500", "Napa Extra"],
                "schedule": ["1+0+1", "0+1+0"],
                "age": 35,
                "gender": "M",
            }
        }


class MedicationInfo(BaseModel):
    name: str
    url: Optional[str] = None
    medex_data: Optional[str] = None
    schedule: str


class AdviceResponse(BaseModel):
    advice: str
    medications_found: int
    pubmed_articles: int
    context_sources: List[str]


class DrugSearchResult(BaseModel):
    query: str
    results: List[str]


class HealthResponse(BaseModel):
    status: str
    services: str
    timestamp: Optional[str] = None


class DocumentMetadata(BaseModel):
    id: str
    title: str
    content: str
    source: str
    source_type: str
    mesh_terms: List[str] = []
    relevance_score: Optional[float] = None
