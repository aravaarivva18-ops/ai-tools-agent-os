# =============================================================================
# Stage 1: Builder — install build dependencies and sync Python deps
# =============================================================================
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy lockfiles and project configuration first (for layer caching)
COPY pyproject.toml uv.lock ./
COPY geo-seo/pyproject.toml geo-seo/
COPY ai-sales/pyproject.toml ai-sales/
COPY ai-marketing/pyproject.toml ai-marketing/
COPY ai-legal/pyproject.toml ai-legal/

# Install dependencies (no source code yet — maximizes Docker layer cache)
RUN uv sync --frozen --no-install-project

# =============================================================================
# Stage 2: Runtime — minimal image with only the virtualenv + source code
# =============================================================================
FROM python:3.12-slim AS runtime

# Install only runtime system libraries (no build-essential, no dev headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy project source code
COPY . .

# Finalize install (installs project packages themselves)
RUN uv sync --frozen

# Create a non-root user and change ownership of work directory
RUN groupadd -g 10001 nonroot && useradd -u 10001 -g nonroot -s /bin/sh -m nonroot \
    && chown -R nonroot:nonroot /app

USER nonroot

ENV PATH="/app/.venv/bin:$PATH"

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "python", "tools/monitoring/dashboard.py"]
