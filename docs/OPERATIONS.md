# AccessGuard AI — Operations Runbook & Administration Guide

This operations guide outlines operational procedures, configuration requirements, maintenance workflows, backup/restore procedures, and incident troubleshooting runbooks for running AccessGuard AI in production and staging environments.

---

## 1. System Topology & Operational Architecture

AccessGuard AI operates as a containerized modular architecture orchestrated via Docker Compose or Kubernetes:

```text
                               +----------------------------------+
                               |     Public Ingress / Load Balancer|
                               +----------------------------------+
                                                |
                               +----------------------------------+
                               |    accessguard-frontend (Nginx)  |
                               |    Port 80 / 443                 |
                               +----------------------------------+
                                       /                     \
                             (Static SPA Assets)         (/api/v1/ Reverse Proxy)
                                     /                         \
                                    v                           v
                       +-------------------------+   +-------------------------+
                       |   React 19 Dashboard    |   |  accessguard-backend    |
                       |   (Client Browser)      |   |  FastAPI (Port 8000)    |
                       +-------------------------+   +-------------------------+
                                                                  |
                                       +--------------------------+--------------------------+
                                       |                          |                          |
                                       v                          v                          v
                        +----------------------+   +----------------------+   +----------------------+
                        | accessguard-postgres |   |  accessguard-redis   |   |  accessguard-qdrant  |
                        | PostgreSQL 16 (5432) |   |    Redis 7 (6379)    |   | Vector Engine (6333) |
                        +----------------------+   +----------------------+   +----------------------+
                                       ^                          ^                          ^
                                       |                          |                          |
                                       +--------------------------+--------------------------+
                                                                  |
                                                     +-------------------------+
                                                     |   accessguard-worker    |
                                                     | Celery + Playwright     |
                                                     +-------------------------+
```

---

## 2. Configuration & Secrets Management

All production settings are loaded from environment variables (or Docker secrets) defined in `.env`:

| Variable | Required | Default | Purpose |
|---|:---:|---|---|
| `SECRET_KEY` | **Yes** | *None* | Cryptographic signing key for JWT tokens. Minimum 32 random characters. |
| `POSTGRES_SERVER` | **Yes** | `postgres` | Hostname of PostgreSQL database. |
| `POSTGRES_PORT` | No | `5432` | Port of PostgreSQL database. |
| `POSTGRES_DB` | **Yes** | `accessguard` | Relational database name. |
| `POSTGRES_USER` | **Yes** | `accessguard` | Relational database user. |
| `POSTGRES_PASSWORD` | **Yes** | *None* | Relational database password. |
| `REDIS_URL` | **Yes** | `redis://redis:6379/0` | Celery broker and result backend URL. |
| `QDRANT_HOST` | No | `qdrant` | Hostname of Qdrant vector engine. |
| `QDRANT_PORT` | No | `6333` | Port of Qdrant vector engine. |
| `LLM_PROVIDER` | No | `gemini` | Primary LLM provider (`gemini`, `groq`, or `mock`). |
| `GEMINI_API_KEY` | Conditional | *None* | Required if `LLM_PROVIDER=gemini`. |
| `GROQ_API_KEY` | Conditional | *None* | Required if `LLM_PROVIDER=groq`. |
| `AXE_BUNDLE_PATH` | No | `/app/tools/axe/...` | Absolute path to local `axe.min.js` bundle. |
| `STORAGE_DIR` | No | `/app/storage` | Directory for DOM snapshots and PDF reports. |
| `TEST_ALLOW_LOOPBACK`| No | `false` | **Set to `false` in production.** Allows loopback URLs for internal test fixtures only. |
| `LOG_LEVEL` | No | `INFO` | Structured JSON log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

> [!WARNING]
> Never set `TEST_ALLOW_LOOPBACK=true` in production environments. Setting this flag disables SSRF loopback protections and permits crawling internal endpoints.

---

## 3. Routine Lifecycle & Bootstrap Operations

### 3.1 Initial Stack Provisioning
To initialize the stack for the first time on a fresh host:

```bash
# 1. Clone repository and initialize environment file
cp .env.example .env
chmod 600 .env

# 2. Populate strong passwords and API keys in .env
nano .env

# 3. Execute automated stack bootstrap script
bash infrastructure/scripts/init-stack.sh
```

### 3.2 Starting and Stopping Containers
```bash
# Start all services in the background
docker compose up -d

# Check running status of all containers
docker compose ps

# View unified structured logs with follow
docker compose logs -f api worker

# Gracefully shut down all services
docker compose down
```

### 3.3 Health Checks & Probes
Automated health checks can be queried by load balancers and orchestrators:

```bash
# Process Liveness Probe (instant process check)
curl -f http://localhost:8000/health/live

# Service Readiness Probe (checks DB, Redis, Qdrant, and axe-core)
curl -f http://localhost:8000/health/ready
```

Expected healthy response from `/health/ready`:
```json
{
  "status": "ready",
  "database": "connected",
  "redis": "connected",
  "qdrant": "connected",
  "axe_core": "available"
}
```

---

## 4. Database Migrations & Schema Evolution

AccessGuard AI uses Alembic for declarative schema migrations.

### 4.1 Applying Migrations
Always execute migrations before deploying new backend containers:

```bash
# Running migrations via Docker Compose
docker compose run --rm api alembic upgrade head

# Running migrations directly in local uv environment
cd backend
uv run alembic upgrade head
```

### 4.2 Checking Migration Status
```bash
docker compose run --rm api alembic current
```

### 4.3 Rolling Back a Migration
If a migration needs to be rolled back during an incident:
```bash
docker compose run --rm api alembic downgrade -1
```

---

## 5. Knowledge Base & Vector Index Operations

The WCAG knowledge base must be seeded into PostgreSQL and Qdrant before RAG retrieval queries can function.

### 5.1 Ingesting Authoritative W3C Sources
```bash
# Run ingestion script inside the worker container
docker compose run --rm worker python scripts/ingest_sources.py
```

### 5.2 Verifying Vector Index Health in Qdrant
```bash
# Check status of wcag_chunks collection in Qdrant
curl http://localhost:6333/collections/wcag_chunks
```

Expected output:
```json
{
  "result": {
    "status": "green",
    "vectors_count": 850,
    "indexed_vectors_count": 850
  }
}
```

---

## 6. Celery Scan Worker Management

The Celery worker executes headless Playwright crawling, axe-core rule evaluation, and LangGraph remediation workflows.

### 6.1 Worker Concurrency
Because headless Chromium processes consume notable CPU and memory:
- **Recommended Concurrency**: 2–4 worker processes per 8 GB of host RAM.
- **Worker Command**:
  ```bash
  celery -A app.worker.celery_app worker --loglevel=INFO --concurrency=2
  ```

### 6.2 Monitoring Task Queues
Inspect active and pending scan jobs using the Celery CLI:
```bash
# Inspect active tasks
docker compose exec worker celery -A app.worker.celery_app inspect active

# Inspect registered tasks
docker compose exec worker celery -A app.worker.celery_app inspect registered

# Check queue ping
docker compose exec worker celery -A app.worker.celery_app inspect ping
```

### 6.3 Handling Stuck Scans
If an audited website hangs or crawler timeouts fail:
1. Scan tasks enforce a hard time limit (`time_limit=300` seconds).
2. Users can trigger cancellation from the frontend dashboard or via API:
   ```bash
   POST /api/v1/scans/{scan_id}/cancel
   ```
3. To purge orphan Celery tasks from Redis:
   ```bash
   docker compose exec redis redis-cli flushdb
   ```

---

## 7. Domain Ownership Verification Troubleshooting

Projects require verified domain ownership before audits can be initiated.

### 7.1 DNS TXT Verification Flow
1. User creates a project with root domain (e.g., `example.com`).
2. System generates a unique verification token: `accessguard-verify=<UUID>`.
3. User creates a DNS TXT record at: `_accessguard-verification.example.com`.
4. User clicks **Verify Domain** in the UI (or triggers `POST /api/v1/projects/{id}/domain-verification/check`).

### 7.2 Troubleshooting Verification Failures
- **Symptom**: `DNS TXT record not found`.
  - **Resolution**: Verify DNS propagation using `dig`:
    ```bash
    dig TXT _accessguard-verification.example.com +short
    ```
  - Note that DNS TTL propagation may take 5–15 minutes depending on the DNS provider.
- **Symptom**: Cloudflare or DNS proxy hiding TXT records.
  - **Resolution**: Ensure the record is created as a pure `TXT` record, not proxied.

---

## 8. Backup, Restore & Disaster Recovery

### 8.1 PostgreSQL Relational Backup
Create automated daily database dumps:
```bash
# Create timestamped SQL backup
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec postgres pg_dump -U accessguard -d accessguard -Fc > /backups/accessguard_${BACKUP_DATE}.dump

# Restore from backup file
docker compose exec -T postgres pg_restore -U accessguard -d accessguard --clean < /backups/accessguard_20261031.dump
```

### 8.2 Qdrant Vector Collection Snapshot
```bash
# Trigger Qdrant snapshot creation
curl -X POST http://localhost:6333/collections/wcag_chunks/snapshots

# List available snapshots
curl http://localhost:6333/collections/wcag_chunks/snapshots
```

### 8.3 Storage Artifacts Backup
Back up the `/app/storage` volume containing DOM snapshots and PDF audit reports:
```bash
tar -czvf /backups/accessguard_storage_${BACKUP_DATE}.tar.gz -C ./storage .
```

---

## 9. Incident Response & Troubleshooting Runbook

### Scenario A: Celery Worker Out-Of-Memory (OOM)
- **Symptoms**: Celery worker container restarts abruptly; scans transition to `failed` with exit code 137.
- **Cause**: Chromium instances consuming excessive RAM during multi-tab crawling.
- **Action**:
  1. Reduce worker concurrency in `docker-compose.yml`: `--concurrency=1`.
  2. Increase container memory limit from `2G` to `4G`.
  3. Restart worker: `docker compose restart worker`.

### Scenario B: LLM Rate Limit (HTTP 429)
- **Symptoms**: Remediation proposal generation fails with `ResourceExhausted` or `rate_limit_exceeded`.
- **Cause**: Free-tier Gemini or Groq API rate limits exceeded.
- **Action**:
  1. AccessGuard AI automatically retries transient errors with exponential backoff.
  2. If quota is exhausted, switch providers in `.env`:
     ```env
     LLM_PROVIDER=groq
     GROQ_API_KEY=gsk_...
     ```
  3. Reload backend: `docker compose restart api worker`.

### Scenario C: SSRF Target Rejected
- **Symptoms**: Scan immediately fails with error `"Target URL rejected by scanner security policy"`.
- **Cause**: The audited domain resolves to a private IP, loopback address, or internal hostname.
- **Action**:
  1. Confirm the domain is publicly resolvable via public DNS (`8.8.8.8`).
  2. If testing against a local fixture in staging, explicitly set `TEST_ALLOW_LOOPBACK=true` in the staging `.env` file.
