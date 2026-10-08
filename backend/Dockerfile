# ------------------------------- Builder Stage -------------------------------
FROM python:3.13-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install UV (fast Python package manager)
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app


# Copy dependency files for build backend
COPY pyproject.toml .

# Create virtual environment and install dependencies
RUN uv venv .venv && uv sync

# ------------------------------ Production Stage -----------------------------
FROM python:3.13-slim-bookworm AS final

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

# Copy UV from builder
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# The FastAPI backend is the only process served here; the Streamlit UI was
# removed in 67914f0 and replaced by the Next.js frontend.
EXPOSE 8000

# Default command: run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
