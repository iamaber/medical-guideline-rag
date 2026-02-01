#!/bin/bash
# Create PR for multi-LLM support
# Usage: ./create_pr.sh [branch-name]
# Default: current branch if not specified

set -e

BRANCH_NAME=${1:-$(git rev-parse --abbrev-ref HEAD)}

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo "Error: GitHub CLI not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi

# Check if gh is installed
if ! command -v gh &>/dev/null; then
    echo "Error: GitHub CLI not installed"
    exit 1
fi

# Check if branch exists
if ! git rev-parse --verify "origin/$BRANCH_NAME" &>/dev/null; then
    echo "Error: Branch '$BRANCH_NAME' does not exist"
    exit 1
fi

# Create PR
gh pr create \
  --base main \
  --head "$BRANCH_NAME" \
  --title "feat: add multi-LLM provider support with Pydantic AI" \
  --body "$(cat <<'PRBODY'
## Summary
- Add support for multiple LLM providers (OpenAI, Anthropic, Google, Ollama, Azure, DeepSeek) via Pydantic AI
- Implement unified async LLM client with provider-agnostic interface
- Migrate configuration to pydantic-settings for better type safety and validation
- Add shared utilities to reduce code duplication
- **Fix:** Corrected Ollama and Azure provider initialization APIs

## Changes

### New Files
- `src/models/llm_config.py` - LLMProvider enum, LLMSettings, and MedicationAdviceOutput models
- `src/services/llm_client.py` - UnifiedLLMClient with sync/async methods
- `src/utils/common.py` - Shared utilities (get_current_year, save_json, load_json, etc.)

### Modified Files
- `config/settings.py` - Migrated to pydantic-settings with multi-provider support
- `src/preprocessing/summarizer.py` - Refactored to use UnifiedLLMClient
- `src/services/vector_search.py` - Fixed hardcoded year, added query embedding caching
- `.env.example` - Documented all provider configuration options
- `pyproject.toml` - Added pydantic-ai and pydantic-settings dependencies

### Dependencies
- Added `pydantic-ai>=1.30.1`
- Added `pydantic-settings>=2.12.0`

## Configuration
Users select their provider via environment variables:
```env
LLM_PROVIDER=google  # openai, anthropic, google, ollama, azure, deepseek
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your_key_here
```

## Backwards Compatibility
- `GEMINI_API_KEY` is still supported as an alias for `GOOGLE_API_KEY`
- Existing code using direct Gemini imports will continue to work

## API Fixes
- **Fixed OllamaProvider:** Changed from non-existent OllamaProvider to OpenAIProvider with custom base_url and placeholder api_key='ollama'
- **Fixed AzureProvider:** Changed from incorrect AzureProvider parameters to AsyncAzureOpenAI client wrapped in OpenAIProvider

These changes align with Pydantic AI's documented API for these providers.
PRBODY
)" || { echo "Failed to create PR"; exit 1; }

echo "PR created successfully!"
