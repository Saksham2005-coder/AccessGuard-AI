# AccessGuard AI — Phase 18 Performance Report

This report evaluates runtime execution latency, password hashing workload characteristics, frontend bundle weight, and build execution times.

---

## 1. Argon2id Password Hashing Profile

- **Cryptographic Parameters:**
  - Algorithm: Argon2id
  - Memory Cost: `65536` KiB (64 MiB)
  - Time Cost: `3` iterations
  - Parallelism: `4` threads
- **Latency Benchmarks (Local Development Workstation):**
  - Average Single Hash Duration: **1.42 seconds**
  - Memory Peak: ~68 MiB per operation
  - CPU Utilization: ~60% across 4 cores during hash computation
- **Production Assessment:**
  - The latency is intentional and aligns with OWASP Password Storage Cheat Sheet recommendations to prevent GPU-accelerated dictionary attacks.
  - Test suites employ cached sessions or mock hash verification where appropriate to maintain 25s complete test execution.

---

## 2. Frontend Bundle Size & Code-Splitting Metrics (BUG-08)

Following Workstream 5 code splitting and Rolldown chunking optimization, the monolithic 983 kB bundle was decomposed into granular, on-demand modules:

| Chunk Name | Raw Size | Gzip Size | Threshold (< 500 kB) | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `index.html` | 0.79 kB | 0.38 kB | **PASS** | Entry document |
| `index--v4QZBNt.css` | 53.22 kB | 9.65 kB | **PASS** | Semantic CSS & Tailwind v4 styles |
| `vendor-icons-*.js` | 23.84 kB | 8.59 kB | **PASS** | Lucide icon glyphs |
| `vendor-query-*.js` | 28.64 kB | 8.89 kB | **PASS** | TanStack Query client & cache |
| `vendor-react-*.js` | 248.79 kB | 78.94 kB | **PASS** | React, React-DOM, React Router |
| `index-*.js` (App Core) | 262.20 kB | 80.35 kB | **PASS** | App shell, AuthStore, Layout, Landing |
| `OverviewPage-*.js` | 360.51 kB | 103.87 kB | **PASS** | Dashboard overview & Recharts |
| `ScansPage-*.js` | 18.96 kB | 4.99 kB | **PASS** | Scans table & live status |
| `ProjectsPage-*.js` | 15.63 kB | 4.24 kB | **PASS** | Project list & DNS verification modal |
| `KnowledgePage-*.js`| 13.03 kB | 3.53 kB | **PASS** | RAG search & evidence drawer |
| `RemediationsPage-*.js` | 11.93 kB | 3.36 kB | **PASS** | Remediation patches & diff viewer |
| `SettingsPage-*.js` | 11.39 kB | 2.47 kB | **PASS** | Profile mutation & password forms |
| `FindingsPage-*.js` | 10.76 kB | 3.07 kB | **PASS** | Findings table & detail drawer |
| `ReportsPage-*.js` | 10.09 kB | 3.05 kB | **PASS** | Health score, JSON & CSV export |

**Verdict:** 100% of chunks are below the 500 kB budget. Zero build warnings.

---

## 3. Build & Test Execution Performance

| Pipeline Step | Duration | Target | Status |
| :--- | :--- | :--- | :--- |
| **Backend Test Suite (69 tests)** | 25.84s | < 45s | **PASS** |
| **Backend Ruff Lint & Format** | 1.82s | < 5s | **PASS** |
| **Frontend Test Suite (24 tests)** | 33.02s | < 45s | **PASS** |
| **Frontend TypeScript (`tsc -b`)** | 2.38s | < 5s | **PASS** |
| **Frontend Production Build (`vite build`)** | 6.86s | < 10s | **PASS** |
| **End-to-End Build + Test Pipeline** | **69.92s** | < 120s | **PASS** |
