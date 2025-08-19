import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List
import uvicorn

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from src.models.schemas import (
    UserInput,
    DrugSearchResult,
    HealthResponse,
    MedicationInfo,
)
from src.services.drug_lookup import DrugLookup
from src.services.jina_scraper import JinaScraper
from src.services.vector_search import VectorSearch
from src.services.gemini_client import GeminiClient
from src.services.medical_knowledge_graph import MedicalKnowledgeGraph
from config.settings import API_PORT, LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Global service instances
drug_lookup = None
jina_scraper = None
vector_search = None
gemini_client = None
knowledge_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up Medical Advisor API...")

    global drug_lookup, jina_scraper, vector_search, gemini_client, knowledge_graph

    try:
        # Initialize services
        drug_lookup = DrugLookup()
        jina_scraper = JinaScraper()
        vector_search = VectorSearch()
        gemini_client = GeminiClient()
        knowledge_graph = MedicalKnowledgeGraph()

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
        if not all(
            [drug_lookup, jina_scraper, vector_search, gemini_client, knowledge_graph]
        ):
            raise HTTPException(
                status_code=503,
                detail="One or more required services are not available",
            )

        # Enhanced medication processing with interaction analysis
        medications = []
        medex_contexts = []
        interaction_warnings = []
        successful_scrapes = 0

        logger.info("Step 1/4: Processing medications and scraping drug information...")
        for i, (med_name, schedule) in enumerate(
            zip(user_input.meds, user_input.schedule)
        ):
            logger.info(
                f"Processing medication {i + 1}/{len(user_input.meds)}: {med_name}"
            )

            # Lookup drug URL
            url = drug_lookup.find_drug_url(med_name)
            medex_data = None

            # Scrape MedEx data if URL found
            if url:
                logger.info(f"Scraping drug information for {med_name}...")
                medex_data = jina_scraper.scrape_medex_page(url)
                if medex_data:
                    medex_contexts.append(medex_data)
                    successful_scrapes += 1
                    # Extract interaction information
                    interactions = extract_interaction_info(medex_data)
                    if interactions:
                        interaction_warnings.extend(interactions)

            medications.append(
                MedicationInfo(
                    name=med_name, url=url, medex_data=medex_data, schedule=schedule
                )
            )

        logger.info("Step 2/4: Analyzing drug-drug interactions...")
        # Analyze drug-drug interactions using knowledge graph
        drug_interactions = knowledge_graph.analyze_drug_interactions(user_input.meds)

        logger.info("Step 3/4: Searching for relevant medical literature...")
        # Enhanced context search including interactions and combination therapy
        medication_query = " ".join(user_input.meds)
        
        # Create comprehensive search query for combination therapy
        if len(user_input.meds) > 1:
            combination_query = f"{medication_query} combination therapy drug interactions polypharmacy"
        else:
            combination_query = f"{medication_query} monotherapy safety monitoring"
        
        pubmed_context = vector_search.enhanced_medical_search(
            query=combination_query,
            medications=user_input.meds,
            patient_info={"age": user_input.age, "gender": user_input.gender.value},
            k=5,
        )

        logger.info("Step 4/4: Generating integrated medication regimen guidance...")
        # Generate advice with comprehensive combination analysis
        patient_info = {
            "age": user_input.age,
            "gender": user_input.gender.value,
            "drug_interactions": drug_interactions,
            "interaction_warnings": interaction_warnings,
            "medication_count": len(medications),
            "regimen_type": "combination_therapy" if len(medications) > 1 else "monotherapy"
        }

        advice = gemini_client.generate_advice(
            medications=[med.dict() for med in medications],
            patient_info=patient_info,
            pubmed_context=pubmed_context,
            medex_context=medex_contexts,
        )

        # Prepare enhanced response with more detailed information
        response_data = {
            "advice": advice,
            "medications_processed": len(medications),
            "medications_found": len([m for m in medications if m.url]),
            "successful_scrapes": successful_scrapes,
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
            "drug_interactions_found": len(drug_interactions)
            if drug_interactions
            else 0,
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

        logger.info(f"Successfully generated integrated regimen guidance for {len(medications)} medications")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating advice: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating medication advice",
        )


@app.post("/advise/html")
async def get_medication_advice_html(user_input: UserInput):
    """Generate medication advice with HTML table formatting.

    Args:
        user_input: User input containing medications, schedule, age, and gender
    
    Returns:
        HTML formatted response with styled do's and don'ts table
    """
    try:
        # Get the regular advice first
        advice_response = await get_medication_advice(user_input)
        advice_text = advice_response["advice"]
        
        # Convert markdown table to HTML with styling
        html_content = convert_markdown_to_html(advice_text)
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error generating HTML advice: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating HTML medication advice",
        )


def convert_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown advice to styled HTML."""
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Medication Guidance</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            h3 {
                color: #34495e;
                margin-top: 25px;
            }
            .dos-donts-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .dos-donts-table th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
            }
            .dos-donts-table td {
                padding: 15px;
                border-bottom: 1px solid #ddd;
                vertical-align: top;
            }
            .dos-donts-table tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            .dos-donts-table tr:hover {
                background-color: #e8f4f8;
                transition: background-color 0.3s ease;
            }
            .dont-column {
                background-color: #fff5f5 !important;
                border-left: 4px solid #e53e3e;
            }
            .do-column {
                background-color: #f0fff4 !important;
                border-left: 4px solid #38a169;
            }
            .emoji {
                font-size: 20px;
                margin-right: 8px;
            }
            .medication-list {
                background-color: #e8f5e8;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #4caf50;
            }
            .warning-box {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #f39c12;
            }
            .info-box {
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #17a2b8;
            }
            ul {
                padding-left: 20px;
            }
            li {
                margin-bottom: 8px;
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Medication Guidance Report</h1>
            <div id="content">
                {content}
            </div>
            <div class="footer">
                <p><strong>Disclaimer:</strong> This information is for educational purposes only. 
                Always consult your healthcare provider before making any changes to your medication regimen.</p>
                <p>Generated on {timestamp}</p>
            </div>
        </div>
        
        <script>
            // Enhance table formatting
            document.addEventListener('DOMContentLoaded', function() {
                const tables = document.querySelectorAll('table');
                tables.forEach(table => {
                    if (table.innerHTML.includes('DON\\'T') && table.innerHTML.includes('DO')) {
                        table.className = 'dos-donts-table';
                        
                        // Style table cells
                        const rows = table.querySelectorAll('tr');
                        rows.forEach((row, index) => {
                            if (index > 1) { // Skip header and separator
                                const cells = row.querySelectorAll('td');
                                if (cells.length >= 2) {
                                    cells[0].className = 'dont-column';
                                    cells[1].className = 'do-column';
                                }
                            }
                        });
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    # Convert markdown to HTML (basic conversion)
    import re
    from datetime import datetime
    
    # Convert headers
    content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', markdown_text, flags=re.MULTILINE)
    content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    
    # Convert bullet points
    content = re.sub(r'^• (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
    content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
    
    # Wrap consecutive list items in <ul> tags
    content = re.sub(r'(<li>.*</li>(?:\s*<li>.*</li>)*)', r'<ul>\1</ul>', content, flags=re.DOTALL)
    
    # Convert bold text
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
    
    # Convert paragraphs
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []
    
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            # Check if it's a table
            if '|' in p and ('DON\'T' in p or 'DO' in p):
                # It's our do's and don'ts table - convert to HTML table
                lines = p.split('\n')
                if len(lines) >= 3:  # Header, separator, data
                    table_html = '<table class="dos-donts-table">\n'
                    
                    # Header
                    header = lines[0].split('|')[1:-1]  # Remove empty first and last
                    table_html += '<tr>'
                    for cell in header:
                        table_html += f'<th>{cell.strip()}</th>'
                    table_html += '</tr>\n'
                    
                    # Data rows
                    for line in lines[2:]:  # Skip separator
                        if line.strip():
                            cells = line.split('|')[1:-1]  # Remove empty first and last
                            table_html += '<tr>'
                            for cell in cells:
                                table_html += f'<td>{cell.strip()}</td>'
                            table_html += '</tr>\n'
                    
                    table_html += '</table>'
                    formatted_paragraphs.append(table_html)
                else:
                    formatted_paragraphs.append(f'<p>{p}</p>')
            else:
                formatted_paragraphs.append(f'<p>{p}</p>')
        else:
            formatted_paragraphs.append(p)
    
    content = '\n'.join(formatted_paragraphs)
    
    # Clean up extra paragraph tags around headers and lists
    content = re.sub(r'<p>(<h[1-6]>.*</h[1-6]>)</p>', r'\1', content)
    content = re.sub(r'<p>(<ul>.*</ul>)</p>', r'\1', content, flags=re.DOTALL)
    content = re.sub(r'<p>(<table.*</table>)</p>', r'\1', content, flags=re.DOTALL)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return html_template.format(content=content, timestamp=timestamp)


def extract_interaction_info(medex_data: str) -> List[str]:
    """Extract drug interaction information from MedEx data."""
    interactions = []

    # Simple keyword-based extraction - in practice, this would be more sophisticated
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

        if knowledge_graph:
            stats["services"]["knowledge_graph"] = knowledge_graph.get_stats()

        return stats

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=500, detail="Error occurred while retrieving system statistics"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )
