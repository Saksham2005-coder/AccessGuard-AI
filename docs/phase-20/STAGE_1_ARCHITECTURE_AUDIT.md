# ACCESSGUARD AI — PHASE 20
## STAGE 1: INDEPENDENT REPOSITORY & ARCHITECTURE AUDIT

- **Auditor:** Principal Software Architect, Application Security Lead, Staff DevOps Engineer
- **Date:** 2026-11-01
- **Target Branch:** `main`
- **Audit Basis:** Actual code inspection across backend, frontend, database, scanner, and infrastructure components.

---

## 1. Repository Structure & Artifact Layout

The repository is organized into a clean monorepo architecture:
- `/backend`: FastAPI asynchronous application, SQLAlchemy 2.0 async models, Alembic migrations, Celery task worker, Playwright crawler & axe-core 4.14.0 runner, LangGraph workflows, Qdrant/vector RAG integration.
- `/frontend`: React 19 SPA powered by Vite, Tailwind CSS with Graphite & Electric Blue design identity, TanStack Query, Lucide icons, and Vitest test suite.
- `/docs`: Phase specifications, architecture diagrams, threat models, and operational runbooks.
- `/docker-compose.yml`: Multi-container composition supporting PostgreSQL, Redis, Qdrant, backend, Celery worker, and frontend.

---

## 2. Architecture & Data Flow Inspection

### 2.1 Authentication & Authorization
- **Implementation:** Stateless JWT access tokens + HTTP-only refresh cookies in `app/api/v1/auth.py` and `app/core/security.py`.
- **Tenant Scoping:** Projects enforce strict ownership (`Project.owner_id == current_user.id`). Child entities (`Scan`, `Finding`, `Remediation`, `ProjectBaseline`, `CompliancePassport`, `GitHubIntegration`, `AssistantConversation`) enforce ownership checks via SQL joins back to `Project.owner_id`.
- **Audit Observation:** Object-level authorization is rigorously implemented across endpoints; unauthorized access returns `NotFoundError` (`404`), preventing tenant enumeration.

### 2.2 Database Models & Migration Pipeline
- **Models:** 16 active SQLAlchemy models in `app/db/models/`:
  - `User`, `RefreshSession`, `Project`, `ProjectDomainVerification`
  - `Scan`, `ScanPage`, `Finding`, `FindingNode`, `ScanEvent`
  - `Remediation`, `RemediationApproval`, `ValidationResult`
  - `AgentRun`, `ProjectBaseline`, `ScanSchedule`, `InAppNotification`
  - `GitHubIntegration`, `GitHubReviewRecord`, `AssistantConversation`, `AssistantMessage`
  - `ScanViewportRun`, `CompliancePassport`
- **Migrations:** 12 sequential forward-only migrations from `0001_initial_auth` to `0012_add_compliance_passports`. Clean initialization from scratch verified on fresh database schemas.

### 2.3 Scanner & Playwright Sandbox
- **Engine:** Playwright Chromium headless runner orchestrating axe-core 4.14.0 inside `app/scanner/`.
- **SSRF Hardening:** Strict URL validation in `app/security/ssrf.py` with DNS resolution pinning, private/loopback/link-local IPv4 & IPv6 blacklists, and redirect-time hop verification.
- **Resource Management:** Browser contexts are opened with strict memory/timeout limits and guaranteed cleanup in `finally` blocks.

### 2.4 AI Provider Abstraction, LangGraph & RAG
- **Providers:** Dynamic provider selection (`gemini`, `openai`, `anthropic`, `mock`) configured in `app/config.py`.
- **Prompt Injection Barriers:** Untrusted external page content wrapped in `<<<EXTERNAL_UNTRUSTED_CONTENT>>>` isolation delimiters.
- **Read-Only Constraints:** Assistant and autonomous agent tool registries strictly enforce read-only interfaces; mutation operations (scans, remediation approvals, site modifications) are barred at the schema level.

---

## 3. Phase 19 Feature Inspection & Findings

| # | Feature | Status | Verification Observations |
|---|---|---|---|
| 1 | Visual Heatmap | Functional | Extracts exact `(x, y, width, height)` bounding boxes for findings; Canvas/SVG overlay with accessible table fallback. |
| 2 | Remediation Comparison | Functional | Isolates patches in temporary in-memory DOM representations; verifies axe delta without altering target production servers. |
| 3 | Autonomous Agents | Functional | Four specialized LangGraph agents grounded in findings and WCAG chunk retrieval; provides clear caveat notices. |
| 4 | Screen Reader Simulator | Functional | Traverses semantic accessibility tree (landmarks, headings, controls); redacts sensitive form inputs and passwords. |
| 5 | Keyboard Simulator | Functional | Deterministic Tab/Shift+Tab simulation; calculates computed focus styles; detects focus traps via cycle limits. |
| 6 | Regression Monitoring | Functional | Pinned baseline scan comparisons; classifies New, Resolved, and Persistent findings; scheduled scans supported. |
| 7 | GitHub Integration | Functional | Webhook endpoint verifies HMAC-SHA256 signatures; preview URLs validated against verified domains; sticky PR comments created. |
| 8 | Conversational Assistant | Functional | Read-only RAG assistant; validates citations against verified WCAG criteria; tenant-scoped chat history. |
| 9 | Responsive Matrix | Functional | Desktop (1440x900), Tablet (768x1024), Mobile (390x844) viewport testing; distinguishes shared vs specific violations. |
| 10 | Compliance Passport | Functional | Immutable versioned audit packages with deterministic SHA-256 integrity hash; human auditor review checklist included. |

---

## 4. Discovered Risks, Edge Cases & Acceptance Gaps

1. **Background Tasks & Port Clashes:** Vite (5173) and FastAPI (8000) must be managed cleanly during live end-to-end browser audits to prevent port lockups on Windows.
2. **Mock AI In Test Environments:** Production environments require real API keys, but automated test harnesses must deterministically use mock providers without degrading test integrity.
3. **Canvas JSDOM Limitations:** Vitest frontend tests in JSDOM environment emit expected `HTMLCanvasElement.getContext` warnings; verified that components gracefully handle headless execution.
4. **Legal Compliance Disclaimers:** All automated reporting artifacts and UI modals must strictly maintain that automated checks do not constitute legal WCAG compliance certification.

---

## 5. Next Steps for Stage 2 & Stage 3

- Produce formal baseline reproduction record (`STAGE_2_BASELINE_RESULTS.md`).
- Execute real browser end-to-end acceptance tests across all 12 key user journeys.
- Conduct focused security penetration testing (SSRF, auth bypass, tenant isolation, prompt injection).
