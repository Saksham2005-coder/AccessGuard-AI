# AccessGuard AI — Phase 18 Interaction Audit

This document records the verification of all interactive components, user controls, form validations, and asynchronous workflows across the AccessGuard AI web application.

---

## 1. Global Navigation & Layout Controls

| Interactive Element | Location | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Skip to main content** | App Header (Hidden until focused) | Directs keyboard focus to `#main-content` | Jumps focus directly to `<main id="main-content">` | **PASS** |
| **Theme Toggle (Desktop)** | Header Top-Right | Toggles between Dark and Light color themes | Updates `data-theme` on `<html>`, persists to `localStorage`, changes icon between Sun/Moon | **PASS** |
| **Theme Toggle (Mobile)** | Mobile Menu Drawer | Toggles between Dark and Light color themes | Updates theme and announces state change via `aria-label` | **PASS** |
| **Mobile Drawer Toggle** | Header Left (Small screens) | Opens slide-over navigation menu | Expands drawer, sets `aria-expanded="true"`, focuses first nav item | **PASS** |
| **Sign Out Button** | Sidebar Bottom / Header | Invalidates local session, calls `/api/v1/auth/logout`, redirects to `/login` | Clears Zustand auth store, clears cookie, redirects cleanly | **PASS** |

---

## 2. Authentication Workflows

| Control / Input | Expected Behavior | Tested Interaction | Result |
| :--- | :--- | :--- | :--- |
| **Register Display Name** | Required string, min 2 chars | Validates input format; displays red helper text on invalid input | **PASS** |
| **Register Email** | Standard email format with valid TLD | Displays inline helper guidance; accepts corporate and standard TLDs | **PASS** |
| **Register Password** | Min 8 chars, hashed via Argon2id | Rejects < 8 chars; hashes using strict Argon2id parameters | **PASS** |
| **Register Confirm Password** | Must match password exactly | Displays "Passwords do not match" if mismatch occurs | **PASS** |
| **Login Email & Password** | Validates credentials against DB | Invalid credentials display localized alert; valid credentials redirect to `/app/overview` | **PASS** |

---

## 3. Projects Management Workflows

| Action / Button | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| **New Project Button** | Opens modal to register a monitored domain | Modal opens with keyboard trap, focus on domain input | **PASS** |
| **Create Project Submission** | Normalizes base domain, generates DNS TXT token | Project registered with `is_verified: false` and DNS challenge token | **PASS** |
| **Copy DNS Token** | Copies `accessguard-verification=...` to clipboard | Copies cleanly and triggers confirmation badge | **PASS** |
| **Verify DNS Button** | Performs TXT lookup via backend | Updates verification status to true if TXT record matches; shows retry alert otherwise | **PASS** |

---

## 4. Scan Execution & Guardrails

| Control | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Launch Scan Button** | Disabled if selected project domain is unverified | Button shows disabled state and tooltip "Domain verification required" | **PASS** |
| **Scan Execution Trigger** | Submits scan request to backend API | If unverified, API returns HTTP 403 Forbidden; if verified, queues Celery crawl task | **PASS** |
| **Real-Time Scan Progress** | Live updates via SSE / polling | Scans table updates status from `pending` -> `running` -> `completed` | **PASS** |

---

## 5. Remediation Approval & Sandbox Testing

| Action | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Status Filter Dropdown** | Filters by DB status (`proposed`, `approved`, `validated`, etc.) | Dropdown filters findings list by exact backend enum status | **PASS** |
| **Inspect Patch Diff** | Displays side-by-side or unified safe diff | Diff viewer renders sanitized additions (+) and deletions (-) | **PASS** |
| **Approve Patch Button** | Opens approval modal requiring reviewer notes | Reviewer notes captured, patch state transitioned to `approved` | **PASS** |
| **Validate in Sandbox** | Triggers headless Chromium DOM validation with network egress blocked | Sandbox runs axe-core on patched DOM, verifies violation clearance | **PASS** |

---

## 6. Compliance Reports & Data Export

| Button | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Health Score Banner** | Shows "N/A — Not yet assessed" if 0 completed scans exist | Truthful score display; never synthetic 100/100 | **PASS** |
| **Download JSON** | Exports structured audit dataset | Generates formatted JSON blob with scans, findings, and metadata | **PASS** |
| **Download CSV** | Exports findings table with sanitized spreadsheet fields | Neutralizes formula injection (`=`, `+`, `-`, `@` prepended with `'`) and downloads CSV | **PASS** |
| **Print Report** | Triggers browser print stylesheet | Invokes `window.print()` with print-optimized CSS layout | **PASS** |

---

## 7. Knowledge Base & RAG Retrieval

| Control | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Search Query Input** | Accepts criteria names, WCAG IDs, keywords | Live input with instant clear (X) icon | **PASS** |
| **Retrieval Mode Selector** | Toggles between Hybrid, Dense (vector), and Lexical (BM25) | Passes selected retrieval mode parameter to `/api/v1/knowledge/search` | **PASS** |
| **Search RAG Button** | Queries Qdrant vector database via backend | Renders retrieved evidence chunks with relevance scores and understanding links | **PASS** |
| **Evidence Chunk Card** | Opens detailed guideline drawer on click | Drawer displays normative text, failure conditions, and WCAG criteria breakdown | **PASS** |

---

## 8. Account Settings & Password Change

| Action | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Edit Profile Button** | Toggles display name input from read-only to editable | Input activates with current name, displays Save and Cancel buttons | **PASS** |
| **Save Profile Changes** | Submits `PATCH /api/v1/auth/me` | Backend updates user display name, shows green success banner | **PASS** |
| **Update Password Form** | Verifies current password, enforces min 8 chars for new password | Argon2id verifies current hash; updates hash; revokes other sessions | **PASS** |
