#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo " AccessGuard AI — Stack Initialization & Health Bootstrap"
echo "=========================================================="

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

echo "[1/4] Ensuring core data services are healthy..."
docker compose up -d postgres redis qdrant

# Wait for postgres readiness
echo "Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-accessguard}" -d "${POSTGRES_DB:-accessguard}" > /dev/null 2>&1; do
    sleep 2
done
echo "✓ PostgreSQL is ready."

# Wait for Redis readiness
echo "Waiting for Redis..."
until docker compose exec -T redis redis-cli ping | grep -q PONG; do
    sleep 2
done
echo "✓ Redis is ready."

# Wait for Qdrant readiness
echo "Waiting for Qdrant..."
until docker compose exec -T qdrant bash -c '</dev/tcp/127.0.0.1/6333' > /dev/null 2>&1; do
    sleep 2
done
echo "✓ Qdrant vector database is ready."

echo "[2/4] Running database migrations..."
docker compose run --rm api uv run alembic upgrade head
echo "✓ Database schema migrations applied successfully."

echo "[3/4] Starting application API, Celery worker, and frontend..."
docker compose up -d --build api worker frontend

echo "[4/4] Verifying live endpoints..."
docker compose ps

echo "=========================================================="
echo " AccessGuard AI is running and operational:"
echo " - Frontend Web UI:  http://localhost:3000"
echo " - Backend REST API: http://localhost:8000"
echo " - API Documentation:http://localhost:8000/docs"
echo " - Qdrant Dashboard: http://localhost:6333/dashboard"
echo "=========================================================="
