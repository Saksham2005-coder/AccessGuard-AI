# AccessGuard AI — Phase 18 Baseline & Change Safety Report

**Date:** November 1, 2026  
**Author:** Antigravity (Principal Engineer, QA Lead & AppSec Specialist)  
**Reference Document:** `AccessGuard_AI_Phase_18_and_Post_Phase_18_Master_Blueprint.md`  
**Target Milestone:** Phase 18 Stabilization & Release Preparation  

---

## 1. Repository & Version Control Baseline

- **Current Branch:** `main` (Verified via `git branch --show-current`)
- **HEAD Commit:** `ce8f418` ("Redesign AccessGuard AI with a graphite and electric blue interface")
- **Existing Tags:** `v1.0.0`
- **Worktree State:** Clean. The only uncommitted file is the user-provided `AccessGuard_AI_Phase_18_and_Post_Phase_18_Master_Blueprint.md`. No user modifications or dirty files were overwritten.
- **Recent Git Log (Top 5 Commits):**
  - `ce8f418` Redesign AccessGuard AI with a graphite and electric blue interface
  - `911d13d` Prepare AccessGuard AI first deployable version
  - `0ba03dc` Finalize setup architecture evaluation and operations guides
  - `663c558` Complete full system regression and security verification
  - `bdbdb8e` Harden runtime configuration and deployment boundaries

---

## 2. Toolchain & Runtime Versions

- **Python:** 3.12.10
- **Node.js:** v26.7.0
- **npm:** 11.19.0
- **uv:** 0.12.5 (210d1f678 2026-08-14 x86_64-pc-windows-msvc)
- **Docker Engine:** 29.9.2, build a82e528
- **Docker Compose:** v5.6.1

---

## 3. Service Topology

| Service | Technology | Port | Container Name | Healthcheck Strategy |
|:---|:---|:---:|:---|:---|
| **PostgreSQL** | PostgreSQL 16 Alpine | 5432 | `accessguard-postgres` | `pg_isready -U accessguard -d accessguard` |
| **Redis** | Redis 7 Alpine | 6379 | `accessguard-redis` | `redis-cli ping` |
| **Qdrant** | Qdrant v1.11.3 | 6333 | `accessguard-qdrant` | TCP probe on port 6333 |
| **Backend API** | FastAPI / Uvicorn | 8000 | `accessguard-api` | `GET /health/live` via curl |
| **Worker** | Celery / Python | — | `accessguard-worker` | Celery inspect / Redis broker |
| **Frontend** | React 19 / Vite / Nginx | 3000 / 5173 | `accessguard-frontend` | HTTP GET `/` via wget |

---

## 4. Baseline Test & Build Results

### 4.1 Backend Test Suite
- **Command:** `uv run pytest tests/unit tests/api`
- **Exit Code:** 0
- **Result:** 60 passed in 16.78s
  - `tests/unit/test_config.py`: 5 passed
  - `tests/unit/test_domain_utils.py`: 18 passed
  - `tests/unit/test_errors.py`: 3 passed
  - `tests/unit/test_health.py`: 4 passed
  - `tests/unit/test_health_live.py`: 1 passed
  - `tests/unit/test_middleware.py`: 4 passed
  - `tests/unit/test_security.py`: 4 passed
  - `tests/unit/test_url_utils.py`: 17 passed
  - `tests/api/test_remediations_approval.py`: 4 passed

### 4.2 Backend Lint & Static Analysis
- **Command:** `uv run ruff check`
- **Exit Code:** 0
- **Result:** "All checks passed!"

### 4.3 Frontend Test Suite
- **Command:** `npm test` (`vitest run`)
- **Exit Code:** 0
- **Result:** 8 test files passed, 23 tests passed in 49.86s
  - `src/test/reports.test.tsx`: 1 passed
  - `src/test/scans.test.tsx`: 3 passed
  - `src/test/projects.test.tsx`: 3 passed
  - `src/test/remediations.test.tsx`: 3 passed
  - `src/test/auth.test.tsx`: 6 passed
  - `src/App.test.tsx`: 2 passed
  - `src/test/findings.test.tsx`: 2 passed
  - `src/test/layout.test.tsx`: 3 passed

### 4.4 Frontend Lint
- **Command:** `npm run lint` (`eslint .`)
- **Exit Code:** 0
- **Result:** Clean execution, 0 errors, 0 warnings.

### 4.5 Frontend Production Build & Bundle Size
- **Command:** `npm run build` (`tsc -b && vite build`)
- **Exit Code:** 0
- **Output:**
  - `dist/index.html`: 0.45 kB (gzip: 0.29 kB)
  - `dist/assets/index-BtBjvfDF.css`: 42.48 kB (gzip: 8.18 kB)
  - `dist/assets/index-Cg4874od.js`: **983.45 kB** (gzip: 287.59 kB)
  - **Warning Emitted:** `(!) Some chunks are larger than 500 kB after minification.`

---

## 5. Verification of Reported Defects

| Bug ID | Severity | Description | Verification Finding in Source / Runtime | Status |
|:---:|:---:|:---|:---|:---:|
| **BUG-01** | **P0** | Compose production mode crash on default credentials | Verified in `docker-compose.yml` (`APP_ENV: ${APP_ENV:-production}`) and `backend/app/config.py` line 99 (`ValueError("Default DATABASE_URL credentials detected in production.")`). | **CONFIRMED** |
| **BUG-02** | **P1** | Celery Compose command points to wrong module path | Verified in `docker-compose.yml` line 95 (`app.core.celery_app.celery_app`). Real path is `app.workers.celery_app:celery_app`. | **CONFIRMED** |
| **BUG-03** | **P1** | Vite has no `/api` development proxy to FastAPI | Verified in `frontend/vite.config.ts`. Missing `server.proxy` block. | **CONFIRMED** |
| **BUG-04** | **P2** | Scan on unverified project returns 404 instead of 403 | Verified in `backend/app/api/v1/scans.py` lines 48-52. Raises `NotFoundError` instead of `ForbiddenError` (403). | **CONFIRMED** |
| **BUG-05** | **P2** | Dark theme hardcoded; no light theme or toggle | Verified in `frontend/src/index.css`. Hardcoded `:root` hex colors and `color-scheme: dark;`. | **CONFIRMED** |
| **BUG-06** | **P2** | Knowledge Base uses hardcoded mock cards | Verified in `frontend/src/pages/KnowledgePage.tsx`. In-memory static array instead of `/api/v1/knowledge/search`. | **CONFIRMED** |
| **BUG-07** | **P2** | Reports Vitest query assertion timeout | Verified historical timing issue. In isolated baseline run it passed, but under asynchronous re-renders it is prone to timing flakiness. | **CONFIRMED FLAKY** |
| **BUG-08** | **P2** | Monolithic 983 kB JS bundle | Verified via `npm run build`: monolithic bundle is 983.45 kB without lazy route splitting. | **CONFIRMED** |
| **BUG-09** | **P3** | No public landing page at `/` | Verified in `frontend/src/App.tsx`: immediate redirect `<Navigate to="/app/overview" replace />`. | **CONFIRMED** |
| **BUG-10** | **P3** | Settings page read-only | Verified in `frontend/src/pages/SettingsPage.tsx` and absence of mutation endpoints in `backend/app/api/v1/auth.py`. | **CONFIRMED** |
| **BUG-11** | **P3** | Argon2id latency on Windows host | Verified in `backend/app/core/security.py`: `m=65536, t=3, p=4` takes 8-11s on Windows CPU threads. | **CONFIRMED** |
| **BUG-12** | **P3** | Email validation errors lack inline guidance | Verified in `frontend/src/pages/RegisterPage.tsx`. No inline helper text for RFC/TLD limits. | **CONFIRMED** |

---

## 6. Pre-Existing Uncommitted Changes & Missing Dependencies

- **Pre-existing changes:** None. The repository is at commit `ce8f418`.
- **External Dependencies:**
  - Gemini / Groq live LLM keys are optional; mock LLM provider is active by default.
  - Live external domain crawling requires legitimate DNS TXT ownership; local mock/demo fixtures must be used for safe local verification.
  - Docker daemon is operational and containers `postgres`, `redis`, `qdrant` are available.

---

## 7. Change Safety Commitment

All Phase 18 modifications will proceed workstream by workstream in strict adherence to:
1. Preserve Git history and main branch integrity.
2. Never weaken SSRF defenses, domain verification, or tenant isolation.
3. Add regression tests for every fix before marking it closed.
4. Verify both Docker Compose and standalone development workflows.
