# AGENTS.md

This document provides essential information for agentic coding assistants working in this repository.

## Build/Lint/Test Commands

This project uses UV as the package manager (modern, fast Python package manager).

### Environment Setup
```bash
uv sync                    # Installs runtime and dev dependencies
```

### Code Quality
```bash
# Format code (Black 25.1.0)
uv run black src/ app/ config/ tests/

# Sort imports (isort 6.0.1)
uv run isort src/ app/ config/ tests/

# Lint code (flake8 7.3.0)
uv run flake8 src/ app/ config/ tests/
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run a single test file
uv run pytest tests/test_drug_lookup.py -v

# Run a specific test function
uv run pytest tests/test_api.py::test_advise_reports_fallback_source -v
```

### Running the Application
```bash
# FastAPI backend
uv run uvicorn app.main:app --reload --port 8000

```

## Code Style Guidelines

### Imports
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

### Formatting
- Use Black (100 char line length, 4 spaces)
- Use isort for import sorting
- No trailing whitespace
- Follow existing code patterns in each file

### Type Annotations
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

### Naming Conventions
- Classes: PascalCase (DrugLookup, VectorSearch, UnifiedLLMClient)
- Functions/methods: snake_case (find_drug_url, search_drugs)
- Variables: snake_case (drug_name, query, results)
- Constants: UPPER_SNAKE_CASE (LOG_LEVEL, API_PORT)
- Private methods: _prefix (_load_model, _initialize_client)
- Config properties: effective_api_key (for computed values)

### Error Handling
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

### Documentation
- Module-level docstrings explaining purpose
- Function docstrings with Args/Returns sections
- Inline comments for complex logic
- Use logging for debugging: `logger.info("Processing request...")`

### Configuration
- Load settings from `config/settings` via pydantic-settings
- Use `SecretStr` for API keys
- Use environment variables with `.env` file
- Example:
  ```python
  from src.models.llm_config import LLMSettings

  settings = LLMSettings()
  api_key = settings.get_api_key_for_provider()
  ```

### Service Architecture
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

### API Endpoints (FastAPI)
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

### File Organization
```
app/              # FastAPI application endpoints

src/
  services/        # Business logic services
  models/          # Pydantic data models
  utils/           # Shared utility functions
  data_collection/ # Data fetching/processing
  preprocessing/    # Data cleaning/transforming
config/           # Configuration management
data/             # Data files (processed, raw, indexes)
```

### Medical-Specific Guidelines
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

### Testing Guidelines
- Tests live in `backend/tests/` (pytest + pytest-asyncio); add a test with each feature
- Use a fake model/service in API tests so no network call is made
- Place tests in `tests/` directory
- Name test files: `test_{module_name}.py`
- Use descriptive test names with snake_case

### Logging Best Practices
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

## Important Notes

- Python 3.12+ required
- No existing test suite - add tests for new features
- Medical safety is critical - validate all medication-related inputs
- The project uses FAISS for vector search and sentence-transformers for embeddings
- Groq / qwen/qwen3.8-27b is the default LLM provider/model; Gemini remains optional
- Use GROQ_API_KEY or the unified LLM_API_KEY (which takes precedence)
- GROQ_REASONING_EFFORT defaults to "none" for instruct mode; empty omits the parameter
- Locked Pydantic AI 1.30.1 sends reasoning_effort via ModelSettings.extra_body
- Groq calls use no retries, one model request and a 30-second deadline
- Complete prompts: 16,000 characters (~4,000 tokens); output: 1,200 tokens by default, cap 2,048
- Preserve evidence caps: top five articles, 700 characters/article, 6,000 total; monographs 4,000
- Failure notes must stay request-local; never log provider error bodies, keys or tracebacks
- All API keys should be in `.env` file (never commit secrets)
