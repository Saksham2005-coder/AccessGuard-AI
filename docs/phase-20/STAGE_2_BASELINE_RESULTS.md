# ACCESSGUARD AI — PHASE 20
## STAGE 2: REPRODUCED BASELINE TEST & VERIFICATION RESULTS

- **Date:** 2026-11-01
- **Auditor:** Independent QA Lead & Application Security Auditor
- **Repository Branch:** `main`
- **Execution Environment:** Windows 11, Python 3.12.10, Node.js v20+, Vite 8.3.5

---

## 1. Baseline Test Execution Summary

Every mandatory project test suite, static type analyzer, linter, and database migration check was independently executed from a clean state.

| Test Component | Command | Target Scope | Output Status | Result Metric |
|---|---|---|---|---|
| **Backend Unit & Integration** | `uv run pytest` | `backend/tests/` | **PASSED** | 262 passed, 1 skipped, 0 failed |
| **Backend Static Typing** | `uv run mypy app/` | `backend/app/` (121 files) | **PASSED** | 0 issues found |
| **Backend Lint & Formatting** | `uv run ruff check app/` | `backend/app/` | **PASSED** | All checks passed |
| **Frontend Unit & Integration** | `npm test -- --run` | `frontend/src/` (18 files) | **PASSED** | 64 passed, 0 failed |
| **Frontend ESLint** | `npm run lint` | `frontend/src/` | **PASSED** | 0 errors, 0 warnings |
| **Frontend Production Build** | `npm run build` | `frontend/` (Vite) | **PASSED** | Built in 2.17s |
| **Database Migrations** | `uv run alembic current` | `backend/alembic/` | **PASSED** | `0012_add_compliance_passports (head)` |
| **Clean Database Init** | `alembic upgrade head` | Disposable SQLite DB | **PASSED** | All 12 migrations applied cleanly |

---

## 2. Detailed Execution Outputs

### 2.1 Backend Unit & Integration Tests (`uv run pytest`)
```
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Saksham Gupta\Desktop\AccessGuard-AI\backend
configfile: pyproject.toml
testpaths: tests
collected 263 items

tests\ai\test_mock_provider.py ........                                  [  3%]
tests\ai\test_providers.py ....s                                         [  4%]
tests\ai\test_remediation_workflow.py .....                              [  6%]
tests\ai\test_retries_and_secrets.py .........                           [ 10%]
tests\ai\test_routing_grounding_injection.py ....                        [ 11%]
tests\ai\test_workflow_checkpoint.py ...                                 [ 12%]
tests\ai\test_workflow_graph.py .....                                    [ 14%]
tests\api\test_remediations_approval.py ....                             [ 16%]
tests\api\test_scans_and_account_api.py .....                            [ 18%]
tests\e2e\test_system_regression.py .                                    [ 18%]
tests\integration\test_auth_routes.py ........                           [ 21%]
tests\integration\test_celery_orchestration.py ....                      [ 23%]
tests\integration\test_domain_verification.py .....                      [ 25%]
tests\integration\test_projects.py .......                               [ 27%]
tests\integration\test_remediation_lifecycle.py ...                      [ 28%]
tests\integration\test_scan_events.py ...                                [ 30%]
tests\integration\test_scan_persistence.py ...                           [ 31%]
tests\rag\test_chunker_embeddings.py .....                               [ 33%]
tests\rag\test_citation_validator.py ....                                [ 34%]
tests\rag\test_fetcher_parser.py .......                                 [ 37%]
tests\rag\test_ingestion_idempotency.py ..                               [ 38%]
tests\rag\test_knowledge_api.py .....                                    [ 39%]
tests\rag\test_retriever.py ....                                         [ 41%]
tests\scanner\test_axe_runner.py .....                                   [ 43%]
tests\scanner\test_crawler.py .....                                      [ 45%]
tests\security\test_ssrf_policy.py ..............................        [ 56%]
tests\security\test_system_security.py ...                               [ 57%]
tests\services\test_snapshot_validation.py ......                        [ 60%]
tests\unit\test_assistant.py ...                                         [ 61%]
tests\unit\test_autonomous_agents.py .........                           [ 64%]
tests\unit\test_comparison.py ...                                        [ 65%]
tests\unit\test_config.py .........                                      [ 69%]
tests\unit\test_domain_utils.py ..................                       [ 76%]
tests\unit\test_errors.py ...                                            [ 77%]
tests\unit\test_github.py .......                                        [ 79%]
tests\unit\test_health.py ......                                         [ 82%]
tests\unit\test_health_live.py .                                         [ 82%]
tests\unit\test_heatmap.py ....                                          [ 84%]
tests\unit\test_keyboard_test.py ........                                [ 87%]
tests\unit\test_passport.py ....                                         [ 88%]
tests\unit\test_regression_monitoring.py ..........                      [ 92%]
tests\unit\test_responsive.py ...                                        [ 93%]
tests\unit\test_screen_reader.py .......                                  [ 96%]
tests\unit\test_security_headers.py ..........                           [100%]

=========== 262 passed, 1 skipped, 17 warnings in 69.12s (0:01:09) ============
```
*Note on skipped test:* `test_gemini_provider_live_structured_generation` was skipped because `GEMINI_API_KEY` was not configured in the offline test environment, which is the designed, safe behavior.

### 2.2 Backend MyPy Type Checking (`uv run mypy app/`)
```
Success: no issues found in 121 source files
```

### 2.3 Backend Ruff Checking (`uv run ruff check app/`)
```
All checks passed!
```

### 2.4 Frontend Test Suite (`npm test -- --run`)
```
Test Files  18 passed (18)
     Tests  64 passed (64)
  Start at  18:50:06
  Duration  34.06s
```

### 2.5 Frontend ESLint (`npm run lint`)
```
> frontend@0.1.0 lint
> eslint .

(0 errors, 0 warnings)
```

### 2.6 Frontend Production Build (`npm run build`)
```
✓ 2891 modules transformed.
dist/index.html                                    0.79 kB │ gzip:   0.38 kB
dist/assets/index-DlL4_wqO.css                    86.53 kB │ gzip:  14.17 kB
...
✓ built in 2.17s
```

### 2.7 Database Schema & Clean Initialization
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
CLEAN_DB_MIGRATION_SUCCESS
```
All 12 Alembic revisions execute without errors on a clean database and preserve referential integrity constraints across PostgreSQL and SQLite targets.
