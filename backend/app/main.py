"""FastAPI application for Medical Guideline RAG API.

This module defines the main FastAPI application with all endpoints
for medication advice, drug search, and system health monitoring.
"""

import logging
import re
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn

sys.path.append(str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from config.settings import Defaults, Paths, get_settings
from src.models.schemas import (
    DrugSearchResult,
    HealthResponse,
    MedicationInfo,
    UserInput,
)
from src.services.container import ServiceContainer, get_services
from src.utils.api_utils import handle_api_errors, ensure_service, ServiceError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

services: Optional[ServiceContainer] = None


def _get_services() -> ServiceContainer:
    """Get services instance, raising error if not initialized."""
    if services is None:
        raise ServiceError("Services not initialized", status_code=503)
    return services


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global services
    logger.info("Starting up Medical Advisor API...")

    try:
        services = get_services()
        services.drug_lookup()
        services.jina_scraper()
        services.vector_search()
        services.llm_client()
        services.knowledge_graph()
        logger.info("Medical Advisor API startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")

    yield

    logger.info("Shutting down Medical Advisor API...")


app = FastAPI(
    title="Medical Guideline RAG API",
    description="AI-powered medication advisor using Retrieval-Augmented Generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error occurred"}
    )


@app.get("/", response_model=dict)
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "message": "Medical Guideline RAG API",
        "status": "operational",
        "version": "1.0.0",
        "docs_url": "/docs",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health", response_model=HealthResponse)
@handle_api_errors
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    services_status = services.get_health_status() if services else {}

    status = "degraded" if services_status and not all(services_status.values()) else "healthy"

    return HealthResponse(
        status=status,
        services="operational" if services else "unavailable",
        timestamp=datetime.now().isoformat(),
        services_detail=services_status,
    )


@app.get("/search_drugs", response_model=DrugSearchResult)
@handle_api_errors
async def search_drugs(
    query: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=50)
) -> DrugSearchResult:
    """Search for drug names in the database."""
    svc = _get_services()
    drug_lookup = svc.drug_lookup()
    ensure_service(drug_lookup, "Drug lookup")

    results = drug_lookup.search_drugs(query.strip(), limit)
    return DrugSearchResult(query=query, results=results)


@app.get("/drug_info/{drug_name}")
@handle_api_errors
async def get_drug_info(drug_name: str) -> dict:
    """Get information about a specific drug."""
    svc = _get_services()
    drug_lookup = svc.drug_lookup()
    ensure_service(drug_lookup, "Drug lookup")

    url = drug_lookup.find_drug_url(drug_name)

    if not url:
        raise HTTPException(
            status_code=404, detail=f"Drug '{drug_name}' not found in database"
        )

    return {"drug_name": drug_name, "url": url, "found": True}


@app.post("/advise", response_model=dict)
@handle_api_errors
async def get_medication_advice(user_input: UserInput) -> dict:
    """Generate medication advice based on user input."""
    logger.info(f"Processing advice request for {len(user_input.meds)} medications")

    _validate_medication_input(user_input)

    svc = _get_services()
    if not svc.all_available():
        raise ServiceError("One or more required services are not available")

    medications, medex_contexts, interaction_warnings = await _process_medications(
        user_input.meds, user_input.schedule, svc
    )

    drug_interactions = svc.knowledge_graph().analyze_drug_interactions(
        user_input.meds
    )

    pubmed_context = _search_medical_literature(user_input, svc)

    advice = _generate_advice(medications, user_input, drug_interactions, pubmed_context, medex_contexts, svc)

    return _build_response(
        advice, medications, drug_interactions, interaction_warnings, pubmed_context, user_input
    )


@app.post("/advise/html")
@handle_api_errors
async def get_medication_advice_html(user_input: UserInput) -> HTMLResponse:
    """Generate medication advice with HTML table formatting."""
    advice_response = await get_medication_advice(user_input)
    html_content = _render_html_advice(advice_response["advice"])
    return HTMLResponse(content=html_content)


@app.post("/drug_interactions")
@handle_api_errors
async def check_drug_interactions(request_data: dict) -> dict:
    """Check for drug-drug interactions with patient context."""
    medications = request_data.get("medications", [])
    patient_info = request_data.get("patient_info", {})

    if len(medications) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 medications required for interaction check",
        )

    svc = _get_services()
    interactions = svc.knowledge_graph().analyze_drug_interactions(
        medications, patient_info=patient_info
    )

    enhanced_interactions = [
        _enhance_interaction(interaction, patient_info)
        for interaction in interactions
    ]

    logger.info(f"Found {len(enhanced_interactions)} drug interactions")
    return {"data": enhanced_interactions}


@app.get("/stats")
@handle_api_errors
async def get_system_stats() -> dict:
    """Get system statistics and status."""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "api_version": "1.0.0",
        "services": {},
    }

    svc = _get_services()
    if svc.is_available("drug_lookup"):
        stats["services"]["drug_database"] = {
            "total_drugs": len(svc.drug_lookup().drug_db),
            "status": "operational",
        }

    if svc.is_available("vector_search"):
        stats["services"]["vector_search"] = svc.vector_search().get_stats()

    if svc.is_available("llm_client"):
        stats["services"]["llm_client"] = svc.llm_client().get_model_info()

    if svc.is_available("knowledge_graph"):
        stats["services"]["knowledge_graph"] = svc.knowledge_graph().get_stats()

    return stats


def _validate_medication_input(user_input: UserInput) -> None:
    """Validate medication input consistency."""
    if len(user_input.meds) != len(user_input.schedule):
        raise HTTPException(
            status_code=400,
            detail="Number of medications must match number of schedules",
        )


async def _process_medications(
    meds: List[str], schedules: List[str], svc: ServiceContainer
) -> tuple[List[MedicationInfo], List[str], List[str]]:
    """Process medications and scrape drug information.

    Args:
        meds: List of medication names.
        schedules: List of dosing schedules.
        svc: Service container instance.

    Returns:
        Tuple of (medications, medex_contexts, interaction_warnings).
    """
    medications = []
    medex_contexts = []
    interaction_warnings = []

    drug_lookup = svc.drug_lookup()
    jina_scraper = svc.jina_scraper()

    for i, (med_name, schedule) in enumerate(zip(meds, schedules)):
        logger.info(f"Processing medication {i + 1}/{len(meds)}: {med_name}")

        url = drug_lookup.find_drug_url(med_name)
        medex_data = None

        if url:
            logger.info(f"Scraping drug information for {med_name}...")
            medex_data = jina_scraper.scrape_medex_page(url)
            if medex_data:
                medex_contexts.append(medex_data)
                interactions = _extract_interaction_info(medex_data)
                interaction_warnings.extend(interactions)

        medications.append(
            MedicationInfo(
                name=med_name, url=url, medex_data=medex_data, schedule=schedule
            )
        )

    return medications, medex_contexts, interaction_warnings


def _search_medical_literature(user_input: UserInput, svc: ServiceContainer) -> List[Dict[str, Any]]:
    """Search for relevant medical literature."""
    medication_query = " ".join(user_input.meds)

    if len(user_input.meds) > 1:
        combination_query = f"{medication_query} combination therapy drug interactions polypharmacy"
    else:
        combination_query = f"{medication_query} monotherapy safety monitoring"

    return svc.vector_search().enhanced_medical_search(
        query=combination_query,
        medications=user_input.meds,
        patient_info={"age": user_input.age, "gender": user_input.gender.value},
        k=5,
    )


def _generate_advice(
    medications: List[MedicationInfo],
    user_input: UserInput,
    drug_interactions: List[Dict],
    pubmed_context: List[Dict],
    medex_contexts: List[str],
    svc: ServiceContainer,
) -> str:
    """Generate medication advice using LLM."""
    patient_info = {
        "age": user_input.age,
        "gender": user_input.gender.value,
        "medical_conditions": user_input.conditions or [],
        "drug_interactions": drug_interactions,
        "medication_count": len(medications),
        "regimen_type": "combination_therapy" if len(medications) > 1 else "monotherapy",
    }

    return svc.llm_client().generate_medication_advice(
        medications=[med.model_dump() for med in medications],
        patient_info=patient_info,
        pubmed_context=pubmed_context,
        medex_context=medex_contexts,
    )


def _build_response(
    advice: str,
    medications: List[MedicationInfo],
    drug_interactions: List[Dict],
    interaction_warnings: List[str],
    pubmed_context: List[Dict],
    user_input: UserInput,
) -> dict:
    """Build the response dictionary for medication advice."""
    return {
        "advice": advice,
        "medications_processed": len(medications),
        "medications_found": len([m for m in medications if m.url]),
        "successful_scrapes": len([m for m in medications if m.medex_data]),
        "pubmed_articles": len(pubmed_context),
        "context_sources": [
            {
                "title": doc.get("title", f"Medical Research Article {i+1}"),
                "source": doc.get("source", "Medical Literature"),
                "url": doc.get("url", "#"),
                "section_type": doc.get("section_type", "general"),
                "publication_year": doc.get("publication_year", ""),
            }
            for i, doc in enumerate(pubmed_context[:5])
        ],
        "drug_interactions_found": len(drug_interactions) if drug_interactions else 0,
        "interaction_warnings": len(interaction_warnings),
        "processing_time": "Generated successfully",
        "patient_age": user_input.age,
        "patient_gender": user_input.gender.value,
        "medications_detail": [
            {
                "name": med.name,
                "schedule": med.schedule,
                "found_in_database": med.url is not None,
                "has_detailed_info": med.medex_data is not None,
            }
            for med in medications
        ],
        "advice_format": "structured_with_table",
    }


def _render_html_advice(markdown_text: str) -> str:
    """Render markdown advice as HTML using template."""
    template_path = Paths.TEMPLATES_DIR / "medication_advice.html"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        logger.warning(f"Template not found at {template_path}, using inline template")
        template = _get_fallback_html_template()

    content = _convert_markdown_to_html_content(markdown_text)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return template.replace("{{ content }}", content).replace("{{ timestamp }}", timestamp)


def _convert_markdown_to_html_content(markdown_text: str) -> str:
    """Convert markdown text to HTML content."""
    content = re.sub(r"^## (.+)$", r"<h2>\1</h2>", markdown_text, flags=re.MULTILINE)
    content = re.sub(r"^### (.+)$", r"<h3>\1</h3>", content, flags=re.MULTILINE)
    content = re.sub(r"^• (.+)$", r"<li>\1</li>", content, flags=re.MULTILINE)
    content = re.sub(r"^- (.+)$", r"<li>\1</li>", content, flags=re.MULTILINE)
    content = re.sub(r"(<li>.*</li>(?:\s*<li>.*</li>)*)", r"<ul>\1</ul>", content, flags=re.DOTALL)
    content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
    content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", content)

    paragraphs = content.split("\n\n")
    formatted_paragraphs = []

    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith("<"):
            if "|" in p and ("DON'T" in p or "DO" in p):
                formatted_paragraphs.append(_convert_table(p))
            else:
                formatted_paragraphs.append(f"<p>{p}</p>")
        else:
            formatted_paragraphs.append(p)

    content = "\n".join(formatted_paragraphs)
    content = re.sub(r"<p>(<h[1-6]>.*</h[1-6]>)</p>", r"\1", content)
    content = re.sub(r"<p>(<ul>.*</ul>)</p>", r"\1", content, flags=re.DOTALL)

    return content


def _convert_table(p: str) -> str:
    """Convert markdown table to HTML."""
    lines = p.split("\n")
    if len(lines) < 3:
        return f"<p>{p}</p>"

    table_html = '<table class="dos-donts-table">\n'

    header = lines[0].split("|")[1:-1]
    table_html += "<tr>"
    for cell in header:
        table_html += f"<th>{cell.strip()}</th>"
    table_html += "</tr>\n"

    for line in lines[2:]:
        if line.strip():
            cells = line.split("|")[1:-1]
            table_html += "<tr>"
            for cell in cells:
                table_html += f"<td>{cell.strip()}</td>"
            table_html += "</tr>\n"

    table_html += "</table>"
    return table_html


def _get_fallback_html_template() -> str:
    """Get fallback HTML template if file not found."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Medication Guidance</title>
</head>
<body>
    <div class="container">
        <h1>Medication Guidance Report</h1>
        <div id="content">{{ content }}</div>
        <div class="footer">
            <p>Generated on {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>"""


def _extract_interaction_info(medex_data: str) -> List[str]:
    """Extract drug interaction information from MedEx data."""
    interactions = []
    interaction_keywords = [
        "drug interaction",
        "contraindicated",
        "caution",
        "avoid",
        "concurrent use",
        "may increase",
        "may decrease",
    ]

    lines = medex_data.split("\n")
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in interaction_keywords):
            interactions.append(line.strip())

    return interactions


def _enhance_interaction(interaction: Dict, patient_info: Dict) -> Dict:
    """Enhance interaction with patient-specific risk factors."""
    risk_factors = []
    monitoring = []

    age = patient_info.get("age", 0)
    conditions = patient_info.get("medical_conditions", [])

    if age > 65:
        risk_factors.append("Elderly patients - increased sensitivity to drug effects")
        monitoring.append("Renal function monitoring recommended")
    elif age < 18:
        risk_factors.append("Pediatric patient - dosing considerations apply")
        monitoring.append("Pediatric-specific monitoring parameters")

    for condition in conditions:
        condition_lower = condition.lower()
        if "kidney" in condition_lower or "renal" in condition_lower:
            risk_factors.append("Renal impairment - dose adjustment may be required")
            monitoring.extend(["Serum creatinine", "BUN", "eGFR"])
        elif "heart" in condition_lower or "cardiac" in condition_lower:
            risk_factors.append("Heart disease - monitor cardiac function")
            monitoring.append("BNP or NT-proBNP levels")
        elif "liver" in condition_lower or "hepatic" in condition_lower:
            risk_factors.append("Liver impairment - monitor liver enzymes")
            monitoring.extend(["ALT", "AST", "Bilirubin"])

    return {
        "medications": [interaction.get("drug1"), interaction.get("drug2")],
        "severity": interaction.get("severity", "unknown"),
        "category": interaction.get("category", "unknown"),
        "description": interaction.get("description", ""),
        "mechanism": interaction.get("mechanism", ""),
        "clinical_significance": interaction.get("clinical_significance", ""),
        "risk_factors": risk_factors,
        "monitoring_required": monitoring,
        "management_strategy": interaction.get("management_strategy", "Consult healthcare provider"),
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
