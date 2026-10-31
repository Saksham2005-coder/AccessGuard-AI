# AccessGuard AI — Technology Stack and Dependency Governance

This document records the locked technology decisions, exact runtime versions, and dependency governance rules for AccessGuard AI.

---

## Architecture Overview: Modular Monolith

AccessGuard AI is structured as a modular monolith. All backend domain logic, scanner integration, WCAG RAG pipelines, and multi-agent workflows execute within a unified backend codebase partitioned into clean architectural layers:
- `app/api/` — FastAPI versioned REST routing and dependency injection
- `app/core/` — Security, JWT, logging, error handling, request context
- `app/db/` — PostgreSQL models, async sessions, Alembic migrations
- `app/scanner/` — Target policy, SSRF validation, Playwright crawler, axe-core runner
- `app/rag/` — WCAG ingestion, chunking, local MiniLM embeddings, Qdrant dense retrieval, PostgreSQL lexical search, RRF fusion
- `app/ai/` — LLM provider abstraction (Gemini, Groq, Mock), prompts, schemas
- `app/agents/` — LangGraph multi-agent graph, state, nodes, checkpoints
- `app/remediation/` — Remediation proposals, safe patch policy, isolated DOM snapshot validation
- `app/reports/` — PDF (ReportLab) and JSON audit report generation
- `app/workers/` — Celery background tasks and Redis broker

---

## Locked Technology Matrix

| Layer | Component | Version / Specification | Rationale / Notes |
|---|---|---|---|
| **Runtime** | Python | 3.12.x | High-performance async runtime, stable typing |
| **Package Manager** | `uv` | 0.12+ | Deterministic, rapid lockfile resolution |
| **Backend Framework** | FastAPI | >=0.115 | Asynchronous REST API, OpenAPI generation |
| **Data Validation** | Pydantic v2 | >=2.9 | Fast Rust-backed validation and settings |
| **Database** | PostgreSQL | 16-alpine | ACID relational source of truth |
| **ORM** | SQLAlchemy 2.0 | Async engine (`psycopg` v3 binary) | Type-safe queries, connection pooling |
| **Migrations** | Alembic | >=1.13 | Explicit versioned database migrations |
| **Queue & Broker** | Celery + Redis | Celery 5.4+, Redis 7-alpine | Durable background jobs, SSE event streaming |
| **Vector Database** | Qdrant | >=1.11 | Cosine distance dense vector search for WCAG chunks |
| **Embedding Model** | `all-MiniLM-L6-v2` | Sentence-Transformers | 384-dimensional local embeddings; no external API key |
| **Lexical Search** | PostgreSQL FTS | PostgreSQL GIN index (`simple` dict) | Exact criterion IDs, ARIA tags, axe rule IDs |
| **Reranker** | `ms-marco-MiniLM-L-6-v2` | Cross-Encoder (optional) | Activated via `RERANKER_ENABLED=true` |
| **Browser Engine** | Playwright Chromium | Chromium headless | Sandboxed, controlled rendering and crawling |
| **Accessibility Engine** | `axe-core` | Locally pinned npm package | Injected via `page.add_script_tag()`; no runtime CDN |
| **Agent Orchestration**| LangGraph | >=0.2.34 | Stateful directed graph with human approval checkpoints |
| **LLM Providers** | Gemini & Groq | Provider Protocol | Gemini primary, Groq alternative, Mock for tests |
| **Frontend Framework** | React 19 + TypeScript | Vite 6 | Modern, type-safe Single Page Application |
| **Frontend Styling** | Tailwind CSS 4 | `@tailwindcss/vite` | Modern tokenized styling, clean enterprise look |
| **Frontend Routing** | React Router | v7 | Client-side routing with protected navigation |
| **Server State** | TanStack Query | v5 | Caching, deduplication, optimistic updates |
| **Form Management** | React Hook Form + Zod | Latest | Type-safe form validation |
| **Icons & Visuals** | Lucide React + Recharts | Latest | Polished enterprise observability UI |
| **Testing Backend** | Pytest + pytest-asyncio | Latest | Async unit, integration, scanner, RAG tests |
| **Testing Frontend** | Vitest + Testing Library| Latest | Component and hook tests |
| **Code Formatting** | Ruff (Py) / Prettier (TS)| Latest | Automated linting and formatting gates |

---

## Dependency Governance & Version Pinning Policy

1. **Deterministic Locks:** `uv.lock` for backend and `package-lock.json` for frontend and `tools/axe` must remain committed.
2. **Local Isolation:** axe-core is pinned and bundled locally under `tools/axe/node_modules/axe-core/axe.min.js`. The scanner never fetches bundles from CDNs at runtime.
3. **Container Pinning:** Dockerfiles and `docker-compose.yml` use explicit tags (e.g., `postgres:16-alpine`, `redis:7-alpine`, `qdrant/qdrant:v1.11.3`), never `latest`.
4. **No Secrets in Code:** Environment variables are strictly parsed via Pydantic Settings and loaded from local `.env`. No credentials or API keys may be committed or logged.
