"""Main FastAPI application for the Medical Guideline RAG system."""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.models.schemas import (
    UserInput,
    AdviceResponse,
    DrugSearchResult,
    HealthResponse,
    MedicationInfo,
)
from src.services.drug_lookup import DrugLookup
from src.services.jina_scraper import JinaScraper
from src.services.vector_search import VectorSearch
from src.services.gemini_client import GeminiClient
from config.settings import API_PORT, LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Global service instances
drug_lookup = None
jina_scraper = None
vector_search = None
gemini_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up Medical Advisor API...")

    global drug_lookup, jina_scraper, vector_search, gemini_client

    try:
        # Initialize services
        drug_lookup = DrugLookup()
        jina_scraper = JinaScraper()
        vector_search = VectorSearch()
        gemini_client = GeminiClient()

        # Load vector search index
        logger.info("Loading vector search index...")
        if not vector_search._load_index():
            logger.info("Creating new vector search index...")
            vector_search.load_processed_data()

        logger.info("Medical Advisor API startup completed successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Medical Advisor API...")


# Initialize FastAPI app
app = FastAPI(
    title="Medical Guideline RAG API",
    description="AI-powered medication advisor using Retrieval-Augmented Generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Medical Guideline RAG API",
        "status": "operational",
        "version": "1.0.0",
        "docs_url": "/docs",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "services": "operational",
        "timestamp": datetime.now().isoformat(),
    }

    # Check service health
    services_status = {}

    if drug_lookup:
        services_status["drug_lookup"] = len(drug_lookup.drug_db) > 0

    if vector_search:
        services_status["vector_search"] = vector_search.index is not None

    if gemini_client:
        services_status["gemini_client"] = gemini_client.model is not None

    if jina_scraper:
        services_status["jina_scraper"] = True

    health_status["services_detail"] = services_status

    # Determine overall health
    if not all(services_status.values()):
        health_status["status"] = "degraded"

    return health_status


@app.get("/search_drugs", response_model=DrugSearchResult)
async def search_drugs(query: str, limit: int = 10):
    """Search for drug names in the database.

    Args:
        query: Search query string
        limit: Maximum number of results to return
    """
    if not query or len(query.strip()) < 2:
        raise HTTPException(
            status_code=400, detail="Query must be at least 2 characters long"
        )

    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")

    try:
        if not drug_lookup:
            raise HTTPException(
                status_code=503, detail="Drug lookup service not available"
            )

        results = drug_lookup.search_drugs(query.strip(), limit)
        return DrugSearchResult(query=query, results=results)

    except Exception as e:
        logger.error(f"Error searching drugs: {e}")
        raise HTTPException(
            status_code=500, detail="Error occurred while searching drugs"
        )


@app.get("/drug_info/{drug_name}")
async def get_drug_info(drug_name: str):
    """Get information about a specific drug.

    Args:
        drug_name: Name of the drug to look up
    """
    try:
        if not drug_lookup:
            raise HTTPException(
                status_code=503, detail="Drug lookup service not available"
            )

        url = drug_lookup.find_drug_url(drug_name)

        if not url:
            raise HTTPException(
                status_code=404, detail=f"Drug '{drug_name}' not found in database"
            )

        return {"drug_name": drug_name, "url": url, "found": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drug info: {e}")
        raise HTTPException(
            status_code=500, detail="Error occurred while retrieving drug information"
        )


@app.post("/advise", response_model=dict)
async def get_medication_advice(user_input: UserInput):
    """Generate medication advice based on user input.

    Args:
        user_input: User input containing medications, schedule, age, and gender
    """
    try:
        logger.info(f"Processing advice request for {len(user_input.meds)} medications")

        # Validate input
        if len(user_input.meds) != len(user_input.schedule):
            raise HTTPException(
                status_code=400,
                detail="Number of medications must match number of schedules",
            )

        # Check service availability
        if not all([drug_lookup, jina_scraper, vector_search, gemini_client]):
            raise HTTPException(
                status_code=503,
                detail="One or more required services are not available",
            )

        # Process medications
        medications = []
        medex_contexts = []
        successful_scrapes = 0

        for med_name, schedule in zip(user_input.meds, user_input.schedule):
            # Lookup drug URL
            url = drug_lookup.find_drug_url(med_name)
            medex_data = None

            # Scrape MedEx data if URL found
            if url:
                medex_data = jina_scraper.scrape_medex_page(url)
                if medex_data:
                    medex_contexts.append(medex_data)
                    successful_scrapes += 1

            medications.append(
                MedicationInfo(
                    name=med_name, url=url, medex_data=medex_data, schedule=schedule
                )
            )

        # Search for relevant PubMed articles
        logger.info("Searching for relevant medical literature...")
        pubmed_context = vector_search.search_by_medications(user_input.meds, k=5)

        # Generate advice using Gemini
        logger.info("Generating medication advice...")
        patient_info = {"age": user_input.age, "gender": user_input.gender.value}

        advice = gemini_client.generate_advice(
            medications=[med.dict() for med in medications],
            patient_info=patient_info,
            pubmed_context=pubmed_context,
            medex_context=medex_contexts,
        )

        # Prepare response
        response_data = {
            "advice": advice,
            "medications_processed": len(medications),
            "medications_found": len([m for m in medications if m.url]),
            "successful_scrapes": successful_scrapes,
            "pubmed_articles": len(pubmed_context),
            "context_sources": [doc.get("source", "") for doc in pubmed_context[:5]],
            "processing_time": "Generated successfully",
        }

        logger.info(f"Successfully generated advice for {len(medications)} medications")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating advice: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating medication advice",
        )


@app.get("/stats")
async def get_system_stats():
    """Get system statistics and status."""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "api_version": "1.0.0",
            "services": {},
        }

        if drug_lookup:
            stats["services"]["drug_database"] = {
                "total_drugs": len(drug_lookup.drug_db),
                "status": "operational",
            }

        if vector_search:
            stats["services"]["vector_search"] = vector_search.get_stats()

        if gemini_client:
            stats["services"]["gemini_client"] = gemini_client.get_model_info()

        return stats

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=500, detail="Error occurred while retrieving system statistics"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )
