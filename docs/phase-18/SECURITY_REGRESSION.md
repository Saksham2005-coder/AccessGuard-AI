# AccessGuard AI — Phase 18 Security Regression Report

This document records the verification of core security invariants, cryptographic parameters, authorization boundaries, and vulnerability mitigations.

---

## 1. Security Invariants Verification Matrix

| Security Domain | Invariant | Verification Mechanism | Status |
| :--- | :--- | :--- | :--- |
| **Password Hashing** | Strict Argon2id parameters (`time_cost=3`, `memory_cost=65536` [64 MiB], `parallelism=4`) enforced | `backend/tests/unit/test_security.py::test_argon2_password_hashing` | **PASS** |
| **Session Cryptography** | JWT tokens signed via HMAC-SHA256 with strong secrets | `backend/tests/unit/test_security.py::test_jwt_access_token_creation_and_decoding` | **PASS** |
| **Session Revocation** | Password changes invalidate all active refresh tokens | `backend/tests/api/test_scans_and_account_api.py::test_change_password_flow` | **PASS** |
| **Multi-Tenancy** | Projects, scans, findings, and remediations isolated strictly by `owner_id` | `backend/tests/api/test_scans_and_account_api.py::test_create_scan_cross_tenant_project_not_found` | **PASS** |
| **Domain Ownership** | Scans blocked with HTTP 403 unless domain DNS TXT challenge is verified | `backend/tests/api/test_scans_and_account_api.py::test_create_scan_unverified_domain_forbidden` | **PASS** |
| **SSRF Mitigation** | Crawler blocks IPv4/IPv6 loopback, private ranges, link-local, AWS metadata (169.254.169.254) | `backend/tests/unit/test_url_utils.py` (17 tests) | **PASS** |
| **Production Fail-Closed** | Production refuses startup on default secrets, placeholder DB URLs, or insecure cookies | `backend/tests/unit/test_config.py` (4 tests) | **PASS** |
| **Sandbox Egress** | Remediation patch DOM validation runs in isolated browser context with network egress aborted | `backend/app/services/sandbox_service.py` | **PASS** |
| **Formula Injection** | CSV reports escape and neutralize spreadsheet formula characters (`=`, `+`, `-`, `@`) | `frontend/src/pages/ReportsPage.tsx` | **PASS** |

---

## 2. In-Depth Verification Details

### A. Domain Verification Gate (BUG-04)
- **Constraint:** Crawlers must never target arbitrary web servers without cryptographically proven domain ownership.
- **Verification:** 
  - Verified that creating a scan against an unverified project immediately aborts and returns:
    ```json
    {
      "code": "AUTHORIZATION_FAILED",
      "message": "Domain 'example.com' is not verified. Please complete DNS TXT verification before running a scan.",
      "status_code": 403
    }
    ```
  - Cross-tenant scan attempts return HTTP 404 to avoid leaking project existence.

### B. Session Invalidation on Password Change (BUG-06)
- **Constraint:** When a user changes their password, all active sessions and stored refresh tokens must be revoked to protect against session hijacking.
- **Verification:**
  - `auth_service.change_user_password()` marks all active `RefreshSession` records for the user as `is_revoked = True`.
  - Integration test `test_change_password_flow` verifies:
    1. User changes password using valid current password and matching confirmation.
    2. Old password fails authentication.
    3. New password authenticates successfully and generates fresh session tokens.
    4. Previous refresh tokens are rejected upon subsequent refresh attempts.

### C. SSRF & Crawler Loopback Mitigation
- **Constraint:** Automated accessibility crawlers must never be weaponized to probe internal infrastructure, loopback interfaces (`127.0.0.1`, `::1`), or cloud metadata endpoints (`169.254.169.254`).
- **Verification:**
  - `app.core.url_utils.is_safe_url()` resolves hostnames and checks all resolved IP addresses against private and reserved CIDR blocks before connection initiation.
  - 17 dedicated test cases in `backend/tests/unit/test_url_utils.py` verify that IPv4/IPv6 loopback, Docker bridge networks, CGNAT, link-local, and AWS/GCP metadata addresses are rejected.

### D. CSV Formula Injection Defense
- **Constraint:** Exported CSV reports containing untrusted accessibility findings (e.g., malicious element text or attributes like `=cmd|' /C calc'!A0`) could execute code in spreadsheet software.
- **Verification:**
  - In `frontend/src/pages/ReportsPage.tsx`, `sanitizeCsvField()` checks for leading `=, +, -, @, \t, \r` characters and prepends `'` (single quote) to treat them as plain literal strings in Excel, LibreOffice, and Google Sheets.
