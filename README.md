# Medical Guideline RAG

[**Try the live demo**](https://iamaber-medical-guideline-rag.hf.space/consultation) · [Drug interaction checker](https://iamaber-medical-guideline-rag.hf.space/drug-interaction)

![Entering two medications in the live demo and getting advice whose PMID citations link to PubMed](assets/demo.gif)

Enter a patient's medications, schedules, age and conditions. Get medication advice that cites the PubMed articles and MedEx drug monographs it used, with a link to each article. Built for clinicians, pharmacy and medical students, and anyone who wants to see a RAG system that shows its sources.

- Searches 12,465 records from 4,461 PubMed articles and 8 WHO guidelines with FAISS.
- Maps 22,974 Bangladeshi brand names to generic drugs, so "Comet 500" is searched as metformin.
- Gives the model each drug's MedEx monograph and uses the patient's conditions in the search.
- Checks a small knowledge graph of known interactions (11 drugs, 5 pairs).
- Shows a labeled safety notice instead of advice when the model is unavailable.

## How answers stay grounded

The model gets the retrieved abstracts and monographs, and the prompt tells it to cite them next to each claim and never invent a citation. Each `[PMID:…]` citation links to the article. From a live answer for a 58-year-old man with type 2 diabetes and hypertension on Comet 500 (metformin) and Amdocal 5 (amlodipine):

> **Answer:** "Poor adherence is a major challenge in hypertension management and is associated with suboptimal BP control [[PMID:39838337](https://pubmed.ncbi.nlm.nih.gov/39838337/)]."
>
> **Cited abstract** ([PMID 39838337](https://pubmed.ncbi.nlm.nih.gov/39838337/)): "In Bangladesh, as in many other countries, poor adherence to medication represents a challenge to effective hypertension management."

When the evidence is silent, the answer says so: "specific pharmacokinetic interaction data for Amlodipine-Metformin is not detailed in the provided text, but the class effect on glucose should be assumed."

**For education only. This is not medical advice.**

## How it works

![System Architecture](assets/System%20Architecture.svg)

FastAPI backend (Python 3.12, uv), Next.js frontend, sentence-transformers embeddings (all-MiniLM-L6-v2), FAISS, NetworkX, and Groq running Qwen 3.8 27B through Pydantic AI.

## Run locally

```bash
cd backend && cp .env.example .env    # set GROQ_API_KEY
uv sync && uv run uvicorn app.main:app --reload --port 8000

cd frontend && npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev    # http://localhost:3000
```

Or run the whole app in one container on port 7860:

```bash
docker build -t medical-guideline-rag .
docker run --rm -p 7860:7860 --env-file backend/.env medical-guideline-rag
```

Without an LLM key the API still starts; `/health` reports `degraded` and `/advise` returns the safety notice.

## Configuration

Set these in `backend/.env` (see `.env.example` for the rest):

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Required for generated advice. `LLM_API_KEY` also works and takes precedence. |
| `LLM_PROVIDER`, `LLM_MODEL` | Switch provider: `groq` (default), `google`, `openai`, `anthropic`, `zai`, `deepseek`, `ollama`, `azure`. |
| `LLM_FALLBACK_MODEL` | Model tried once when the main one is rate limited (default `openai/gpt-oss-120b` on Groq; empty disables). Repeat consultations are served from a 24-hour in-memory cache. |
| `JINA_API_KEY` | Optional. Raises the rate limit for MedEx monograph scraping. |
| `API_KEY` | Optional. When set, `/advise`, `/advise/html` and `/drug_interactions` require `X-API-Key`. |
| `RATE_LIMIT_PER_MINUTE` | Per-client request limit (default 20). |
| `CORS_ALLOW_ORIGINS` | Allowed browser origins (default `http://localhost:3000`). |

## Deploy to Hugging Face

The root `Dockerfile` builds a Docker Space that serves the UI and API on port 7860. Set `GROQ_API_KEY` as a Space secret, never as a public variable. The Space's configuration lives in `hf-space/README.header.md` so it stays off GitHub; the Space's `README.md` is that header followed by this file:

```bash
cat hf-space/README.header.md README.md > /tmp/space-README.md
hf upload iamaber/medical-guideline-rag /tmp/space-README.md README.md --repo-type space
```

## API

| Endpoint | Purpose |
|---|---|
| `POST /advise` | Cited medication advice for a patient |
| `POST /advise/html` | The same advice as an HTML report |
| `POST /drug_interactions` | Known interactions between medications |
| `GET /search_drugs` | Brand name autocomplete |
| `GET /health`, `GET /stats` | Status and index statistics |

```bash
curl -X POST localhost:8000/advise -H 'content-type: application/json' -d '{
  "meds": ["Comet 500", "Amdocal 5"], "schedule": ["1+0+1", "1+0+0"],
  "age": 58, "gender": "M", "conditions": ["type 2 diabetes", "hypertension"]}'
```

## Development

```bash
cd backend && uv run pytest && uv run black --check . && uv run isort --check-only . && uv run flake8
cd frontend && npm run lint && npm run type-check
```

## License

Code is [MIT](LICENSE). The WHO guideline PDFs and everything derived from them (summaries, metadata, index entries) are CC BY-NC-SA 3.0 IGO, for non-commercial use only; WHO does not endorse this project. PubMed abstracts and the MedEx brand database have their own terms, which neither license covers. Details and attributions are in [LICENSE-DATA.md](LICENSE-DATA.md).
