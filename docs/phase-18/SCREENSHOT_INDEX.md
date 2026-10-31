# AccessGuard AI — Phase 18 Screenshot Index

All screenshots documented below were captured autonomously using Playwright Chromium at 1440x900 viewport resolution against the running development stack (`http://localhost:5173` and `http://127.0.0.1:8000`).

---

## Screenshot Catalog

### 1. `01_landing_page_dark.png`
- **File Path:** `artifacts/phase-18/screenshots/01_landing_page_dark.png`
- **Size:** 99.8 kB
- **Interface:** Public Marketing Landing Page (Dark Theme)
- **Features Highlighted:** Hero banner with gradient typography, "Start Free Audit" and "Sign In to Account" CTAs, 5-step remediation lifecycle overview, security verification badge, and WCAG 2.2 AA transparency notice.

### 2. `02_landing_page_light.png`
- **File Path:** `artifacts/phase-18/screenshots/02_landing_page_light.png`
- **Size:** 98.8 kB
- **Interface:** Public Marketing Landing Page (Light Theme)
- **Features Highlighted:** Clean high-contrast light mode styling, slate border elements, accessible text ratios, and moon toggle icon.

### 3. `03_login_page.png`
- **File Path:** `artifacts/phase-18/screenshots/03_login_page.png`
- **Size:** 30.3 kB
- **Interface:** Sign In Authentication Screen
- **Features Highlighted:** Brand badge, input fields for email and password, Argon2id security badge, and link to account registration.

### 4. `04_register_page.png`
- **File Path:** `artifacts/phase-18/screenshots/04_register_page.png`
- **Size:** 44.4 kB
- **Interface:** Account Registration Screen
- **Features Highlighted:** Full name, email, password, and confirm password fields with inline helper guidance regarding standard TLD domains and Argon2id password complexity.

### 5. `05_dashboard_overview_dark.png`
- **File Path:** `artifacts/phase-18/screenshots/05_dashboard_overview_dark.png`
- **Size:** 106.1 kB
- **Interface:** Accessibility Overview Dashboard (Dark Theme)
- **Features Highlighted:** Monitored projects KPI, audit scans count, open findings, snapshot validated metrics, findings severity distribution chart, audit engine live status badge (`axe-core 4.14.0 Engine Active`), and real-time SSE indicator.

### 6. `06_dashboard_overview_light.png`
- **File Path:** `artifacts/phase-18/screenshots/06_dashboard_overview_light.png`
- **Size:** 107.6 kB
- **Interface:** Accessibility Overview Dashboard (Light Theme)
- **Features Highlighted:** Full light theme styling of stat cards, high-contrast typography, sidebar navigation styling, and active moon toggle button.

### 7. `07_projects_page.png`
- **File Path:** `artifacts/phase-18/screenshots/07_projects_page.png`
- **Size:** 57.5 kB
- **Interface:** Monitored Projects Management
- **Features Highlighted:** Monitored projects workspace, empty state with "Create First Project" callout, and "New Project" header action.

### 8. `08_scans_page.png`
- **File Path:** `artifacts/phase-18/screenshots/08_scans_page.png`
- **Size:** 58.8 kB
- **Interface:** Automated Accessibility Scans
- **Features Highlighted:** Scan execution table, target URL filter, status badges, page progress metrics, and domain verification guardrails.

### 9. `09_findings_page.png`
- **File Path:** `artifacts/phase-18/screenshots/09_findings_page.png`
- **Size:** 59.7 kB
- **Interface:** Findings Explorer
- **Features Highlighted:** Axe rule classifications, severity level tags (Critical, Serious, Moderate, Minor), impact filter buttons, and DOM element selector indicators.

### 10. `10_remediations_page.png`
- **File Path:** `artifacts/phase-18/screenshots/10_remediations_page.png`
- **Size:** 66.0 kB
- **Interface:** AI Remediation Hub
- **Features Highlighted:** Human-in-the-loop review workflow, code patch diff viewer, database status filter dropdown (`proposed`, `approved`, `validated`), and isolated sandbox validation trigger.

### 11. `11_reports_page_truthful_health.png`
- **File Path:** `artifacts/phase-18/screenshots/11_reports_page_truthful_health.png`
- **Size:** 52.1 kB
- **Interface:** Audit Compliance Reports
- **Features Highlighted:** Truthful zero-state handling ("No Projects Available for Reporting"), "Download JSON", sanitized "Download CSV", and "Print Report" toolbar buttons.

### 12. `12_knowledge_page_rag.png`
- **File Path:** `artifacts/phase-18/screenshots/12_knowledge_page_rag.png`
- **Size:** 106.8 kB
- **Interface:** WCAG Knowledge Base & Standards
- **Features Highlighted:** Live knowledge sources queried from backend DB (WAI-ARIA 1.2, WCAG 2.2, Techniques, Understanding), multi-mode retrieval toggles (Hybrid, Dense, Lexical), search bar with clear button, and Qdrant vector status.

### 13. `13_settings_page_account.png`
- **File Path:** `artifacts/phase-18/screenshots/13_settings_page_account.png`
- **Size:** 79.5 kB
- **Interface:** Account Settings & Security Boundaries
- **Features Highlighted:** User Profile & Tenant Isolation panel with "Edit Profile" action, "Change Account Password" form (Argon2id current password verification, min 8 chars, session revocation), and crawler SSRF loopback security policy.
