# =============================================================================
# CodeLens AI — Backend Dockerfile
# =============================================================================
# Multi-stage build for a lean production image.
#
# Build:   docker build -t codelens-backend .
# Run:     docker run -p 8000:8000 --env-file ../.env codelens-backend
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Builder: install Python deps into a virtual-env
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system packages required by compiled wheels (e.g. asyncpg, cryptography)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency manifests first (layer caching)
COPY requirements.txt .

# Install Python deps into a dedicated prefix so we can copy them cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — Runtime: slim image with only the runtime artifacts
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Labels
LABEL maintainer="CodeLens AI Team"
LABEL description="FastAPI backend for CodeLens AI legacy modernization platform"

# Install runtime system dependencies:
#   - git: needed to clone user repositories
#   - libpq5: PostgreSQL client library (required by asyncpg at runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application source code
COPY . .

# Create a non-root user for security
RUN addgroup --system codelens && \
    adduser --system --ingroup codelens codelens && \
    # Ensure the temp repos directory exists and is writable
    mkdir -p /tmp/repos && chown codelens:codelens /tmp/repos

USER codelens

# Expose the API port
EXPOSE 8000

# Default command — production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
