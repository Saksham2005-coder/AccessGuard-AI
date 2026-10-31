# AccessGuard AI — Complete End-to-End Development Blueprint

> **Document purpose:** This is the single source of truth for building AccessGuard AI with Antigravity. Follow it phase by phase. Do not improvise the architecture, invent completed work, silently omit acceptance criteria, or replace real functionality with mock data.
>
> **Project type:** Portfolio-grade, intermediate-level Agentic AI + Advanced RAG application.
>
> **Primary outcome:** A deployable web application that scans user-authorized websites with Playwright and axe-core, explains findings using grounded WCAG 2.2 retrieval, proposes human-reviewable remediations using LangGraph, and validates proposed changes in a safe isolated snapshot/test environment.
>
> **Important limitation:** Automated scans do not certify that a website conforms to WCAG. The product must say “automated accessibility findings” and “automated checks passed/failed”; it must never claim complete WCAG compliance based only on axe-core or an AI-generated score.

---

## Table of contents

1. [How Antigravity must use this document](#1-how-antigravity-must-use-this-document)
2. [Product definition and boundaries](#2-product-definition-and-boundaries)
3. [Non-negotiable engineering rules](#3-non-negotiable-engineering-rules)
4. [Locked technology choices](#4-locked-technology-choices)
5. [User journeys and acceptance outcomes](#5-user-journeys-and-acceptance-outcomes)
6. [System architecture](#6-system-architecture)
7. [Repository and folder structure](#7-repository-and-folder-structure)
8. [Local development prerequisites](#8-local-development-prerequisites)
9. [Initial repository setup and commands](#9-initial-repository-setup-and-commands)
10. [Backend implementation specification](#10-backend-implementation-specification)
11. [Database design and migrations](#11-database-design-and-migrations)
12. [Website crawler and accessibility scanner](#12-website-crawler-and-accessibility-scanner)
13. [Advanced RAG and WCAG knowledge base](#13-advanced-rag-and-wcag-knowledge-base)
14. [LLM integration and API-key timing](#14-llm-integration-and-api-key-timing)
15. [LangGraph multi-agent workflow](#15-langgraph-multi-agent-workflow)
16. [Remediation proposal and validation design](#16-remediation-proposal-and-validation-design)
17. [Frontend product and UI specification](#17-frontend-product-and-ui-specification)
18. [REST API contract](#18-rest-api-contract)
19. [Background jobs and real-time progress](#19-background-jobs-and-real-time-progress)
20. [Security, privacy and abuse prevention](#20-security-privacy-and-abuse-prevention)
21. [Testing strategy and test data](#21-testing-strategy-and-test-data)
22. [RAG and agent evaluation](#22-rag-and-agent-evaluation)
23. [Docker and local deployment](#23-docker-and-local-deployment)
24. [GitHub repository management](#24-github-repository-management)
25. [GitHub Actions CI/CD](#25-github-actions-cicd)
26. [Logging, monitoring and operational behavior](#26-logging-monitoring-and-operational-behavior)
27. [Reports, export and product documentation](#27-reports-export-and-product-documentation)
28. [End-to-end development phases](#28-end-to-end-development-phases)
29. [Required 51-commit plan](#29-required-51-commit-plan)
30. [Definition of done and release checklist](#30-definition-of-done-and-release-checklist)
31. [Known risks and explicit non-goals](#31-known-risks-and-explicit-non-goals)
32. [Future enhancements after the first complete release](#32-future-enhancements-after-the-first-complete-release)
33. [Master Antigravity build prompt](#33-master-antigravity-build-prompt)
34. [Official technical references](#34-official-technical-references)

---

# 1. How Antigravity must use this document

## 1.1 Treat this as the source of truth

Antigravity must read this entire file before changing the repository. All major product, stack, architecture, security, UI, API, testing, Git and deployment decisions are defined here. Do not ask the user to select a framework, database, color palette, folder structure or agent design already specified here.

If an implementation detail is genuinely unspecified, choose the smallest conventional option consistent with this document, document the decision in `docs/decisions/`, and do not add unnecessary infrastructure.

If a requirement cannot be implemented as written because a package API changed, consult the package's official documentation, make the smallest compatible adjustment, record the change, and test it. Do not invent function names, package capabilities, environment variables or CLI flags.

## 1.2 Work sequentially

Build one phase at a time. At the beginning of a phase:

1. Read the phase requirements and dependencies.
2. Inspect the actual current repository state.
3. Identify missing files and existing behavior.
4. Make a short implementation checklist.
5. Implement only that phase and required prerequisites.
6. Run the specified tests and quality checks.
7. Fix every failure caused by the phase.
8. Update documentation and the phase status.
9. Create exactly 2–3 meaningful commits for the phase after its acceptance criteria pass.
10. Report the changed files, commands executed, real test results, commit hashes and any remaining limitations.

Do not start the next phase while the current phase has failing required tests. A pre-existing unrelated failure must be documented with evidence and must not be represented as a passing test.

## 1.3 No fabricated completion

Never claim that a command ran unless it actually ran. Never invent test totals, coverage percentages, benchmark scores, successful deployments or API responses. Do not replace a failing test with a weaker test just to get a green pipeline. Do not mark a TODO as complete.

If a test requires an API key that is not available, run the documented mocked-provider test and report that the live-provider test is blocked until the user supplies a key. Do not create fake API keys or use a developer's personal credentials.

## 1.4 No premature API-key request

Do not ask the user for Gemini or Groq API keys during repository setup, scanner implementation, database setup, deterministic tests or initial RAG ingestion. These components must work without an LLM key.

The first provider key is required only when starting **Phase 10: live LLM provider integration and model-backed agent reasoning**. At that exact point, stop before making live provider calls and tell the user how to put one key in the local `.env` file. Gemini is the default provider; Groq is an alternative. Only one key is required for the normal workflow. Do not ask the user to paste the secret into chat.

## 1.5 UI decisions are already made

Use the visual system in Section 17. Build the full initial UI in that style. The user will review the website after the end-to-end build and may request visual refinements later. Do not pause implementation to ask about visual preferences.

## 1.6 Git rules

- Keep the primary branch named `main`.
- This is a single-developer portfolio project; work directly on `main` unless a specific task needs an isolated branch.
- Aim for approximately 50 commits; the exact plan below contains 51 commits across 17 phases.
- Every phase must end with 2–3 commits. This document specifies three commits per phase.
- **Never use these words in commit messages:** `feat`, `fix`, `chore` (including conventional-commit prefixes containing those words).
- Use the message templates in Section 29. Do not squash the planned commits at the end.
- Do not force-push. Do not amend a commit already pushed to GitHub without user approval.
- Do not commit `.env`, API keys, tokens, passwords, user scan screenshots, local database files or generated private reports.

## 1.7 Time and scope discipline

The user has limited development time. Complete the specified MVP and production-readiness work first. Do not add Kubernetes, microservices, billing, paid crawler APIs, complex graph databases, autonomous live website editing or unrelated features. Prefer a modular monolith, a small fixed set of reliable agents, and explicit acceptance criteria.

---

# 2. Product definition and boundaries

## 2.1 Product summary

**AccessGuard AI** is a web application for developers and teams who want to understand automated accessibility findings on websites they are authorized to test.

A user creates a project, verifies a website domain, starts an audit, reviews actual axe-core findings, opens the supporting WCAG references, requests an AI explanation and suggested remediation, approves or rejects a proposal, and runs a controlled validation against a captured page snapshot or an isolated supplied fixture.

## 2.2 The problem

Web teams often receive accessibility findings but lack a clear workflow for connecting a finding to a standard, understanding the affected element, deciding on an appropriate code change, and checking whether that change introduces a regression.

AccessGuard connects these stages:

1. **Observe:** crawl and render a page with Playwright.
2. **Detect:** execute axe-core against the rendered document.
3. **Explain:** retrieve relevant official W3C guidance using RAG.
4. **Recommend:** use an LLM through LangGraph to propose a context-aware correction.
5. **Review:** require a human decision before treating a patch as approved.
6. **Validate:** run a controlled test on an isolated snapshot or test fixture.
7. **Report:** preserve the finding, evidence, citations, decision and validation history.

## 2.3 Supported first-release scope

The first release must support:

- Account registration, login, logout and current-user endpoint.
- Project creation and management.
- Website domain verification before scanning a project domain.
- Single-URL scan and bounded same-origin crawl.
- User-configurable page limit and crawl depth with safe hard caps.
- Playwright-based rendered-page collection.
- axe-core automated WCAG-tagged accessibility analysis.
- Finding normalization, grouping and duplicate suppression.
- Screenshots and small DOM evidence snippets where safe.
- Scan progress and error status.
- Search/filter/sort findings.
- WCAG 2.2 knowledge ingestion and retrieval.
- Dense retrieval plus lexical retrieval and rank fusion.
- Optional local cross-encoder reranking.
- Grounded explanation with source links and criterion metadata.
- LangGraph orchestration for explanation and remediation proposals.
- Structured remediation suggestions with before/after snippets or bounded patch operations.
- Human approval/rejection workflow.
- Safe validation on an isolated DOM snapshot or dedicated local test fixture.
- Scan history, report view and PDF/JSON export.
- Docker Compose local deployment.
- GitHub Actions tests and container build.
- Setup, security, architecture and evaluation documentation.

## 2.4 Explicit limits of the automated audit

The product must be honest about what it can and cannot establish.

- axe-core checks many important rules but does not test every WCAG success criterion or every real user interaction.
- Automated success is not the same as WCAG conformance.
- Some issues require keyboard-only inspection, screen-reader testing, cognitive review, human judgment or knowledge of the intended content.
- An image's correct alternative text depends on its purpose and context. A decorative image may need `alt=""`; an informative image may need a meaningful text alternative.
- A contrast issue may depend on rendered states, opacity, gradients, overlays, background images or browser rendering.
- An HTML snapshot cannot fully reproduce the behavior of a production React/Vue/Angular application.
- A suggested snippet is not a guaranteed production patch.

Use these labels in the UI:

- `Automated finding`
- `Automated check passed`
- `Needs manual review`
- `AI suggestion — not applied`
- `Snapshot validation passed`
- `Snapshot validation failed`

Never display `WCAG certified`, `100% compliant`, `fully accessible`, or equivalent claims unless an independent and valid full conformance process has been performed outside this product.

## 2.5 User roles

For the first release, support one user role: `user`. All project, scan, finding, remediation, report and knowledge-admin resources must still be authorized server-side. Reserve `admin` for future knowledge-index administration; do not build a complex role hierarchy now.

---

# 3. Non-negotiable engineering rules

1. **Deterministic before generative:** axe-core is responsible for detecting automated accessibility violations. The LLM must not invent findings.
2. **Evidence before explanation:** every guideline statement generated for a finding must be grounded in retrieved source material and include source metadata.
3. **Structured outputs:** validate all model responses with Pydantic before persisting or showing them.
4. **Human approval:** no generated code is applied to a production website automatically.
5. **Least privilege:** the browser/scanner must not have access to API keys, database credentials or unnecessary internal services.
6. **Tenant isolation:** every user-owned database read and write must be scoped by the authenticated user and project ownership.
7. **No secrets in frontend:** provider API keys exist only on the backend and only in environment variables or a secrets manager.
8. **No hidden mock product data:** demo fixtures are permitted only in explicit demo/test mode. The normal UI must show real database-backed records and honest empty states.
9. **No unbounded crawling:** enforce page, depth, time, response-size and same-origin limits.
10. **No arbitrary code execution:** never use `eval`, `exec`, shell tools or unrestricted code execution on model output or website content.
11. **Traceability:** preserve scan configuration, axe version, browser version, WCAG source version, prompt/model metadata and validation outcomes.
12. **Reproducible dependencies:** lock Python and Node dependencies. Pin Docker image versions to tested versions; avoid `latest` in release configuration.
13. **Accessible product UI:** AccessGuard itself must have semantic markup, keyboard operability, clear focus indicators and readable contrast.
14. **Testable design:** business logic must be separable from FastAPI routes, browser automation and external LLM calls.
15. **No claims without measurements:** benchmark numbers must come from the committed evaluation scripts and datasets.

---

# 4. Locked technology choices

Use this stack unless an official package compatibility issue forces a documented substitution.

| Layer | Selection | Notes |
|---|---|---|
| Runtime | Python 3.12 | Backend and workers |
| Backend API | FastAPI | Versioned REST API |
| Validation | Pydantic 2 | Request, response and model schemas |
| ORM | SQLAlchemy 2.x | Async engine/session preferred for API |
| Migrations | Alembic | Every schema change through migrations |
| Database | PostgreSQL 16 | Source of truth for application data |
| Background jobs | Celery | Durable scan/analysis tasks |
| Broker/cache | Redis 7 | Celery broker and short-lived cache/events |
| Agent orchestration | LangGraph | Stateful graph and approval checkpoints |
| LLM providers | Gemini primary; Groq alternative | Server-side only; optional until Phase 10 |
| Browser automation | Playwright Python | Browser-based rendering and crawling |
| Accessibility engine | axe-core | Locally installed and version-pinned JavaScript bundle |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model; no API key |
| Vector search | Qdrant | Dense vector index |
| Lexical search | PostgreSQL full-text search or in-process BM25 | Exact WCAG terms/identifiers; fuse with dense results |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Optional after baseline retrieval; local model |
| Frontend | React + TypeScript + Vite | SPA |
| UI styling | Tailwind CSS 4 | Default light appearance |
| UI components | Accessible custom primitives + Radix where needed | Do not over-customize a component library |
| Icons | Lucide React | Consistent icon set |
| Charts | Recharts | Dashboard visualizations |
| API state | TanStack Query | Query cache and mutations |
| Routing | React Router | Client-side routes |
| Form validation | React Hook Form + Zod | Typed forms |
| Client state | Zustand only where needed | Avoid duplicate server state |
| Tests | Pytest, pytest-asyncio, Vitest, React Testing Library, Playwright E2E | Multiple layers |
| Lint/format | Ruff, ESLint, Prettier, TypeScript compiler | CI gates |
| Containers | Docker + Compose | Local and deployment packaging |
| CI | GitHub Actions | Tests, builds, security checks |

## 4.1 Version policy

Do not guess version numbers for packages that may have changed. At project setup:

- Select current stable versions compatible with Python 3.12 and Node 22 LTS.
- Use package lockfiles (`uv.lock` or an equivalent committed Python lock; `package-lock.json` for Node).
- Pin Playwright Python and browser image versions together.
- Pin axe-core via the `tools/axe/package-lock.json`.
- Pin PostgreSQL and Redis container tags to tested major/minor versions.
- Avoid `latest` tags in deployment Compose.
- Record all key dependency versions in `docs/TECH_STACK.md`.
- Do not upgrade a major dependency mid-phase without running the full regression suite.

## 4.2 Why a modular monolith

Do not create many independently deployed services. The backend should be one modular application with clear boundaries: API, domain services, persistence, scanner integration, retrieval, agents, worker tasks and reporting. PostgreSQL, Redis and Qdrant are supporting infrastructure containers, not separate business microservices.

The scanner execution must be separated from API/provider secrets. In local Compose, use a dedicated scanner/worker image and a restrictive network/egress policy. Before exposing arbitrary URL scanning publicly, add a production egress control (outbound proxy/firewall or isolated scan runner) that prevents access to private and internal address ranges. Application URL validation alone is not sufficient protection against DNS rebinding or browser network abuse.

---

# 5. User journeys and acceptance outcomes

## 5.1 First-time user

1. User opens AccessGuard.
2. User sees a clear product landing/login screen.
3. User creates an account.
4. User logs in.
5. User creates a project with a name and base domain.
6. System generates a DNS TXT verification token and explains how to add it.
7. User clicks “Verify domain”; backend checks the expected TXT record.
8. Once verified, the user can create a scan.
9. System validates the URL against the verified project domain and security policy.
10. Scan begins and the UI shows actual progress events.
11. User sees pages scanned and errors per page.
12. User opens findings and reviews actual axe-core results.
13. User opens a finding to view affected selector, short HTML evidence, axe help URL, impact and WCAG tags.
14. User asks for an explanation/remediation.
15. System retrieves relevant WCAG guidance and generates a structured recommendation.
16. User reviews citations, confidence caveats and suggested change.
17. User approves or rejects the proposal.
18. If approved, system validates against an isolated snapshot/fixture and records the result.
19. User exports the scan report.

## 5.2 Empty-state behavior

If a user has no projects, show an invitation to create one. If a project has no scans, show a clear “Start first scan” action. If a scan has no violations, show “No axe-core violations were detected in the pages and rules tested” with a limitation note. Do not populate the database with artificial analytics.

## 5.3 Scan status behavior

Allowed statuses:

- `queued`
- `validating_target`
- `crawling`
- `auditing`
- `normalizing_findings`
- `investigating`
- `awaiting_review`
- `validating_proposals`
- `completed`
- `completed_with_errors`
- `failed`
- `cancel_requested`
- `cancelled`

The scan status must be updated transactionally. A scan can complete with page-level errors if other eligible pages were audited; display those errors rather than hiding them.

---

# 6. System architecture

## 6.1 High-level component flow

```mermaid
flowchart TB
    U[User Browser] --> FE[React + TypeScript]
    FE --> API[FastAPI]
    API --> PG[(PostgreSQL)]
    API --> R[(Redis)]
    API --> Q[(Qdrant)]
    API --> C[Celery Queue]
    C --> W[Background Worker]
    W --> SC[Playwright Scanner]
    SC --> AX[axe-core]
    W --> RAG[RAG Service]
    RAG --> Q
    RAG --> PG
    W --> LG[LangGraph]
    LG --> LLM[Gemini or Groq API]
    LG --> PG
    W --> REP[Report Service]
    REP --> PG
    FE <-->|SSE progress| API
```

## 6.2 Responsibility boundaries

### Frontend

- Displays user-owned projects/scans/findings/remediations.
- Submits user actions.
- Uses API response types generated or manually synchronized with Pydantic schemas.
- Never holds provider API keys or database credentials.
- Does not calculate security-sensitive permissions.
- Does not claim findings were fixed before validation is persisted.

### FastAPI

- Authenticates and authorizes every request.
- Validates input and output schemas.
- Creates scans and queues background work.
- Exposes scan status and persisted events.
- Provides knowledge and report endpoints.
- Does not execute long browser scans inside request handlers.

### Celery worker

- Executes scan orchestration asynchronously.
- Updates statuses and emits progress events.
- Calls scanner, RAG and agent services.
- Uses idempotency to avoid duplicate work after retries.
- Keeps provider secrets in its environment only when needed.

### Scanner module

- Validates target policy.
- Uses Playwright with bounded navigation and timeouts.
- Injects the locally installed axe-core bundle.
- Returns normalized raw results and evidence.
- Does not call an LLM.

### RAG service

- Loads official source material and local metadata.
- Splits documents semantically by criterion/section.
- Creates local embeddings.
- Retrieves dense and lexical candidates.
- Fuses and optionally reranks candidates.
- Returns source-backed evidence objects.

### LangGraph

- Coordinates structured analysis, RAG and remediation.
- Uses typed state and Pydantic output models.
- Persists graph checkpoints for approvals/resume.
- Cannot bypass authorization, URL security or human approval.

### PostgreSQL

- Source of truth for all user-owned entities and status.
- Stores guideline source metadata and chunk text needed for retrieval.
- Stores references to screenshots/report files, not unlimited binary blobs.

### Qdrant

- Stores vectors and stable chunk IDs/metadata.
- Does not replace PostgreSQL for user ownership or transactional data.

---

# 7. Repository and folder structure

Create this monorepo structure. Do not put the entire backend in `main.py` or the entire frontend in `App.tsx`.

```text
AccessGuard-AI/
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── projects.py
│   │   │       ├── scans.py
│   │   │       ├── findings.py
│   │   │       ├── remediations.py
│   │   │       ├── reports.py
│   │   │       └── knowledge.py
│   │   ├── core/
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   ├── errors.py
│   │   │   └── request_context.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── schemas/
│   │   ├── domain/
│   │   │   ├── enums.py
│   │   │   ├── policies.py
│   │   │   └── exceptions.py
│   │   ├── scanner/
│   │   │   ├── target_policy.py
│   │   │   ├── crawler.py
│   │   │   ├── browser.py
│   │   │   ├── axe_runner.py
│   │   │   ├── normalizer.py
│   │   │   ├── deduplicator.py
│   │   │   └── evidence.py
│   │   ├── rag/
│   │   │   ├── ingestion.py
│   │   │   ├── parser.py
│   │   │   ├── chunker.py
│   │   │   ├── embeddings.py
│   │   │   ├── dense_retriever.py
│   │   │   ├── lexical_retriever.py
│   │   │   ├── fusion.py
│   │   │   ├── reranker.py
│   │   │   ├── service.py
│   │   │   └── citations.py
│   │   ├── ai/
│   │   │   ├── providers/
│   │   │   │   ├── base.py
│   │   │   │   ├── factory.py
│   │   │   │   ├── gemini.py
│   │   │   │   └── groq.py
│   │   │   ├── prompts/
│   │   │   └── schemas/
│   │   ├── agents/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   ├── nodes/
│   │   │   ├── routing.py
│   │   │   ├── checkpointing.py
│   │   │   └── tools/
│   │   ├── remediation/
│   │   │   ├── proposal.py
│   │   │   ├── patch_policy.py
│   │   │   ├── snapshot.py
│   │   │   └── validation.py
│   │   ├── reports/
│   │   │   ├── report_service.py
│   │   │   ├── pdf.py
│   │   │   └── json_export.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── project_service.py
│   │       ├── scan_service.py
│   │       └── event_service.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── scanner/
│   │   ├── rag/
│   │   ├── agents/
│   │   ├── security/
│   │   └── e2e/
│   └── scripts/
│       ├── seed_demo.py
│       ├── ingest_knowledge.py
│       └── evaluate_rag.py
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── app/
│       ├── routes/
│       ├── components/
│       │   ├── ui/
│       │   ├── layout/
│       │   ├── dashboard/
│       │   ├── projects/
│       │   ├── scans/
│       │   ├── findings/
│       │   ├── remediation/
│       │   └── reports/
│       ├── features/
│       ├── hooks/
│       ├── lib/
│       ├── services/
│       ├── store/
│       ├── types/
│       ├── styles/
│       └── test/
├── tools/
│   └── axe/
│       ├── package.json
│       └── package-lock.json
├── knowledge_base/
│   ├── sources.yaml
│   ├── raw/                 # downloaded source files; do not commit large copyrighted copies
│   ├── processed/           # generated locally; ignored unless small evaluation fixtures
│   └── evaluation/
│       ├── retrieval_cases.jsonl
│       └── README.md
├── test_sites/
│   ├── accessible/
│   ├── violations/
│   └── README.md
├── infrastructure/
│   ├── docker/
│   ├── scripts/
│   └── deployment/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── SECURITY.md
│   ├── EVALUATION.md
│   ├── RUNBOOK.md
│   ├── TECH_STACK.md
│   ├── decisions/
│   └── screenshots/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── container.yml
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile               # optional convenience wrapper; commands must also work directly
├── README.md
└── LICENSE
```

Use `.gitkeep` only where an empty tracked directory is necessary. Do not commit model cache files, browser binaries, generated screenshots, private reports, database volumes, `.venv`, `node_modules`, `.env` or downloaded source archives unnecessarily.

---

# 8. Local development prerequisites

The user develops on Windows. Prefer PowerShell commands and ensure Docker Desktop is running.

Required local tools:

- Git.
- GitHub account and an empty repository named `AccessGuard-AI` (or a user-approved equivalent).
- Python 3.12.
- Node.js 22 LTS and npm.
- Docker Desktop with Compose.
- VS Code or Antigravity.
- At least 8 GB RAM recommended; 16 GB is more comfortable for local embedding/reranking models and browsers.
- Internet connection for package/model downloads and public-source ingestion.

Optional but useful:

- `uv` for Python dependency management.
- `make` is not required on Windows; direct commands are documented.
- GitHub CLI is optional; normal `git` remote commands are sufficient.

Before implementation, run and record:

```powershell
git --version
py --version
node --version
npm --version
docker --version
docker compose version
```

Expected: Git available, Python 3.12.x selected explicitly, Node 22.x, Docker Compose v2. If the `py` launcher points elsewhere, use `py -3.12` in the commands below. Do not silently use a different Python version.

---

# 9. Initial repository setup and commands

## 9.1 Create the repository locally

In PowerShell:

```powershell
mkdir AccessGuard-AI
cd AccessGuard-AI
git init -b main
mkdir backend, frontend, tools, knowledge_base, test_sites, infrastructure, docs, .github
mkdir tools\axe, knowledge_base\evaluation, test_sites\accessible, test_sites\violations
mkdir docs\decisions, docs\screenshots
```

Create `.gitignore` before adding generated files:

```gitignore
# Environment and secrets
.env
.env.*
!.env.example
*.pem
*.key

# Python
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
.pyright/

# Models and generated knowledge data
.cache/
.huggingface/
.sentence_transformers/
knowledge_base/raw/**
knowledge_base/processed/**
!knowledge_base/processed/.gitkeep
*.safetensors
*.pt
*.bin

# Node
node_modules/
dist/
.vite/

# Playwright / browser output
playwright-report/
test-results/
artifacts/
scan_artifacts/
*.har

# Local data
*.sqlite3
*.db
postgres_data/
qdrant_data/
redis_data/

# IDE / OS
.vscode/
.idea/
.DS_Store
Thumbs.db
```

Do not add `.env` to Git even if it contains placeholder strings. Commit only `.env.example` with empty values and safe defaults.

## 9.2 Create the frontend

From the repository root:

```powershell
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router-dom @tanstack/react-query zustand axios zod react-hook-form @hookform/resolvers lucide-react recharts sonner clsx tailwind-merge class-variance-authority
npm install -D tailwindcss @tailwindcss/vite eslint prettier prettier-plugin-tailwindcss vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/node
```

Configure Tailwind CSS 4 using its official Vite plugin. In `vite.config.ts`, add the Tailwind Vite plugin alongside the React plugin. In the main stylesheet, import Tailwind with `@import "tailwindcss";`. Do not follow an older Tailwind v3 setup tutorial if the installed version is v4.

Add scripts to `package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 0.0.0.0",
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

Preserve package scripts that Vite or the installed tooling requires. Configure ESLint and Prettier with TypeScript-aware settings. Do not disable lint rules globally to make the build green.

## 9.3 Create the backend with uv

From repository root:

```powershell
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install uv
cd backend
uv init --python 3.12
```

Add application dependencies (use current compatible stable package versions and commit `uv.lock`):

```powershell
uv add "fastapi[standard]" "sqlalchemy[asyncio]" "psycopg[binary]" alembic pydantic-settings email-validator python-multipart pyjwt "pwdlib[argon2]" httpx tenacity celery redis langgraph langchain-core langchain-text-splitters qdrant-client sentence-transformers rank-bm25 playwright reportlab structlog orjson
```

Add provider integrations now as packages if helpful, but do not call them and do not require API keys until Phase 10:

```powershell
uv add langchain-google-genai langchain-groq
```

Development dependencies:

```powershell
uv add --dev pytest pytest-asyncio pytest-cov respx ruff mypy types-redis
```

Create or verify `pyproject.toml` with:

- Python requirement `>=3.12,<3.13` for the first release.
- Ruff lint and format configuration.
- Pytest `asyncio_mode = "auto"` or an explicit consistent async fixture mode.
- Coverage configuration excluding migrations and generated code where appropriate.
- Mypy configuration appropriate to the codebase; do not claim complete typing if `Any` is pervasive.

Lock dependencies:

```powershell
uv lock
uv sync --all-groups
```

Install Playwright browser binaries after the package is installed:

```powershell
uv run playwright install chromium
```

On Linux CI/container images, install the required browser system dependencies using Playwright's documented installation command or the official Playwright container base. Keep the Python Playwright version and browser build synchronized.

## 9.4 Install a local axe-core bundle

From root:

```powershell
cd tools\axe
npm init -y
npm install --save-exact axe-core
```

Commit both `package.json` and `package-lock.json`. The Python scanner must inject the local `node_modules/axe-core/axe.min.js` file with Playwright's `page.add_script_tag(path=...)`. Do not download axe from a public CDN each time a scan runs. Pinning a local bundle makes scans more reproducible and avoids trusting a runtime CDN.

The Docker build must copy the pinned axe bundle into the scanner image. Include a startup assertion that the bundle exists and record its installed axe version in scan metadata.

## 9.5 Initialize Git

```powershell
cd ..\..
git add .gitignore README.md backend frontend tools docs knowledge_base test_sites infrastructure .github
git status --short
```

Review staged files. Confirm no `.env`, `.venv`, `node_modules`, model files, screenshots or database files are staged. Do not commit until the phase acceptance checklist passes.

---

# 10. Backend implementation specification

## 10.1 Application configuration

Use `pydantic-settings` and a typed `Settings` class in `app/config.py`.

Required settings (initially, with no live provider key):

```text
APP_ENV=development
APP_NAME=AccessGuard AI
API_V1_PREFIX=/api/v1
FRONTEND_ORIGINS=http://localhost:5173
DATABASE_URL=postgresql+psycopg://accessguard:change-me@localhost:5432/accessguard
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=wcag_knowledge
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ACCESS_TOKEN_MINUTES=30
JWT_REFRESH_TOKEN_DAYS=7
COOKIE_SECURE=false
LLM_PROVIDER=mock
GEMINI_API_KEY=
GROQ_API_KEY=
GEMINI_MODEL=
GROQ_MODEL=
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_ENABLED=false
MAX_SCAN_PAGES=20
MAX_CRAWL_DEPTH=2
PAGE_TIMEOUT_SECONDS=25
SCAN_TOTAL_TIMEOUT_SECONDS=300
MAX_RESPONSE_BYTES=5000000
MAX_HTML_EVIDENCE_CHARS=12000
```

Rules:

- Fail startup for missing production secrets, not for missing LLM keys while `LLM_PROVIDER=mock`.
- Never log secret values.
- Do not expose the settings object via an endpoint.

Example `.env.example` baseline (values are placeholders, never real secrets):

```env
APP_ENV=development
APP_NAME=AccessGuard AI
API_V1_PREFIX=/api/v1
FRONTEND_ORIGINS=http://localhost:5173
# For API/worker containers, use the Compose service hostname `postgres`.
DATABASE_URL=postgresql+psycopg://accessguard:change-me@postgres:5432/accessguard
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=wcag_knowledge
JWT_SECRET_KEY=replace-with-a-random-local-secret
JWT_ACCESS_TOKEN_MINUTES=30
JWT_REFRESH_TOKEN_DAYS=7
COOKIE_SECURE=false
LLM_PROVIDER=mock
GEMINI_API_KEY=
GROQ_API_KEY=
GEMINI_MODEL=
GROQ_MODEL=
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_ENABLED=false
MAX_SCAN_PAGES=20
MAX_CRAWL_DEPTH=2
PAGE_TIMEOUT_SECONDS=25
SCAN_TOTAL_TIMEOUT_SECONDS=300
MAX_RESPONSE_BYTES=5000000
MAX_HTML_EVIDENCE_CHARS=12000
ARTIFACT_STORAGE_DIR=/app/storage
```

When running FastAPI directly on the Windows host rather than inside Docker, override the database/Redis/Qdrant hostnames with `localhost` in the local `.env`. Inside Compose, use service DNS names (`postgres`, `redis`, `qdrant`). Never print the `.env` file or secret values in a terminal transcript.
- Use different settings for test and production.
- Validate page/depth/timeout settings so they cannot be set to unlimited values by a user.
- The maximum page and depth values are server hard limits; request values can only be lower.

## 10.2 FastAPI application

`app/main.py` should:

- Construct the FastAPI application.
- Configure lifespan startup/shutdown.
- Verify database connectivity and required local resources where appropriate.
- Register the versioned API router.
- Register centralized exception handlers.
- Configure CORS with explicit allowed origins, methods and headers.
- Add request IDs and structured logging middleware.
- Expose `/health/live` and `/health/ready`.
- Avoid doing document ingestion or browser scans in the startup lifespan.

`/health/live` confirms the process is alive. `/health/ready` checks required dependencies (database and Redis at minimum) with bounded timeouts. Do not make public provider calls in health checks.

## 10.3 Layering

Use the following flow:

`HTTP route -> dependency/auth -> service -> repository -> SQLAlchemy model`

A route should not contain a large query, scanner loop, RAG pipeline or agent prompt. Services should orchestrate business rules. Repositories should own reusable persistence operations. Domain logic should be testable without FastAPI.

## 10.4 Authentication

Implement:

- Email and password registration.
- Email normalization (trim and lowercase).
- Password hashing with Argon2 via `pwdlib`.
- Access JWT with a short expiry.
- Refresh-token rotation or a secure refresh session table.
- Logout/revocation behavior for refresh sessions.
- `GET /auth/me`.
- Rate limits on registration/login where practical.

For the SPA, prefer secure, HttpOnly, SameSite cookies for refresh credentials. If using bearer access tokens in memory, do not store long-lived tokens in localStorage. Document the chosen CSRF strategy if cookies are used for state-changing requests. Every token must be verified server-side and every resource query must include user ownership conditions.

Never use a default JWT secret in a production configuration. Provide a PowerShell command to generate a safe local secret, for example:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The developer copies the output into local `.env`; it is not committed.

## 10.5 Error handling

Use a consistent JSON error shape:

```json
{
  "error": {
    "code": "SCAN_TARGET_NOT_ALLOWED",
    "message": "The requested target is not permitted by the project scan policy.",
    "request_id": "...",
    "details": {}
  }
}
```

Do not return Python tracebacks, raw SQL, file-system paths or secrets to clients. Log the internal stack trace with request ID and safe context.

## 10.6 Pagination and filtering

List endpoints must support pagination. Use a stable ordering with a unique tie-breaker. Example query parameters:

- `limit` (default 20, server maximum 100)
- `cursor` or `offset` (choose one strategy consistently; cursor pagination is preferable for growing scan histories)
- `status`
- `severity`
- `criterion`
- `search`

Validate and normalize all filters server-side. Do not load unbounded findings into memory for a large project.

## 10.7 API schema discipline

Define separate Pydantic models for create/update/read operations. Do not expose ORM models directly. Use UUID types, enums, explicit nullability and output filtering. Ensure all timestamps are timezone-aware UTC values.

---

# 11. Database design and migrations

## 11.1 Database is the source of truth

Use PostgreSQL for users, projects, verification, scans, pages, findings, source documents, remediations, approvals, validations, events, reports and agent metadata. Qdrant stores vectors keyed by stable knowledge chunk IDs.

Use UUID primary keys, UTC timestamps, foreign keys and deletion policies deliberately. Prefer soft-delete or explicit cascade behavior according to data retention policy. Do not cascade-delete a project in a way that silently destroys audit evidence without a confirmation and clear product behavior.

## 11.2 Core tables

### `users`

- `id UUID PRIMARY KEY`
- `email CITEXT or normalized VARCHAR UNIQUE NOT NULL`
- `password_hash TEXT NOT NULL`
- `display_name VARCHAR(120)`
- `is_active BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

If `CITEXT` is not enabled, normalize email consistently in application code and keep a unique constraint on normalized email.

### `projects`

- `id UUID PRIMARY KEY`
- `owner_id UUID NOT NULL REFERENCES users(id)`
- `name VARCHAR(160) NOT NULL`
- `base_domain VARCHAR(253) NOT NULL`
- `created_at`, `updated_at`
- `archived_at TIMESTAMPTZ NULL`

### `project_domain_verifications`

- `id UUID PRIMARY KEY`
- `project_id UUID NOT NULL REFERENCES projects(id)`
- `domain VARCHAR(253) NOT NULL`
- `verification_token VARCHAR(128) NOT NULL`
- `status VARCHAR(20) NOT NULL` (`pending`, `verified`, `expired`)
- `verified_at TIMESTAMPTZ NULL`
- `expires_at TIMESTAMPTZ NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

The verification token must be generated with a cryptographically secure random generator. Verify via DNS TXT record under a dedicated name such as `_accessguard-verification.<domain>`. Do not accept a user-supplied “verified=true” flag.

### `scans`

- `id UUID PRIMARY KEY`
- `project_id UUID NOT NULL REFERENCES projects(id)`
- `requested_by UUID NOT NULL REFERENCES users(id)`
- `target_url TEXT NOT NULL`
- `status VARCHAR(40) NOT NULL`
- `config JSONB NOT NULL`
- `started_at TIMESTAMPTZ NULL`
- `completed_at TIMESTAMPTZ NULL`
- `total_pages INTEGER NOT NULL DEFAULT 0`
- `pages_succeeded INTEGER NOT NULL DEFAULT 0`
- `pages_failed INTEGER NOT NULL DEFAULT 0`
- `total_violations INTEGER NOT NULL DEFAULT 0`
- `axe_version VARCHAR(40)`
- `browser_version VARCHAR(80)`
- `error_code VARCHAR(80) NULL`
- `error_summary TEXT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

Store a snapshot of effective scan limits/configuration in `config` so future changes do not rewrite old scan history.

### `scan_pages`

- `id UUID PRIMARY KEY`
- `scan_id UUID NOT NULL REFERENCES scans(id)`
- `url TEXT NOT NULL`
- `normalized_url TEXT NOT NULL`
- `page_title TEXT NULL`
- `http_status INTEGER NULL`
- `audit_status VARCHAR(30) NOT NULL`
- `load_duration_ms INTEGER NULL`
- `screenshot_storage_key TEXT NULL`
- `dom_snapshot_storage_key TEXT NULL`
- `error_code VARCHAR(80) NULL`
- `error_summary TEXT NULL`
- `scanned_at TIMESTAMPTZ NULL`
- `created_at TIMESTAMPTZ NOT NULL`

Unique constraint: `(scan_id, normalized_url)`.

### `findings`

- `id UUID PRIMARY KEY`
- `scan_page_id UUID NOT NULL REFERENCES scan_pages(id)`
- `axe_rule_id VARCHAR(160) NOT NULL`
- `impact VARCHAR(20) NULL` (`minor`, `moderate`, `serious`, `critical`)
- `description TEXT NOT NULL`
- `help TEXT NULL`
- `help_url TEXT NULL`
- `wcag_tags JSONB NOT NULL DEFAULT '[]'`
- `selector TEXT NULL`
- `html_snippet TEXT NULL` (sanitized and length-limited)
- `failure_summary TEXT NULL`
- `fingerprint VARCHAR(128) NOT NULL`
- `is_incomplete BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at TIMESTAMPTZ NOT NULL`

Use a fingerprint derived from stable fields such as page normalized URL, axe rule ID, normalized selector and relevant target context. Do not fingerprint only the selector if multiple nodes share the same selector. Use an appropriate unique constraint or deduplication policy per scan page.

### `finding_nodes`

Optional but recommended for multiple affected nodes per axe rule:

- `id UUID PRIMARY KEY`
- `finding_id UUID NOT NULL REFERENCES findings(id)`
- `target JSONB NOT NULL`
- `html_snippet TEXT NULL`
- `failure_summary TEXT NULL`
- `screenshot_reference TEXT NULL`

Do not combine many affected DOM nodes into one giant unstructured text value.

### `knowledge_sources`

- `id UUID PRIMARY KEY`
- `source_key VARCHAR(160) UNIQUE NOT NULL`
- `title TEXT NOT NULL`
- `source_url TEXT NOT NULL`
- `publisher VARCHAR(120) NOT NULL`
- `standard_version VARCHAR(40) NULL`
- `content_version VARCHAR(120) NULL`
- `fetched_at TIMESTAMPTZ NULL`
- `checksum VARCHAR(128) NULL`
- `is_active BOOLEAN NOT NULL DEFAULT TRUE`

### `knowledge_chunks`

- `id UUID PRIMARY KEY`
- `source_id UUID NOT NULL REFERENCES knowledge_sources(id)`
- `chunk_key VARCHAR(200) UNIQUE NOT NULL`
- `criterion_id VARCHAR(30) NULL`
- `criterion_level VARCHAR(10) NULL`
- `principle VARCHAR(40) NULL`
- `section_title TEXT NULL`
- `content_type VARCHAR(40) NOT NULL`
- `content TEXT NOT NULL`
- `source_url TEXT NOT NULL`
- `metadata JSONB NOT NULL DEFAULT '{}'`
- `content_hash VARCHAR(128) NOT NULL`
- `embedding_model VARCHAR(160) NOT NULL`
- `indexed_at TIMESTAMPTZ NULL`
- `created_at TIMESTAMPTZ NOT NULL`

Do not store full copied websites or arbitrary user webpage text in the WCAG collection. Preserve source attribution and only retain content necessary for the product's retrieval, respecting source terms and copyright.

### `remediations`

- `id UUID PRIMARY KEY`
- `finding_id UUID NOT NULL REFERENCES findings(id)`
- `status VARCHAR(30) NOT NULL` (`proposed`, `needs_review`, `approved`, `rejected`, `validating`, `validated`, `validation_failed`, `manual_review_required`)
- `root_cause TEXT NOT NULL`
- `recommendation TEXT NOT NULL`
- `patch_format VARCHAR(40) NOT NULL`
- `patch_payload JSONB NOT NULL`
- `before_snippet TEXT NULL`
- `after_snippet TEXT NULL`
- `confidence NUMERIC(4,3) NULL`
- `model_provider VARCHAR(40) NULL`
- `model_name VARCHAR(120) NULL`
- `prompt_version VARCHAR(40) NULL`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

Confidence is not a probability unless it is calibrated. Label it “model-reported confidence” or omit it from the user interface until calibrated.

### `remediation_approvals`

- `id UUID PRIMARY KEY`
- `remediation_id UUID NOT NULL REFERENCES remediations(id)`
- `reviewer_id UUID NOT NULL REFERENCES users(id)`
- `decision VARCHAR(20) NOT NULL` (`approved`, `rejected`)
- `comments TEXT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

### `validation_results`

- `id UUID PRIMARY KEY`
- `remediation_id UUID NOT NULL REFERENCES remediations(id)`
- `validation_mode VARCHAR(40) NOT NULL` (`dom_snapshot`, `local_fixture`, `repository_test` future)
- `passed BOOLEAN NOT NULL`
- `original_rule_resolved BOOLEAN NOT NULL DEFAULT FALSE`
- `new_violations JSONB NOT NULL DEFAULT '[]'`
- `details JSONB NOT NULL DEFAULT '{}'`
- `created_at TIMESTAMPTZ NOT NULL`

### `agent_runs`

- `id UUID PRIMARY KEY`
- `scan_id UUID NOT NULL REFERENCES scans(id)`
- `finding_id UUID NULL REFERENCES findings(id)`
- `agent_name VARCHAR(80) NOT NULL`
- `status VARCHAR(30) NOT NULL`
- `input_summary JSONB NOT NULL DEFAULT '{}'`
- `output_summary JSONB NOT NULL DEFAULT '{}'`
- `provider VARCHAR(40) NULL`
- `model_name VARCHAR(120) NULL`
- `prompt_version VARCHAR(40) NULL`
- `duration_ms INTEGER NULL`
- `error_code VARCHAR(80) NULL`
- `created_at TIMESTAMPTZ NOT NULL`

Do not store API keys, complete private page contents, unnecessary personal information or unlimited chain-of-thought in agent logs. Save concise execution metadata and user-visible rationale, not hidden model reasoning.

### `scan_events`

- `id BIGSERIAL PRIMARY KEY`
- `scan_id UUID NOT NULL REFERENCES scans(id)`
- `sequence_number BIGINT NOT NULL`
- `event_type VARCHAR(80) NOT NULL`
- `payload JSONB NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

Unique: `(scan_id, sequence_number)`. Use for SSE replay/reconnection and audit history.

### `reports`

- `id UUID PRIMARY KEY`
- `scan_id UUID NOT NULL REFERENCES scans(id)`
- `format VARCHAR(20) NOT NULL` (`pdf`, `json`)
- `storage_key TEXT NOT NULL`
- `generated_by UUID NOT NULL REFERENCES users(id)`
- `created_at TIMESTAMPTZ NOT NULL`

### `refresh_sessions`

Persist refresh-session identifiers/hashes, expiries and revocation timestamps if refresh tokens are used. Store a hash of the refresh token, not the raw token.

## 11.3 Indexes

At minimum:

- `projects(owner_id, created_at DESC)`
- `scans(project_id, created_at DESC)`
- `scans(status, created_at)`
- `scan_pages(scan_id, normalized_url)` unique
- `findings(scan_page_id, impact)`
- `findings(axe_rule_id)`
- `findings(fingerprint)`
- `knowledge_chunks(criterion_id)`
- Full-text GIN index for `knowledge_chunks.content` using a deliberately selected text-search configuration.
- `remediations(finding_id, created_at DESC)`
- `scan_events(scan_id, sequence_number)` unique

Add indexes only where justified by queries; avoid indiscriminate indexing of every JSON field.

## 11.4 Migrations

Initialize Alembic after database settings are established. Every schema change must be a migration.

Commands from `backend/`:

```powershell
uv run alembic init alembic
uv run alembic revision --autogenerate -m "create initial application schema"
uv run alembic upgrade head
uv run alembic current
uv run alembic history
```

Review generated migrations manually. Never assume autogenerate captures every constraint or index. Test both an empty database upgrade and an upgrade from the previous schema. Do not edit a migration that has already been applied in a shared environment; create a new migration.

---

# 12. Website crawler and accessibility scanner

This module is the factual foundation of AccessGuard. Implement and test it before connecting an LLM.

## 12.1 Scanner responsibilities

The scanner must:

1. Accept only a scan request created by an authenticated user for a project they own.
2. Require the project's base domain to be verified before scanning.
3. Validate the initial URL and every subsequent navigation/request.
4. Restrict pages to the verified registrable domain and approved subdomains according to project settings. The default should be exact host only; do not silently include every subdomain.
5. Limit protocols to HTTP/HTTPS and ports to 80/443 by default.
6. Limit crawl depth, total pages, response size, total scan time and per-page load time.
7. Avoid form submission, login, checkout, POST/PUT/DELETE requests and other actions that change target website state.
8. Discover links from rendered pages and normalize them.
9. Render each eligible page using Playwright Chromium.
10. Inject the local axe-core bundle and execute `axe.run()` with a clearly documented WCAG tag selection.
11. Record violations and incomplete results separately.
12. Return structured page results; persistence is performed through the application service/repository layer.

## 12.2 Domain verification

A user should prove control of the website domain before running a scan. This is an abuse-control measure, not a complete security boundary.

Workflow:

1. User creates project with `example.com`.
2. Backend generates a random token with at least 128 bits of entropy.
3. UI displays a DNS TXT instruction, for example:
   - Record name: `_accessguard-verification.example.com`
   - Record type: `TXT`
   - Value: `accessguard-verification=<token>`
4. User adds the record at their DNS provider.
5. Backend resolves TXT records and checks for an exact token match.
6. Backend marks the domain verified with timestamp and expiry policy.
7. Reverification can be required after a configurable long period or on suspicious changes.

Never allow a user to verify a domain by changing a client-side boolean. DNS lookup must have strict timeout, response and retry limits. In tests, mock DNS resolver results; do not rely on a live external DNS provider.

## 12.3 URL normalization

Create a single tested function for normalization:

- Parse with a standard URL parser.
- Require `http` or `https`.
- Reject userinfo (`user:pass@host`).
- Reject missing hostname.
- Normalize host with IDNA handling and lowercase.
- Remove default ports.
- Remove fragments.
- Normalize empty path to `/`.
- Preserve query parameters by default because they may identify different content, but provide a configurable query allowlist/normalization rule if query explosion becomes an issue.
- Reject malformed percent encoding and control characters.
- Do not strip parameters blindly; `?page=2` may be a distinct page.

Use URL parsing, not regex alone.

## 12.4 SSRF and network safety

This is mandatory because Playwright visits user-controlled URLs and web pages can initiate subrequests.

Application checks:

- Resolve hostname before navigation.
- Reject loopback, private, link-local, multicast, reserved, unspecified and other non-public IP addresses.
- Reject IPv4-mapped IPv6 forms that resolve to blocked ranges.
- Validate all A/AAAA answers, not just the first.
- Revalidate redirect destinations.
- Validate every request URL and subresource where possible.
- Block `file:`, `ftp:`, `data:` navigation and unsupported protocols.
- Block downloads, popups and unexpected new pages.
- Disable or tightly control service workers.
- Never let an LLM choose a URL or make network requests directly.

Infrastructure checks:

- Run browser scans in a dedicated, unprivileged container/process.
- Do not mount the Docker socket into the scanner.
- Do not pass API keys, database passwords or signing secrets to the browser process.
- Keep PostgreSQL, Redis and Qdrant off any network that an untrusted browser can access.
- Use outbound network policy or an egress proxy in deployments that accept arbitrary user targets. Block private/internal address ranges at the network boundary as well as in application code.
- Do not expose internal administration ports to the public internet.

Important: DNS validation followed by a browser resolving the hostname again can be vulnerable to DNS rebinding. The implementation must not claim complete SSRF protection from a one-time DNS lookup. Before public deployment, enforce address restrictions at the egress boundary or use a controlled proxy that resolves and pins public destinations. If such infrastructure cannot be deployed, restrict the hosted product to explicitly allowlisted, verified domains and disclose that limitation.

## 12.5 Playwright browser configuration

Use Chromium headless. Set:

- A fixed, documented viewport (for example 1365×900) in the first release.
- A fixed locale and timezone.
- A bounded navigation timeout.
- A bounded total page timeout.
- No persistent browser profile.
- A new browser context per scan or per target isolation boundary.
- No user-supplied cookies or browser extensions in MVP.
- Downloads disabled.
- Popups/new tabs closed or rejected.
- Request routing enabled for URL policy enforcement.
- A deterministic user agent that identifies the scan product if appropriate and does not impersonate another service.

Wait for `domcontentloaded` or a bounded `networkidle` strategy; do not wait indefinitely for sites with long-polling analytics. Use a bounded settle delay after main content is ready before running axe. Document the behavior to keep results repeatable.

## 12.6 Link discovery

- Start from the validated target URL.
- Extract anchors from rendered DOM.
- Resolve relative links against current page URL.
- Keep only HTTP/HTTPS links on allowed host(s).
- Remove fragments.
- Deduplicate normalized URLs.
- Exclude mailto, tel, javascript, downloads and links with unsupported schemes.
- Respect crawl depth and maximum pages.
- Do not submit forms.
- Do not follow links that contain likely state-changing paths if a conservative block rule is configured (for example, logout/delete/checkout). Prefer not to navigate action links at all unless explicitly selected by the user.
- Store crawl errors for blocked/failed URLs without failing the entire project scan.

A simple breadth-first queue is sufficient. Do not implement a distributed web crawler.

## 12.7 Injecting axe-core

Install axe-core from `tools/axe` and copy `node_modules/axe-core/axe.min.js` into the scanner runtime image. From Python Playwright use the documented `page.add_script_tag(path=...)` method.

Illustrative pseudocode:

```python
await page.add_script_tag(path=str(AXE_CORE_JS_PATH))
raw_results = await page.evaluate(
    """async () => {
      return await axe.run(document, {
        runOnly: {
          type: 'tag',
          values: [
            'wcag2a', 'wcag2aa',
            'wcag21a', 'wcag21aa',
            'wcag22aa',
            'best-practice'
          ]
        }
      });
    }"""
)
```

This is an example tag configuration, not a guarantee that every criterion or best-practice rule is covered. Confirm the actual tags supported by the pinned axe-core version. Store the exact configured tags in the scan record. Keep `best-practice` findings distinguishable from WCAG-tagged findings.

Do not claim a best-practice rule is a WCAG success criterion. A finding can carry multiple WCAG tags, and one axe rule can map to several criteria.

## 12.8 Normalize axe-core results

Normalize the raw result into internal models with:

- `rule_id`
- `impact`
- `description`
- `help`
- `help_url`
- `tags`
- `wcag_criteria` (parse only recognized WCAG tag identifiers and preserve original tags)
- `nodes[]`
  - `target[]`
  - `html`
  - `failure_summary`
  - `any[]`, `all[]`, `none[]` checks where relevant
- `result_type` (`violation`, `incomplete`, `pass` when stored for summary)

Store incomplete results separately from definite violations. Do not convert an `incomplete` item into a confirmed violation. Display it as “Needs manual review” or “Incomplete automated check”.

## 12.9 Finding deduplication

Within one scan, group repeated axe rules and affected nodes sensibly. Across scans, use a fingerprint to support historical comparison, but never overwrite previous scan findings. Keep each scan's finding snapshot immutable.

A fingerprint can include:

- normalized page URL
- axe rule ID
- stable target selector path
- selected failure summary hash

Avoid using full HTML as the only fingerprint input because dynamic attributes can change on each render.

## 12.10 Screenshots and DOM evidence

- Capture a page screenshot only when the user enables it or when a finding requires visual evidence.
- Use a maximum output size and storage retention policy.
- Capture a short sanitized HTML snippet, not the entire page by default.
- Escape evidence in the UI; never render untrusted HTML directly as active markup.
- Store artifact references (file/object storage keys), not arbitrary disk paths returned by a browser.
- Do not expose evidence from another user's scan.

For the first release, local Docker volume storage is acceptable, but implement an `ArtifactStorage` interface so production object storage can be added without changing route logic. Apply retention and deletion rules.

## 12.11 Scanner tests

Create local fixture websites under `test_sites/` with known cases:

1. `accessible/` — simple accessible page with semantic landmarks, labels and appropriate image alternatives.
2. `violations/` — missing image alternative, missing form label, empty button, low contrast fixture and heading-order fixture.
3. `dynamic/` — delayed DOM content, client-rendered element and a route that returns a controlled failure.
4. `external_links/` — same-origin and cross-origin links for crawler tests.
5. `long_page/` — large DOM to test timeout/size limits.

Serve fixtures locally during tests. The scanner test configuration may allow loopback only for the test harness, behind a test-only setting that cannot be enabled in production. Do not weaken production URL policy just to scan fixtures.

Tests must verify:

- axe script is injected from local file.
- Known fixture violations are detected.
- A clean fixture does not produce fabricated findings.
- Incomplete checks are stored separately.
- Same-origin links are crawled within limit.
- Cross-origin links are not followed by default.
- Duplicate URLs are scanned once.
- Timeout and browser crash become page errors, not process crashes.
- Private IP, localhost and metadata endpoint targets are rejected outside test mode.

---

# 13. Advanced RAG and WCAG knowledge base

## 13.1 Knowledge sources

Use official W3C resources as the authoritative knowledge base. Start with:

- WCAG 2.2 Recommendation: `https://www.w3.org/TR/WCAG22/`
- Understanding WCAG 2.2: `https://www.w3.org/WAI/WCAG22/Understanding/`
- Techniques for WCAG 2.2: `https://www.w3.org/WAI/WCAG22/Techniques/`
- WAI-ARIA Authoring Practices Guide: `https://www.w3.org/WAI/ARIA/apg/`
- WAI-ARIA overview and standards guidance: `https://www.w3.org/WAI/standards-guidelines/aria/`

Keep the source registry in `knowledge_base/sources.yaml`. Record URL, title, publisher, version/date if present, retrieval date, parser type and content hash.

Do not treat community blog posts, generated summaries or LLM-created content as normative WCAG sources. They may be added later as clearly labeled secondary guidance, not as authoritative criteria.

## 13.2 Ingestion architecture

Pipeline:

1. Read the curated source registry.
2. Fetch only allowed official source URLs.
3. Apply request timeout, response size limit and content-type check.
4. Save raw downloaded content to ignored local storage for reproducibility where permitted.
5. Parse HTML/document structure.
6. Extract heading hierarchy, paragraphs, lists, examples, criterion IDs and anchors.
7. Build canonical sections and remove navigation/footer noise.
8. Create criterion-aware chunks.
9. Attach source metadata and canonical source URL.
10. Compute content hash; skip unchanged chunks.
11. Generate local embeddings.
12. Upsert dense vectors into Qdrant with stable chunk IDs.
13. Store chunk text and metadata in PostgreSQL.
14. Run retrieval smoke tests.
15. Record ingestion summary and version.

The ingestion script must be idempotent. Running it twice against unchanged sources must not create duplicate chunks or duplicate vector points.

## 13.3 Chunking strategy

Do not split a success criterion's identifier from its normative text. Do not use an arbitrary fixed character splitter as the only strategy.

Preferred chunk structure:

- One chunk for each WCAG success criterion's normative statement plus its core metadata.
- Separate chunks for the corresponding Understanding page sections (intent, benefits, examples, related resources) where useful.
- Separate technique chunks linked by criterion metadata.
- Separate ARIA pattern chunks linked to a pattern title and official URL.

A chunk should usually be 200–800 tokens, but semantic integrity is more important than exact length. Preserve parent/child relationships in metadata. Use overlap only when a long section must be split, and keep criterion identifiers repeated in every child chunk.

Metadata fields:

```json
{
  "chunk_id": "wcag22_sc_1_1_1_normative",
  "source_key": "wcag22_recommendation",
  "source_title": "Web Content Accessibility Guidelines (WCAG) 2.2",
  "source_url": "https://www.w3.org/TR/WCAG22/#non-text-content",
  "publisher": "W3C",
  "standard_version": "WCAG 2.2",
  "criterion_id": "1.1.1",
  "criterion_level": "A",
  "principle": "Perceivable",
  "guideline_id": "1.1",
  "content_type": "normative_criterion",
  "section_title": "Non-text Content",
  "content_hash": "sha256:..."
}
```

The exact text must come from the official source parser; this sample is metadata only. Verify criterion IDs and levels from the source rather than typing the entire standard manually.

## 13.4 Embedding model

Use local `sentence-transformers/all-MiniLM-L6-v2` initially. Record:

- model identifier
- model revision/hash where obtainable
- embedding dimension
- normalization behavior
- text preprocessing version

The embedding model runs locally and requires no Gemini/Groq API key. Download it once and cache it in a model cache volume. Do not commit model weights to Git.

If the model is unavailable at startup, surface a precise dependency error and instructions. Do not silently use random vectors or zero vectors.

## 13.5 Dense retrieval

- Embed the query using the same model/version as indexed chunks.
- Query Qdrant by cosine similarity.
- Retrieve an initial candidate set, initially 20.
- Apply metadata filters when a known criterion or source type is available.
- Return chunk ID, score and metadata.
- Verify the chunk exists in PostgreSQL before using its content.

## 13.6 Lexical retrieval

A lexical path is needed because exact identifiers such as `1.4.3`, `2.4.11`, `aria-label`, and axe rule IDs can be important.

Use PostgreSQL full-text search with a deliberately selected configuration or a simple BM25 implementation over the indexed corpus. For the first implementation, PostgreSQL FTS with a `simple` dictionary is acceptable if exact identifiers are tested. Add a separate normalization/tokenization path for criterion IDs and ARIA tokens if the default tokenizer splits punctuation unexpectedly.

## 13.7 Hybrid fusion

Retrieve dense top 20 and lexical top 20, then merge with Reciprocal Rank Fusion (RRF) in Python. Use stable chunk IDs and deterministic tie-breaking.

Example formula:

`RRF_score(document) = Σ 1 / (k + rank_i(document))`

Choose a documented `k` (commonly 60) and keep it configurable for evaluation. Do not add cosine similarity values directly to BM25 scores because their scales differ.

The baseline RAG must work with hybrid fusion before adding a reranker.

## 13.8 Reranking

After hybrid retrieval, optionally rerank the top 20 candidates with a local cross-encoder and return top 5. Use `RERANKER_ENABLED=false` by default until the baseline is stable and evaluation demonstrates improvement.

The chosen reranker must be pinned by model ID/revision and loaded once per worker process. It must not be loaded once per API request. Because the reranker consumes RAM/CPU, record latency and memory. If unavailable, use the fused ordering and mark the fallback in retrieval metadata; do not fail all scans.

## 13.9 Retrieval query construction

Build the query from structured scanner evidence:

- axe rule ID
- axe description/help
- recognized WCAG tags
- failure summary
- safe HTML snippet
- relevant element role/tag/type
- user question (if one exists)

Do not send an entire page to the embedding model or LLM. Minimize the context. Escape or delimit untrusted page content and instruct the model that page content is data, never instructions.

## 13.10 Evidence object

The RAG service returns structured objects:

```json
{
  "chunk_id": "...",
  "criterion_id": "1.1.1",
  "title": "Non-text Content",
  "source_title": "Understanding Success Criterion 1.1.1",
  "source_url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html",
  "content_type": "understanding",
  "excerpt": "...",
  "dense_rank": 2,
  "lexical_rank": 1,
  "fusion_rank": 1,
  "reranker_score": null
}
```

The excerpt must be a short relevant passage, not a large copy of the source. Persist enough metadata to trace it back to the exact source.

## 13.11 Citation validation

Before showing an answer:

- Verify every cited chunk ID exists.
- Verify the citation URL matches stored metadata.
- Verify the answer's criterion IDs are present in evidence or in the finding's original axe tags.
- Do not let the LLM create arbitrary URLs.
- Render citations as links to stored official URLs.
- If no relevant evidence clears the calibrated threshold, return `insufficient_evidence` and request manual review.

## 13.12 RAG API and scripts

Ingestion command from repository root (once implemented):

```powershell
cd backend
uv run python scripts/ingest_knowledge.py --sources ..\knowledge_base\sources.yaml
```

Evaluation command:

```powershell
uv run python scripts/evaluate_rag.py --dataset ..\knowledge_base\evaluation\retrieval_cases.jsonl
```

Adjust module paths to the actual final script placement; keep one canonical documented command. Do not create multiple nearly identical ingestion scripts.

Provide CLI options:

- `--dry-run`
- `--force-reindex`
- `--source-key`
- `--limit`
- `--report-json`

Dry run must parse and report what would be indexed without changing Qdrant/PostgreSQL.

---

# 14. LLM integration and API-key timing

## 14.1 When the key is actually needed

**No provider API key is required for Phases 1–9.** The following all work without Gemini or Groq:

- React frontend and API shell.
- PostgreSQL schema and authentication.
- DNS verification test harness.
- Playwright crawler.
- axe-core scanning.
- Scan persistence and reports.
- WCAG source ingestion.
- Local embeddings.
- Qdrant dense retrieval.
- Lexical retrieval and RRF.
- Deterministic RAG evaluation.
- Agent graph structure with a `MockLLMProvider` used in tests.

**A real LLM API key is first required in Phase 10**, when the project begins live model-backed explanations and remediation. At that point:

1. The agent must tell the user that the deterministic scanner and RAG are already working.
2. Ask the user to choose Gemini (recommended default) or Groq.
3. Instruct the user to create the key on the provider's official developer console.
4. Ask the user to put the key in local `.env` only.
5. Never ask the user to paste the key into a chat response or GitHub issue.
6. Verify the key through one short provider smoke test.
7. Record provider and model name, not the key.

Only one key is required. A second provider key is optional.

## 14.2 Environment configuration

Default pre-key config:

```env
LLM_PROVIDER=mock
GEMINI_API_KEY=
GROQ_API_KEY=
GEMINI_MODEL=
GROQ_MODEL=
```

When the user supplies a Gemini key locally:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=replace-locally
GEMINI_MODEL=use-a-current-supported-model-id
```

If the user chooses Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=replace-locally
GROQ_MODEL=use-a-current-supported-model-id
```

Do not put a real key in `.env.example`. The selected model ID must be checked against current provider documentation when Phase 10 starts; do not assume a model name from an old tutorial is still active.

## 14.3 Provider interface

Define a provider-independent contract. For example:

```python
class LLMProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, object],
        output_schema: type[BaseModel],
        model: str,
        temperature: float = 0.0,
    ) -> BaseModel:
        ...
```

Implement:

- `MockLLMProvider` — deterministic test responses, no network.
- `GeminiLLMProvider` — default real integration.
- `GroqLLMProvider` — optional alternative.
- `LLMProviderFactory` — reads config and validates required key only when that provider is selected.

Use low temperature for structured analysis. Treat provider JSON mode/structured output as an aid, not a substitute for local Pydantic validation. Provider model support and schema constraints can change. Validate every response and return a typed error for invalid output.

## 14.4 Provider error handling

Classify:

- Authentication/invalid key: do not retry; show configuration guidance.
- Rate limit: retry with bounded exponential backoff and jitter; respect provider retry headers where available.
- Temporary server error/network timeout: retry a small bounded number of times.
- Invalid request/schema: do not blindly retry the same payload; log sanitized error and mark task as requiring review.
- Token/context limit: reduce context using retrieval thresholds and safe truncation; do not silently drop source citations.
- Model unavailable/retired: report configuration issue and require a supported model ID.

Never silently fall back to another provider unless the user explicitly configured it and the product records which provider actually responded. A provider switch can change output behavior and has cost/privacy implications.

## 14.5 Prompt design rules

Store prompts in version-controlled files under `app/ai/prompts/`. Each prompt has a version ID. Prompts must:

- Clearly separate trusted system instructions from untrusted webpage content.
- Treat DOM snippets, page text and retrieved excerpts as data, not instructions.
- Request a strict output schema.
- Ask for uncertainty and abstention when evidence is insufficient.
- Require citations from the supplied evidence objects only.
- Prohibit invented WCAG criteria and fabricated source URLs.
- Prohibit destructive or unrelated code changes.
- Never request hidden chain-of-thought. Request concise, user-visible rationale and evidence instead.

---

# 15. LangGraph multi-agent workflow

## 15.1 Do not build six free-form chatbots

The product needs a small deterministic graph with specialized nodes. The scanner performs crawling and axe execution before the LLM graph starts. Agents should not redo deterministic work through prompts.

Initial node roles:

1. `scan_context_node` — load normalized scan/finding context.
2. `knowledge_retrieval_node` — call RAG service and attach evidence.
3. `finding_analysis_node` — classify likely cause and required manual review.
4. `remediation_node` — propose a bounded correction.
5. `review_node` — validate schema, evidence references and policy.
6. `approval_interrupt_node` — pause for user approval.
7. `validation_node` — run approved snapshot/fixture validation.
8. `finalize_node` — persist final status and user-visible summary.

The crawler and axe scanner may be represented in overall product architecture as “crawler/audit stages”, but they do not need to be LLM agents.

## 15.2 Shared graph state

Use `TypedDict` or a well-defined Pydantic state adapter. Example:

```python
class AccessGuardState(TypedDict, total=False):
    scan_id: str
    finding_id: str
    user_id: str
    target_url: str
    finding: dict
    retrieved_evidence: list[dict]
    analysis: dict
    remediation_proposal: dict
    review_result: dict
    human_decision: dict
    validation_result: dict
    status: str
    errors: list[dict]
```

Do not place full page DOM or giant screenshots in graph state. Store artifacts in storage and pass references plus bounded snippets. State should be serializable and safe for checkpointing.

## 15.3 Typed output schemas

At minimum:

### `FindingAnalysis`

- `summary: str`
- `likely_root_cause: str`
- `affected_element_type: str | None`
- `relevant_criterion_ids: list[str]`
- `needs_manual_review: bool`
- `limitations: list[str]`
- `evidence_chunk_ids: list[str]`

### `RemediationProposal`

- `problem: str`
- `recommendation: str`
- `before_snippet: str | None`
- `after_snippet: str | None`
- `patch_format: Literal["snippet", "dom_operations", "manual_steps"]`
- `patch_operations: list[PatchOperation]`
- `expected_effect: str`
- `manual_checks: list[str]`
- `evidence_chunk_ids: list[str]`
- `model_confidence: float | None`

### `ReviewResult`

- `accepted_for_human_review: bool`
- `rejection_reasons: list[str]`
- `evidence_complete: bool`
- `policy_checks_passed: list[str]`
- `policy_checks_failed: list[str]`

Schema validation must enforce lengths, enumerations and max list sizes. Do not allow arbitrary extra fields unless explicitly needed.

## 15.4 Graph control flow

```mermaid
flowchart TD
    A([Start Remediation]) --> B[Load Finding Context]
    B --> C[Hybrid RAG Retrieval]
    C --> D{Evidence Sufficient?}
    D -->|No| E[Mark Manual Review Required]
    D -->|Yes| F[Finding Analysis]
    F --> G[Generate Remediation Proposal]
    G --> H[Deterministic Schema and Policy Review]
    H --> I{Review Passed?}
    I -->|No| J[One Bounded Regeneration or Manual Review]
    J --> E
    I -->|Yes| K[Human Approval Interrupt]
    K --> L{Approved?}
    L -->|No| M[Persist Rejected Decision]
    L -->|Yes| N[Validate Isolated Snapshot]
    N --> O{Validation Passed?}
    O -->|No| P[Manual Review Required]
    O -->|Yes| Q[Persist Snapshot Validation]
    E --> R([Finalize])
    M --> R
    P --> R
    Q --> R
```

## 15.5 Routing behavior

- If RAG returns insufficient evidence, do not call remediation generation; mark manual review required.
- If the finding is `incomplete`, require human review and avoid presenting a confirmed-fix workflow.
- If provider call fails after bounded retry, preserve the finding and report AI analysis unavailable; the scanner remains usable.
- If the proposal references nonexistent evidence chunk IDs, reject it.
- If patch operations are outside the allowed operation set, reject them.
- If review fails, allow at most one controlled regeneration with precise feedback; then stop and require manual review.
- Only an authenticated user who owns the project can approve or reject.
- On resume after approval, re-check ownership and current remediation status; do not trust a stale graph state alone.

## 15.6 LangGraph persistence and human approval

Use LangGraph checkpointer persistence when the graph reaches an approval interrupt. A PostgreSQL checkpointer is appropriate for durable continuation. Use a stable `thread_id` tied to the remediation/approval workflow, but do not expose raw internal checkpoint identifiers as authorization tokens.

Approval route flow:

1. API verifies authenticated user owns the remediation's project.
2. API validates decision and status transition.
3. API records approval row in a transaction.
4. API resumes the graph using the checkpointed thread and a typed `Command` resume value.
5. Validation runs asynchronously.
6. API returns current persisted state; frontend receives progress event.

Be aware that a resumed LangGraph node may re-execute from the node containing an interrupt. Keep operations before the interrupt idempotent and do not perform external side effects before the interrupt unless they are safe to repeat.

## 15.7 Agent observability

Persist:

- agent name
- run ID
- scan/finding/remediation ID
- status
- start/end/duration
- provider/model (if used)
- prompt version
- retrieved chunk IDs
- error code
- concise output summary

Do not persist hidden reasoning traces. The user needs a transparent explanation, source references and action history, not hidden chain-of-thought.

---

# 16. Remediation proposal and validation design

## 16.1 No live website mutation

The first release must never log in to a third-party CMS, edit a production website, deploy code or apply patches to a live site. The user owns that decision and implementation.

The product creates:

- a problem explanation
- a recommended solution
- an illustrative before/after code snippet
- optional constrained DOM operations for a test snapshot
- manual verification steps
- WCAG/technique citations

## 16.2 Supported patch formats

Support three formats only in the first release:

1. `snippet`: a code example the developer can copy and adapt.
2. `dom_operations`: a narrowly constrained list of operations applied only to an isolated snapshot or fixture.
3. `manual_steps`: explanation when an automated patch is inappropriate.

Do not accept arbitrary JavaScript or Python code from the LLM.

Example allowed DOM operation schema:

```json
{
  "operation": "set_attribute",
  "selector": "img.brand-logo",
  "attribute": "alt",
  "value": "Example brand"
}
```

Allowed operations should be deliberately limited, for example:

- `set_attribute` for an allowlisted attribute.
- `remove_attribute` for an allowlisted attribute only when safe and relevant.
- `replace_text` within a known text node/selector.
- `insert_before`/`insert_after` only if a carefully defined safe markup fragment is supported.

Prefer the first three initially. Reject selectors that are too broad, attributes such as `onload`/`onclick`, script tags, event-handler attributes, URLs with unsafe schemes, and arbitrary CSS/JS.

## 16.3 Snapshot validation

The first release can validate a bounded, sanitized DOM snapshot or a local fixture page. It must label this result accurately:

- `Snapshot validation passed` means the applicable automated rule did not reproduce in that isolated snapshot and no prohibited new axe violations were introduced in the checked snapshot.
- It does not mean the actual deployed site is fixed.
- It does not mean the application state, responsive layouts, all routes or assistive technology behavior are correct.

Validation steps:

1. Fetch stored snapshot reference for the finding.
2. Reconstruct a local isolated test document without loading remote scripts, stylesheets or images.
3. Apply allowlisted DOM operations only.
4. Run axe-core locally.
5. Compare the relevant original rule and all new violation fingerprints.
6. Record input snapshot hash, patch hash, axe version and results.
7. Delete the temporary workspace after completion.

If sanitization changes semantics or the snapshot cannot be reconstructed, mark validation `not_supported` or `manual_review_required`; never invent a pass.

## 16.4 Future repository integration

A later optional GitHub integration may allow a user to connect a source repository, create a branch, apply a reviewed patch, run repository tests and open a pull request. This is not part of the first release. Do not request GitHub credentials or implement repository write permissions in the MVP.

---

# 17. Frontend product and UI specification

The initial design is locked for the first build. The user may request a visual redesign after reviewing the working application.

## 17.1 Product appearance

**Design direction:** premium developer-focused SaaS / accessibility observability tool.

**Default theme:** light. Do not spend initial development time implementing a second theme. If a dark theme is added later, it must be designed as a separate cohesive token set and tested for contrast.

**Visual characteristics:**

- Calm, confident, enterprise-oriented interface.
- Background: cool near-white (`#F7F8FA` or a nearby neutral token).
- Main text: deep slate/navy (`#172033`).
- Secondary text: muted slate (`#667085`).
- Primary action: restrained indigo/blue (`#4657D8` or a nearby accessible token).
- Success: green used for verified/passed states.
- Warning: amber used for incomplete/manual review states.
- Error/critical: red used sparingly for critical findings and failures.
- Borders: subtle cool gray.
- Cards: white, fine border, small radius and very light shadow only when hierarchy needs it.
- Typography: Inter or Geist Sans. Use one family for product UI.
- Icons: Lucide React, consistent size and stroke.
- Motion: subtle hover/focus/transition, no distracting gradients, no constant animated backgrounds.
- Layout: fixed-width collapsible-feeling left sidebar on desktop; responsive drawer on small screens; compact top bar; readable content width.

Do not use excessive glassmorphism, neon glow, giant gradient text, random floating icons, generic AI star decorations or huge empty cards. The UI should look like a real developer product.

## 17.2 Main navigation

Left sidebar:

1. Overview
2. Projects
3. Scans
4. Findings
5. AI Remediation
6. Reports
7. Knowledge Base
8. Settings

Footer/sidebar profile area displays the signed-in user's name/email and a logout action. Knowledge ingestion/reindex administration is not available to normal users; show the knowledge page as read-only with collection status and source references.

## 17.3 Required routes

Public routes:

- `/login`
- `/register`

Protected routes:

- `/app/overview`
- `/app/projects`
- `/app/projects/new`
- `/app/projects/:projectId`
- `/app/scans`
- `/app/scans/:scanId`
- `/app/scans/:scanId/findings`
- `/app/findings/:findingId`
- `/app/remediations/:remediationId`
- `/app/reports`
- `/app/reports/:reportId`
- `/app/knowledge`
- `/app/settings`

Unknown routes must show a helpful 404 page. Expired sessions should redirect to login with a non-sensitive return path.

## 17.4 Page-level specifications

### Login and register

- Product logo/wordmark.
- Concise value proposition.
- Email and password form.
- Inline validation and server error display.
- Password visibility toggle with accessible label.
- Loading state and disabled submit state.
- Links to the alternate auth route.
- No fake demo credentials in production.

### Overview dashboard

Top heading: `Overview` with a short explanation and primary `New scan` button.

Metric cards (real data only):

- Projects monitored.
- Scans completed.
- Pages audited.
- Open automated findings.
- Critical/serious findings.
- Verified snapshot validations.

Charts/sections:

- Findings by axe impact (critical, serious, moderate, minor; unknown separately).
- Findings over time based on saved scan snapshots.
- Recent scans with status and timestamp.
- Projects needing attention.

Do not show a “WCAG compliance score”. If a summary score is ever requested, it must be labeled as an internal heuristic and accompanied by its transparent formula. Prefer raw metrics for the first release.

### Projects page

- Project cards/list with project name, verified domain, last scan time and last scan status.
- Create project dialog/page.
- Domain verification status with clear DNS instructions.
- Edit project name.
- Archive/delete action with confirmation and clear retention behavior.
- Empty state guiding user to create their first project.

### New scan page

Inputs:

- Project/domain selection (verified only).
- Target URL on verified domain.
- Max pages (default 10; server hard limit 20 initially).
- Crawl depth (default 1; server hard limit 2 initially).
- Screenshot capture toggle (default off if storage is limited).
- Audit tag profile. Default WCAG 2.2 A/AA plus selected best-practice rules; display the actual rule tags used.

Show a confirmation that the user is authorized to scan this site. Do not allow user to type a different unverified hostname and bypass project ownership.

### Scan details page

Header:

- Project and target URL.
- Status pill.
- Start/completion timestamps.
- Scan duration.
- Re-run scan action.

Progress section:

- Stage label.
- Progress percentage only if measurable from discovered/completed pages; otherwise show counts and indeterminate progress.
- Pages discovered, audited, failed.
- Recent event log (bounded).

Results sections:

- Findings summary by impact.
- Page list with per-page status and violation count.
- Errors/incomplete checks.
- Findings table.
- Export report actions.

### Findings explorer

Columns:

- Impact.
- Rule ID.
- Description.
- WCAG tags/criterion IDs.
- Page URL.
- Affected node count.
- Review status.

Filters:

- Impact.
- WCAG criterion.
- Rule ID.
- Page.
- Remediation status.
- Search text.

Use server-side pagination and filtering. Table rows must be keyboard navigable. On mobile, convert to readable cards or horizontally scroll with accessible table semantics.

### Finding detail page

Show:

- Plain-language description from axe-core.
- Impact and rule ID.
- WCAG tags and any recognized criterion mappings.
- Official axe help link.
- Page URL and page title.
- Affected target selector(s).
- Sanitized HTML snippet in escaped code display.
- Failure summary.
- Screenshot link if available.
- Incomplete/manual-review label if applicable.
- `Generate AI explanation` and `Generate remediation` actions.

Do not render raw HTML evidence as live HTML. Use a syntax-highlighted escaped code block.

### AI Remediation workspace

Two-column desktop layout:

- Left: finding details, DOM evidence and retrieved WCAG sources.
- Right: AI explanation, proposed correction, before/after code, rationale and manual checks.

Show evidence citations with criterion, source title and official URL. Display model/provider only in a compact metadata area. Show “AI suggestion — not applied”.

Controls:

- Approve proposal.
- Reject proposal.
- Add reviewer note.
- Run snapshot validation after approval.

The UI must prevent duplicate approvals while a request is pending and reflect server status, not optimistic assumptions.

### Reports page

- List saved reports.
- Show scan ID, project, report format and creation time.
- Download PDF and JSON.
- Empty state if no reports exist.

### Knowledge page

- Explain which standards/sources are indexed.
- Show source title, source URL, version/date if known, last indexed time and chunk count.
- Provide an evidence search panel for a normal user (read-only query).
- Do not expose an unauthenticated reindex endpoint.

### Settings page

- User profile details.
- Change password/session actions if implemented.
- Data deletion instructions.
- Product version and build commit.
- Do not show or edit API keys in the browser.

## 17.5 Shared design components

Implement reusable components:

- `AppShell`
- `Sidebar`
- `Topbar`
- `PageHeader`
- `MetricCard`
- `StatusBadge`
- `SeverityBadge`
- `EmptyState`
- `ErrorState`
- `LoadingSkeleton`
- `ConfirmDialog`
- `DataTable`
- `FilterBar`
- `CodeBlock`
- `CitationCard`
- `ScanProgress`
- `ToastProvider`

Create semantic variants for statuses. Color must not be the only way to communicate severity; include text and/or icon.

## 17.6 Frontend accessibility requirements

AccessGuard must demonstrate accessibility practices itself:

- Semantic landmarks (`header`, `nav`, `main`, etc.).
- Visible keyboard focus.
- Keyboard-operable menus, dialogs and tables.
- Correct labels and descriptions for fields.
- `aria-live` or status region for scan progress and background updates, used carefully to avoid excessive announcements.
- Sufficient text and component contrast.
- No focus traps outside open modal/dialog contexts.
- Dialog focus management and escape behavior.
- Reduced-motion preference support.
- Responsive reflow without loss of functionality.
- Meaningful button names; icon-only controls need accessible names.
- Error messages associated with relevant inputs.

Run axe-core against AccessGuard's own frontend in Playwright CI. A green automated scan is a baseline, not proof of full accessibility.

## 17.7 Frontend state and API patterns

- TanStack Query owns server/cache state.
- Zustand only for small client-only state such as sidebar state or transient UI preferences.
- Axios or `fetch` through a single typed API client.
- Centralize auth refresh/401 behavior.
- Define TypeScript interfaces for API responses.
- Use React Hook Form + Zod for forms.
- Handle loading, empty, error and success states explicitly.
- Invalidate relevant queries after mutations.
- Do not hardcode dashboard values or fake chart data.

---

# 18. REST API contract

Prefix every route with `/api/v1`. Use JSON request/response bodies except file downloads and event streaming.

## 18.1 Auth

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Authenticate |
| POST | `/auth/refresh` | Refresh session/token |
| POST | `/auth/logout` | Revoke refresh session |
| GET | `/auth/me` | Current user |

Example registration request:

```json
{
  "email": "developer@example.com",
  "password": "a-long-user-selected-password",
  "display_name": "Developer"
}
```

Never echo password/hash. Rate-limit login/registration and use uniform error messaging where necessary to reduce account enumeration.

## 18.2 Projects and domains

| Method | Path | Purpose |
|---|---|---|
| POST | `/projects` | Create project |
| GET | `/projects` | List current user's projects |
| GET | `/projects/{project_id}` | Project details |
| PATCH | `/projects/{project_id}` | Update name/settings |
| DELETE | `/projects/{project_id}` | Archive/delete according to retention policy |
| POST | `/projects/{project_id}/domain-verification` | Create/refresh token |
| POST | `/projects/{project_id}/domain-verification/check` | Verify DNS TXT record |

Example project creation:

```json
{
  "name": "Company Website",
  "base_domain": "example.com"
}
```

## 18.3 Scans

| Method | Path | Purpose |
|---|---|---|
| POST | `/scans` | Queue scan |
| GET | `/scans` | List scans for current user |
| GET | `/scans/{scan_id}` | Scan summary |
| GET | `/scans/{scan_id}/status` | Current state/progress |
| GET | `/scans/{scan_id}/events` | SSE progress events |
| GET | `/scans/{scan_id}/pages` | Scanned pages |
| POST | `/scans/{scan_id}/cancel` | Request cancellation |
| POST | `/scans/{scan_id}/retry-failed-pages` | Retry eligible failed pages (optional in MVP) |

Example scan request:

```json
{
  "project_id": "00000000-0000-0000-0000-000000000000",
  "target_url": "https://example.com/",
  "config": {
    "max_pages": 10,
    "max_depth": 1,
    "capture_screenshots": false,
    "rule_profile": "wcag22_a_aa_and_best_practice"
  }
}
```

Server must reject unverified or mismatched target host. Server must apply hard caps regardless of client values.

Response:

```json
{
  "id": "...",
  "status": "queued",
  "created_at": "2026-01-01T10:00:00Z"
}
```

Use an idempotency key for scan creation where practical to prevent accidental duplicate submissions after a network retry.

## 18.4 Findings

| Method | Path | Purpose |
|---|---|---|
| GET | `/scans/{scan_id}/findings` | Paginated findings |
| GET | `/findings/{finding_id}` | Finding details |
| GET | `/findings/{finding_id}/evidence` | Evidence metadata and stored snippets |
| GET | `/findings/{finding_id}/related` | Related findings/criteria if available |

Filter options: `impact`, `rule_id`, `criterion_id`, `page_id`, `remediation_status`, `search`, `limit`, `cursor`.

## 18.5 Knowledge

| Method | Path | Purpose |
|---|---|---|
| GET | `/knowledge/sources` | List indexed official sources |
| POST | `/knowledge/search` | Search evidence as authenticated user |
| GET | `/knowledge/criteria/{criterion_id}` | Get criterion/source metadata |

Admin-only ingestion/reindex routes should not be exposed until admin authorization exists. Ingestion is a CLI operation in the initial release.

## 18.6 Remediation

| Method | Path | Purpose |
|---|---|---|
| POST | `/findings/{finding_id}/remediations` | Generate proposal |
| GET | `/remediations/{remediation_id}` | Get proposal |
| POST | `/remediations/{remediation_id}/approve` | Approve proposal |
| POST | `/remediations/{remediation_id}/reject` | Reject proposal |
| POST | `/remediations/{remediation_id}/validate` | Queue snapshot validation |
| GET | `/remediations/{remediation_id}/validation` | Validation history |

Approval/rejection must be idempotent or reject a duplicate status transition with a clear conflict response. Only the owner can decide.

## 18.7 Reports

| Method | Path | Purpose |
|---|---|---|
| POST | `/scans/{scan_id}/reports` | Generate report |
| GET | `/reports` | List reports |
| GET | `/reports/{report_id}` | Report metadata |
| GET | `/reports/{report_id}/download` | Download file |

The download endpoint must authorize ownership before streaming the file. Do not expose storage paths.

## 18.8 API documentation

FastAPI OpenAPI docs should be enabled in development. In production, protect or disable interactive docs according to deployment configuration. Maintain `docs/API.md` with the key request/response and auth behavior. Add examples using only dummy data.

---

# 19. Background jobs and real-time progress

## 19.1 Why background workers

Browser scans and model calls can take longer than a normal HTTP request. The scan endpoint should create a scan record, enqueue a task and return quickly. It should not wait for Playwright to finish.

## 19.2 Celery task design

Use a Celery application configured with Redis broker. Configure:

- task acknowledgement strategy deliberately for long tasks.
- bounded task time limits.
- bounded retries for transient failures.
- exponential backoff and jitter for safe transient operations.
- JSON-only task serializer.
- task arguments that contain IDs and validated config, not large DOM blobs.
- task idempotency using scan ID and stage state.
- worker concurrency appropriate to available memory; start with one browser task at a time on a student laptop.

Do not retry invalid URLs, ownership failures, policy blocks or deterministic parsing errors. Retry only recoverable infrastructure/provider errors.

## 19.3 Job stages

Implement a scan orchestration task with stages:

1. Load scan and verify status.
2. Validate target and domain ownership policy.
3. Mark `crawling`.
4. Crawl pages within limits.
5. Persist discovered page rows.
6. Mark `auditing`.
7. Execute axe on eligible pages.
8. Persist page results and normalized findings.
9. Update counts and scan events.
10. Mark `completed` or `completed_with_errors`.
11. Optionally enqueue AI investigation only when requested or configured; do not call the LLM for every finding automatically by default.

For first release, make AI analysis user-triggered from a finding detail page. This keeps API use and latency predictable.

## 19.4 Progress events

Persist scan events in PostgreSQL and stream them through SSE.

Event examples:

```json
{"type":"stage_changed","stage":"crawling","message":"Discovering eligible pages"}
{"type":"page_discovered","page_url":"https://example.com/about","discovered":3,"max_pages":10}
{"type":"page_audited","page_id":"...","violations":4,"completed":2,"total_discovered":3}
{"type":"scan_completed","status":"completed_with_errors","pages_succeeded":8,"pages_failed":2}
```

Never send raw HTML or private source contents in SSE events. Events should be small and safe.

## 19.5 SSE reconnection

- Support `Last-Event-ID` or an equivalent event cursor.
- Query persisted events after the last sequence number.
- Send heartbeats at a bounded interval.
- Close stream when scan reaches terminal state after pending events have been delivered.
- Authorize scan ownership before opening the stream.
- Avoid unbounded in-memory subscriber dictionaries as the only source of truth.

If Redis pub/sub is used for low-latency live delivery, PostgreSQL remains the replay source of truth.

---

# 20. Security, privacy and abuse prevention

Security is a product requirement because this scanner visits external websites and stores their output.

## 20.1 Authentication and tenant isolation

- Every project query must include `owner_id = current_user.id`.
- Every nested resource access must join back to a project owned by the current user.
- Never authorize based only on a UUID being hard to guess.
- Check ownership before reading artifacts, reports, scan events or graph state.
- Test IDOR cases by attempting to access another test user's resource IDs.
- Do not trust `user_id` passed in request bodies for ownership.

## 20.2 SSRF protections

Implement Section 12.4 and add a production egress policy. Specifically test:

- `localhost` and subdomains resolving to loopback.
- `127.0.0.1`, `::1` and IPv4-mapped IPv6.
- RFC1918 private IPv4 ranges.
- Link-local addresses.
- Cloud metadata addresses (including common metadata IPs).
- Multicast/reserved/unspecified ranges.
- Redirects from public host to blocked address.
- Hostname resolving to mixed public/private DNS answers.
- non-standard ports.
- encoded IP representations where parsers may differ.
- DNS rebinding simulation in test policy.

Do not claim full protection if only the first DNS lookup is checked. Production egress must prevent the browser from reaching internal networks.

## 20.3 Browser isolation

- Run non-root.
- Drop Linux capabilities where possible.
- Use seccomp/AppArmor or container hardening available in deployment.
- No host filesystem mounts except a dedicated temporary artifact directory.
- No Docker socket.
- No credentials in browser process environment.
- Read-only filesystem where feasible; use a small writable temp directory.
- Apply CPU, memory, process and time limits.
- Kill browser processes on cancellation/timeout.
- Keep internal databases/vector stores on a private application network.

For public deployment, prefer an isolated scan runner or egress proxy. Do not put a browser directly on the same unrestricted network as internal secrets-bearing services.

## 20.4 Prompt injection defenses

Page text, HTML comments, alt text, metadata, scripts, links and retrieved third-party content are untrusted. The LLM prompt must explicitly say these are data only.

- Do not give an agent a shell tool.
- Do not allow the agent to open arbitrary URLs.
- Do not allow the agent to read `.env` or local files.
- Do not place secrets in prompts.
- Do not execute model-generated code.
- Tool functions must accept typed parameters and validate them.
- Limit tool calls and recursion depth.
- Store only minimum page context needed.
- Add prompt-injection test fixtures.

## 20.5 File and artifact security

- Generate random storage object IDs.
- Store artifacts outside public static frontend folders.
- Authorize every download.
- Sanitize filenames.
- Enforce content type and size limits.
- Do not serve captured HTML as a live page on the same origin as the app.
- If HTML preview is implemented, use a separate isolated origin with restrictive CSP or display escaped source only.
- Set retention/deletion rules for scan artifacts.

## 20.6 Secrets

- `.env` is local and ignored.
- `.env.example` contains variable names and empty placeholders only.
- GitHub Actions uses repository secrets only for a future deployment job, not for normal tests.
- `GITHUB_TOKEN` should use minimum permissions.
- Never print environment variables to debug logs.
- Rotate any key accidentally committed; removing it from a later commit does not make it safe.

## 20.7 CORS, CSRF and browser cookies

- Allow only the configured frontend origin(s).
- Do not use `*` with credentials.
- If using cookie-based auth, implement CSRF protection on state-changing requests.
- Use `Secure` cookies in HTTPS deployment.
- Use `HttpOnly` and appropriate `SameSite` policy.
- Validate `Origin` where appropriate.
- Avoid storing long-lived refresh credentials in localStorage.

## 20.8 Data minimization

- Do not ingest authenticated/private pages in MVP.
- Do not support user-provided login cookies.
- Do not store full page bodies by default.
- Sanitize and bound HTML snippets.
- Redact query parameters that may carry tokens or personal data before persistence where possible.
- Document the artifact retention period.
- Provide a project/scan deletion workflow.

---

# 21. Testing strategy and test data

Testing is not a final activity. Each phase adds tests and all tests run in CI.

## 21.1 Test pyramid

### Unit tests

Fast tests for pure logic:

- URL normalization and policy.
- IP range classification.
- Domain match logic.
- Finding normalization.
- Fingerprint generation.
- Severity grouping.
- RAG chunking and metadata extraction.
- RRF ranking.
- Citation validator.
- Pydantic schemas.
- Remediation patch allowlist.
- State routing decisions.
- Scan status transition policy.

### Integration tests

Use isolated test containers or CI services for:

- PostgreSQL repositories and migrations.
- Auth/session persistence.
- Qdrant collection upsert/query.
- Redis/Celery enqueue and task execution.
- LangGraph checkpoint persistence.
- SSE event persistence/replay.
- Report storage and download authorization.

### Scanner tests

Use local fixture websites, never live third-party websites as the only test source. Verify real axe-core behavior against known fixtures.

### Frontend component tests

Use Vitest + React Testing Library for:

- auth forms
- project form
- scan form validation
- findings filters
- status badges
- remediation approval/rejection states
- citation rendering
- empty/error/loading states

### End-to-end tests

Use Playwright to test the AccessGuard frontend against a test backend/database and scan fixture site. Test:

1. Register/login.
2. Create project.
3. Test-mode domain verification.
4. Start scan.
5. Observe progress.
6. Open finding.
7. Request mock-provider remediation.
8. Approve/reject.
9. Run snapshot validation.
10. Export report.
11. Logout.

### Security tests

Cover SSRF, IDOR, injection, artifact authorization, CORS/CSRF policy, oversized input, rate limits and unsafe patch operations.

## 21.2 Required test fixtures

Create deterministic local HTML files/served pages covering:

- Informative image without alt.
- Decorative image with appropriate empty alt.
- Form control without accessible name.
- Button with no accessible name.
- Low contrast text.
- Valid contrast control.
- Incorrectly nested or missing landmarks.
- Invalid ARIA attribute/use.
- Keyboard focus visibility test case (manual/limited automated handling).
- Delayed-rendered element.
- Cross-origin link.
- Redirect endpoint.
- Oversized document.
- Prompt injection text such as “ignore previous instructions” embedded in page content.

For each fixture, document expected axe rule IDs and expected result classification. Do not make expected results depend on uncertain CSS/browser behavior without pinning viewport and browser version.

## 21.3 Test database policy

- Use a separate test database/schema.
- Never point tests at the developer's real database.
- Clean up created rows/artifacts after tests.
- Use transaction rollback fixtures where possible.
- Test Alembic from empty database.
- Add at least one migration-upgrade test from previous version once multiple migrations exist.

## 21.4 Test commands

From `backend/`:

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
uv run pytest tests/unit -q
uv run pytest tests/scanner -q
uv run pytest tests/rag -q
uv run pytest tests/agents -q
uv run pytest tests/security -q
uv run pytest tests/integration -q
uv run pytest --cov=app --cov-report=term-missing
```

From `frontend/`:

```powershell
npm run lint
npm run format:check
npx tsc --noEmit
npm run test
npm run build
```

Full local environment:

```powershell
docker compose up -d postgres redis qdrant
cd backend
uv run alembic upgrade head
uv run pytest -q
cd ..\frontend
npm run test
npm run build
```

Exact commands may be wrapped in scripts, but preserve these independent checks and document the canonical one-command test command if created.

## 21.5 Test quality rules

- Do not mock the function under test so heavily that the test proves nothing.
- Use mocks for provider/network boundaries, not for deterministic core logic.
- Keep at least one real axe-core browser test against local fixtures.
- Keep at least one real Qdrant retrieval integration test.
- Keep live provider tests optional and explicitly marked `requires_api_key`.
- Mark network-dependent tests separately; default CI must be deterministic and not rely on live websites.
- Avoid flaky fixed sleeps; use Playwright condition/event waits.
- Capture logs and screenshots for failed E2E tests as CI artifacts, but do not upload private production scan data.

---

# 22. RAG and agent evaluation

This section is a formal evaluation plan, not a promise of scores.

## 22.1 RAG evaluation dataset

Create approximately 100–150 human-reviewed retrieval cases before claiming advanced RAG quality. Start with 50 while implementing; expand as the pipeline stabilizes.

Each JSONL row should contain:

```json
{
  "case_id": "rag-0001",
  "query": "What does WCAG say about text alternatives for informative images?",
  "expected_criterion_ids": ["1.1.1"],
  "relevant_chunk_ids": ["wcag22_sc_1_1_1_normative"],
  "expected_source_domains": ["w3.org"],
  "should_abstain": false,
  "reviewer_notes": "Criterion and source checked against official W3C text."
}
```

Use questions covering:

- Exact criterion ID lookups.
- Plain-language criterion questions.
- axe rule descriptions.
- ARIA patterns.
- Conflicting or ambiguous contexts.
- Questions where the evidence is insufficient.
- Questions containing irrelevant prompt-injection text.

Split by topic/criterion into development and held-out test subsets to reduce near-duplicate leakage. Keep the final held-out set unchanged while tuning.

## 22.2 Retrieval metrics

Calculate:

- `Recall@5`: fraction of expected relevant chunks found among top five.
- `Precision@5`: fraction of top five retrieved chunks labeled relevant.
- `MRR`: reciprocal rank of first relevant chunk.
- `nDCG@5`: ranking quality with graded relevance if available.
- `Criterion Hit Rate@5`: whether at least one relevant expected criterion appears in top five.
- `Citation Source Accuracy`: whether the source URL/title points to the expected authoritative source.

Compare at least:

1. Dense only.
2. Lexical only.
3. Hybrid RRF.
4. Hybrid RRF + reranker.

Use the same query set and the same source corpus. Report latency and memory alongside relevance. Do not assume hybrid or reranking is automatically better; select based on measured held-out results.

## 22.3 Generation metrics

For a sample of generated answers, label:

- Correctness (human rubric).
- Faithfulness to evidence.
- Citation validity.
- Criterion mapping correctness.
- Actionability of recommendation.
- Appropriate abstention.
- Unsupported claim rate.

RAGAS or another LLM-as-judge framework can be used as a supporting signal, but do not use it as the only ground truth. Keep a manually reviewed sample and describe evaluator model/provider in the report.

## 22.4 Agent evaluation dataset

Create at least 30–50 scenarios with known input finding, evidence and expected behavior. Include:

- Missing alt text where image context is informative.
- Decorative image case where empty alt is appropriate.
- Missing form label.
- Ambiguous image purpose requiring manual review.
- Missing accessible name on button.
- Low contrast finding.
- `incomplete` axe result.
- No relevant RAG evidence.
- Malicious prompt text inside HTML.
- Invalid model JSON.
- Provider rate limit.
- Provider timeout.
- Patch with unsafe event-handler attribute.
- Patch referencing nonexistent evidence.
- Approved and rejected user decisions.

Metrics:

- Schema-valid output rate.
- Evidence-reference validity.
- Criterion mapping correctness.
- Review policy rejection rate for unsafe proposals.
- Snapshot validation success on known deterministic cases.
- Regression introduction count.
- Human approval acceptance rate after a real pilot (do not fabricate before pilot).
- End-to-end latency and provider call count.

## 22.5 Targets

Targets are engineering goals, not achieved facts:

- RAG Recall@5: target 0.85 or higher on the held-out set.
- Citation source accuracy: target 0.95 or higher.
- Pydantic schema-valid response after bounded retry: target 0.95 or higher.
- Zero accepted proposals containing prohibited patch operations in the security test set.
- Zero unauthorized cross-user resource reads in IDOR tests.
- All documented SSRF unit cases blocked at application policy level; production network egress tests must also pass before public arbitrary scanning is enabled.

If the target is not reached, report actual measurements and discuss limitations. Do not manipulate the test set or thresholds to claim success.

## 22.6 Benchmark report format

Write `docs/EVALUATION.md` with:

- Dataset construction and annotation method.
- Corpus/source versions.
- Model and embedding versions.
- Retrieval configuration.
- Metrics definitions.
- Dense/lexical/hybrid/reranked comparison table.
- Latency and resource measurement method.
- Agent scenario results.
- Human-review sample details.
- Failure examples and limitations.
- Date of evaluation.

---

# 23. Docker and local deployment

## 23.1 Compose services

Initial local Compose services:

- `frontend`
- `api`
- `worker`
- `postgres`
- `redis`
- `qdrant`

Playwright browser dependencies may live in the worker/scanner image. The worker must run with non-root permissions and conservative resource limits. Keep production egress/network separation as described in Section 20.

Do not use `latest` image tags in the release Compose file. Pin tested major/minor tags and document upgrade procedure.

## 23.2 Dockerfiles

### Backend/worker image

- Use a slim Python 3.12 base compatible with Playwright browser dependencies.
- Install OS dependencies only as needed.
- Install Python dependencies from the lockfile.
- Install Chromium browser matching the installed Playwright package.
- Copy the local axe-core bundle from `tools/axe/node_modules/axe-core/axe.min.js`.
- Copy backend source.
- Run as non-root user.
- Use separate commands for API and worker services.
- Do not bake `.env` or keys into the image.
- Add health check appropriate to each service.

### Frontend image

Use multi-stage build:

1. Node builder installs from package lock and runs production build.
2. Minimal static web server serves `dist/` with SPA fallback and security headers.

For local development, a Vite dev server is fine. For deployment, serve the compiled static build rather than running the dev server.

## 23.3 Compose file requirements

- Named volumes for PostgreSQL and Qdrant data.
- Health checks for PostgreSQL, Redis and Qdrant.
- `depends_on` with health conditions where supported; remember container start order is not the same as application readiness.
- Internal service DNS names.
- No public port for PostgreSQL or Redis in production configuration.
- Expose API/frontend ports only as needed.
- Environment variables from `.env` locally, secrets via deployment secret manager in production.
- Restrictive network separation and scanner egress rules.
- Resource limits where Compose/deployment platform supports them.
- `restart` policies appropriate to local vs deployment.

## 23.4 Local commands

At repository root:

```powershell
Copy-Item .env.example .env
# Edit .env locally and set DATABASE_URL, JWT_SECRET_KEY and other local values.
docker compose config
docker compose build
docker compose up -d postgres redis qdrant
docker compose ps
```

Run migrations from a one-off backend container or local virtual environment:

```powershell
docker compose run --rm api alembic upgrade head
```

Start the full stack:

```powershell
docker compose up -d --build
```

Inspect services:

```powershell
docker compose ps
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f frontend
```

Stop without deleting persistent data:

```powershell
docker compose down
```

Reset local development volumes only when the user explicitly intends to erase local data:

```powershell
docker compose down -v
```

Never run the `down -v` command automatically as a troubleshooting step. It deletes database/vector data.

## 23.5 First-run initialization

Document a single repeatable setup script or command sequence that:

1. Waits for PostgreSQL/Redis/Qdrant readiness.
2. Runs Alembic migrations.
3. Ensures the Qdrant collection exists.
4. Runs WCAG knowledge ingestion if the collection is empty or explicitly requested.
5. Creates no default production user/password.
6. Prints URLs and health status.

Knowledge ingestion should be an explicit command or an idempotent one-time initialization task; do not download/re-embed the entire corpus on every API restart.

---

# 24. GitHub repository management

## 24.1 Repository naming and metadata

Repository name: `AccessGuard-AI`.

Description:

`AI-assisted web accessibility auditing and remediation guidance using Playwright, axe-core, LangGraph and grounded WCAG 2.2 RAG.`

Topics:

`accessibility`, `wcag`, `axe-core`, `playwright`, `agentic-ai`, `langgraph`, `rag`, `fastapi`, `react`, `qdrant`, `postgresql`, `docker`.

The README must explain that automated scanning does not certify WCAG conformance.

## 24.2 Branch policy

Use `main` as the primary branch. For this single-developer build, direct commits to `main` are acceptable. If Antigravity creates temporary work branches, merge them back to `main` with the planned commit history preserved. Do not create unnecessary permanent branches.

## 24.3 Commit policy

- 51 planned commits over 17 phases.
- Three commits per phase.
- Use the exact or semantically equivalent messages in Section 29.
- Do not use the prohibited words `feat`, `fix`, `chore` in any commit message.
- Commit only after phase tests pass.
- Do not combine unrelated phases.
- Do not add generated artifacts to a code commit.
- Ensure every commit leaves the repository in a coherent state.

## 24.4 Suggested commit command

```powershell
git status --short
git add <specific-paths>
git diff --cached --check
git diff --cached --stat
git commit -m "scanner: establish browser runtime and audit fixtures"
git status --short
```

Use specific paths rather than `git add .` when there is a risk of staging `.env` or local artifacts. Before every commit, inspect staged diff and scan for secrets.

## 24.5 GitHub setup

After local repository and first phase are ready:

```powershell
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/AccessGuard-AI.git
git branch -M main
git push -u origin main
```

If `origin` already exists, inspect it with `git remote -v`; do not blindly overwrite it.

Enable repository settings:

- Main branch is default.
- Pull request checks required if using PR workflow.
- Secret scanning/push protection if available on the account/repository plan.
- Dependabot alerts if available.
- GitHub Actions enabled.
- Add a repository description/topics.

Never store provider keys in repository variables if the application can use local `.env`; add deployment secrets only when a deployment workflow genuinely needs them.

## 24.6 Releases and tags

After all acceptance tests pass:

```powershell
git tag -a v1.0.0 -m "AccessGuard AI first complete release"
git push origin v1.0.0
```

Do not tag an incomplete, untested build. Create a GitHub Release with verified screenshots and actual features only.

---

# 25. GitHub Actions CI/CD

## 25.1 Required CI workflow

Run on:

- push to `main`
- pull requests targeting `main`

Jobs:

1. Backend lint/format/type checks.
2. Backend unit tests.
3. PostgreSQL/Qdrant/Redis integration tests.
4. Frontend lint/type checks/tests/build.
5. Scanner fixture tests with Playwright and axe-core.
6. Security tests.
7. Docker build.
8. Optional deployment after a successful main-branch build and required secrets exist.

CI must not require Gemini/Groq keys. Use `MockLLMProvider` for default agent tests. A separate optional workflow can run live-provider smoke tests only when a repository secret is intentionally configured; the user should be aware this may consume provider quota.

## 25.2 GitHub Actions security

- Use `permissions:` with least privilege.
- Use `contents: read` for test jobs.
- Pin third-party actions to reviewed full commit SHAs where practical.
- Do not echo secrets.
- Do not run untrusted pull-request code with write permissions or secrets.
- Use dependency caching carefully.
- Upload test reports only if they contain no sensitive scan artifacts.
- Keep Docker image publishing separate from test jobs.

## 25.3 CI result requirements

A green workflow means:

- Ruff passes.
- Python tests pass.
- DB migrations pass against a clean test database.
- Frontend lint and type check pass.
- Frontend tests pass.
- Production frontend build passes.
- Scanner fixture tests pass.
- No prohibited patch operations are accepted in security tests.
- Docker images build successfully.

Do not say “all tests passed” if an integration job was skipped. Report skipped jobs explicitly.

## 25.4 Deployment workflow

Choose a hosting platform only after Docker local deployment works. The application must remain deployable as containers without depending on a specific provider.

Production deployment requirements:

- HTTPS.
- Secure cookies.
- Production secrets managed by platform secret store.
- Persistent PostgreSQL and Qdrant volumes/services.
- Redis service for background queue.
- Database migrations run as a one-off release job, not concurrently in every API replica.
- API and worker separate processes.
- Worker concurrency limited for memory and browser safety.
- Health checks and restart policy.
- Backup and restore documentation.
- Outbound scanner policy/firewall.
- Artifact storage with authorization and retention.
- CORS set to real frontend domain.
- Debug/docs configuration set appropriately.

Do not deploy public arbitrary URL scanning until SSRF/equivalent network egress controls are tested in the actual hosting environment.

---

# 26. Logging, monitoring and operational behavior

## 26.1 Structured logs

Use JSON structured logs in production. Include:

- timestamp
- level
- request_id
- user_id (internal UUID, not email)
- project_id/scan_id when applicable
- route/task name
- duration
- error_code

Do not log passwords, auth tokens, API keys, complete HTML pages, private query strings or entire LLM prompts by default.

## 26.2 Metrics

At minimum, measure:

- HTTP request count and latency.
- API error rates.
- Celery queue depth and task duration.
- Scan duration, pages succeeded/failed.
- axe execution duration.
- RAG retrieval duration and candidate counts.
- Provider latency/error/rate-limit counts.
- Agent duration by node.
- Validation pass/failure/manual-review counts.
- Database connection health.

Prometheus/Grafana is optional for the first release. Do not let monitoring infrastructure delay the core project. A simple `/health/ready`, structured logs and an internal diagnostics view are enough initially.

## 26.3 Failure behavior

- Browser crash: mark page failed; continue remaining eligible pages if time remains.
- Redis unavailable: reject new scans with a clear retryable error; do not create an indefinitely stuck pending scan.
- PostgreSQL unavailable: API readiness should fail; workers must not report success without persistence.
- Qdrant unavailable: scanner remains usable; AI knowledge retrieval reports unavailable.
- Embedding model unavailable: RAG health fails and gives exact model loading error; scanner remains usable.
- Gemini/Groq unavailable: findings remain accessible; AI explanation indicates provider unavailable.
- Report generation fails: scan remains completed; report request can be retried.
- Cancellation: stop discovering new pages and terminate browser work safely; persist cancellation status.

---

# 27. Reports, export and product documentation

## 27.1 PDF report contents

- Product name and report generation time.
- Project name and verified domain.
- Scan ID and target URL.
- Scan configuration, axe version and browser version.
- Pages attempted/succeeded/failed.
- Summary of automated violations by impact.
- Finding list with rule ID, description, affected URL, WCAG tags and axe help URL.
- Incomplete/manual review checks section.
- AI remediation proposals, clearly labeled as suggestions.
- Human decisions.
- Snapshot validation outcomes and limitations.
- Statement that automated testing does not establish full WCAG conformance.
- Official links for source material.

Do not include private user credentials or internal exception tracebacks.

## 27.2 JSON export

Provide a documented JSON export schema. Include schema version. Include only user-authorized scan data. Ensure that the exported report can be parsed and validated against a Pydantic report schema.

## 27.3 README and documentation

README must contain:

1. Name and description.
2. Problem statement.
3. What it does and does not do.
4. Feature list.
5. Screenshots (actual application screenshots only).
6. Architecture diagram.
7. Multi-agent workflow.
8. RAG retrieval/evaluation method.
9. Technology stack.
10. Local setup with commands.
11. `.env` configuration and API-key timing.
12. Docker setup.
13. Testing commands.
14. Security limitations.
15. Known limitations.
16. Roadmap.
17. License.

Create:

- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/SECURITY.md`
- `docs/EVALUATION.md`
- `docs/RUNBOOK.md`
- `docs/TECH_STACK.md`
- `docs/decisions/ADR-001-modular-monolith.md`
- `docs/decisions/ADR-002-scanner-security-boundary.md`
- `docs/decisions/ADR-003-rag-retrieval.md`

Documentation must match actual implementation. Remove obsolete instructions when commands change.

---

# 28. End-to-end development phases

The project is divided into 17 phases. Every phase below has a defined goal, implementation tasks, commands, tests, acceptance criteria and three planned commits. Antigravity must maintain `docs/PHASE_STATUS.md` with a checkbox for every phase and the actual commit hashes. Do not mark a phase complete until all required acceptance criteria are met.

## Phase 1 — Repository foundation and engineering conventions

**Goal:** Establish a clean, reproducible monorepo with formatting, linting and basic documentation.

### Tasks

1. Inspect the current working directory. If files already exist, inspect before overwriting.
2. Initialize Git `main` if not already initialized.
3. Create folder structure from Section 7.
4. Create complete `.gitignore` and `.env.example` with blank secrets.
5. Add README overview and limitations statement.
6. Add backend `pyproject.toml` and lock dependencies.
7. Create frontend Vite React TypeScript app and lock dependencies.
8. Add axe-core package under `tools/axe` and commit its lock.
9. Configure Ruff, ESLint, Prettier and TypeScript strict mode.
10. Add a small `/health/live` placeholder backend route and a simple frontend shell only if needed to validate toolchain; do not create fake product functionality.
11. Add `docs/PHASE_STATUS.md` and `docs/TECH_STACK.md`.

### Commands

Use Sections 8–9. Then:

```powershell
cd backend
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
cd ..\frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
cd ..
```

### Tests and gate

- All package managers resolve successfully.
- Frontend build succeeds.
- Backend lint/format checks succeed.
- No secrets or generated binary files are staged.
- `git status` is clean after commits.

### Commits

1. `project: establish AccessGuard monorepo structure`
2. `project: configure Python and TypeScript toolchains`
3. `docs: record initial architecture and development rules`

---

## Phase 2 — Backend core, configuration and API foundation

**Goal:** Create a reliable FastAPI application structure before implementing domain features.

### Tasks

1. Implement `Settings` using Pydantic Settings.
2. Implement application factory/lifespan.
3. Add API v1 router.
4. Add `/health/live` and `/health/ready`.
5. Add CORS from explicit environment origins.
6. Add request ID middleware and structured logging.
7. Add centralized exception handlers and standard error schema.
8. Add API dependency wiring for database and current user placeholders.
9. Add OpenAPI metadata, app version and environment labels.
10. Configure test settings and dependency overrides.
11. Add a minimal test app using FastAPI TestClient or HTTPX ASGI transport.
12. Create `docs/API.md` initial conventions.

### Commands

```powershell
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

Run tests:

```powershell
uv run pytest tests/unit -q
uv run ruff check app tests
uv run ruff format --check app tests
```

### Tests and gate

- Startup does not require Gemini/Groq keys with `LLM_PROVIDER=mock`.
- Invalid settings fail with a useful safe message.
- CORS rejects unlisted origins.
- Request IDs appear in responses and logs.
- Health endpoints correctly distinguish liveness from readiness.
- Error responses do not leak stack traces.

### Commits

1. `api: establish FastAPI application and configuration`
2. `api: add health checks middleware and error handling`
3. `tests: cover API startup configuration and health routes`

---

## Phase 3 — PostgreSQL, SQLAlchemy, Alembic and authentication

**Goal:** Establish database persistence and secure account access.

### Tasks

1. Configure async SQLAlchemy engine/session and safe connection lifecycle.
2. Define declarative base and model conventions.
3. Implement users and refresh sessions.
4. Implement Alembic with async-compatible configuration or a documented sync migration URL.
5. Create first migration and test upgrade from empty database.
6. Implement Argon2 password hashing.
7. Implement register/login/refresh/logout/me routes.
8. Implement access token validation and refresh session rotation/revocation.
9. Add rate-limit boundary for login/register; if Redis-based rate limiting is not ready, implement a clear adapter and add Redis implementation in a later phase.
10. Ensure request models never serialize password hashes.
11. Implement test database fixtures and user factories.

### Commands

Start infrastructure locally:

```powershell
# From repository root; Compose file may be minimal in this phase.
docker compose up -d postgres redis
docker compose ps
```

Backend:

```powershell
cd backend
uv run alembic upgrade head
uv run alembic current
uv run pytest tests/unit -q
uv run pytest tests/integration -q
```

### Tests and gate

- Registration creates a normalized unique email.
- Password is hashed, never stored in plaintext.
- Incorrect password is rejected.
- Access token expiry is checked.
- Refresh token rotation/revocation is checked.
- Logout invalidates refresh session.
- User A cannot use User B's refresh session.
- Migration can create schema from empty PostgreSQL.
- All timestamps are timezone-aware UTC.

### Commits

1. `database: add SQLAlchemy models and migration foundation`
2. `auth: implement account registration and session lifecycle`
3. `tests: verify authentication and database isolation`

---

## Phase 4 — Projects, domain ownership and project authorization

**Goal:** Users can create and manage projects and prove domain control before scanning.

### Tasks

1. Implement project and domain-verification models.
2. Add migration for projects and verification records.
3. Implement project create/list/read/update/archive endpoints.
4. Add ownership checks in service/repository layer.
5. Implement DNS TXT token generation and verification service.
6. Add configurable verification expiry and bounded DNS timeouts.
7. Add verification status API and response schema.
8. Add test-only DNS resolver injection.
9. Build unit tests for exact domain parsing, punycode/IDNA and subdomain policy.
10. Add frontend API types only after backend response schema is stable; the full UI comes later.

### Commands

```powershell
cd backend
uv run alembic revision --autogenerate -m "add projects and domain verification"
uv run alembic upgrade head
uv run pytest tests/unit tests/integration -q
```

### Tests and gate

- User can create a project.
- Project list returns only current user's projects.
- Direct access to another user's project returns 404 or consistent authorization failure.
- DNS token is random and expires.
- Correct TXT record verifies; absent/wrong TXT does not.
- Domain mismatch or unverified domain cannot create a scan.
- DNS network timeout returns retryable verification error.

### Commits

1. `projects: add project persistence and ownership rules`
2. `security: implement DNS domain verification workflow`
3. `tests: cover project isolation and domain verification`

---

## Phase 5 — Scanner target policy and crawler foundation

**Goal:** Safely validate eligible targets and discover bounded same-origin pages.

### Tasks

1. Implement URL normalization utility.
2. Implement public-IP classification and hostname resolution policy.
3. Implement verified-domain match policy.
4. Implement redirect/request destination validation.
5. Implement bounded Playwright browser context configuration.
6. Implement same-origin breadth-first crawler.
7. Implement timeouts, maximum pages, maximum depth, response size and scan deadline.
8. Implement cancellation and cleanup paths.
9. Implement scanner result schemas and error classification.
10. Build local test fixture server for scanner tests.
11. Add test-only loopback allowance, inaccessible in production settings.
12. Document scanner network threat model.

### Commands

```powershell
cd backend
uv run playwright install chromium
uv run pytest tests/unit -q
uv run pytest tests/security -q
uv run pytest tests/scanner -q
```

### Tests and gate

- Public verified test domain mock passes policy.
- Loopback/private/link-local/reserved targets are blocked.
- Redirect to blocked IP is blocked.
- Cross-origin links are not followed by default.
- Duplicate URLs are removed.
- Page/depth/time limits are enforced server-side.
- Browser timeout/cancellation cleans up context/process.
- Test-only loopback exception cannot be enabled when `APP_ENV=production`.

### Commits

1. `scanner: implement URL normalization and target policy`
2. `scanner: add bounded Playwright crawler`
3. `security: cover SSRF redirect and crawl boundary cases`

---

## Phase 6 — axe-core integration and finding persistence

**Goal:** Detect real accessibility findings on local fixture websites and store normalized results.

### Tasks

1. Install/pin axe-core in `tools/axe`.
2. Add axe version discovery and local bundle path resolution.
3. Inject axe-core with Playwright `page.add_script_tag(path=...)`.
4. Run configured rule tags and store effective tag profile.
5. Normalize violations, passes and incomplete results.
6. Extract nodes, targets, snippets and failure summaries with length bounds.
7. Implement impact normalization and WCAG tag parsing.
8. Implement finding fingerprinting and per-page deduplication.
9. Add `scan_pages`, `findings` and `finding_nodes` migrations/models.
10. Implement scanner-to-persistence service.
11. Add deterministic fixtures and expected results documentation.
12. Save axe version and browser version on scan.

### Commands

```powershell
cd tools\axe
npm ci
cd ..\..
cd backend
uv run alembic revision --autogenerate -m "add scan pages and findings"
uv run alembic upgrade head
uv run pytest tests/scanner -q
uv run pytest tests/integration -q
```

### Tests and gate

- Scanner executes locally bundled axe-core without public CDN.
- Known fixture has expected rule IDs.
- Incomplete results are not reported as confirmed violations.
- WCAG tags are preserved in full.
- Best-practice tags are not mislabeled as success criteria.
- HTML evidence is length-bounded and escaped in API/UI contracts.
- Finding fingerprint is stable for same fixture and changes when relevant context changes.
- Empty/clean fixture does not produce fake findings.

### Commits

1. `scanner: bundle axe-core and execute accessibility rules`
2. `database: persist normalized scan pages and findings`
3. `tests: verify axe results against deterministic website fixtures`

---

## Phase 7 — Celery background scans, progress events and cancellation

**Goal:** Make scans asynchronous and observable.

### Tasks

1. Configure Celery app with Redis broker and JSON task serialization.
2. Implement scan orchestration task with idempotent stage transitions.
3. Implement scan events table and migration.
4. Implement bounded progress payloads and sequence numbers.
5. Implement SSE endpoint with authorization and replay cursor.
6. Implement cancellation request and safe browser cleanup.
7. Add bounded retries for transient infrastructure errors only.
8. Add `completed_with_errors` state.
9. Add worker startup command and health checks.
10. Ensure AI is not automatically invoked for every finding; it remains user-triggered.

### Commands

```powershell
docker compose up -d postgres redis
cd backend
uv run celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
```

In another terminal, run API:

```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

### Tests and gate

- Creating scan returns quickly with queued status.
- Worker updates stages and persists events.
- SSE replays events after last sequence ID.
- User cannot open another user's scan event stream.
- Duplicate task delivery does not duplicate all findings.
- Transient errors retry within configured limit.
- Permanent policy errors do not retry.
- Cancellation stops remaining work and reaches terminal state.

### Commits

1. `workers: add Celery scan orchestration`
2. `api: stream persisted scan progress events`
3. `tests: verify job retries cancellation and event replay`

---

## Phase 8 — WCAG source ingestion and local embedding pipeline

**Goal:** Build the WCAG knowledge corpus without needing Gemini/Groq.

### Tasks

1. Create `knowledge_base/sources.yaml` with official W3C/ARIA references.
2. Implement bounded official-source fetcher.
3. Implement HTML parsing and extraction of headings/sections.
4. Implement criterion-aware chunker and metadata schema.
5. Implement stable content hashes and idempotent ingestion.
6. Add knowledge source/chunk database models and migration.
7. Implement local Sentence Transformers embedder.
8. Create Qdrant collection with correct vector dimension and cosine distance.
9. Implement vector upsert/delete/reindex behavior.
10. Add CLI dry-run and source-specific ingestion controls.
11. Add source metadata/chunk count reporting.
12. Add a small initial evaluation JSONL with hand-checked examples.

### Commands

```powershell
cd backend
uv run alembic revision --autogenerate -m "add WCAG knowledge tables"
uv run alembic upgrade head
uv run python scripts/ingest_knowledge.py --dry-run --sources ..\knowledge_base\sources.yaml
uv run python scripts/ingest_knowledge.py --sources ..\knowledge_base\sources.yaml
```

### Tests and gate

- Ingestion rejects non-allowlisted source domains.
- Fetch has time/size limits.
- Parser extracts headings and criterion IDs from verified source markup.
- Chunk IDs and content hashes are deterministic.
- Second ingestion produces no duplicates.
- Embedding dimension matches Qdrant collection.
- Qdrant point references corresponding PostgreSQL chunk.
- No provider API key is required.

### Commits

1. `rag: ingest official WCAG and WAI source material`
2. `rag: add criterion-aware chunking and local embeddings`
3. `tests: verify ingestion idempotency and vector indexing`

---

## Phase 9 — Hybrid retrieval, citations and baseline RAG evaluation

**Goal:** Deliver traceable knowledge retrieval before adding generative answers.

### Tasks

1. Implement dense Qdrant retriever.
2. Implement lexical PostgreSQL FTS or BM25 retriever.
3. Implement stable Reciprocal Rank Fusion.
4. Implement optional cross-encoder reranker behind config.
5. Implement evidence object and citation validator.
6. Implement `/knowledge/search` endpoint.
7. Build 50+ manually reviewed retrieval cases initially.
8. Implement evaluation script for Recall@5, Precision@5, MRR and nDCG@5.
9. Compare dense, lexical, hybrid and hybrid+reranker with same dataset.
10. Record actual results in `docs/EVALUATION.md`.
11. Add abstention behavior when no adequate evidence is found.
12. Ensure source link is taken from database metadata, never model output.

### Commands

```powershell
cd backend
uv run pytest tests/rag -q
uv run python scripts/evaluate_rag.py --dataset ..\knowledge_base\evaluation\retrieval_cases.jsonl
```

### Tests and gate

- Exact criterion-ID queries can retrieve the corresponding criterion.
- Plain-language paraphrase queries retrieve relevant evidence.
- RRF order is deterministic.
- Citation ID must exist in the database.
- Model/user cannot inject arbitrary citation URL.
- Empty/irrelevant query can abstain.
- Evaluation output includes dataset version and actual metric values.
- No live LLM API key is needed.

### Commits

1. `rag: implement dense and lexical hybrid retrieval`
2. `rag: add citation validation and retrieval benchmarks`
3. `docs: record measured baseline retrieval evaluation`

---

## Phase 10 — Live LLM provider integration (**API key is needed here**)

**Goal:** Add live model-backed explanations and structured outputs while preserving a no-key test path.

### User interaction required at start of this phase

Tell the user:

> “The scanner and WCAG retrieval are now working without paid API access. AccessGuard is ready for live AI explanation/remediation. Please choose Gemini (recommended default) or Groq and add the API key to your local `.env` file. Do not paste the key into chat or commit it to GitHub.”

Give current official provider-console instructions and verify current model availability at that time. Do not assume a free quota or a model ID from an old tutorial.

### Tasks

1. Implement `LLMProvider` protocol/interface.
2. Implement deterministic `MockLLMProvider`.
3. Implement Gemini adapter.
4. Implement Groq adapter as optional alternative.
5. Implement provider factory and configuration validation.
6. Add typed structured-output schemas.
7. Add bounded retries for rate limit/network/server errors.
8. Add provider timeout and request size limits.
9. Add prompt version metadata.
10. Add sanitized provider errors and latency metadata.
11. Keep provider selection explicit; no silent switching.
12. Add optional live smoke test, excluded from default CI unless key is explicitly configured.

### Commands

```powershell
# In backend environment
uv run python -c "from app.ai.providers.factory import get_provider; print(type(get_provider()).__name__)"
uv run pytest tests/agents tests/unit -q
```

After the user locally adds a key:

```powershell
# Do not print the key. Run a smoke test that prints only provider/model and success/failure.
uv run python scripts/provider_smoke_test.py
```

### Tests and gate

- App starts with `LLM_PROVIDER=mock` and no keys.
- Selecting Gemini without key produces a clear configuration error, not startup crash for unrelated scanner routes.
- Selecting Groq without key produces equivalent error.
- Mock provider returns deterministic Pydantic-valid output.
- Invalid JSON/schema is rejected.
- Rate limit uses bounded retry/backoff.
- Secret is never included in logs or error response.
- Live smoke test passes only if user provided a valid key; otherwise mark blocked, not passed.

### Commits

1. `ai: define provider abstraction and deterministic mock model`
2. `ai: integrate configured Gemini and Groq adapters`
3. `tests: validate structured outputs retries and secret handling`

---

## Phase 11 — LangGraph analysis and remediation proposal workflow

**Goal:** Build the stateful multi-agent pipeline using the real RAG evidence and optional live LLM.

### Tasks

1. Define typed graph state.
2. Implement graph builder and conditional routing.
3. Implement context-loading node.
4. Implement RAG retrieval node using the existing retrieval service.
5. Implement finding analysis node.
6. Implement remediation proposal node.
7. Implement deterministic review/schema policy node.
8. Implement evidence sufficiency threshold/abstention.
9. Implement prompt injection safe context formatting.
10. Persist agent execution metadata.
11. Add provider/model/prompt version metadata.
12. Make every graph node unit-testable with injected fake services.
13. Add at most one bounded proposal regeneration after policy rejection.
14. Keep approval/validation node hooks ready for Phase 12.

### Tests and gate

- Graph routes to manual review when evidence is insufficient.
- Graph never invents a criterion outside supplied evidence/finding tags.
- All citations map to stored chunks.
- Structured proposal matches Pydantic schema.
- Malicious page content does not change system instruction or trigger tool execution.
- Provider failure leaves original finding accessible.
- Agent runs are persisted without secrets or hidden reasoning.
- Tests work with mock provider; live smoke tests are optional.

### Commits

1. `agents: build typed LangGraph investigation workflow`
2. `agents: generate evidence-grounded remediation proposals`
3. `tests: cover routing grounding and prompt-injection scenarios`

---

## Phase 12 — Human approval, safe patch policy and snapshot validation

**Goal:** Complete the responsible remediation lifecycle.

### Tasks

1. Add remediation and approval tables/migrations.
2. Add approval/rejection endpoints with ownership checks.
3. Integrate LangGraph checkpoint persistence and interrupt/resume.
4. Define constrained patch operations and allowlist.
5. Reject unsafe attributes, scripts, event handlers and arbitrary code.
6. Implement sanitized DOM snapshot storage and retrieval.
7. Implement isolated snapshot reconstruction with remote loading disabled.
8. Apply only allowed operations to the isolated snapshot.
9. Run local axe-core validation.
10. Compare original and new violation fingerprints.
11. Persist validation details and patch/snapshot hashes.
12. Label result as snapshot validation; do not claim live site fixed.
13. Add manual-review path for unsupported/ambiguous cases.

### Tests and gate

- Non-owner cannot approve/reject.
- Duplicate/stale approval is rejected safely.
- Graph resumes after approval using persisted checkpoint.
- Reject decision finalizes without validation.
- Unsafe patch operation is rejected.
- Valid deterministic patch resolves known fixture violation in snapshot.
- Invalid patch is recorded as failed.
- New violations are listed and prevent a pass.
- Snapshot does not load remote scripts/resources.
- Live website is never modified.

### Commits

1. `remediation: add human approval and graph checkpoint persistence`
2. `security: constrain patch operations and validate isolated snapshots`
3. `tests: verify approval resume and remediation regression handling`

---

## Phase 13 — Frontend shell, authentication and design system

**Goal:** Build the product's visual foundation and authenticated routing.

### Tasks

1. Implement app shell with sidebar/topbar/main content.
2. Implement selected design tokens, fonts, spacing, borders and status colors.
3. Implement React Router routes and protected route behavior.
4. Implement centralized API client and auth session handling.
5. Implement login/register pages with React Hook Form + Zod.
6. Implement reusable buttons, inputs, cards, tables, dialogs, badges, skeletons and toasts.
7. Implement responsive sidebar/drawer.
8. Implement loading, error and empty-state components.
9. Implement profile/logout menu.
10. Add frontend tests for auth and shared UI components.
11. Run axe-core/Playwright basic audit against the frontend routes.

### Commands

```powershell
cd frontend
npm run lint
npx tsc --noEmit
npm run test
npm run build
npm run dev
```

### Tests and gate

- Login/register flow works against backend.
- Protected routes redirect correctly.
- Session expiry is handled safely.
- No API key appears in browser bundle/network storage.
- UI is responsive at desktop/tablet/mobile widths.
- Keyboard focus and labels are tested.
- No fake KPI values appear.

### Commits

1. `ui: establish AccessGuard design system and application shell`
2. `ui: implement authentication and protected navigation`
3. `tests: verify frontend auth responsive layout and accessibility baseline`

---

## Phase 14 — Projects, domain verification and scan management UI

**Goal:** Enable the user's complete project-to-scan workflow through the frontend.

### Tasks

1. Implement projects list and create form.
2. Implement project detail and domain verification instructions.
3. Implement DNS verification status and retry interaction.
4. Implement scan creation form with server-aligned hard limits.
5. Implement scans list and filter.
6. Implement scan detail page with progress states.
7. Implement SSE client with reconnect and event cursor behavior.
8. Implement pages scanned/failed counts and errors.
9. Implement cancellation confirmation.
10. Implement TanStack Query cache invalidation.
11. Add E2E tests with test DNS resolver and local fixture URL.

### Tests and gate

- Unverified project cannot start scan.
- Verified project can create scan.
- Scan progress updates without manual page refresh.
- SSE reconnect loads missed events.
- Cancel action is reflected from server state.
- Page list and failures appear accurately.
- User cannot navigate to another user's project by changing URL.

### Commits

1. `ui: implement project creation and domain verification screens`
2. `ui: add scan creation history and real-time progress`
3. `tests: cover project and scan journeys in browser`

---

## Phase 15 — Findings, AI remediation, reports and knowledge UI

**Goal:** Complete the main product experience.

### Tasks

1. Implement findings explorer with filters/pagination.
2. Implement finding detail and safe HTML evidence display.
3. Display axe rule help link and stored WCAG tags.
4. Implement knowledge source page and evidence search.
5. Implement “Generate AI explanation/remediation” action.
6. Implement remediation detail with evidence citations and before/after snippets.
7. Implement approve/reject controls with reviewer notes.
8. Implement validation result history and clear snapshot-only label.
9. Implement reports list and PDF/JSON download.
10. Implement dashboard cards/charts entirely from real API aggregations.
11. Implement scan history comparison with immutable scan snapshots.
12. Add UI tests and end-to-end remediation/report flow.

### Tests and gate

- Findings filter correctly by rule, impact and criterion.
- Source citations use official stored URLs.
- Untrusted HTML is escaped, not executed.
- AI output is clearly labeled as a suggestion.
- Approval cannot be assumed before server response.
- Snapshot validation wording is accurate.
- Report is accessible only to owner.
- Dashboard displays correct aggregations from database fixtures.
- Responsive tables/cards remain usable.

### Commits

1. `ui: build findings explorer and evidence detail views`
2. `ui: add AI remediation review and report workflows`
3. `tests: verify findings approval validation and reporting journeys`

---

## Phase 16 — Docker hardening, CI/CD and deployment readiness

**Goal:** Make the complete system reproducible and deployable.

### Tasks

1. Complete backend Dockerfile with pinned Python environment and Playwright browser dependencies.
2. Copy local axe-core bundle into runtime image.
3. Complete frontend multi-stage Dockerfile.
4. Complete Compose services, named volumes, health checks and networks.
5. Ensure worker/scanner execution is isolated from provider secrets and database exposure as far as local architecture permits.
6. Add production egress policy/proxy deployment notes and safeguards.
7. Add CI workflow for lint/type/unit/integration/scanner/frontend/build/Docker.
8. Pin GitHub Actions to reviewed full commit SHAs where practical.
9. Add least-privilege workflow permissions.
10. Add container vulnerability/dependency scanning if available.
11. Add production `.env.example` comments and secret documentation.
12. Test clean-machine setup from clone to running stack.
13. Test database migration and backup/restore instructions.
14. Confirm production build serves SPA routes correctly.

### Commands

```powershell
# From repository root
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=200 api worker frontend
```

Run all test/lint commands from Sections 21 and 25. Validate container health and scan fixture through the full Compose stack.

### Tests and gate

- Clean Docker build succeeds.
- Compose services become healthy.
- Migrations run once and complete.
- Frontend/API/worker communicate correctly.
- Qdrant data persists across restart.
- PostgreSQL data persists across restart.
- API and worker logs contain no secrets.
- PostgreSQL/Redis are not publicly exposed in deployment profile.
- CI passes without provider keys.
- CI live-provider tests are marked skipped unless explicitly configured.
- Deployment documentation includes egress/SSRF requirements.

### Commits

1. `deploy: containerize frontend backend worker and data services`
2. `ci: automate backend frontend scanner and container checks`
3. `security: harden runtime configuration and deployment boundaries`

---

## Phase 17 — Full regression, documentation, release and final handoff

**Goal:** Verify the whole product, clean up technical debt and prepare the user to inspect it.

### Tasks

1. Run clean clone setup on a fresh directory or environment.
2. Run all database migrations from empty state.
3. Run knowledge ingestion and retrieval evaluation.
4. Run scanner fixture suite.
5. Run auth/project/scan/finding/remediation/report E2E suite.
6. Run security tests for IDOR, SSRF and unsafe patch policy.
7. Run frontend axe scan.
8. Run all lint/type/format/build checks.
9. Run Docker Compose startup/shutdown/persistence tests.
10. Review all TODO/FIXME and dead code.
11. Remove placeholder/mock data from normal runtime paths.
12. Check error messages and empty states.
13. Verify mobile responsiveness and keyboard navigation.
14. Review README, architecture/API/security/evaluation/runbook docs against actual code.
15. Capture genuine screenshots for README after user data is reset to clean demo fixtures.
16. Create a final release checklist and record actual results.
17. Tag `v1.0.0` only if all required acceptance criteria pass.
18. Produce a concise handoff report: local URL, start/stop commands, API-key status, tests passed/blocked, known limitations and next UI review actions.

### Final commands

```powershell
# Frontend
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run test
npm run build

# Backend
cd ..\backend
uv sync --all-groups
uv run ruff check app tests
uv run ruff format --check app tests
uv run pytest --cov=app --cov-report=term-missing
uv run alembic upgrade head

# Full stack
cd ..
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Also run the full E2E and security suite with infrastructure running.

### Tests and gate

- All mandatory CI jobs pass.
- Any skipped live-provider tests are documented as such.
- No unresolved critical/high security issue remains for the actual deployment scope.
- No secret or user-private scan data is committed.
- No fabricated metrics or sample-only claims are in README.
- Application starts from documented clean setup.
- Main user journey works end-to-end.
- Final Git history contains approximately 50 planned commits (51 in this plan).
- Tag/release only after verification.

### Commits

1. `tests: complete full system regression and security verification`
2. `docs: finalize setup architecture evaluation and operations guides`
3. `release: prepare AccessGuard AI first deployable version`

---

# 29. Required 51-commit plan

The list below contains exactly 3 planned commits for each of 17 phases = 51 commits total. Every commit message avoids the prohibited words specified in Section 1.6.

| # | Phase | Commit message |
|---:|---|---|
| 01 | 1 | `project: establish AccessGuard monorepo structure` |
| 02 | 1 | `project: configure Python and TypeScript toolchains` |
| 03 | 1 | `docs: record initial architecture and development rules` |
| 04 | 2 | `api: establish FastAPI application and configuration` |
| 05 | 2 | `api: add health checks middleware and error handling` |
| 06 | 2 | `tests: cover API startup configuration and health routes` |
| 07 | 3 | `database: add SQLAlchemy models and migration foundation` |
| 08 | 3 | `auth: implement account registration and session lifecycle` |
| 09 | 3 | `tests: verify authentication and database isolation` |
| 10 | 4 | `projects: add project persistence and ownership rules` |
| 11 | 4 | `security: implement DNS domain verification workflow` |
| 12 | 4 | `tests: cover project isolation and domain verification` |
| 13 | 5 | `scanner: implement URL normalization and target policy` |
| 14 | 5 | `scanner: add bounded Playwright crawler` |
| 15 | 5 | `security: cover SSRF redirect and crawl boundary cases` |
| 16 | 6 | `scanner: bundle axe-core and execute accessibility rules` |
| 17 | 6 | `database: persist normalized scan pages and findings` |
| 18 | 6 | `tests: verify axe results against deterministic website fixtures` |
| 19 | 7 | `workers: add Celery scan orchestration` |
| 20 | 7 | `api: stream persisted scan progress events` |
| 21 | 7 | `tests: verify job retries cancellation and event replay` |
| 22 | 8 | `rag: ingest official WCAG and WAI source material` |
| 23 | 8 | `rag: add criterion-aware chunking and local embeddings` |
| 24 | 8 | `tests: verify ingestion idempotency and vector indexing` |
| 25 | 9 | `rag: implement dense and lexical hybrid retrieval` |
| 26 | 9 | `rag: add citation validation and retrieval benchmarks` |
| 27 | 9 | `docs: record measured baseline retrieval evaluation` |
| 28 | 10 | `ai: define provider abstraction and deterministic mock model` |
| 29 | 10 | `ai: integrate configured Gemini and Groq adapters` |
| 30 | 10 | `tests: validate structured outputs retries and secret handling` |
| 31 | 11 | `agents: build typed LangGraph investigation workflow` |
| 32 | 11 | `agents: generate evidence-grounded remediation proposals` |
| 33 | 11 | `tests: cover routing grounding and prompt-injection scenarios` |
| 34 | 12 | `remediation: add human approval and graph checkpoint persistence` |
| 35 | 12 | `security: constrain patch operations and validate isolated snapshots` |
| 36 | 12 | `tests: verify approval resume and remediation regression handling` |
| 37 | 13 | `ui: establish AccessGuard design system and application shell` |
| 38 | 13 | `ui: implement authentication and protected navigation` |
| 39 | 13 | `tests: verify frontend auth responsive layout and accessibility baseline` |
| 40 | 14 | `ui: implement project creation and domain verification screens` |
| 41 | 14 | `ui: add scan creation history and real-time progress` |
| 42 | 14 | `tests: cover project and scan journeys in browser` |
| 43 | 15 | `ui: build findings explorer and evidence detail views` |
| 44 | 15 | `ui: add AI remediation review and report workflows` |
| 45 | 15 | `tests: verify findings approval validation and reporting journeys` |
| 46 | 16 | `deploy: containerize frontend backend worker and data services` |
| 47 | 16 | `ci: automate backend frontend scanner and container checks` |
| 48 | 16 | `security: harden runtime configuration and deployment boundaries` |
| 49 | 17 | `tests: complete full system regression and security verification` |
| 50 | 17 | `docs: finalize setup architecture evaluation and operations guides` |
| 51 | 17 | `release: prepare AccessGuard AI first deployable version` |

**Commit execution rules:**

- The table is a plan, not proof that commits exist. Create commits only after corresponding code/tests are genuinely complete.
- A commit should contain a coherent unit of work. If the implementation of one planned commit is too large, split internally only if total remains near the 50-commit target; do not combine multiple phase-end commits into one.
- Never create empty commits to reach 51.
- If a phase needs more than three commits for correctness, correctness takes priority; document the deviation and keep the final count near 50.
- Do not use `git commit --allow-empty`.

---

# 30. Definition of done and release checklist

## 30.1 Functional checklist

- [ ] Registration and login work.
- [ ] Refresh/logout behavior works.
- [ ] Project create/list/detail/archive works.
- [ ] Domain verification works with real DNS and a deterministic test resolver.
- [ ] Scan requires verified domain.
- [ ] Crawler uses strict limits.
- [ ] axe-core is locally bundled and version recorded.
- [ ] Real violations are persisted with source evidence.
- [ ] Incomplete checks are labeled correctly.
- [ ] Scan status/progress persists and streams.
- [ ] Findings filters and pagination work.
- [ ] WCAG corpus ingests idempotently.
- [ ] Dense and lexical retrieval work.
- [ ] RRF and citation validation work.
- [ ] Retrieval metrics are generated from labeled cases.
- [ ] Provider abstraction works without keys using mock provider.
- [ ] Live Gemini or Groq provider works after local key configuration.
- [ ] LangGraph analysis and remediation flow works.
- [ ] Insufficient evidence triggers abstention/manual review.
- [ ] Human approval/rejection is authenticated and persisted.
- [ ] Snapshot validation is isolated and accurately labeled.
- [ ] PDF and JSON reports download securely.
- [ ] Dashboard values are database-backed.

## 30.2 Quality checklist

- [ ] Ruff passes.
- [ ] Python tests pass.
- [ ] Frontend ESLint passes.
- [ ] TypeScript strict check passes.
- [ ] Vitest passes.
- [ ] Production frontend build passes.
- [ ] Scanner fixture tests pass.
- [ ] PostgreSQL migrations pass from empty database.
- [ ] Qdrant integration test passes.
- [ ] Celery task test passes.
- [ ] E2E journey passes.
- [ ] Frontend automated accessibility baseline passes or documented issues remain.
- [ ] Docker Compose clean startup succeeds.
- [ ] CI pipeline passes.

## 30.3 Security checklist

- [ ] No secrets in Git history.
- [ ] All database queries are tenant-scoped.
- [ ] IDOR tests pass.
- [ ] SSRF application tests pass.
- [ ] Production egress boundary is configured and tested before public scanning.
- [ ] Browser execution has no provider/database secrets.
- [ ] Prompt injection tests pass.
- [ ] Model output cannot execute arbitrary code.
- [ ] Patch operation allowlist is enforced.
- [ ] Artifact download ownership is enforced.
- [ ] CORS/CSRF/cookie policy is configured.
- [ ] Rate limits and scan limits are enforced.
- [ ] Logs do not contain secrets or raw private page content.

## 30.4 Deployment checklist

- [ ] Docker images build from lockfiles.
- [ ] Non-root runtime where feasible.
- [ ] Database and Qdrant volumes persist.
- [ ] PostgreSQL/Redis are not publicly exposed.
- [ ] HTTPS is enabled.
- [ ] Secure production secret configuration is used.
- [ ] Migrations run as a release step.
- [ ] Worker health and concurrency are configured.
- [ ] Scanner egress restrictions are active.
- [ ] Backup/restore instructions are tested.
- [ ] API docs/debug settings are appropriate for production.
- [ ] README has accurate startup and deployment commands.

---

# 31. Known risks and explicit non-goals

## 31.1 Known risks

1. **Automated testing coverage:** axe-core does not cover every WCAG criterion; manual review remains necessary.
2. **Dynamic sites:** single-page apps and authenticated flows can hide content from a basic crawler.
3. **Snapshot limitations:** isolated DOM snapshots do not fully reproduce the original app's scripts/state/responsive behavior.
4. **False positives/false negatives:** heuristic rules and browser environment influence outcomes.
5. **LLM hallucination:** controlled by source grounding, schemas, citations, validation and abstention, but not eliminated completely.
6. **Provider availability/cost:** model IDs, free quotas and rate limits change. Provider use is optional and configurable.
7. **Crawling security:** SSRF is an ongoing threat. Public arbitrary scanning requires actual egress restrictions, not only URL parsing.
8. **Storage costs:** screenshots/DOM snapshots can grow. Add retention, size limits and deletion.
9. **Local model performance:** embedding/reranking models consume RAM and can be slow on CPU.
10. **Accessibility law/compliance:** the product is a developer tool, not legal advice or a certification service.

## 31.2 Out of scope for first release

- Live production website modification.
- Automatic deployment of code patches.
- Automatic GitHub pull requests.
- Authenticated website scanning with stored user cookies.
- Full manual screen-reader audit replacement.
- Legal compliance certification.
- Enterprise SSO and complex RBAC.
- Billing/subscriptions.
- Multi-tenant enterprise organization hierarchy.
- Kubernetes.
- Microservices.
- Browser extension.
- Mobile app.
- Training a custom LLM.
- Building a proprietary foundation model.

These are intentionally excluded to keep the project finishable and technically defensible.

---

# 32. Future enhancements after the first complete release

Only after v1.0.0 is stable, consider:

1. GitHub repository connection with read-only permissions first.
2. Source-code-aware patch generation and branch/PR creation after explicit approval.
3. More browser engines and viewports.
4. Keyboard-only workflow testing helpers.
5. Manual audit checklist with reviewer evidence.
6. Historical trend analysis across many scans.
7. Organization/team workspaces and RBAC.
8. Additional official language resources.
9. Optional screen-reader test guidance.
10. Additional retrieval models if measured performance requires them.

Any feature that writes to a user's repository or website must use least-privilege permissions, explicit approval and an auditable action record.

---

# 33. Master Antigravity build prompt

Copy the prompt below into Antigravity after placing this document in the repository root as `AccessGuard_AI_Complete_Development_Blueprint.md` (or make it available in the Antigravity workspace). The prompt intentionally tells Antigravity to follow the specification, not reinterpret it.

```text
You are the lead full-stack engineer, AI engineer, test engineer and release engineer responsible for building AccessGuard AI.

FIRST ACTION:
1. Read the entire file `AccessGuard_AI_Complete_Development_Blueprint.md` from beginning to end.
2. Treat it as the authoritative implementation specification.
3. Inspect the actual repository and current Git status before modifying anything.
4. Create or update `docs/PHASE_STATUS.md` with all 17 phases and their acceptance gates.
5. Do not ask the user to choose the technology stack, architecture, folder layout, UI appearance, database, agent roles or development order. Those decisions are already made in the specification.

PRODUCT:
Build AccessGuard AI, a deployable AI-assisted web accessibility auditing and remediation guidance platform. It uses React + TypeScript + Vite, FastAPI, PostgreSQL, Redis/Celery, Playwright, locally bundled axe-core, local sentence-transformer embeddings, Qdrant, hybrid retrieval, LangGraph, and a configurable Gemini/Groq provider.

NON-NEGOTIABLE RULES:
- Follow all 17 phases in Section 28 in order.
- Do not skip tests, security, documentation or deployment steps.
- Do not make up test results, metrics, completed work, deployments or API responses.
- Do not create fake product dashboard data. Demo data is allowed only in explicit test/demo fixtures.
- Do not let an LLM detect accessibility violations. axe-core is the deterministic detector.
- Do not let the LLM invent WCAG criteria or URLs. All citations must come from stored RAG evidence.
- Do not execute model-generated code or arbitrary JavaScript.
- Do not modify a live website. Require human approval and validate only in an isolated snapshot/fixture in v1.
- Do not claim an automated scan certifies WCAG conformance.
- Implement tenant isolation, SSRF protections, URL/domain verification, prompt injection defenses, artifact authorization and safe patch allowlists.
- Keep API keys out of frontend bundles, Git, logs, tests and chat.
- Do not ask for Gemini/Groq keys until Phase 10. Phases 1–9 must work without any LLM API key and use `MockLLMProvider` for tests.
- Use the selected premium light SaaS UI in Section 17. The user will review and request UI changes after end-to-end completion.
- Keep `main` as the primary branch.
- Finish each phase with three meaningful commits according to Section 29, approximately 51 commits overall.
- NEVER include the words `feat`, `fix` or `chore` in any commit message. Use the messages in Section 29.
- Never create empty commits. Never force-push. Never commit `.env`, keys, generated private scans, model weights, browser binaries, database files or `node_modules`.

WORK METHOD:
For each phase:
1. State the phase number and goal in your work log.
2. Inspect actual repository state and identify prerequisites.
3. Implement the phase completely using the exact architecture and schema from the specification.
4. Add or update automated tests in the same phase.
5. Run all required commands for that phase.
6. Inspect failing logs and fix underlying defects. Do not weaken tests or disable lint rules to hide failures.
7. Run relevant regression tests from previous phases.
8. Update documentation and `docs/PHASE_STATUS.md` with actual commands and results.
9. Review `git diff`, check for secrets and generated files, then create 2–3 meaningful commits. Use the three planned messages for that phase where possible.
10. Report real commit hashes, changed modules, commands executed, test counts from actual output, skipped/blocked tests and remaining limitations.
11. Proceed to the next phase only after acceptance criteria pass.

API KEY TIMING:
At the start of Phase 10 only, pause and tell the user that live model-backed explanations require one provider key. Recommend Gemini as the default; allow Groq as an alternative. Explain that the user should create the key on the official provider console and add it to local `.env` as `GEMINI_API_KEY` or `GROQ_API_KEY`. Never ask them to paste the key into chat. Verify currently supported model IDs from current official provider documentation. If no key is supplied, continue with the mock provider and mark live-provider tests blocked; do not fabricate success.

UI:
Implement the Section 17 UI as written: premium light developer SaaS layout, clean sidebar, neutral surfaces, navy/slate text, restrained indigo/blue primary actions, accessible status colors, Inter/Geist typography, Lucide icons, real data only, responsive screens and keyboard support. Do not ask for design approval before building. The user will review after all phases are complete.

REPOSITORY AND COMMANDS:
Use Python 3.12, Node 22 LTS, Docker Compose v2. Use lockfiles and pinned container versions. Follow PowerShell commands in the specification for local development. Ensure `docker compose up -d --build` works after migrations and initialization. Make the README's actual setup steps match the tested commands.

FINAL RELEASE REQUIREMENTS:
Do not call the project complete until the full main user journey works:
register/login -> create project -> verify domain -> start scan -> crawl -> axe-core audit -> persist findings -> search WCAG evidence -> request AI explanation/remediation -> human approve/reject -> isolated snapshot validation -> export report.

Run the full unit, integration, scanner, RAG, agent, security, frontend, E2E, Docker and CI checks. Produce a final handoff with:
- repository URL and final commit/tag;
- how to start and stop locally;
- frontend/API URLs;
- whether a provider key is configured and which provider/model was actually tested (never reveal the key);
- exact test commands and real outcomes;
- actual RAG evaluation metrics, if measured;
- remaining known limitations;
- confirmation that no live site is modified and automated results are not WCAG certification;
- a request for the user to review the working website and provide UI/UX changes.

Start by reading the specification and assessing the repository. Do not generate the entire application in one uncontrolled code dump. Build it phase by phase with working tests and commits.
```

---

# 34. Official technical references

Use official documentation as the source of truth when implementing package-specific APIs. Package versions and provider model availability can change; verify current stable documentation during implementation rather than copying stale tutorials.

## Accessibility standards and tools

- W3C WCAG 2.2 Recommendation: <https://www.w3.org/TR/WCAG22/>
- W3C Understanding WCAG 2.2: <https://www.w3.org/WAI/WCAG22/Understanding/>
- W3C WCAG Techniques: <https://www.w3.org/WAI/WCAG22/Techniques/>
- WAI-ARIA Authoring Practices Guide: <https://www.w3.org/WAI/ARIA/apg/>
- axe-core repository and usage: <https://github.com/dequelabs/axe-core>
- Playwright Python documentation: <https://playwright.dev/python/>
- Playwright `page.add_script_tag`: <https://playwright.dev/python/docs/api/class-page>

## Backend and database

- FastAPI: <https://fastapi.tiangolo.com/>
- Pydantic: <https://docs.pydantic.dev/latest/>
- SQLAlchemy 2.x: <https://docs.sqlalchemy.org/en/20/>
- Alembic: <https://alembic.sqlalchemy.org/>
- Celery: <https://docs.celeryq.dev/en/stable/>
- Redis: <https://redis.io/docs/latest/>
- Qdrant: <https://qdrant.tech/documentation/>
- Qdrant hybrid search: <https://qdrant.tech/documentation/search-tuning/hybrid-search/>
- Qdrant hybrid retrieval with reranking: <https://qdrant.tech/documentation/tutorials-basics/reranking-hybrid-search/>

## Agent and model providers

- LangGraph overview: <https://docs.langchain.com/oss/python/langgraph/overview>
- LangGraph persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
- LangGraph interrupts/human-in-the-loop: <https://docs.langchain.com/oss/python/langgraph/interrupts>
- Google Gemini API quickstart: <https://ai.google.dev/gemini-api/docs/get-started>
- Gemini structured outputs: <https://ai.google.dev/gemini-api/docs/structured-output>
- Groq documentation: <https://console.groq.com/docs/overview>
- Groq structured outputs: <https://console.groq.com/docs/structured-outputs>
- Sentence Transformers: <https://www.sbert.net/>

## Frontend and delivery

- React: <https://react.dev/>
- Vite: <https://vite.dev/guide/>
- Tailwind CSS with Vite: <https://tailwindcss.com/docs/installation/using-vite>
- TanStack Query: <https://tanstack.com/query/latest/docs/framework/react/overview>
- React Router: <https://reactrouter.com/>
- Docker Compose: <https://docs.docker.com/compose/>
- Compose startup order and health checks: <https://docs.docker.com/compose/how-tos/startup-order/>
- GitHub Actions: <https://docs.github.com/actions>
- GitHub Actions security hardening: <https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>

---

# Final instruction to the implementer

Build a truthful, complete and reproducible product. A smaller working implementation that passes its tests is preferable to a large collection of disconnected mock screens. Follow the phases in order, keep the scanner deterministic, ground AI outputs in official evidence, require human approval for remediation, preserve scan history, protect the browser execution boundary, and document exactly what has and has not been verified.

**The user will inspect the live website after the full build and then request visual/functional refinements. Do not stop early after producing an attractive dashboard. Finish the backend, scanner, RAG, agents, persistence, tests, security, Docker, CI and deployment documentation first.**
