# Multi-stage production container for AccessGuard AI Backend and Worker
FROM python:3.12-slim-bookworm AS base

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PLAYWRIGHT_BROWSERS_PATH=/home/accessguard/.cache/ms-playwright \
    AXE_BUNDLE_PATH=/app/tools/axe/node_modules/axe-core/axe.min.js

# Install minimal system dependencies and curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv binary from official distribution
COPY --from=ghcr.io/astral-sh/uv:0.6.5 /uv /uvx /bin/

# Create non-root user and group
RUN groupadd -g 10001 accessguard && \
    useradd -u 10001 -g accessguard -m -s /bin/bash accessguard

WORKDIR /app

# Copy dependency definition files first for optimal layer caching
COPY backend/pyproject.toml backend/uv.lock ./

# Install application dependencies in frozen mode without development packages
RUN uv sync --frozen --no-dev --no-install-project

# Install Playwright browser and its Linux OS shared libraries
RUN uv run playwright install --with-deps chromium

# Copy pinned axe-core library bundle from repository tools
COPY tools/axe/node_modules/axe-core/ /app/tools/axe/node_modules/axe-core/

# Copy backend application source and database migration configurations
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app

# Set non-root ownership on working directories and Playwright cache
RUN chown -R accessguard:accessguard /app /home/accessguard

# Switch to non-root user
USER accessguard

EXPOSE 8000

# Health check probe against live endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default command starts FastAPI application server
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
