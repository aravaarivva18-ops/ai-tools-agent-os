# Use official lightweight Python image
FROM python:3.12-slim

# Install system dependencies needed for lxml, selectolax, and other compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory inside the container
WORKDIR /app

# Copy lockfiles and configuration
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-install-project

# Copy project source code
COPY . .

# Run dev sync to finalize packages
RUN uv sync --frozen

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "python", "tools/dashboard.py"]
