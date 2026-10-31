# AccessGuard AI — Phase 18 Test Matrix

This matrix documents the comprehensive automated test coverage for AccessGuard AI following Phase 18 stabilization.

---

## 1. Backend Test Suite (`pytest`)
- **Total Test Cases:** 69
- **Passed:** 69 (100%)
- **Failed:** 0
- **Execution Duration:** 25.84s
- **Test Runner:** `pytest 9.2.0` on Python 3.12.10

### Detailed Test Inventory

| Module / Test File | Test Function Name | Area Verified | Result |
| :--- | :--- | :--- | :--- |
| `tests/unit/test_config.py` | `test_production_rejects_insecure_database_url` | Production security fail-closed on default DB password | **PASS** |
| `tests/unit/test_config.py` | `test_production_rejects_default_jwt_secret` | Production security fail-closed on default JWT secret | **PASS** |
| `tests/unit/test_config.py` | `test_production_enforces_secure_cookies` | Production cookie security enforcement | **PASS** |
| `tests/unit/test_config.py` | `test_production_rejects_loopback_override` | SSRF loopback override prevention | **PASS** |
| `tests/unit/test_config.py` | `test_development_allows_placeholder_db_credentials` | Developer onboarding convenience in dev mode | **PASS** |
| `tests/unit/test_config.py` | `test_settings_custom_env_values` | Custom environment configuration loading | **PASS** |
| `tests/unit/test_config.py` | `test_settings_derived_properties` | Config derived properties (CORS, URLs) | **PASS** |
| `tests/unit/test_config.py` | `test_settings_default_values` | Default configuration attributes | **PASS** |
| `tests/unit/test_config.py` | `test_settings_case_insensitive` | Case-insensitive environment parsing | **PASS** |
| `tests/unit/test_domain_utils.py` | `test_extract_apex_domain_*` (18 tests) | Apex domain parsing, subdomain normalization, TLD checks | **PASS** |
| `tests/unit/test_errors.py` | `test_domain_error_hierarchy` (3 tests) | Base exception classes, HTTP mapping, error payloads | **PASS** |
| `tests/unit/test_health.py` | `test_health_*` (4 tests) | Deep readiness probes (PostgreSQL, Redis, Qdrant) | **PASS** |
| `tests/unit/test_health_live.py` | `test_health_live_endpoint` | Liveness probe `/health/live` returns 200 OK | **PASS** |
| `tests/unit/test_middleware.py` | `test_request_id_middleware_*` (4 tests) | `X-Request-ID` propagation, structured logging context | **PASS** |
| `tests/unit/test_security.py` | `test_argon2_password_hashing` | Argon2id password hashing and verification | **PASS** |
| `tests/unit/test_security.py` | `test_jwt_access_token_creation_and_decoding` | Cryptographic JWT token encoding/decoding | **PASS** |
| `tests/unit/test_security.py` | `test_jwt_access_token_expiry` | Expired JWT token rejection | **PASS** |
| `tests/unit/test_security.py` | `test_refresh_token_generation_and_hashing` | Secure random refresh token generation | **PASS** |
| `tests/unit/test_url_utils.py` | `test_ssrf_validator_*` (17 tests) | IPv4/IPv6 loopback, link-local, AWS metadata, DNS rebinding | **PASS** |
| `tests/api/test_remediations_approval.py` | `test_remediation_approval_flow` (4 tests) | Proposal approval, reviewer notes, snapshot validation | **PASS** |
| `tests/api/test_scans_and_account_api.py` | `test_create_scan_unverified_domain_forbidden` | HTTP 403 Forbidden on unverified domain crawl attempt | **PASS** |
| `tests/api/test_scans_and_account_api.py` | `test_create_scan_nonexistent_project_not_found` | HTTP 404 Non-disclosure for nonexistent project | **PASS** |
| `tests/api/test_scans_and_account_api.py` | `test_create_scan_cross_tenant_project_not_found` | Multi-tenant tenant boundary isolation (404) | **PASS** |
| `tests/api/test_scans_and_account_api.py` | `test_user_profile_update` | `PATCH /api/v1/auth/me` display name update | **PASS** |
| `tests/api/test_scans_and_account_api.py` | `test_change_password_flow` | `POST /api/v1/auth/change-password` + token revocation | **PASS** |

---

## 2. Frontend Test Suite (`vitest`)
- **Total Test Files:** 8
- **Total Test Cases:** 24
- **Passed:** 24 (100%)
- **Failed:** 0
- **Execution Duration:** 33.02s
- **Test Runner:** `vitest 5.0.5` with JSDOM environment

### Detailed Test Inventory

| Test File | Test Suite / Case | Area Verified | Result |
| :--- | :--- | :--- | :--- |
| `src/App.test.tsx` | `renders public landing page at root route for unauthenticated visitors` | Root `/` renders public marketing landing page | **PASS** |
| `src/App.test.tsx` | `redirects unauthenticated users trying to access protected routes to login page` | Unauthenticated protected route access redirects to `/login` | **PASS** |
| `src/App.test.tsx` | `renders protected app shell when authenticated` | Protected app shell, navigation items, and overview render | **PASS** |
| `src/test/auth.test.tsx` | `sets user and updates isAuthenticated` | Zustand auth store user assignment & state mutation | **PASS** |
| `src/test/auth.test.tsx` | `clears error state when clearError is called` | Auth error state clearing | **PASS** |
| `src/test/auth.test.tsx` | `renders accessible loading indicator when checking session` | Loading indicator accessibility attributes (`role="status"`) | **PASS** |
| `src/test/auth.test.tsx` | `renders children when authenticated` | ProtectedRoute renders children when authenticated | **PASS** |
| `src/test/auth.test.tsx` | `validates required fields on login submit` | Login form client-side schema validation | **PASS** |
| `src/test/auth.test.tsx` | `validates matching passwords on register submit` | Registration form password matching validation | **PASS** |
| `src/test/projects.test.tsx` | `renders projects list with verification badges` | Project domain status badges and metadata table | **PASS** |
| `src/test/projects.test.tsx` | `validates form inputs in CreateProjectModal` | Project creation modal domain and name validation | **PASS** |
| `src/test/projects.test.tsx` | `copies DNS verification token to clipboard` | DNS TXT verification token copy action | **PASS** |
| `src/test/scans.test.tsx` | `renders scan history table with metrics and status` | Audit scan execution history and metrics table | **PASS** |
| `src/test/scans.test.tsx` | `disables scan launch when project domain is not verified` | Domain verification gate on scan launch | **PASS** |
| `src/test/scans.test.tsx` | `launches scan and displays progress` | Scan launch trigger and real-time status display | **PASS** |
| `src/test/findings.test.tsx` | `renders findings table and filters by search query` | Findings search filtering and impact badges | **PASS** |
| `src/test/findings.test.tsx` | `opens FindingDetailDrawer and shows WCAG tags and selector` | Findings detail drawer with code selectors and WCAG tags | **PASS** |
| `src/test/remediations.test.tsx` | `renders pending remediation proposal and safe patch diff` | Remediation proposal table and diff inspection | **PASS** |
| `src/test/remediations.test.tsx` | `opens approval modal, submits reviewer notes, and approves patch` | Human reviewer approval modal and note submission | **PASS** |
| `src/test/remediations.test.tsx` | `triggers isolated snapshot validation on approved remediation` | Sandbox snapshot validation trigger | **PASS** |
| `src/test/reports.test.tsx` | `calculates compliance health score and renders WCAG principle breakdowns` | Health score calculation, POUR breakdowns, print trigger | **PASS** |
| `src/test/layout.test.tsx` | `provides an accessible skip to content link` | Accessibility skip-link targeting `#main-content` | **PASS** |
| `src/test/layout.test.tsx` | `toggles mobile drawer navigation menu` | Responsive mobile drawer toggle (`aria-expanded`) | **PASS** |
| `src/test/layout.test.tsx` | `calls onLogout callback when signing out` | User sign-out action and session cleanup callback | **PASS** |

---

## 3. Build & Static Analysis Verification

| Check | Tool | Parameters | Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Backend Linting | `ruff` | `ruff check` | **PASS** | 0 lint errors |
| Backend Formatting | `ruff` | `ruff format --check` | **PASS** | 127 files formatted |
| Frontend TypeScript | `tsc` | `tsc -b` | **PASS** | 0 compilation errors |
| Frontend Bundle Build | `vite` | `vite build` | **PASS** | 0 chunk warnings; all chunks < 500 kB |
