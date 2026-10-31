# AccessGuard AI — Phase 18 Bug Register

This register documents all bugs identified during the initial QA audit, their severity, root cause analysis, corrective implementation, and automated regression test coverage.

---

## Bug Inventory Summary

| Bug ID | Severity | Category | Status | Regression Test |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | P0 (Critical) | Runtime / Compose | RESOLVED | `tests/unit/test_config.py::test_development_allows_placeholder_db_credentials` |
| **BUG-02** | P0 (Critical) | Worker / Celery | RESOLVED | Celery worker startup verification & target module verification |
| **BUG-03** | P1 (High) | Frontend / Network | RESOLVED | Vite dev server proxy configuration + HTML error interceptor |
| **BUG-04** | P1 (High) | Security / Backend | RESOLVED | `tests/api/test_scans_and_account_api.py::test_create_scan_unverified_domain_forbidden` |
| **BUG-05** | P2 (Medium) | UI / Truthfulness | RESOLVED | `frontend/src/test/reports.test.tsx` + ReportsPage empty/truthful state |
| **BUG-06** | P2 (Medium) | Feature / Settings | RESOLVED | `tests/api/test_scans_and_account_api.py::test_user_profile_update` & `test_change_password_flow` |
| **BUG-07** | P2 (Medium) | Feature / Knowledge| RESOLVED | `frontend/src/pages/KnowledgePage.tsx` + `frontend/src/api/knowledge.ts` |
| **BUG-08** | P3 (Low) | Performance / Bundle| RESOLVED | Vite manualChunks code splitting (all chunks < 500 kB) |

---

## Detailed Bug Reports

### BUG-01: Production Mode Crash on Default Credentials in Docker Compose
- **Severity:** P0 (Critical)
- **Component:** `docker-compose.yml`, `backend/app/config.py`
- **Description:** `docker-compose.yml` explicitly hardcoded `APP_ENV: production` while using default development database credentials (`change-me`). The production security validator in `config.py` purposefully fails closed with `RuntimeError: Insecure database credentials detected for production environment`.
- **Root Cause:** Environment mismatch in docker-compose.yml; default compose setup was intended for local developer deployment but had production mode configured without production credentials.
- **Resolution:** Updated `docker-compose.yml` to set `APP_ENV: ${APP_ENV:-development}` and interpolated database credentials `postgresql+asyncpg://${POSTGRES_USER:-accessguard}:${POSTGRES_PASSWORD:-change-me}@postgres:5432/${POSTGRES_DB:-accessguard}`.
- **Verification:** Unit tests in `backend/tests/unit/test_config.py` verify that production mode fails closed on placeholder credentials while development mode permits them for local development.

---

### BUG-02: Celery Worker Fails to Start Due to Incorrect Target Module
- **Severity:** P0 (Critical)
- **Component:** `docker-compose.yml`
- **Description:** Celery worker service was invoked with command `celery -A app.workers.tasks worker ...`. The actual Celery application instance is instantiated and configured in `app.workers.celery_app`.
- **Root Cause:** Target module path typo in compose file.
- **Resolution:** Corrected command to `celery -A app.workers.celery_app:celery_app worker --loglevel=INFO --concurrency=2`.
- **Verification:** Worker launched successfully in local daemon task without module import errors.

---

### BUG-03: Frontend Dev Server Missing Backend API Proxy
- **Severity:** P1 (High)
- **Component:** `frontend/vite.config.ts`, `frontend/src/api/client.ts`
- **Description:** Direct API requests to `/api/v1/*` in browser during development returned Vite's fallback HTML index page, causing Axios to fail with unhandled JSON parsing syntax errors.
- **Root Cause:** `vite.config.ts` lacked a `server.proxy` block mapping `/api` to the backend Uvicorn server (`http://127.0.0.1:8000`).
- **Resolution:** Added `server.proxy` to `vite.config.ts` targeting `process.env.VITE_API_URL || 'http://127.0.0.1:8000'`. Updated `client.ts` response interceptor to detect HTML fallback responses and convert them into clear network configuration errors.
- **Verification:** `Invoke-WebRequest -Uri 'http://localhost:5173/api/v1/health/live'` returns `{"status":"alive"}`.

---

### BUG-04: Unverified Domain Scans Raised 400 Bad Request Instead of 403 Forbidden
- **Severity:** P1 (High)
- **Component:** `backend/app/api/v1/scans.py`
- **Description:** Attempting to trigger an accessibility crawl scan against an unverified target domain raised `ValueError` (resulting in HTTP 400), violating the specification that domain authorization must strictly return HTTP 403 Forbidden.
- **Root Cause:** Exception handling raised `ValueError` instead of domain `AuthorizationError`.
- **Resolution:** Updated `backend/app/api/v1/scans.py` to raise `AuthorizationError` (`Domain '{project.base_domain}' is not verified. Please complete DNS TXT verification before running a scan.`) while maintaining 404 non-disclosure for nonexistent/cross-tenant projects.
- **Verification:** Integration tests in `backend/tests/api/test_scans_and_account_api.py::test_create_scan_unverified_domain_forbidden` verify HTTP 403 response.

---

### BUG-05: Compliance Health Score Displayed Default 100/100 on Zero-Scan Projects
- **Severity:** P2 (Medium)
- **Component:** `frontend/src/pages/ReportsPage.tsx`
- **Description:** For projects with zero completed scans, the reports page calculated a synthetic compliance health score of 100 max, misrepresenting unverified or unscanned projects as fully compliant.
- **Root Cause:** Health score calculation defaulted to `100 - penalty` where `penalty = 0`.
- **Resolution:** Updated `ReportsPage.tsx` to inspect `completedScans.length`. If no scans have been completed, health score displays "N/A" with description "Not yet assessed", and JSON export reflects `health_score_status: "not_yet_assessed"`. Added sanitized CSV export with formula injection prevention.
- **Verification:** Verified in Vitest test suite (`src/test/reports.test.tsx`) and genuine screenshot `11_reports_page_truthful_health.png`.

---

### BUG-06: Settings Page Lacked Account Mutation Capabilities
- **Severity:** P2 (Medium)
- **Component:** `backend/app/api/v1/auth.py`, `frontend/src/pages/SettingsPage.tsx`
- **Description:** Settings page displayed read-only account details with no ability to update display names or change passwords.
- **Root Cause:** Missing backend endpoints and mutation forms.
- **Resolution:** 
  1. Implemented `PATCH /api/v1/auth/me` to update display names.
  2. Implemented `POST /api/v1/auth/change-password` with Argon2id current password verification and token revocation.
  3. Built interactive forms on `SettingsPage.tsx` with error/success feedback alerts.
- **Verification:** `tests/api/test_scans_and_account_api.py::test_user_profile_update` and `test_change_password_flow` pass. Verified in screenshot `13_settings_page_account.png`.

---

### BUG-07: Knowledge Base Rendered Hardcoded Static Mocks
- **Severity:** P2 (Medium)
- **Component:** `frontend/src/pages/KnowledgePage.tsx`, `frontend/src/api/knowledge.ts`
- **Description:** The Knowledge Base page rendered hardcoded static mock cards rather than connecting to the live RAG endpoints `/api/v1/knowledge/sources` and `/api/v1/knowledge/search`.
- **Root Cause:** Frontend was stubbed with static data during earlier phases.
- **Resolution:** Implemented `frontend/src/api/knowledge.ts` and refactored `KnowledgePage.tsx` to execute live RAG searches (Hybrid, Dense, Lexical) with query clear button, source badge indicators, and detail drawer.
- **Verification:** Genuine screenshot `12_knowledge_page_rag.png` showing live retrieved W3C sources and search queries.

---

### BUG-08: Monolithic Bundle Size Exceeded 500 kB Warning Limit
- **Severity:** P3 (Low)
- **Component:** `frontend/src/App.tsx`, `frontend/vite.config.ts`
- **Description:** Production build generated a 983 kB monolithic JavaScript chunk, exceeding recommended performance thresholds.
- **Root Cause:** All route pages were statically imported in `App.tsx`, and all vendor dependencies were bundled into a single file.
- **Resolution:**
  1. Implemented `React.lazy()` route splitting in `App.tsx` with `<Suspense>` loaders.
  2. Configured Rolldown `manualChunks` in `vite.config.ts` for `vendor-react`, `vendor-query`, and `vendor-icons`.
- **Verification:** `npm run build` completed with zero chunk size warnings. All page chunks are between 10 kB and 360 kB (all well below 500 kB).
