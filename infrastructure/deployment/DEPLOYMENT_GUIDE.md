# AccessGuard AI — Deployment Hardening & Operations Guide

This guide specifies the operational boundaries, container hardening measures, security policies, and deployment lifecycle for AccessGuard AI in production.

---

## 1. Runtime Boundaries & Least Privilege

### Non-Root Container Execution
All backend API and Celery worker processes execute as an unprivileged user (`accessguard`, UID/GID `10001`):
- Read-only root filesystem recommendations where supported.
- Explicit permissions granted only to `/app` and Playwright cache directory `/home/accessguard/.cache`.
- Zero host volume mount write privileges.

### Network Segmentation
- **Internal Network**: `accessguard-network` is a private bridge network isolating `postgres`, `redis`, and `qdrant`.
- **Egress Isolation**: The scanner browser runs with strict egress controls:
  - Private IP address blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `::1`) are rejected at the application policy layer prior to HTTP connection.
  - AWS/GCP cloud metadata endpoints (`169.254.169.254`) are explicitly blocked.
  - Snapshot validation in Playwright aborts all outbound network calls (`page.route("**/*", abort)`).

### Secret Management
- Secrets (`DATABASE_URL`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`) must never be baked into Docker images or committed to Git.
- In production, inject secrets via environment variables from a platform secret store (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault).
- At startup, `Settings.validate_runtime_security()` automatically fails if default placeholders (such as `change-me` or `local-dev-secret`) are detected in production mode.

---

## 2. Database Migration Lifecycle

Database migrations must run as a **single release hook or one-off container job** before deploying new application replicas:
```bash
# Execute Alembic migration release job
docker compose run --rm api uv run alembic upgrade head
```
Never execute migrations concurrently inside the startup lifecycle of auto-scaling API containers, preventing schema migration deadlocks.

---

## 3. Health Checks & Probes

| Probe Endpoint | Purpose | Checks Performed |
|---|---|---|
| `GET /health/live` | Liveness check (K8s/Docker) | Lightweight process uptime check; returns `HTTP 200 {"status": "live"}` |
| `GET /health/ready` | Readiness check | Validates active connections to PostgreSQL, Redis broker, and Qdrant vector database |

---

## 4. Resource Allocation & Worker Concurrency

Browser automation requires substantial memory. To avoid out-of-memory container crashes:
- Limit Celery worker concurrency to `2` per container:
  `celery worker --loglevel=info --concurrency=2`
- Recommended container memory limits:
  - `api`: 1 GB RAM, 1 vCPU
  - `worker`: 2 GB RAM, 2 vCPUs (Playwright Chromium)
  - `postgres`: 1 GB RAM, 1 vCPU
  - `redis`: 512 MB RAM, 0.5 vCPU
  - `qdrant`: 1 GB RAM, 1 vCPU
  - `frontend`: 256 MB RAM, 0.25 vCPU

---

## 5. Backup & Disaster Recovery

### PostgreSQL
```bash
# Daily automated backup
docker compose exec -T postgres pg_dump -U accessguard accessguard | gzip > /backups/accessguard-$(date +%F).sql.gz

# Restore
gunzip < /backups/accessguard-backup.sql.gz | docker compose exec -T postgres psql -U accessguard -d accessguard
```

### Qdrant Vector Snapshots
```bash
# Trigger Qdrant snapshot
curl -X POST "http://localhost:6333/collections/wcag_knowledge/snapshots"
```
Snapshots are stored under the persistent named volume `qdrant_data`.
