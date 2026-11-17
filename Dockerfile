# Build a static UI; no Node process or secrets are needed in the runtime image.
FROM node:22-bookworm-slim AS frontend-build

WORKDIR /frontend
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_API_URL=""
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-bookworm AS backend-build

ARG UV_VERSION=0.13.8
RUN pip install --no-cache-dir "uv==${UV_VERSION}"
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime

# FAISS and PyTorch require native C++ and OpenMP runtimes on Debian slim.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 user

WORKDIR /app
COPY --from=backend-build --chown=1000:1000 /app/.venv /app/.venv
COPY --chown=1000:1000 backend/app/ app/
COPY --chown=1000:1000 backend/config/ config/
COPY --chown=1000:1000 backend/src/ src/
COPY --chown=1000:1000 backend/templates/ templates/
COPY --chown=1000:1000 backend/data/ data/
COPY --chown=1000:1000 backend/pyproject.toml backend/uv.lock ./
COPY --from=frontend-build --chown=1000:1000 /frontend/out/ /app/static/

# Runtime secrets (GROQ_API_KEY, JINA_API_KEY, NCBI_*) are supplied by Spaces.
# Trust private infrastructure hops, not every address: public clients must
# remain untrusted for the application's right-to-left X-Forwarded-For parser.
ENV PATH="/app/.venv/bin:$PATH" \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/static \
    API_PORT=7860 \
    OMP_NUM_THREADS=2 \
    TOKENIZERS_PARALLELISM=false \
    TRUSTED_PROXIES="127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7"

USER 1000
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import json, sys, urllib.request; body = json.load(urllib.request.urlopen('http://127.0.0.1:7860/health', timeout=4)); sys.exit(0 if body.get('status') != 'unhealthy' else 1)"]

# The application, rather than Uvicorn, validates forwarded client IP headers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--no-proxy-headers"]
