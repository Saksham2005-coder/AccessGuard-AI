# AccessGuard AI --- Phase 18 Stabilization & Post-Phase 18 Innovation Blueprint

**Purpose:** Master implementation specification for Antigravity.\
**Phase 18:** Stabilize, complete, test, inspect and prepare the
existing product for a reliable demonstration.\
**Future roadmap:** Detailed specifications for the innovations to
consider after Phase 18.

> This document is based on the supplied BUG_REPORT.md,
> INTERACTION_AUDIT.md, UI_UX_AUDIT.md and screenshots. The prior
> audit's metrics are historical reports, not guaranteed facts about the
> current checkout. Verify every issue against the current repository
> before changing code.

# 0. Master instructions to Antigravity

Act as principal engineer, frontend/backend engineer, QA lead,
application-security engineer, DevOps engineer and product designer.
This is a continuation of an existing 17-phase project with an existing
Git history. Do not rebuild it from scratch.

## 0.1 Objective

Make AccessGuard AI reliably start, behave honestly, complete its real
user journeys, and be demonstrable without bypassing security.

The target journey is:

1.  User opens a public product landing page.
2.  User registers and signs in.
3.  User creates a project.
4.  User verifies ownership of the target domain using the existing DNS
    TXT challenge.
5.  User configures and starts a scan against an authorized target.
6.  Playwright and axe-core scan the permitted pages and persist actual
    findings.
7.  User inspects findings and DOM evidence.
8.  User searches real WCAG guidance through the RAG system.
9.  AI proposes an evidence-grounded remediation.
10. A human approves or rejects the proposal.
11. Approved changes are applied only to an isolated snapshot under the
    existing safe patch policy.
12. The snapshot is re-audited and regressions are reported.
13. User exports a report based on persisted data.
14. User can return and inspect historical projects, scans and
    decisions.

A page, button, endpoint, schema, mock response or static card does not
prove a feature works. Verify the full action, backend behavior,
persistence, response, UI state and error handling.

## 0.2 Non-negotiable rules

-   Work on `main` only unless the repository owner explicitly changes
    this.
-   Preserve all existing commits and tags. Never rewrite history,
    force-push, reset away user work or delete existing branches.
-   Inspect `git status`, current branch and recent commits before
    editing.
-   Never overwrite uncommitted user work. If the worktree is dirty,
    document it and stop before touching conflicting files.
-   Do not weaken domain ownership verification, SSRF controls, redirect
    revalidation, tenant isolation, JWT/session security, safe patch
    policy, snapshot isolation or network-egress restrictions.
-   Never hardcode secrets, API keys, tokens, user data, scan findings,
    health scores, RAG counts or service statuses.
-   Never present mock data as live customer data. Clearly label demo
    data.
-   Automated axe-core checks do not prove complete WCAG conformance.
    State coverage and limitations honestly.
-   Do not scan an external site unless it is authorized and verified.
    Use local fixtures for development and demo workflows.
-   Do not claim a live AI workflow passed if only a mock provider was
    used.
-   Keep provider keys on the backend; never expose them in frontend
    bundles.
-   Avoid unnecessary dependency upgrades.
-   Preserve the existing Graphite & Electric Blue visual identity;
    improve it rather than replacing it with an unrelated design.
-   Record bugs before fixing them. Do not silently patch during QA.
-   Do not claim success without command output, browser evidence, API
    evidence or persisted data.

## 0.3 Required development loop

For each workstream: inspect → reproduce → identify root cause → plan →
implement → add regression tests → run focused tests → run relevant full
suites → lint/typecheck/build → run browser verification → capture
evidence → update docs → commit. A bug is closed only after its
reproducer passes. Never delete or weaken a meaningful test merely to
get green output.

# 1. Existing baseline to verify

The prior audit reported these routes:

-   `/` --- redirects to login; public landing page missing.
-   `/login`, `/register`.
-   `/app/overview`.
-   `/app/projects`.
-   `/app/scans`.
-   `/app/findings`.
-   `/app/remediations`.
-   `/app/reports`.
-   `/app/knowledge`.
-   `/app/settings`.
-   Not-found route.

The reported architecture includes React/TypeScript/Vite/Tailwind,
FastAPI, PostgreSQL/SQLAlchemy, Celery/Redis, Qdrant,
Playwright/Chromium, locally bundled axe-core, LangGraph, local
sentence-transformer embeddings, Gemini/Groq provider adapters and
Docker Compose. Inspect the repository; do not assume these details
remain exact.

## 1.1 Reported bug inventory

  ----------------------------------------------------------------------------
  ID                      Severity                Reported issue
  ----------------------- ----------------------- ----------------------------
  BUG-01                  P0                      Compose sets production mode
                                                  while using default database
                                                  credentials; backend guard
                                                  crashes

  BUG-02                  P1                      Celery Compose command
                                                  points to incorrect module
                                                  path

  BUG-03                  P1                      Vite has no `/api`
                                                  development proxy to FastAPI

  BUG-04                  P2                      Scan request for an existing
                                                  unverified project returns
                                                  404 instead of a meaningful
                                                  verification/authorization
                                                  response

  BUG-05                  P2                      Dark theme hardcoded; no
                                                  light theme or toggle

  BUG-06                  P2                      Knowledge Base uses
                                                  hardcoded cards instead of
                                                  live RAG

  BUG-07                  P2                      One Reports Vitest query
                                                  assertion times out

  BUG-08                  P2                      Frontend bundle reportedly
                                                  about 983 kB; route imports
                                                  are static

  BUG-09                  P3                      No public landing page

  BUG-10                  P3                      Settings page read-only

  BUG-11                  P3                      Argon2id latency reportedly
                                                  8--11 seconds on Windows
                                                  host

  BUG-12                  P3                      Email validation errors lack
                                                  useful inline guidance
  ----------------------------------------------------------------------------

The prior interaction audit reported 57 interactive elements: 50 PASS
and 7 FAIL/missing. Reported missing/broken items include root landing
page, forgot-password link/flow, theme switcher, remediation status
filter, Knowledge Base search and Settings profile/password controls.
Rebuild the inventory from the current running app; do not reuse the old
count as the new denominator.

# 2. Phase 18 workstream plan

  -----------------------------------------------------------------------
  Workstream              Name                    Outcome
  ----------------------- ----------------------- -----------------------
  0                       Repository baseline and Known state and
                          change safety           protected history

  1                       Runtime/deployment      Docker and standalone
                          stabilization           development startup
                                                  work

  2                       Backend/API correctness Correct API semantics
                                                  and persisted behavior

  3                       Frontend functional     Real working controls
                          completion              and missing workflows

  4                       Data integrity and      Metrics/statuses
                          truthful states         reflect persisted facts

  5                       UI/UX and accessibility Landing page, themes,
                          polish                  responsive accessible
                                                  UI

  6                       Performance and         Measured improvements
                          security hardening      without security
                                                  regression

  7                       End-to-end QA and       Reproducible verified
                          release readiness       demo and evidence
  -----------------------------------------------------------------------

# 3. Workstream 0 --- Repository baseline & change safety

Run:

``` bash
git status --short
git branch --show-current
git log --oneline -15
git tag --list
```

Verify current branch, dirty worktree, existing tags, user
modifications, project structure, README, environment examples,
dependency locks, migrations, CI, tests, Compose files, API entrypoints,
Celery task discovery, Vite config and route structure.

Create `docs/phase-18/BASELINE.md` with: - Branch, commit and tag
state. - Runtime versions. - Service topology. - Exact startup/test
commands. - Baseline backend/frontend tests. - Baseline
lint/typecheck/build. - Compose config/build result. - Defects
reproduced and not reproduced. - Missing external dependencies. -
Pre-existing uncommitted changes.

Use the repository's actual package manager/scripts. Record exact
commands and exit codes. Do not invent commands.

**Exit:** repository state and existing behavior are documented; user
work is protected.

# 4. Workstream 1 --- Runtime & deployment stabilization

This is the first implementation priority. Do not add features before
startup works.

## 4.1 BUG-01 --- Docker Compose credential guard

The report says Compose sets `APP_ENV=production` while using a
placeholder database password such as `change-me`. The backend correctly
rejects default credentials in production.

Implement: 1. Inspect settings validation and Compose configuration. 2.
Preserve the production guard. 3. Separate local Compose development
configuration from production deployment. 4. Use environment
substitution for DB credentials. 5. Provide safe `.env.example`
placeholders only. 6. Document local-only development configuration. 7.
Ensure production fails closed if secrets are missing or weak/default.
8. Ensure secrets are never logged or exposed in frontend config. 9. Add
tests for valid development config, secure production config, missing
production credentials, placeholder credentials and malformed URLs.

Do NOT make the guard accept `change-me`, bake real passwords into
images or silently default production to weak secrets.

**Acceptance:** `docker compose config` succeeds; local stack starts;
production still rejects missing/default secrets; tests prove both
paths.

## 4.2 BUG-02 --- Celery worker path

Inspect the actual Celery app module, working directory and Docker
image. The report says Compose points to
`app.core.celery_app.celery_app` while the real app is
`app.workers.celery_app:celery_app`.

Implement: - Correct import path and working directory. - Verify task
autodiscovery and registration. - Verify Redis broker/result
configuration. - Verify graceful shutdown/restart. - Add a disposable
test task or smoke test. - Confirm logs contain no secrets.

**Acceptance:** worker starts, connects to Redis, registers expected
tasks and consumes a test task.

## 4.3 BUG-03 --- Vite API proxy

Inspect Vite config and API client. Add a development-only `/api` proxy
to the actual FastAPI URL. Preserve `/api/v1`; make target configurable
with a safe local default. Ensure SSE works through the proxy if used.
Do not leak development proxy configuration into production.

Improve API-client error handling: HTML fallback returned where JSON is
expected should become a useful proxy/network error, not an unhandled
JSON parse exception.

Test independent startup: - FastAPI on its documented port. - Vite on
its documented port. - Login request reaches FastAPI. - Invalid
credentials return backend JSON, not Vite HTML. - Projects/scans API
requests reach FastAPI. - SSE connection works if supported.

## 4.4 Full Compose verification

Verify PostgreSQL, Redis, Qdrant, API, Celery worker, frontend and
Playwright/Chromium dependencies. Check healthchecks, readiness, service
hostnames, bridge network, persistent volumes, migration strategy,
browser libraries, non-root execution, file permissions, graceful
shutdown and restart.

Test from a disposable empty volume: 1. Start dependencies. 2. Wait for
readiness. 3. Run migrations. 4. Start API and worker. 5. Verify
live/ready endpoints. 6. Verify frontend-to-API connectivity. 7. Run a
background test task. 8. Restart API/worker and verify persistence. 9.
Stop cleanly. 10. Repeat using the documented command.

Do not call a container healthy merely because it is running.

**Exit:** Docker and standalone development workflows both work; P0/P1
startup issues are fixed.

# 5. Workstream 2 --- Backend/API correctness

## 5.1 BUG-04 --- Scan creation status

Separate project existence, tenant authorization and domain-verification
preconditions.

Expected behavior: - Unknown project: documented not-found response. -
Project belonging to another tenant: preserve non-disclosure behavior;
do not reveal existence. - Existing project owned by user but
unverified: clear domain-verification-required response, normally 403 or
documented precondition status. - Verified project and valid payload:
enqueue scan. - Invalid payload: structured validation error.

Test unknown project, own unverified project, foreign-tenant project,
verified project, URL outside verified scope, invalid page/depth limits
and idempotency if supported.

## 5.2 API error contract

Review endpoints for consistent status codes, RFC 7807/problem detail if
already adopted, request IDs, machine-readable codes, human-readable
messages and field validation. Never return stack traces, secrets or raw
internal exceptions.

## 5.3 Domain verification integrity

Verify: - Cryptographically random challenge. - Challenge scoped to
project/domain. - Rotation invalidates old challenge where intended. -
Exact expected TXT record checked. - Base-domain/subdomain rules
documented. - Verification state persisted transactionally. - DNS errors
and propagation delays distinguished. - Failure never marks verified. -
No cross-tenant token reuse. - Scan blocked before verification.

Do not bypass this protection for demos.

## 5.4 Authentication/account APIs

Verify registration, login, refresh rotation, logout/revocation,
password hashing, session expiry, token reuse behavior, identity
endpoint and tenant access.

If profile/password endpoints do not exist, implement according to
existing API conventions.

Profile update: - Authenticated user updates only permitted fields. -
User ID/role cannot be changed. - Email changes, if supported, require
verification. - Validate/normalize values. - Persist transactionally.

Password change: - Require current password. - Apply documented password
policy. - Hash using approved Argon2id configuration. - Revoke other
sessions where appropriate. - Never log/return password. - Apply rate
limiting consistent with the architecture.

## 5.5 RAG API

Inspect the actual RAG route/schema. Verify dense retrieval, lexical
retrieval, fusion/reranking, source metadata, corpus version, empty
results, provider-independent retrieval, authorization and citation
correctness. Do not assume `/api/v1/rag/search` is the route; use the
real contract. Do not create duplicate routes just to match an old
audit.

## 5.6 Reports API

Verify project selection, latest completed scan versus historical
aggregate, severity counts, WCAG mapping, score, no-scan state,
failed/cancelled scans and export data. Never treat failed/incomplete
scans as clean.

**Exit:** API behavior, tenant boundaries, domain verification, account
mutation, RAG and reports are tested.

# 6. Workstream 3 --- Frontend functional completion

## 6.1 BUG-09 --- Public landing page

Create public `/` route: - Product headline and concise value
proposition. - CTA to create account and sign in. - Real features only:
browser scans, WCAG evidence retrieval, AI proposals, human approval,
isolated snapshot validation, reporting if implemented. - Workflow: Scan
→ Understand → Propose → Review → Validate. - Security section
explaining domain verification and snapshot isolation. - Honest
statement that automated tests do not certify complete WCAG
conformance. - Footer links only to real destinations.

Design: - Preserve Graphite & Electric Blue identity. - Responsive,
accessible and polished. - Use real screenshots only. - No fake
testimonials, customer logos, compliance badges or invented metrics. -
Ensure CTA routes work.

Acceptance: signed-out `/` renders landing page; signed-in state has
sensible dashboard CTA; login/register links work; refresh/direct
navigation works.

## 6.2 BUG-05 --- Light/dark theme system

Create/extend ThemeProvider with `light`, `dark`, and optionally
`system`. Use semantic CSS variables for canvas, sidebar, header, cards,
elevated surfaces, inputs, text, muted text, borders, focus, accent,
success, warning, danger, info, charts and overlays.

Persist selection using existing preferences/local storage as
appropriate. Add a one-click accessible switch in the app shell. Respect
`prefers-color-scheme` in system mode. Avoid initial theme flash. Do not
mechanically invert colors.

Inspect both themes on: - Auth. - Landing. - Dashboard. -
Projects/dialogs. - DNS verification. - Scans/progress. -
Findings/drawer. - Remediation/diff. - Reports/charts. - Knowledge. -
Settings. - 404.

Check contrast, focus, charts, code diffs and status semantics. No
dark-only hardcoded surfaces should remain in shared components.

## 6.3 BUG-06 --- Live Knowledge Base

Remove static mock corpus and fabricated chunk counts. Use actual RAG
API/schema.

UI: - Natural-language/keyword search. - Search and clear controls. -
Supported category filters. - Loading, no-results, error and retry
states. - Result title, WCAG criterion/technique if returned, excerpt,
source link, relevance only if meaningful, corpus version if
available. - Details panel. - Safe rendering of untrusted retrieved
text.

Integration: - Existing API client and query/cache patterns. - Debounce
where useful. - Cancel stale requests or prevent stale results replacing
new ones. - Graceful Qdrant/API unavailable state. - No provider key in
browser. - Source metadata comes from backend. - Search should work
without LLM key if retrieval is provider-independent.

Only display corpus health/counts if a real endpoint supplies them.
Otherwise show truthful service state, not invented counts.

## 6.4 BUG-10 --- Settings

Implement only real capabilities: - Profile name/email display and
editable fields if API supports them. - Save/cancel, inline validation,
feedback. - Change password with current/new/confirm values and secure
behavior. - Active sessions/revocation only if supported by backend. -
API tokens only if a real secure token model exists: hash server-side,
show token once, scopes/expiry/revocation. If not implemented, do not
display fake token controls. - Preferences only if persisted and
functional.

Acceptance: profile persists after refresh; password change verified
with disposable account; no sensitive values logged; every visible
control works.

## 6.5 Forgot password

Do not add a dead link.

Option A: implement real single-use, time-limited hashed reset tokens,
configured email provider or development email sink,
account-enumeration-resistant responses, rate limits and session
revocation after reset.

Option B: if email delivery is unavailable, explicitly defer the feature
and do not show a fake link.

Never return reset tokens in public production API responses.

## 6.6 Registration validation

Align frontend and backend validation. Provide inline syntax guidance,
explain whether internal domains are supported, show field-level errors
instead of raw Pydantic text, show password policy/strength feedback
based on actual server rules, preserve autocomplete/password manager
support. Do not rely on simplistic regex alone.

## 6.7 Remediation filter

Add filter for statuses that genuinely exist in backend. Use server
filtering for large datasets or client filtering over complete data.
Provide empty states and ensure counts/results match backend.

## 6.8 Findings/project UX

Preserve search/filter behavior; ensure filters compose; details drawer
shows correct finding; syntax highlighting must not render unsafe HTML;
copy actions give feedback; project deletion requires confirmation; no
cross-tenant operations; dialogs restore focus and support Escape.

## 6.9 CSV export

Only if real report data exists. Include stable columns for project/scan
IDs, timestamp/status, finding ID, rule, severity, WCAG mapping, URL,
selector and status when available. Escape CSV fields and neutralize
spreadsheet formula injection. Test file contents, not just download
event.

**Exit:** every visible frontend interaction is functional, correctly
routed, accessible and tested.

# 7. Workstream 4 --- Data integrity and truthful product states

## 7.1 Health score

The uploaded report screenshot showed 100 with zero findings while no
completed scan was visibly available. Investigate the source.

Distinguish: - Never scanned. - Queued. - Running. - Completed with
findings. - Completed with zero findings. - Failed. - Cancelled. -
Partial crawl/stale result.

No completed scan must show "Not yet assessed", not 100. A completed
zero-finding scan may score 100 only if the documented scoring method
supports it. Failed/cancelled scans are never clean. Partial crawl must
show pages/coverage and not imply full-site coverage. Historical score
shows timestamp and source scan.

Document formula, severity weights, deduplication, page weighting,
incomplete-scan treatment, bounds and limitations. Never describe score
as legal certification.

## 7.2 Service health consistency

The screenshot showed "axe-core Engine Active" in one location and
"Offline" elsewhere. Build one backend-derived health source for API,
browser worker, axe-core availability/version, Celery, Redis, Qdrant,
RAG and AI provider configuration/availability.

Use statuses Healthy, Degraded, Unavailable, Not configured, Unknown. A
version string alone does not prove active service.

## 7.3 Demo data policy

Remove accidental mock data from production UI. If demo mode exists,
label it clearly, isolate it from customer data and provide reset.
Reports must show data source/time. Never seed default perfect scores.

## 7.4 UI states

Every data page distinguishes loading, genuinely empty,
filter-no-results, API error, service unavailable, partial data and
stale data. "No findings" must not appear when no scan has run.

## 7.5 Traceability

Each result should trace to project, scan ID, page URL, timestamp,
scanner version, rule/impact, evidence, verified WCAG source,
remediation proposal, approval decision and snapshot re-audit.

**Exit:** all dashboard/report/status states are derived from persisted
evidence and do not mislead users.

# 8. Workstream 5 --- UI/UX and accessibility polish

Preserve graphite base, cyan accent, slate surfaces, icon language and
clean typography. Improve hierarchy, spacing, hover/focus, tables,
dialogs, loading/empty/error states, chart labels and responsiveness.
Avoid excessive gradients/glows/glass effects.

## 8.1 Quick Start

Guide a new user through: 1. Create project. 2. Verify domain. 3. Start
scan. 4. Review findings. 5. Generate remediation. 6. Validate approved
snapshot.

Persist completion only if supported. Allow dismiss/reopen. Step status
must come from real data. Explain DNS. Never bypass verification. A
local demo fixture must be isolated and labeled.

## 8.2 Responsive QA

Test 1440×900, 1366×768, 1024×768, 768×1024, 390×844 and 360×800. Check
sidebar/drawer, header, tables, charts, modals, long URLs/selectors,
code diffs, forms, focus, touch targets and horizontal overflow.

## 8.3 Accessibility of AccessGuard itself

Check landmarks, headings, labels, descriptions/errors, keyboard-only
use, focus visibility, modal trap/restoration, Escape, contrast in both
themes, reduced motion, scan progress announcements, toast
announcements, table semantics and accessible button names. Do not rely
on color alone.

**Exit:** all routes coherent in both themes, responsive and reviewed
with automated plus manual accessibility checks.

# 9. Workstream 6 --- Performance and security hardening

## 9.1 BUG-08 --- Bundle size

Measure current bundle. Identify large dependencies. Lazy-load route
components. Split charts/code viewers where useful. Add stable Suspense
fallbacks. Configure manual chunks only where measured boundaries
justify it. Handle lazy chunk load errors. Test direct
navigation/refresh. Compare initial JS and route chunk sizes. Do not
silence warnings arbitrarily.

Acceptance: initial shell does not eagerly download every page's heavy
code; reports loads charts when needed; build sizes documented; routes
remain reliable.

## 9.2 BUG-11 --- Argon2 latency

Benchmark before changing parameters. Separate hash time from DB/network
latency. Check optimized library and event-loop blocking. Use bounded
thread/process execution if appropriate. Review parameters against
threat model. Do not weaken production parameters to speed up tests. Any
faster profile must be test-only and impossible in production. Report
measured latency and responsiveness.

## 9.3 Security regression

Retest: - Loopback, RFC1918, link-local, metadata, IPv6
private/loopback. - DNS rebinding/re-resolution. - Redirect chains and
forbidden schemes. - URL parser edge cases. - Domain verification
bypass. - Cross-tenant access. - JWT replay/revocation. - Password reset
lifecycle if implemented. - Unsafe patch payloads, event handlers,
scripts and `javascript:` URLs. - Snapshot network egress. - Secret
leakage in logs and frontend bundles.

Use local controlled targets only. Review dependency lockfiles,
container non-root, image contents, `.env` exclusion, pinned browser/axe
versions, production secret handling and dependency advisories. Do not
claim certification based on scanners.

**Exit:** performance measured and improved where justified; no security
protections weakened.

# 10. Workstream 7 --- Full end-to-end QA

## 10.1 Test layers

Backend unit/API/database/migration/Celery/RAG/auth/tenant/SSRF/patch
tests.\
Frontend component/form/query/theme/navigation/download/accessibility
tests.\
E2E authentication, project, verification, scan, SSE progress, findings,
RAG, AI proposal, approval/rejection, snapshot validation, report and
settings tests.

## 10.2 Full controlled user journey

Use a disposable account, disposable project and local test website.

A. Register/login, refresh, protected routes, logout.\
B. Create project, confirm unverified, generate challenge, exercise
legitimate local demo verification if supported, confirm only valid
challenge verifies.\
C. Start scan only on verified controlled target; confirm API job,
worker execution, progress, persisted pages/findings and terminal
status.\
D. Search/filter findings; inspect selector, page URL, DOM evidence and
metadata against API/database.\
E. Search known WCAG query; verify real indexed result and citation;
test no result and Qdrant unavailable.\
F. Use real AI provider for live inference. If provider unavailable,
mark BLOCKED; never substitute mock and claim success. Validate
structured output, citations, patch allowlist and prompt-injection
resistance.\
G. Approve/reject; confirm decision persistence. Apply only to isolated
snapshot; verify original unchanged, egress blocked, re-audit executed,
resolved/remaining/new findings reported.\
H. Export JSON/CSV/print; inspect contents and verify scan
IDs/timestamps.\
I. Update profile; refresh; change password using disposable account;
verify old/new credentials and session behavior.

## 10.3 Interaction audit

Rebuild inventory from actual DOM and running pages. For every
interactive item record route, accessible name, type, expected/actual
behavior, destination URL/API request, resulting state, evidence and
status PASS/FAIL/PARTIAL/BLOCKED/NOT APPLICABLE.

A click handler firing is not enough. PASS requires intended result.

## 10.4 Browser/network inspection

Collect console errors, unhandled rejections, failed requests,
unexpected 4xx/5xx, HTML where JSON expected, broken assets, SSE
failures, React warnings and runtime errors. Distinguish expected
validation/security blocks from defects.

## 10.5 Screenshot evidence

Capture genuine Playwright screenshots after fixes:

``` text
artifacts/phase-18/
  screenshots/
    landing/
    authentication/
    dashboard/
    projects/
    scans/
    findings/
    knowledge/
    remediation/
    reports/
    settings/
    responsive/
    themes/
  reports/
  logs/
  videos/
  traces/
```

Capture landing desktop/mobile; login/register; dashboard both themes;
project list/create; DNS modal; scan config/running/completed;
findings/list/detail; Knowledge search; remediation
proposal/diff/approval/rejection; re-audit; reports/export; Settings;
404; mobile/tablet navigation. Screenshots must be actual runtime
captures, not generated or edited to hide defects. Capture blocked
states honestly.

## 10.6 Required artifacts

Create: 1. `artifacts/phase-18/BASELINE.md` 2. `IMPLEMENTATION_LOG.md`
3. `BUG_REGISTER.md` 4. `TEST_MATRIX.md` 5. `INTERACTION_AUDIT.md` 6.
`UI_UX_AUDIT.md` 7. `SECURITY_REGRESSION.md` 8. `PERFORMANCE_REPORT.md`
9. `SCREENSHOT_INDEX.md` 10. `DEPLOYMENT_VERIFICATION.md` 11.
`FINAL_RELEASE_READINESS.md`

Distinguish verified, failed, blocked, not tested and inferred.

## 10.7 Defect loop

For each defect: unique ID, severity, route/component/API, reproduction,
expected/actual, screenshot/trace/log, root cause, safe fix, regression
test, focused rerun, integration/E2E rerun and evidence-backed closure.

## 10.8 Release gates

**Startup:** Compose config valid; all services healthy;
API/worker/frontend ready; standalone mode works.\
**Core journey:** auth, project, legitimate verification, scan,
findings, RAG, real-provider remediation when configured, approval,
snapshot validation and report all verified.\
**Quality:** no unresolved P0/P1; critical interactions pass;
themes/routes/responsive inspected; tests/lint/typecheck/build pass or
exceptions documented; no unhandled runtime errors.\
**Demo:** controlled target and repeatable instructions; no customer
data; demo data labeled; provider availability disclosed;
screenshots/report included.

Final verdict must be READY FOR LIVE DEMONSTRATION, READY WITH
DOCUMENTED LIMITATIONS, or NOT READY. Do not declare READY when a
critical journey was not tested.

# 11. Implementation order

1.  Baseline and repository safety.
2.  Compose credential configuration and worker.
3.  Vite proxy and API client.
4.  Scan API semantics.
5.  Health score and service status truthfulness.
6.  Landing page and theme system.
7.  Real Knowledge Base.
8.  Settings/account APIs.
9.  Remaining interactions and CSV.
10. Performance/security.
11. Full E2E QA.
12. Screenshots and release sign-off.

# 12. Phase 18 definition of done

-   [ ] Existing Git history/main preserved.
-   [ ] Docker Compose works with safe configuration.
-   [ ] Celery worker consumes a test task.
-   [ ] Standalone Vite reaches FastAPI.
-   [ ] Production rejects weak/default credentials.
-   [ ] Scan API semantics correct without tenant privacy leak.
-   [ ] No-scan state is not shown as 100.
-   [ ] Service status is real and consistent.
-   [ ] Knowledge Base uses live RAG.
-   [ ] Settings are functional or unsupported controls omitted.
-   [ ] Public landing page works.
-   [ ] Light/dark themes work across routes.
-   [ ] Registration errors are understandable.
-   [ ] Remediation filters work.
-   [ ] CSV export safe and based on real data if implemented.
-   [ ] Bundle measured and improved.
-   [ ] Argon2 latency investigated without weakening production
    security.
-   [ ] SSRF, tenant isolation, verification and patch protections pass.
-   [ ] Controlled scan-to-remediation journey verified.
-   [ ] Every critical interaction tested.
-   [ ] Screenshots and final QA artifacts created.
-   [ ] No unresolved P0/P1.
-   [ ] Final verdict evidence-based.

------------------------------------------------------------------------

# PART II --- POST-PHASE 18 INNOVATION ROADMAP

All features below are proposals, not current capabilities. Do not start
them until Phase 18 passes its release gates.

# 13. Feature 1 --- Visual Accessibility Heatmap

## Product goal

Show accessibility findings directly on the rendered page. Users should
not need to infer where a selector points from a table.

## User journey

1.  Open completed scan.
2.  Select scanned page.
3.  Open a read-only, securely isolated page snapshot.
4.  Display colored outlines and numbered markers on elements with
    findings.
5.  Select marker to open corresponding finding.
6.  Filter by severity, rule or WCAG principle.
7.  Toggle overlays on/off.
8.  Compare original and patched snapshot if available.

## Finding panel

Show title, impact, rule ID, verified WCAG mapping, selector, DOM
evidence, explanation, source citation and remediation action.

## Technical design

Reuse scan/page/finding IDs, selector, node evidence, impact and
metadata. If overlays need coordinates, record element bounding boxes
during scan with viewport size, device scale factor and scroll position.
Do not assume selectors alone provide stable positions.

Frontend components: - Snapshot viewer. - Overlay layer. - Severity
legend. - Synchronized findings list. - Selected finding panel. -
Zoom/scroll. - Original/patched switch.

## Security

Render untrusted captured pages in isolated origin/iframe or equivalent
sandbox. Never execute captured scripts in the authenticated app origin.
Block external egress where possible. Prevent page content from reading
app cookies/local storage/API. Sanitize evidence.

## Tests and acceptance

-   Finding maps to correct page/element.
-   Overlay aligns at recorded viewport.
-   Selecting overlay opens correct finding.
-   Filters update overlays and list together.
-   Resizing maintains alignment.
-   Hostile page scripts cannot access app origin.
-   No unexpected network egress.
-   Empty state is truthful.

# 14. Feature 2 --- Before-and-After Remediation Preview

## Product goal

Compare original scanned page with AI-patched isolated snapshot before
human approval.

## User journey

1.  Open proposal.
2.  Show original and patched preview.
3.  Switch side-by-side, slider or tabs.
4.  Synchronize scrolling.
5.  Highlight changed elements.
6.  Show code diff and originating finding.
7.  Show risk notes, policy result and validation state.
8.  Approve/reject.
9.  Re-audit patched snapshot.
10. Display resolved, unchanged and new findings.

## Technical design

Use immutable original/patched snapshot references. Store proposal
ID/version, reviewer, approval timestamp, patch hash and validation
result. Use same browser version/viewport for comparisons. Compare
findings using stable identity and expose uncertain matching.

States must distinguish Proposed, Approved, Applied to isolated
snapshot, Validation passed, Validation failed and Manual review
required.

## Security

Original snapshot remains immutable. Patched preview is isolated.
Approval never silently deploys to customer production. No scripts,
event handlers or prohibited patch operations. Keep network egress
blocked.

## Acceptance

Visual diff corresponds to exact patch version; approval persists;
re-audit evidence exists; regressions shown; original website unchanged.

# 15. Feature 3 --- GitHub Pull Request Accessibility Review

## Product goal

Integrate accessibility checks into developer pull request workflows.
Initial release is advisory and must not auto-merge or push code.

## User journey

1.  Connect GitHub via least-privilege GitHub App/OAuth.
2.  Select allowed repositories.
3.  Receive signed PR webhook.
4.  Validate signature and deduplicate event.
5.  Fetch permitted PR metadata and changed files.
6.  Analyze changed code for likely accessibility concerns.
7.  Optionally scan an explicitly authorized preview deployment.
8.  Map findings to files/lines only where mapping is reliable.
9.  Publish PR check/comment with severity, evidence, WCAG source and
    suggestions.
10. Developer updates PR; AccessGuard reruns and updates the check.

## MVP scope

-   GitHub App installation.
-   Repository selection.
-   Signed webhook.
-   Changed-file analysis.
-   Advisory status/check summary.
-   Link to detailed AccessGuard report.

Later: - Preview URL scan. - Inline annotations. - Baseline
comparison. - Re-run on every commit. - Team policies.

## Security

Least privilege, signed webhook validation, replay defense, encrypted
tokens, no frontend token exposure, repository allowlist, isolated
processing, no arbitrary code execution in API process, SSRF controls
for preview URLs, prompt-injection defense and disconnect/revocation.

## Acceptance

Invalid webhook rejected; duplicate event idempotent; unauthorized
repository denied; token never exposed; check tied to correct commit
SHA; comments do not spam; no claim static analysis equals browser
audit.

# 16. Feature 4 --- Keyboard Navigation Auditor

## Goal

Test keyboard-only interaction beyond static axe checks.

## Checks

Tab/Shift+Tab order, visible focus, focus order vs visual order, traps,
Escape, Enter/Space activation, skip links, modal focus restoration,
disabled controls, unreachable controls and focus loss after dynamic
updates.

## UX

Start controlled keyboard audit; show focus-order sequence and
screenshots; report traps/unreachable controls; provide reproducible key
sequence and WCAG references where verified.

## Technical

Use Playwright keyboard APIs. Record target, accessible name, role,
selector and sequence. Use deterministic scripts for common controls. Do
not trigger destructive actions. Support bounded exploration and
application-specific scripts.

## Limits

A finite keyboard test does not prove all workflows keyboard accessible.
Dynamic applications may need human review.

## Acceptance

Sequence reproducible; trap evidence recorded; focus visible;
destructive actions avoided; results link to evidence.

# 17. Feature 5 --- Screen Reader Experience Inspector

## Goal

Inspect browser-exposed semantics and accessible names. This is not a
replacement for testing with actual screen readers.

## Capabilities

Accessible name/role, heading outline, landmarks, form label
relationships, button/link names, image alt text, ARIA states, live
regions, dialog semantics, table headers and approximate reading order.

## UX

Semantic tree beside page preview. Selecting node highlights element.
Show role, name, description, state and selector. Flag
missing/suspicious names.

## Technical and limits

Use supported browser accessibility tree APIs where available, DOM
semantics as labeled fallback. Record browser/version. Do not claim
NVDA/VoiceOver equivalence unless actually integrated and tested.

## Acceptance

Tree derives from actual evidence; selected node maps correctly;
findings traceable; limitations visible; sandbox remains isolated.

# 18. Feature 6 --- Continuous Accessibility Regression Monitoring

## Goal

Schedule scans and compare each new run with baseline to identify
regressions.

## UX

1.  Select verified project.
2.  Configure cadence and allowed window.
3.  Schedule recurring scan.
4.  Execute through background worker.
5.  Compare with previous baseline.
6.  Show new, resolved, unchanged, severity changes, page changes and
    coverage differences.
7.  Notify user on meaningful regressions.
8.  Open exact evidence.

## Finding matching

Do not rely only on CSS selector. Use rule ID, canonical page URL,
selector/path, node fingerprint, attributes, context and scanner/browser
version. Matching may be uncertain after DOM changes; expose uncertainty
rather than claiming resolution.

## Scheduling

Prevent unintended overlapping jobs; support retries/backoff,
pause/resume/delete, run history and rate limits. Keep domain
authorization active. Never scan beyond authorized scope.

## Acceptance

Schedules persist; runs execute on cadence; comparisons evidence-based;
failed scans not shown as regression-free; notifications use configured
channels only.

# 19. Feature 7 --- Conversational Accessibility Assistant

## Goal

Answer questions about the user's own findings and verified WCAG corpus.

Examples: - "Why was this element flagged?" - "Explain WCAG 1.4.3." -
"Which critical issues should I prioritize?" - "Show findings related to
accessible names." - "Explain this proposed patch." - "Compare the last
two scans."

## Architecture

Authenticated backend endpoint; tenant-scoped retrieval; RAG over
verified sources; structured outputs and citations; project-scoped
conversation context; page content treated as untrusted;
prompt-injection defense; no approval or patch application without
explicit human workflow.

## Answer structure

Separate scan evidence, retrieved guidance, AI interpretation,
recommended action and limitations. Citations must resolve to actual
sources. If no source supports a claim, say so.

## Acceptance

Real scan/RAG context; tenant isolation; valid citations; provider
errors handled; AI cannot bypass approval.

# 20. Feature 8 --- Advanced Accessibility Analytics

## Metrics

Findings by severity over time, new/resolved, mean time to remediate,
repeat/regression rate, WCAG criterion distribution, page finding
density, scan coverage, proposal acceptance, validation success and
outstanding finding age.

## Data rules

Use persisted history. Document formulas. Distinguish missing from zero.
Do not average incomparable partial scans without explanation. Include
coverage/timestamps. Export actual data.

## Acceptance

Metric definitions documented; charts match API; filters update all
charts; no fabricated history; failed/incomplete scans represented
honestly.

# 21. Feature 9 --- Accessibility Evidence Passport

## Goal

Versioned evidence package documenting testing activity and remediation
progress. This is not a legal certification.

## Contents

Project and domain, verification status, scan dates/versions, pages and
coverage, automated test scope, engine version, findings, WCAG
references, remediation decisions, snapshot validation, outstanding
risks, reviewer notes if entered, limitations, export timestamp and
report ID.

## Integrity

Stable report ID, optional artifact hash, source scan IDs,
immutable/versioned historical reports, verification endpoint only if
securely implemented. Never call it a WCAG certificate.

## Acceptance

Every claim traces to evidence; historical report immutable/versioned;
integrity check works; disclaimer visible; no unsupported compliance
claims.

# 22. Feature 10 --- Multi-Viewport Accessibility Matrix

## Goal

Test same site at several viewport sizes and identify responsive-only
issues.

## Viewports

Small mobile, large mobile, tablet portrait/landscape, laptop and
desktop, with documented dimensions/device scale factor.

## Checks

Horizontal overflow, clipping, touch targets, responsive navigation,
modal overflow, focus order, hidden content, sticky obstruction,
zoom/reflow where testable, contrast and text visibility.

## Results

Finding by viewport, screenshot, exact browser parameters,
cross-viewport comparison and reproducible evidence.

## Acceptance

Every result includes viewport; screenshots match; no claim that a
limited matrix proves universal accessibility.

# 23. Feature 11 --- Team Workspaces & Review Assignments

## Capabilities

Organization/workspace, member invites, roles, project ownership,
finding assignment, reviewer assignment, comments, activity timeline,
audit log and notification preferences.

## Security

Strict tenant isolation, server-side authorization, hashed/expiring
invite tokens, audited role changes, least privilege, no client-only
permission enforcement, export authorization and membership/session
revocation.

## Acceptance

Cross-tenant tests pass; roles enforced server-side; audit events
persist; invites expire/revoke; UI reflects permissions.

# 24. Feature 12 --- Safe Remediation Policy Studio

## Goal

Allow organizations to define which patch types are permitted,
review-required or prohibited.

Example policies: - Alt text changes: approval required. - Adding
aria-label: evidence and review required. - Role changes:
high-risk/manual review. - Focus order changes: manual review. - Visible
content rewrite: explicit review. - Removing controls: prohibited. -
Scripts/event handlers: prohibited. - External URL changes: prohibited
unless explicitly allowed.

## Policy engine

Versioned deterministic rules, reason codes, test fixtures, approval
requirements, audit history and simulation before activation. AI must
never define or weaken its own safety policy.

## Acceptance

Disallowed patch rejected before snapshot application; decisions
explainable; policy changes versioned/audited; no LLM bypass.

# 25. Suggested future roadmap

  -----------------------------------------------------------------------
  Phase                   Features                Rationale
  ----------------------- ----------------------- -----------------------
  19                      Visual heatmap +        Makes core
                          before/after preview    scan/remediation value
                                                  tangible

  20                      Keyboard auditor +      Adds interaction
                          screen reader inspector testing beyond axe

  21                      Continuous regression   Turns one-off scans
                          monitoring              into ongoing value

  22                      Conversational          Improves investigation
                          assistant + analytics   and visibility

  23                      GitHub PR integration   Integrates with
                                                  developer workflow

  24                      Evidence Passport +     Enterprise governance
                          policy studio           and trust

  25                      Team workspaces +       Collaboration and scale
                          multi-viewport matrix   
  -----------------------------------------------------------------------

This is a suggested sequence, not a promise or fixed requirement.
Reassess after Phase 18 user feedback and actual release evidence.

# 26. Antigravity execution instructions

Before work: 1. Read this entire blueprint. 2. Read README and project
instructions. 3. Inspect Git branch/worktree. 4. Read
`artifacts/qa/BUG_REPORT.md`, `INTERACTION_AUDIT.md`, `UI_UX_AUDIT.md`.
5. Verify each reported issue in current code/runtime. 6. Create
baseline and plan. 7. Report confirmed defects and dependencies.

During work: - Follow workstream order. - Preserve architecture unless a
documented reason requires change. - Implement real backend behavior,
not frontend-only appearance. - Add regression tests for each fix. - Run
focused tests after each change. - Run full relevant suite at workstream
completion. - Keep docs current. - Commit only verified work. - Never
commit secrets or local data. - If provider, DNS, credential or service
is unavailable, record BLOCKED and do not fabricate success.

After work: 1. Start full Docker stack. 2. Start standalone development
setup. 3. Run complete controlled journey. 4. Test all routes and
visible controls. 5. Inspect console/network errors. 6. Test responsive
sizes and both themes. 7. Capture genuine screenshots. 8. Run security
regression. 9. Fix defects and re-test. 10. Produce all Phase 18 QA
artifacts. 11. Report exact commits, commands, test outcomes and
limitations. 12. Stop. Do not start Phase 19 without explicit approval.

Final Antigravity report must include: - Workstreams
complete/deferred. - Materially changed files. - Migrations/API
changes. - Docker and local startup results. - Backend/frontend test
totals and failures. - Lint/typecheck/build. - E2E workflows
passed/failed/blocked. - Interaction audit totals. - Bug counts by
severity before/after. - Security regression results. - Bundle size
before/after. - Screenshot/artifact location. - Commit hashes and
branch. - Remaining limitations. - Evidence-based readiness verdict.

A mock unit test is not proof of live integration. A green build is not
proof of a working product. A blocked provider call is not a successful
AI workflow.

# 27. Product quality principles

1.  Evidence over claims.
2.  Unknown is not zero; unscanned is not compliant; failed is not
    clean.
3.  Preserve security boundaries.
4.  AI proposes; humans approve; deterministic policy validates.
5.  Every visible control must perform its stated action.
6.  AccessGuard AI must itself be accessible.
7.  Fresh developer setup must be reproducible.
8.  Prefer maintainable modular code over speculative abstraction.
9.  Measure performance before and after.
10. State exactly what automated scans can and cannot establish.

**End of master blueprint.**
