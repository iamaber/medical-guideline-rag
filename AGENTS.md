# AGENTS.md

This document provides essential information for agentic coding assistants working in this repository.

## Build/Lint/Test Commands

This project uses UV for backend and npm for frontend.

### Backend Commands

Environment Setup:
```bash
cd backend
uv sync                    # Install dependencies
uv sync --dev             # Install with dev dependencies
```

Code Quality:
```bash
cd backend
# Format code (Black 25.1.0)
uv run black src/ app/

# Sort imports (isort 6.0.1)
uv run isort src/ app/

# Lint code (flake8 7.3.0)
uv run flake8 src/ app/
```

Testing:
```bash
cd backend
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run a single test file
uv run pytest tests/test_vector_search.py -v

# Run a specific test function
uv run pytest tests/test_vector_search.py::test_function_name -v
```

Running Application:
```bash
cd backend
# FastAPI backend
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend Commands

Development:
```bash
cd frontend
npm run dev            # Start development server (localhost:3000)
npm run build          # Build for production
npm run start          # Start production server
npm run lint           # Run ESLint
```

## Project Structure

```
medical-guideline-rag/
├── backend/                 # Python FastAPI backend
│   ├── app/               # FastAPI application endpoints
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
│   └── .env.local        # Frontend environment variables
└── README.md
```

## Code Style Guidelines

### Backend (Python)

#### Imports
- Order: standard library → third-party → local imports
- Separate groups with blank lines
- Use explicit imports, avoid wildcards
- Example:
  ```python
  import logging
  from pathlib import Path
  from typing import List, Dict, Optional

  from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel, Field

  from config.settings import LOG_LEVEL
  from src.services.vector_search import VectorSearch
  ```

#### Formatting
- Use Black (100 char line length, 4 spaces)
- Use isort for import sorting
- No trailing whitespace
- Follow existing code patterns in each file

#### Type Annotations
- ALL functions must have return type annotations
- Use `typing` module generics (List, Dict, Optional, Tuple)
- Use `pydantic` for data models with Field validation
- Use `Enum` for fixed value sets
- Example:
  ```python
  from typing import List, Dict, Optional
  from pydantic import BaseModel, Field

  def search_drugs(self, query: str, limit: int = 10) -> List[str]:
      """Search for drug names."""
      pass

  class UserInput(BaseModel):
      meds: List[str] = Field(..., min_items=1, max_items=10)
      age: int = Field(..., ge=1, le=120)
  ```

#### Naming Conventions
- Classes: PascalCase (DrugLookup, VectorSearch, GeminiClient)
- Functions/methods: snake_case (find_drug_url, search_drugs)
- Variables: snake_case (drug_name, query, results)
- Constants: UPPER_SNAKE_CASE (LOG_LEVEL, API_PORT)
- Private methods: _prefix (_load_model, _initialize_client)
- Config properties: effective_api_key (for computed values)

#### Error Handling
- Log all errors with context: `logger.error(f"Error message: {e}")`
- Catch specific exceptions first, then Exception
- Return meaningful fallback values or raise HTTPException
- Example:
  ```python
  try:
      result = some_operation()
  except FileNotFoundError:
      logger.error(f"File not found: {path}")
      return {}
  except Exception as e:
      logger.error(f"Unexpected error: {e}", exc_info=True)
      raise HTTPException(status_code=500, detail="Internal error")
  ```

#### Configuration
- Load settings from `config/settings` via pydantic-settings
- Use `SecretStr` for API keys
- Use environment variables with `.env` file
- LLM configuration is simplified in `src/models/llm_config.py`
- Example:
  ```python
  from src.models.llm_config import get_llm_settings

  settings = get_llm_settings()
  # Get API key - unified field works for all providers
  api_key = settings.get_api_key_for_provider()
  ```

#### Service Architecture
- Services are initialized as global instances in `app/main.py`
- Use `@asynccontextmanager` lifespan for startup/shutdown
- Services should be stateless where possible
- Example:
  ```python
  vector_search = None

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      global vector_search
      vector_search = VectorSearch()
      yield
  ```

#### API Endpoints (FastAPI)
- Use async functions for I/O operations
- Define request/response models with Pydantic
- Use path/query parameters appropriately
- Validate input and raise HTTPException with status codes
- Example:
  ```python
  @app.get("/search", response_model=SearchResult)
  async def search(query: str = Query(..., min_length=2)):
      if not query:
          raise HTTPException(status_code=400, detail="Query required")
      return search_service(query)
  ```

#### Medical-Specific Guidelines
- Use proper medical terminology
- Include safety disclaimers in AI-generated responses
- Validate medication names against drug database
- Check drug-drug interactions before recommendations
- Age and gender appropriate dosing considerations
- Example interaction check:
  ```python
  if len(medications) > 1:
      interactions = knowledge_graph.analyze_drug_interactions(medications)
      if interactions:
          logger.warning(f"Found interactions: {interactions}")
  ```

#### Testing Guidelines
- No tests currently exist - create them when adding features
- Use pytest with pytest-asyncio for async tests
- Place tests in `tests/` directory
- Name test files: `test_{module_name}.py`
- Use descriptive test names with snake_case

#### Logging Best Practices
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context in log messages
- Use `exc_info=True` for exceptions to get stack traces
- Example:
  ```python
  logger.info(f"Processing {len(medications)} medications")
  logger.warning(f"Drug not found: {drug_name}")
  logger.error(f"Failed to initialize: {e}", exc_info=True)
  ```

### Frontend (TypeScript/React)

#### TypeScript Guidelines
- Use strict mode in tsconfig.json
- All components must have proper TypeScript interfaces
- Use functional components with React hooks
- Define types for API responses in shared types file
- Example:
  ```typescript
  interface UserInput {
    meds: string[];
    schedule: string[];
    age: number;
    gender: 'M' | 'F';
  }

  const handleSubmit = async (input: UserInput) => {
    const response = await apiClient.getMedicationAdvice(input);
  };
  ```

#### Component Guidelines
- Use shadcn/ui components where possible
- Keep components small and focused
- Use proper prop types with TypeScript interfaces
- Follow React best practices (avoid prop drilling, use context when needed)
- Example:
  ```typescript
  interface CardProps {
    title: string;
    children: React.ReactNode;
  }

  export function Card({ title, children }: CardProps) {
    return (
      <div className="border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        {children}
      </div>
    );
  }
  ```

#### State Management
- Use React hooks (useState, useEffect, useCallback, useMemo)
- Lift state up when multiple components need it
- Use form libraries (react-hook-form) for complex forms
- Example:
  ```typescript
  const [medications, setMedications] = useState<Medication[]>([
    { name: '', schedule: '1+0+1' }
  ]);

  const addMedication = useCallback(() => {
    setMedications(prev => [...prev, { name: '', schedule: '1+0+1' }]);
  }, []);
  ```

#### Styling Guidelines
- Use Tailwind CSS for all styling
- Follow design system consistency
- Use shadcn/ui components as base
- Responsive design with mobile-first approach
- Example:
  ```typescript
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div className="p-4 border rounded-lg bg-gray-50">
      Content here
    </div>
  </div>
  ```

#### API Client
- Use the centralized API client from `src/lib/api.ts`
- Handle errors gracefully
- Show loading states during API calls
- Example:
  ```typescript
  import { apiClient } from '@/lib/api';

  try {
    setLoading(true);
    const response = await apiClient.getMedicationAdvice(userInput);
    setResults(response);
  } catch (error) {
    setError('Failed to generate advice');
  } finally {
    setLoading(false);
  }
  ```

## LLM Provider Configuration

The system supports multiple LLM providers with simplified configuration in `backend/.env`:

### Simplified Pattern (Recommended)

Use the single `LLM_API_KEY` field for all providers:

```env
# Select provider
LLM_PROVIDER=zai

# Set model
LLM_MODEL=GLM-4.7

# Set API key (ONE field for all providers)
LLM_API_KEY=your_api_key_here

# Optional generation settings
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
LLM_TOP_P=0.8
```

### Available Providers

- **z.ai**: GLM-4.7, GLM-4-Flash, GLM-4-Air
- **Google**: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
- **OpenAI**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3.5-sonnet-20250514, claude-3.5-sonnet-20241022
- **DeepSeek**: deepseek-chat, deepseek-coder
- **Ollama**: Local models (no API key needed)
- **Azure**: Custom deployment names

### Getting API Keys

Get your key from the provider's website:
- z.ai: https://z.ai
- OpenAI: https://platform.openai.com/api-keys
- Google: https://console.cloud.google.com/apis/credentials
- Anthropic: https://console.anthropic.com/settings/keys
- DeepSeek: https://platform.deepseek.com

### Backward Compatibility

Legacy provider-specific keys still supported (GOOGLE_API_KEY, OPENAI_API_KEY, etc.) for existing configurations. The unified `LLM_API_KEY` takes priority when set.

## Important Notes

- Python 3.11+ required for backend
- Node.js 18+ required for frontend
- No existing test suite - add tests for new features
- Medical safety is critical - validate all medication-related inputs
- The project uses FAISS for vector search and sentence-transformers for embeddings
- Multiple LLM providers supported with z.ai as primary option
- All API keys should be in respective `.env` files (never commit secrets)
- Backend runs on port 8000, Frontend on port 3000 by default
- Frontend communicates with backend via REST API endpoints
