# Contributing

Thanks for helping. Bug reports, data fixes, and pull requests are all welcome.

## Where to start

- Issues labeled [`good first issue`](https://github.com/iamaber/medical-guideline-rag/labels/good%20first%20issue) are scoped for a first pull request.
- Questions and ideas go in [Discussions](https://github.com/iamaber/medical-guideline-rag/discussions).
- Bugs and concrete feature requests go in [Issues](https://github.com/iamaber/medical-guideline-rag/issues/new/choose).

## Setup

You need Python 3.12 with [uv](https://docs.astral.sh/uv/) and Node.js 18 or newer. A [Groq API key](https://console.groq.com/keys) is free and only needed for generated advice; without one, the API starts and returns the safety notice.

```bash
cd backend && cp .env.example .env    # set GROQ_API_KEY
uv sync && uv run uvicorn app.main:app --reload --port 8000

cd frontend && npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev    # http://localhost:3000
```

## Checks

CI runs these on every pull request. Run them before you push:

```bash
cd backend && uv run pytest && uv run black --check app config src tests \
  && uv run isort --check-only app config src tests && uv run flake8 app config src tests
cd frontend && npm run lint && npm run type-check
```

Backend code uses Black at 100 columns, isort, and type annotations on every function. Add a test in `backend/tests/` for each behavior you change.

## Medical content

This project gives medication guidance, so content changes need a source.

- Every new or changed drug interaction, dose, or contraindication must cite a drug label, a guideline, or a PubMed article in the pull request.
- Generated advice must keep citing its evidence and keep the safety notice. Do not remove the "not medical advice" disclaimer.
- Never commit API keys or patient data.

## Pull requests

Keep each pull request to one change. The template asks why the change is needed, what changed, and how you verified it. Screenshots help for UI changes.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
