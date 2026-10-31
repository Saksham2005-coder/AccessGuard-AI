# AccessGuard AI

> Enterprise-grade accessibility observability platform combining automated Playwright + axe-core auditing, hybrid WCAG retrieval-augmented generation (RAG), and human-approved remediation workflows.

---

## Overview

AccessGuard AI is a developer-focused accessibility observability platform designed to continuously audit web properties, detect accessibility barriers against WCAG 2.2 standards, retrieve authoritative W3C guidance, and generate safe, human-approved remediation proposals with isolated DOM snapshot validation.

Unlike generic AI-wrapper tools, AccessGuard AI maintains strict technical and ethical boundaries:
- **Zero Hallucinated Citations:** All regulatory references originate from indexed official W3C recommendations and understanding documents via hybrid dense-lexical retrieval.
- **Strict Human-in-the-Loop:** Automated fixes are never applied directly to production environments. Remediations are presented as structured proposals requiring explicit engineer approval.
- **Isolated Snapshot Validation:** Approved fixes are validated inside isolated sandboxed DOM environments using axe-core before engineers manually incorporate them into codebases.
- **SSRF and Abuse Protections:** DNS ownership verification, strict private IP blocklists, redirect re-validation, and browser sandbox isolation prevent misuse.

---

## Explicit Limits of the Automated Audit

AccessGuard AI is engineered to be transparent and technically accurate regarding audit scope:

1. **Automated Coverage Bounds:** Automated scanning with axe-core covers significant, objective accessibility rules (e.g., contrast ratios, missing accessible names, landmark structure, form control labels). However, automated testing cannot evaluate every WCAG success criterion.
2. **Conformity vs. Automation:** Passing automated checks does not equal full WCAG conformance. True accessibility requires manual evaluation, including keyboard navigation testing, screen reader interoperability, focus management review, and cognitive assessment.
3. **Contextual Nuance:** Code suggestions (such as alternative text for non-text content) depend strictly on visual and functional context. Decorative graphics require empty `alt=""` attributes, whereas informative charts require semantic equivalents.
4. **Snapshot Validation:** A status of `Snapshot validation passed` confirms that the targeted axe-core violation did not reproduce in the isolated, sandboxed DOM snapshot. It does not certify that production single-page application state, dynamic transitions, or assistive tech flows are completely barrier-free.
5. **No False Claims:** AccessGuard AI never issues deceptive claims such as "100% WCAG Compliant" or "Certified Accessible".

---

## Technology Stack

- **Backend:** FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async), Alembic
- **Database:** PostgreSQL 16 (relational source of truth), Redis 7 (broker & caching)
- **Vector Search:** Qdrant (cosine distance vector indexing)
- **Scanner Engine:** Playwright Python (Chromium headless) with locally pinned `axe-core`
- **Retrieval & RAG:** Local `sentence-transformers/all-MiniLM-L6-v2` embeddings, PostgreSQL Full-Text Search (lexical), Reciprocal Rank Fusion (RRF), optional cross-encoder reranker
- **Multi-Agent Orchestration:** LangGraph stateful multi-agent workflow with human-in-the-loop checkpointing
- **LLM Support:** Gemini (default), Groq (alternative), deterministic Mock provider for local/CI runs
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, TanStack Query, React Router v7, Lucide Icons, Recharts
- **Infrastructure & CI:** Docker & Docker Compose, GitHub Actions, UV package manager, Vitest, Pytest

---

## Monorepo Structure

```text
AccessGuard-AI/
├── backend/            # FastAPI backend, domain services, workers, scanner & RAG
├── frontend/           # React + TypeScript + Tailwind CSS 4 web dashboard
├── tools/axe/          # Local, version-pinned axe-core bundle
├── knowledge_base/     # Official W3C WCAG 2.2 sources, evaluation datasets
├── test_sites/         # Local test fixture websites for deterministic audits
├── infrastructure/     # Dockerfiles, deployment configurations, security profiles
├── docs/               # System architecture, API specs, security threat model, evaluation
└── .github/workflows/  # CI/CD pipelines
```

---

## Getting Started

### Prerequisites

- Python 3.12+ and `uv` package manager
- Node.js 22+ (LTS) and `npm`
- Docker and Docker Compose

### 1. Clone & Configure Environment

```powershell
cp .env.example .env
```

### 2. Infrastructure Services

Start PostgreSQL, Redis, and Qdrant:

```powershell
docker compose up -d postgres redis qdrant
```

### 3. Backend Setup

```powershell
cd backend
uv sync --all-groups
uv run playwright install chromium
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

---

## License

AccessGuard AI is open-source under the MIT License.