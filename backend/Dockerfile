# =============================================================================
# CodeLens AI — Backend Dockerfile
# =============================================================================
# Multi-stage build for the FastAPI backend.
# Includes git for repository cloning during analysis.
# =============================================================================

FROM python:3.12-slim AS base

# Install system dependencies (git for repo cloning, build tools for tree-sitter)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pull uv binary from pinned official image — reproducible install path.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

# Install Python deps from lock file. --frozen refuses to resolve if the lock is missing
# or stale, guaranteeing the exact pinned versions are used.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Install the project itself into the existing venv now that source is present.
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose for worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
