# ------------------------------- Builder Stage -------------------------------
FROM python:3.12-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Pin uv so dependency resolution is reproducible
ARG UV_VERSION=0.13.8
RUN pip install --no-cache-dir "uv==${UV_VERSION}"

WORKDIR /app

# Copy the lockfile so the build resolves exactly the committed versions
COPY pyproject.toml uv.lock ./

# Create the virtual environment from the lockfile (no dev tooling in the image)
RUN uv sync --frozen --no-dev

# ------------------------------ Production Stage -----------------------------
FROM python:3.12-slim-bookworm AS final

# Create non-root user for security
RUN useradd --create-home appuser
USER appuser

WORKDIR /app

# Copy virtual environment and source code from builder
COPY --from=builder /app/.venv .venv
COPY app/ app/
COPY config/ config/
COPY data/ data/
COPY src/ src/
COPY templates/ templates/
COPY pyproject.toml .
COPY uv.lock .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# The FastAPI backend is the only process served here; the Streamlit UI was
# removed in 67914f0 and replaced by the Next.js frontend.
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import json, sys, urllib.request; body = json.load(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)); sys.exit(0 if body.get('status') != 'unhealthy' else 1)"]

# Default command: run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
