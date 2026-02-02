# Medical Guideline RAG System

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![UV](https://img.shields.io/badge/UV-Package_Manager-4B8BBE?style=for-the-badge&logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00599C?style=for-the-badge&logo=meta&logoColor=white)](https://faiss.ai)

An AI-powered medical consultation system that provides evidence-based medication guidance using Retrieval-Augmented Generation (RAG) with comprehensive medical literature and drug interaction analysis.

## Project Overview

The Medical Guideline RAG System is a sophisticated AI-powered platform designed to assist healthcare professionals and patients with evidence-based medication guidance. By leveraging cutting-edge RAG technology, the system combines medical literature retrieval with AI-generated advice to provide comprehensive, contextual, and reliable medical consultation services.

### Key Features

- Multi-Modal Medical Search: Advanced vector search across 33 medical domains using FAISS and sentence transformers
- AI-Powered Consultation: Multiple LLM provider support (Google, OpenAI, z.ai, Anthropic, DeepSeek)
- Medical Knowledge Graph: NetworkX-based drug interaction analysis and therapeutic classification
- Modern React Frontend: Next.js with TypeScript and shadcn/ui components
- High-Performance API: FastAPI backend with optimized medical consultation endpoints
- Real-time Analytics: Comprehensive monitoring and PDF report generation
- Safety-First Design: Built-in contraindication checking and drug interaction analysis

## System Architecture

![System Architecture](assets/System%20Architecture.svg)

## Data Statistics

### Medical Literature Coverage
- Total Processed Documents: 33 medical domain files
- Data Points: ~50,000+ medical articles and guidelines
- Medical Domains Covered:
  - Diabetes (1,936 articles)
  - Malaria (2,680 articles) 
  - Tuberculosis (2,157 articles)
  - Cardiovascular diseases
  - WHO health guidelines
  - Drug interaction databases
  - And 27+ additional medical specialties

### Knowledge Graph Statistics
- Total Nodes: 50+ medical entities
- Drug Nodes: 10+ pharmaceutical compounds
- Condition Nodes: 25+ medical conditions
- Drug Class Nodes: 15+ therapeutic classifications
- Known Interactions: 5+ documented drug interactions
- Therapeutic Mappings: 10+ indication relationships

### Vector Search Performance
- Embedding Model: all-MiniLM-L6-v2 (384 dimensions)
- Search Engine: FAISS with cosine similarity
- Multi-stage Retrieval: Enhanced with medical relevance scoring
- Patient Context: Age, gender, and condition-specific filtering
- Query Expansion: Automatic medical term enhancement

## Technology Stack

### Backend Framework
- Backend: FastAPI with async support
- Package Manager: UV for modern Python dependency management
- Python Version: 3.11+

### Frontend Framework
- Framework: Next.js 15 with App Router
- Language: TypeScript
- UI Components: shadcn/ui (Radix UI + Tailwind CSS)
- State Management: React Hooks
- API Client: Fetch API with TypeScript types

### AI & Machine Learning
- LLM: Multiple providers supported (Google, OpenAI, z.ai, Anthropic, DeepSeek)
- Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
- Vector Database: FAISS for high-performance similarity search
- Knowledge Graph: NetworkX for drug interaction modeling

### Data Processing
- Medical Literature: PubMed article processing
- Guidelines: WHO health guideline integration
- Drug Data: Pharmaceutical database integration
- Format Support: JSON, PDF processing capabilities

### Development Tools
- Dependency Management: UV with pyproject.toml
- Code Quality: Black, isort, flake8
- Testing: Pytest with coverage
- Documentation: Comprehensive inline documentation

## Project Structure

```
medical-guideline-rag/
├── backend/                 # Python FastAPI backend
│   ├── app/               # FastAPI application
│   ├── config/            # Configuration management
│   ├── data/              # Medical datasets
│   ├── src/
│   │   ├── services/      # Business logic services
│   │   ├── models/        # Pydantic data models
│   │   ├── utils/         # Shared utility functions
│   │   ├── data_collection/ # Data fetching
│   │   └── preprocessing/   # Data cleaning
│   ├── ui/                # Legacy Streamlit UI (can be removed)
│   ├── .venv/            # Python virtual environment
│   ├── uv.lock            # UV lock file
│   ├── pyproject.toml      # Python dependencies
│   └── .env              # Environment variables
├── frontend/                # Next.js React frontend
│   ├── src/
│   │   ├── app/           # Next.js App Router pages
│   │   ├── components/     # React components
│   │   │   └── ui/       # shadcn/ui components
│   │   └── lib/          # Utilities and API client
│   ├── package.json        # Node.js dependencies
│   ├── tsconfig.json       # TypeScript configuration
│   ├── tailwind.config.ts  # Tailwind CSS configuration
│   └── .env.local        # Frontend environment variables
├── assets/                # Documentation images
├── .gitignore
└── README.md
```

## Local Deployment

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm
- UV package manager
- Git

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment and install dependencies:
```bash
uv sync
```

3. Activate virtual environment:
```bash
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

4. Configure environment variables (create `.env` file in `backend/`):
```env
# AI Service Configuration
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_api_key_here
# or use z.ai
LLM_PROVIDER=zai
ZAI_API_KEY=your_zai_api_key_here

JINA_API_KEY=your_jina_api_key_here  # Optional
NCBI_API_KEY=your_ncbi_api_key_here  # Optional

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_TOKENS=4000
TEMPERATURE=0.3

# Vector Search Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_SEARCH_TOP_K=10
FAISS_INDEX_PATH=data/vector_index.faiss
DOCUMENTS_METADATA_PATH=data/documents_metadata.json

# Data Directories
RAW_DIR=data/raw
PROCESSED_DIR=data/processed
API_PORT=8000
```

5. Initialize the system:
```bash
# Process medical data and create vector index
uv run python -m src.data_processing.process_medical_data

# Start the development server
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables (create `.env.local` in `frontend/`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Endpoints

### Medical Consultation
- POST /advise - Complete medical consultation with AI advice
- POST /advise/html - Medication advice with HTML formatting
- GET /search_drugs - Search for drug names in database
- GET /drug_info/{drug_name} - Drug information lookup
- POST /drug-interactions - Drug interaction analysis

### System Monitoring
- GET /health - System health check
- GET /stats - System statistics and performance metrics
- GET /vector-search/stats - Vector search performance data

### Example API Usage

```python
import requests

# Medical consultation
consultation_data = {
    "patient_info": {
        "age": 45,
        "gender": "F",
        "weight": 70,
        "height": 165,
        "medical_conditions": ["diabetes", "hypertension"]
    },
    "current_medications": ["metformin", "lisinopril"],
    "symptoms": ["fatigue", "dizziness"],
    "consultation_reason": "Medication review and symptom assessment"
}

response = requests.post("http://localhost:8000/advise", json=consultation_data)
medical_advice = response.json()
```

## Development and Testing

### Backend Testing
```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_vector_search.py -v
```

### Code Quality (Backend)
```bash
cd backend

# Format code
uv run black src/ app/ ui/

# Sort imports
uv run isort src/ app/ ui/

# Lint code
uv run flake8 src/ app/ ui/
```

### Frontend Testing
```bash
cd frontend

# Run linting
npm run lint

# Run type checking
npm run type-check

# Run tests
npm test
```

## Medical AI Features

### Evidence-Based Reasoning
- Literature Integration: Real-time access to 50,000+ medical articles
- Guideline Compliance: WHO and medical society guideline integration
- Safety Prioritization: Contraindication and interaction checking
- Contextual Advice: Patient-specific recommendations

### Advanced Search Capabilities
- Semantic Search: Understanding medical terminology and context
- Multi-modal Retrieval: Text, symptoms, and medication-based search
- Relevance Scoring: Medical domain-specific ranking algorithms
- Query Expansion: Automatic medical term enhancement

### Drug Interaction Analysis
- Comprehensive Database: Known drug interactions and contraindications
- Risk Assessment: Severity classification and clinical significance
- Monitoring Parameters: Required clinical monitoring recommendations
- Safety Alerts: Real-time interaction warnings

## LLM Provider Configuration

The system supports multiple LLM providers via environment variables:

### Google (Gemini)
```env
LLM_PROVIDER=google
GOOGLE_API_KEY=your_api_key
LLM_MODEL=gemini-2.0-flash
```

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
LLM_MODEL=gpt-4o
```

### z.ai
```env
LLM_PROVIDER=zai
ZAI_API_KEY=your_api_key
LLM_MODEL=zai-model
```

### Anthropic (Claude)
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key
LLM_MODEL=claude-3-5-sonnet
```

### DeepSeek
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key
LLM_MODEL=deepseek-chat
```

## Safety and Compliance

### Medical Safety Features
- Contraindication Checking: Automatic safety screening
- Drug Interaction Analysis: Comprehensive interaction database
- Age-Appropriate Recommendations: Pediatric and geriatric considerations

### Disclaimer

Important Medical Disclaimer: This system is designed to assist healthcare professionals and provide educational information. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers for medical decisions.

## Contributing

How to make contributions to improve the Medical Guideline RAG System:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/medical-enhancement`
3. Install development dependencies:
   - Backend: `cd backend && uv sync --dev`
   - Frontend: `cd frontend && npm install`
4. Make your changes with comprehensive tests
5. Run quality checks:
   - Backend: `uv run pytest && uv run black . && uv run flake8`
   - Frontend: `npm run lint && npm test`
6. Submit a pull request with detailed medical context

### Development Guidelines
- Follow medical coding standards and terminology
- Include comprehensive test coverage for medical logic
- Document all medical algorithms and decision trees
- Ensure patient safety considerations in all features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Medical Literature: PubMed and medical research community
- WHO Guidelines: World Health Organization health policies
- AI Technology: Google Gemini AI, OpenAI, and Sentence Transformers
- Open Source: FAISS, NetworkX, FastAPI, Next.js, and shadcn/ui communities

## Support & Feedback

If you find this project helpful, please consider starring the repository on GitHub. Feel free to open issues or discussions for feedback, feature requests, or questions.
