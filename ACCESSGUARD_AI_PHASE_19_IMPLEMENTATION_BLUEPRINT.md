# AccessGuard AI — Phase 19: Advanced Accessibility Intelligence & Developer Workflow

> **Document type:** End-to-end implementation specification and execution contract  
> **Target repository:** AccessGuard AI  
> **Target branch:** `main`  
> **Planned feature commits:** Exactly 10 — one coherent commit per feature  
> **Implementation mode:** Extend the existing application; do not rebuild or replace its core  
> **Audience:** Antigravity / implementation agent, reviewer, tester and project owner  
> **Status:** Proposed plan. Nothing in this document means implementation has started or any test has passed.

---

## 0. Mission and non-negotiable outcome

Implement the ten requested capabilities as an integrated extension of the existing AccessGuard AI product:

1. Visual Accessibility Heatmap
2. Live Before-and-After Comparison
3. Autonomous Accessibility Agents
4. Screen Reader Simulator
5. Keyboard Navigation Simulator
6. Accessibility Regression Monitoring
7. GitHub Pull Request Integration
8. Conversational Accessibility Assistant
9. Responsive Accessibility Testing
10. Accessibility Compliance Passport

The result must be a reliable, secure, evidence-based accessibility engineering platform. It must not become a collection of disconnected demo screens, simulated results, fake integrations or AI-generated claims.

### 0.1 Existing product baseline

The available project documentation describes the following existing implementation. Treat this as a documented baseline, **not a substitute for inspecting the live repository**:

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis and Celery.
- Frontend: React, TypeScript, Vite and Tailwind CSS.
- Browser scanning: Playwright and bundled axe-core.
- AI workflow: LangGraph with configured Gemini/Groq provider adapters.
- Knowledge: WCAG 2.2-oriented RAG with dense and lexical retrieval.
- Existing domain workflows: account/session management, projects, DNS TXT domain verification, scans, pages, findings, scan events, remediation proposals, human approval/rejection, isolated DOM snapshot patching, snapshot re-audit and reports.
- Existing security controls documented include tenant isolation, verified-domain scan authorization, SSRF mitigation, safe DOM patch operation constraints, session revocation, CSV formula-injection defense and scan cancellation.
- Existing audit documentation reports a completed Phase 18 acceptance audit, with a few explicitly documented host/runtime limitations and code-quality debt at that audit point.

Before implementation, inspect the current checked-out repository, current `main` commit, actual migrations, models, routes, services, tests, package versions and current test results. The repository state wins over this document if it differs. Do not assume that every item in a historical report is still true.

### 0.2 Product boundary

AccessGuard AI is an accessibility testing and engineering-assistance product. It is **not** a legal certification service, an official WCAG conformance evaluator, a replacement for disabled-user testing, or a tool that can prove complete accessibility from automated checks alone.

Use accurate product language:

- “Automated accessibility findings”
- “Manual review recommended”
- “Screen-reader-oriented reading preview”
- “Keyboard interaction test”
- “Viewport-specific automated results”
- “Regression detected against selected baseline”
- “Evidence passport” or “audit evidence record”

Do not display “WCAG certified”, “100% compliant”, “fully accessible”, or equivalent claims based solely on scanner output, AI reasoning or a score.

### 0.3 Required execution behavior

The implementation agent must:

1. Inspect before editing.
2. Preserve all working core behavior.
3. Write a baseline and identify current test commands/results in its working notes.
4. Implement one feature at a time in the order specified below.
5. Add deterministic tests alongside each feature.
6. Run focused tests, then the complete relevant regression suite.
7. Fix failures caused by the new work; do not weaken or delete existing tests.
8. Create exactly one meaningful commit after each feature has passed its acceptance gate.
9. Keep all ten feature commits on `main`, unless the owner explicitly changes this instruction.
10. Stop and report a blocker rather than inventing an API, provider capability, test result or repository structure.

**Commit policy:** The target is exactly ten feature commits. Do not create separate “setup”, “cleanup”, “fix”, “docs” or “test-only” commits. Include implementation, tests and documentation for a feature in its single commit. If a feature cannot safely fit in one commit, do not silently create extra commits; stop and request approval to revise the commit constraint. Never create an empty commit. Never commit failing or unverified work.

---

## 1. System-wide architecture and integration rules

### 1.1 Extend the modular monolith

Keep the existing FastAPI application and React application. Add modules/services following the current repository conventions. Do not introduce microservices, a second database, a new queue, a new frontend framework, or an unnecessary orchestration layer.

Likely integration boundaries (verify exact paths/names before editing):

| Existing capability | New features that should reuse it |
|---|---|
| Project and verified-domain authorization | All project-level scans, scheduled scans and GitHub repository mappings |
| Playwright browser lifecycle | Heatmap evidence, comparison capture, keyboard tests, responsive viewport runs |
| axe-core execution and normalized findings | Heatmap severity, comparison outcomes, regression detection, responsive results |
| Scan / ScanPage / Finding persistence | Historical baselines, viewport runs, comparison evidence and passport |
| Scan events and existing progress transport | Long-running agent and test-run progress |
| RAG knowledge service | Agent evidence, assistant answers and criterion references |
| LLM provider abstraction | Agent reasoning and conversational responses |
| LangGraph workflow conventions | Specialized accessibility agents and assistant orchestration |
| Remediation proposal state machine | Before/after preview; preserve human approval |
| Isolated snapshot patcher and re-audit | Safe comparison and remediation verification |
| Existing reports/export services | Passport generation and evidence references |
| Authentication and tenant scoping | GitHub connections, schedules, assistant history and evidence access |

Do not duplicate business rules in routes or frontend components. Routes should validate requests, authorize the caller and delegate to services. Frontend views should consume typed API contracts rather than manufacture domain state.

### 1.2 Establish a feature capability boundary

Create or extend a central capability/service layer only if the existing architecture lacks a suitable location. Each feature must expose explicit input/output schemas and typed errors. Avoid one oversized “accessibility manager” service.

A feature must be independently testable and must fail safely if an optional integration is unavailable. For example, no GitHub token must not break ordinary scans; no LLM key must not break deterministic keyboard or axe tests.

### 1.3 Persistence and migration rules

- Use the existing database and migration framework.
- Inspect current models and migration head before adding tables or columns.
- Prefer normalized relational records for ownership, lifecycle, run status and relationships.
- Store large screenshots, HTML snapshots, traces and generated files using the repository’s existing artifact/storage strategy. Do not place unbounded binary blobs in ordinary relational rows unless that is already an intentional project convention.
- Store stable object keys and metadata in the database; do not expose internal filesystem paths.
- Add foreign keys, indexes, tenant ownership constraints and deletion behavior deliberately.
- Migrations must work from both a clean database and the current production-like schema.
- Never edit an already-applied migration. Add a forward migration.
- Do not silently cascade-delete audit evidence or GitHub installation records.
- Use UTC timestamps in storage and convert only for display.
- Use idempotency keys or uniqueness constraints for retried background jobs and webhook deliveries.

### 1.4 API and frontend compatibility

- Follow existing `/api/v1` conventions and response/error envelopes.
- Keep current endpoints backward compatible unless an explicit versioned change is unavoidable.
- Reuse existing authentication and project access checks.
- Do not leak whether another tenant owns a guessed object ID.
- Use typed request/response schemas and frontend API types.
- Add pagination to potentially large lists.
- Add explicit states: queued, running, completed, failed, cancelled, partially completed where appropriate.
- Display empty, loading, stale, unavailable and error states honestly.
- Do not insert placeholder data into normal runtime screens.

### 1.5 Security invariants — mandatory for every feature

1. **Tenant isolation:** Every new query and object lookup must be scoped to the authenticated tenant/user according to existing authorization rules. Test cross-tenant IDs.
2. **SSRF protection:** All browser navigation and resource fetching must pass through the existing URL/domain validation and network egress controls. Revalidate every redirect and resolved address. Block loopback, private, link-local, metadata and other prohibited destinations. Do not bypass the verified-domain gate for convenience.
3. **No arbitrary code execution:** Do not execute website JavaScript supplied by users, LLM output, repository content or GitHub comments on the backend. Playwright must load only the authorized target under the scanner’s existing sandbox policy.
4. **Secret protection:** Never log OAuth tokens, GitHub installation tokens, cookies, authorization headers, API keys or raw webhook secrets. Encrypt stored credentials using an established project secret-management approach; if no safe encryption mechanism exists, stop and design one before storing tokens.
5. **LLM is untrusted:** Website text, DOM, alt text, repository files, pull-request descriptions and issue comments are untrusted prompt-injection inputs. Treat them as data, not instructions. Tool access must be allowlisted and server-authorized.
6. **Human approval:** AI suggestions must never automatically modify a live production website or merge a pull request. Preserve the existing remediation approval/rejection state machine.
7. **Artifact privacy:** Screenshots, snapshots, traces, reports and assistant context may contain personal or confidential information. Enforce tenant access, retention and deletion policies.
8. **Resource limits:** Bound pages, depth, redirects, timeouts, screenshot dimensions, browser contexts, concurrent jobs, token usage and artifact size.
9. **Auditability:** Record who initiated, approved, rejected, connected, disconnected, exported or changed a scheduled task.
10. **Dependency integrity:** Pin and review new dependencies. Do not add a package merely because a tutorial mentions it.

### 1.6 Accessibility of AccessGuard itself

Every new screen and control must meet the same standard the product promotes:

- Semantic landmarks and heading hierarchy.
- Full keyboard operation and visible focus.
- Accessible names and descriptions.
- Contrast appropriate to WCAG 2.2 AA targets.
- Dialog focus management and Escape behavior where appropriate.
- No color-only status communication.
- Reduced-motion support.
- Responsive layout and zoom/reflow checks.
- Automated frontend accessibility tests plus manual keyboard review.

---

## 2. Phase 19 readiness gate — do this before Feature 1

This is required preparation inside the first feature’s work, not an extra commit.

### 2.1 Repository inspection

Inspect and record:

- `git status`, current branch and current commit.
- Full project tree for backend, frontend, tests, migrations, CI and docs.
- Existing architecture documentation and API conventions.
- Current ORM models and migration head.
- Current Playwright scanner lifecycle, browser context options and network restrictions.
- Existing axe-core injection/version and result normalization.
- Existing scan status/event behavior and cancellation semantics.
- Existing snapshot capture, sanitization, patching and re-audit pipeline.
- Existing RAG and LangGraph interfaces.
- Existing report generation and artifact storage.
- Existing frontend routes, design tokens, API client, state/query patterns and test setup.
- Existing GitHub Actions workflows.
- Existing secrets/configuration validation.

### 2.2 Baseline verification

Run the repository’s actual documented commands. Do not copy commands from this plan if package scripts differ. At minimum, identify and execute:

- Backend lint, format check, type check (if configured), unit and integration tests.
- Frontend lint, TypeScript check, unit/component tests and production build.
- Existing scanner fixture tests.
- Existing authentication, tenant-isolation, SSRF, domain-verification and cancellation tests.
- Existing remediation approval, safe-patching and snapshot re-audit tests.
- Migration check against a clean database and an upgraded database where the local environment supports it.

Record exact command, exit code, test count and blockers in a Phase 19 baseline note. A host service restriction is a blocker to the affected test, not a pass. Do not change core code simply to make a baseline test pass unless the defect is independently confirmed and the owner approves expanding scope.

### 2.3 Baseline acceptance

Do not start feature implementation until:

- Current branch is `main` and working tree is understood.
- Existing tests have a recorded baseline.
- No uncommitted user work will be overwritten.
- The current database migration head is known.
- Existing core workflows can be run or any environmental blocker is documented.
- A rollback strategy exists for new migrations and feature flags.

---

# 3. Feature 1 — Visual Accessibility Heatmap

**Priority:** Very high  
**Commit:** `accessibility: add evidence-linked visual accessibility heatmap`

## 3.1 User outcome

A user opens a completed scan page and sees the actual page screenshot with overlays marking the locations of detected accessibility findings. Each marker communicates severity and links to the exact finding record and evidence. The user can filter markers and inspect the element, rule, WCAG reference, selector and explanation.

The heatmap is an evidence visualization, not a new detection engine and not a claim that every inaccessible element has been found.

## 3.2 Technical design

### Capture and evidence model

Use the existing Playwright scan result and `ScanPage` / `Finding` relationships wherever possible. Extend the scan pipeline to capture a screenshot and element geometry only when it can be done safely and consistently.

For each finding eligible for a visual marker, persist or derive:

- Scan and page IDs.
- Finding ID.
- Stable CSS selector or existing target path.
- Rule ID and impact/severity.
- Bounding rectangle: x, y, width, height.
- Viewport width and height.
- Device pixel ratio.
- Scroll position if capture is viewport-based.
- Screenshot/artifact key and content hash.
- Capture timestamp.
- Geometry status: `located`, `not_located`, `ambiguous`, `stale`.
- Optional confidence/quality metadata with a documented deterministic meaning.

Do not use an LLM to invent coordinates. Geometry must come from the browser DOM at capture time. If a selector matches multiple nodes, record ambiguity and do not pretend a single target is certain. If an element is detached, hidden, off-screen or has zero-size geometry, represent that honestly.

### Geometry capture

- Query DOM geometry in the same page state used for the finding.
- Prefer the axe result node target path and validate it against the DOM.
- Use `getBoundingClientRect()` and account for the screenshot coordinate system.
- Define whether screenshot capture is viewport or full-page. Do not mix coordinate systems.
- For viewport screenshots, include scroll offset in the transformation when overlays are rendered in document coordinates.
- Account for device pixel ratio when converting CSS pixels to image pixels.
- Re-capture or mark evidence stale if the page changes between axe execution and geometry capture.
- Do not use arbitrary selector interpolation. Pass selectors as data and use safe browser evaluation patterns.
- Do not add a second unbounded page load just to calculate geometry.

### Overlay rendering

Render overlays in a dedicated viewer layer over the screenshot, not by mutating the captured screenshot. Use a positioned container with the screenshot as its image and a transparent overlay layer. Keep coordinate transforms centralized and tested.

Visual rules:

- Severity colors must be accompanied by text/icon/shape, not color alone.
- Use restrained borders and numbered markers for overlapping findings.
- Clicking a marker selects the finding and opens the existing finding detail experience.
- Clicking a finding in the list highlights the corresponding marker.
- Provide filters for impact, rule, page and geometry availability.
- Support zoom/pan or a clear fit-to-view control without distorting geometry.
- Include a table/list alternative for users who cannot use the visual overlay.
- Provide an explicit “location unavailable” state.

### Suggested UI placement

Add a “Visual map” or “Heatmap” tab/section to the existing scan/page detail route. Do not replace the Findings table. The original Findings workflow remains accessible.

## 3.3 API contract — adapt to existing conventions

Proposed read endpoint (only create if no equivalent exists):

`GET /api/v1/scans/{scan_id}/pages/{page_id}/heatmap`

Response should include screenshot artifact URL/reference, image dimensions, coordinate-space metadata and an array of finding markers. Return only findings the caller is authorized to view. Use short-lived signed artifact URLs if that is the established storage pattern.

Do not expose raw filesystem paths or unrestricted storage URLs.

## 3.4 Testing

Backend:
- Geometry captured for a visible single-match element.
- Zero-size, hidden, detached and missing elements are represented correctly.
- Multiple selector matches are marked ambiguous.
- CSS-pixel to image-pixel conversion is correct at DPR 1 and DPR 2.
- Viewport scroll offsets are correct.
- Screenshot metadata and geometry correspond to the same capture state.
- Cross-tenant scan/page/finding IDs return the application’s normal non-disclosing response.
- Artifact access is authorized and expires according to policy.

Frontend:
- Overlay aligns with known fixture coordinates.
- Zoom and responsive scaling preserve alignment.
- Marker/list selection stays synchronized.
- Overlapping markers remain selectable.
- Keyboard users can access every finding without using the image.
- No screenshot or marker means a useful fallback state.
- Light and dark themes remain legible.

E2E:
- Scan a deterministic fixture with known violations.
- Open its heatmap and verify marker-to-finding navigation.
- Confirm no fabricated marker is displayed for a finding without geometry.

## 3.5 Acceptance gate

Feature 1 is complete only when:
- The heatmap uses real scan evidence and real DOM geometry.
- The coordinate system is documented and covered by tests.
- Every marker links to an authorized finding.
- Ambiguous/unavailable geometry is not hidden or fabricated.
- The ordinary Findings page and scan workflow remain unchanged.
- All focused tests and core regression tests pass.

---

# 4. Feature 2 — Live Before-and-After Comparison

**Priority:** Very high  
**Commit:** `accessibility: add isolated before-and-after remediation comparison`

## 4.1 User outcome

A user selects an existing remediation proposal and sees the original captured page beside the proposed patched version. They can inspect the visual difference, DOM change and re-audit outcome before deciding whether to approve or reject the proposal.

“Live” means an interactive comparison experience in the application. It does **not** mean editing the live production website.

## 4.2 Technical design

Reuse the existing remediation proposal, approval workflow, isolated snapshot patcher and snapshot re-audit pipeline. Do not build a second patch engine.

### Comparison lifecycle

1. User opens a remediation proposal.
2. Backend verifies tenant ownership, finding ownership and proposal state.
3. Backend loads the immutable original snapshot and proposal operations.
4. Existing patch policy validates every operation.
5. Apply changes to a separate isolated copy; never mutate the original snapshot.
6. Run the existing snapshot re-audit against the patched copy.
7. Capture a sanitized after screenshot using the same controlled browser policy.
8. Generate a DOM/text or image diff as evidence.
9. Persist comparison metadata and artifact references.
10. Present original, proposed and re-audit status.
11. User explicitly approves or rejects using the existing state machine.

If validation fails, the user must still be able to inspect the failure reason and reject the proposal. Do not label a failed or incomplete validation as successful.

### Comparison outputs

- Before screenshot and after screenshot.
- Side-by-side synchronized viewport mode.
- Optional draggable image wipe, with an accessible equivalent.
- DOM patch summary: operation, target, allowed attribute/value change.
- Finding status before and after.
- Re-audit rule results.
- Any new violations introduced by the patch.
- Validation timestamp and environment metadata.
- Clear labels: “Original snapshot” and “Proposed snapshot”.

Use a deterministic image-diff algorithm only as a visual aid. Browser rendering can differ because of fonts, timing, animations and dynamic content. A pixel difference is not proof of accessibility improvement. The axe re-audit and human review remain separate evidence.

### Safety rules

- Do not open the production website in an editing mode.
- Do not run arbitrary patch JavaScript.
- Preserve the existing safe operation allowlist and selector policy.
- No external network egress from the snapshot validation environment.
- No execution of scripts embedded in untrusted snapshots.
- Do not let a comparison operation bypass approval/rejection state validation.
- Repeated approval/rejection must preserve terminal-state behavior.
- A proposal must not be applied twice unless the workflow explicitly supports an idempotent replay.

## 4.3 API and UI

Prefer existing remediation detail endpoints. Add a comparison-run endpoint only if the current API has no equivalent. Make comparison execution an asynchronous job if it exceeds normal request latency. Expose progress and final artifact references through the existing scan/event/job pattern.

Add a “Compare” action to the remediation review panel. Preserve existing Approve and Reject controls and their confirmation semantics.

## 4.4 Testing

- Original snapshot remains byte-for-byte unchanged.
- Patched snapshot is isolated and cannot access network resources.
- Unsafe attributes, event handlers, scripts and unsupported operations are rejected.
- Valid patch produces a comparison artifact and re-audit record.
- New violations are displayed; resolved findings are not inferred from visual similarity.
- Failed patch/re-audit produces a failed state, not a success badge.
- Duplicate jobs are idempotent.
- Cross-tenant access is denied.
- Existing approve/reject terminal-state tests continue to pass.
- Browser comparison handles different screenshot dimensions and missing after artifacts.
- UI has accessible labels and a non-visual diff summary.

## 4.5 Acceptance gate

The user can inspect a genuine isolated before/after result and the associated re-audit evidence before making a human decision. No live site is modified.

---

# 5. Feature 3 — Autonomous Accessibility Agents

**Priority:** Very high  
**Commit:** `ai: add evidence-grounded specialized accessibility agents`

## 5.1 User outcome

After a scan, the user can request a coordinated investigation by specialist agents. Each specialist examines one defined dimension and returns findings, evidence, confidence/limitations and practical recommendations. A coordinator consolidates overlapping observations without inventing test results.

## 5.2 Agent scope

Implement specialists as bounded workflows, not independent unrestricted bots:

1. **Contrast investigator** — reviews axe contrast results and available rendered color/background evidence. It may flag cases needing manual verification. It must not claim reliable contrast measurement from incomplete CSS or screenshot inference.
2. **Keyboard investigator** — consumes actual keyboard test events/results from Feature 5 when available. It must not claim keyboard testing occurred if no keyboard run exists.
3. **Screen-reader semantics investigator** — examines DOM accessibility semantics, accessible names, landmarks, headings and reading-order evidence. It is a static/DOM interpretation aid, not an actual NVDA/JAWS/VoiceOver execution.
4. **Semantic HTML investigator** — inspects element roles, native semantics, form relationships, labels and structural markup.
5. **WCAG mapping investigator** — maps verified findings to relevant WCAG 2.2 criteria using the existing RAG corpus and cites retrieved sources.

The agents must consume evidence generated by deterministic tools. LLMs explain and prioritize evidence; they do not manufacture scanner observations.

## 5.3 Workflow architecture

Use the existing LangGraph/provider architecture. Define typed state, bounded nodes and explicit transitions:

- Input validation and authorization.
- Evidence collection from stored scan, findings, keyboard run and DOM snapshot.
- Parallel specialist analysis where safe.
- Schema validation of each specialist result.
- Evidence/citation verification.
- Deduplication and conflict detection.
- Coordinator synthesis.
- Persistence and user-facing summary.

Each agent output should contain:

- Agent identifier and version.
- Scan/page/finding references.
- Dimension examined.
- Evidence references and source type.
- Observation.
- Recommendation.
- WCAG criterion references, if supported.
- Confidence with a documented interpretation.
- Limitations / manual verification needed.
- Status: completed, partial, skipped, failed.

Do not use a numeric confidence unless it is calibrated or its meaning is explicitly documented. Prefer qualitative labels such as `supported`, `tentative`, `insufficient evidence`.

### Prompt-injection defense

All website content, DOM text, repository text and prior assistant messages are untrusted data. Delimit and label evidence. Do not allow content to change agent instructions or invoke arbitrary tools. Agents must not access other tenants or unrelated projects.

### Cost and reliability

- Reuse scan evidence; do not recrawl by default.
- Bound model calls, tokens, retries and total runtime.
- Cache only when inputs, model/provider version, prompt version and knowledge base version match.
- Support deterministic test doubles in CI.
- If provider configuration is missing, show “AI investigation unavailable”; core scans remain functional.
- Partial agent failure must not erase successful results. Display partial status and exact failed dimensions.

## 5.4 API and UI

Add an investigation-run resource linked to a scan. Provide start, status, detail and result endpoints following existing conventions. Use the existing background job/event infrastructure for progress.

UI: “AI Investigation” panel on scan detail. Show each specialist separately, evidence links, skipped/failed labels, cited criteria and manual-review notes. The user must be able to distinguish tool evidence from AI interpretation.

## 5.5 Testing

- Each specialist receives only its declared evidence type.
- Missing keyboard/screen-reader evidence produces skipped/limited output, not fabricated success.
- Invalid structured model output is rejected or retried within a strict bound.
- Citation IDs must resolve to retrieved knowledge records.
- Prompt injection in page text cannot change tool permissions or system instructions.
- Agent cannot query another tenant’s findings.
- Parallel failure and timeout produce accurate partial results.
- Deterministic tests run without Gemini/Groq credentials.
- Live provider tests are optional and explicitly gated by configured secrets.
- Cost/time limits and retry caps are enforced.
- Agent synthesis preserves contradictory evidence rather than silently choosing one.

## 5.6 Acceptance gate

The feature produces specialist, evidence-linked investigations and honest limitations. No agent claims a test ran when it did not.

---

# 6. Feature 4 — Screen Reader Simulator

**Priority:** High  
**Commit:** `accessibility: add screen-reader-oriented page reading simulator`

## 6.1 Important product definition

A browser-based application cannot accurately emulate the complete behavior of NVDA, JAWS, VoiceOver, TalkBack or their combinations with every browser and operating system. Do not market this feature as a true screen-reader emulator.

Implement a **screen-reader-oriented reading and navigation preview** that exposes the accessibility tree/semantics available from the browser and explains the order and names that assistive technology may encounter. Include explicit limitations and encourage testing with real assistive technologies.

## 6.2 User outcome

A user selects a scanned page and sees a structured reading preview containing landmarks, headings, links, buttons, form controls, accessible names, roles, states and reading order. Suspicious or missing semantics link to existing findings where possible.

## 6.3 Technical design

Use Playwright/browser accessibility semantics supported by the installed version. Inspect the actual installed Playwright API before implementation; do not assume a removed or experimental accessibility API exists. If the preferred API is unavailable, use a standards-based DOM inspection approach with explicitly limited semantics. Do not invent an accessibility tree.

Capture a structured snapshot with:

- Node role where determinable.
- Accessible name where determinable.
- Description where determinable.
- State and properties where determinable (expanded, checked, disabled, required, selected).
- Heading level.
- Landmark type.
- Link destination (sanitized and authorized).
- DOM order.
- Parent/child relationships.
- Source selector or stable node reference.
- Source page and capture timestamp.

Avoid collecting form values, password fields, personal data or hidden sensitive text. Redact user-entered values and sensitive attributes. Apply output size limits.

### Reading preview

Provide modes:

- **Landmarks:** navigation, main, complementary, banner, contentinfo and other supported roles.
- **Headings:** outline with heading levels and order.
- **Interactive elements:** links, buttons, inputs, selects and other supported controls.
- **Reading order:** structured node sequence with role/name.
- **Potential issues:** missing accessible name, duplicate/ambiguous names, skipped heading hierarchy (as a review hint), unlabeled controls, suspicious generic roles.

Do not assert that every heading-level skip is automatically a WCAG failure. Label heuristic observations as review hints.

### Playback-style presentation

A “step through” control may move the visual highlight through the captured semantic sequence. It must not synthesize spoken audio and imply it is a real screen reader. If text-to-speech is later added, it must be clearly described as browser speech synthesis, not NVDA/JAWS/VoiceOver output.

## 6.4 Testing

- Correct role/name extraction on deterministic semantic fixtures.
- Landmark and heading order preserved.
- Hidden content handling is explicit and tested.
- Password and form values are never included in stored snapshots.
- Duplicate names are surfaced without claiming a definitive failure.
- Unsupported browser semantics return a documented limitation.
- Large DOM snapshots are bounded.
- Cross-tenant access and artifact privacy are enforced.
- Keyboard-only navigation of the simulator itself works.
- UI labels clearly state “preview/simulator” and its limitations.

## 6.5 Acceptance gate

The user can inspect a useful semantic reading preview backed by actual page structure, with sensitive values excluded and no claim of equivalence to a real assistive technology.

---

# 7. Feature 5 — Keyboard Navigation Simulator

**Priority:** High  
**Commit:** `accessibility: add deterministic keyboard navigation testing`

## 7.1 User outcome

The user starts a keyboard-only test on an authorized page and sees the actual sequence of focusable elements, focus indicators, skipped or unreachable controls, repeated focus states and potential keyboard traps.

## 7.2 Technical design

Build a deterministic browser test harness using Playwright keyboard input and DOM observation. Do not merely calculate `tabindex` order from markup; actual browser focus behavior is the evidence.

### Test procedure

1. Create an isolated browser context using existing scanner security restrictions.
2. Load the authorized page and wait for a bounded, documented readiness condition.
3. Start from a defined initial focus state.
4. Send Tab repeatedly and record `document.activeElement`.
5. Capture stable node reference, role, accessible name, tag, tabindex, bounding box and computed focus indicator evidence.
6. Send Shift+Tab to test reverse traversal.
7. Record repeated focus targets and unexpected cycles.
8. Apply a configurable but hard-capped step/time budget.
9. Detect whether focus remains trapped within a component under a defined test scenario.
10. Record the test environment, viewport, browser version and limitations.

A keyboard trap cannot always be inferred from a single Tab sequence. Test a bounded interaction protocol and label a suspected trap only when the defined protocol supports it. Do not click arbitrary controls or submit forms automatically. Do not activate destructive actions. Do not type into fields.

### Focus visibility

Capture evidence for the focused element’s outline/border/box-shadow and screenshot where feasible. CSS heuristics are not a complete proof of visible focus. Report “focus indicator evidence unavailable/needs manual review” where browser style inspection is inconclusive.

### Results

- Ordered focus sequence.
- Duplicate/cyclic sequence indicators.
- Elements with no discernible accessible name.
- Focus target outside viewport or clipped (as a review hint).
- Reverse traversal mismatch.
- Potential trap with steps/evidence.
- Focus indicator evidence and limitations.
- Test completion reason: finished, capped, timed out, blocked, failed.

Do not treat browser-internal controls or cross-origin embedded content as if they were fully tested. Record skipped frames and boundaries.

## 7.3 API and UI

Create a keyboard test-run resource linked to a scan/page and expose status, sequence and evidence. Reuse existing job/event infrastructure. Add a “Keyboard test” panel with a visual sequence, element details and clear manual-review flags.

## 7.4 Testing

Use deterministic fixtures for:
- Native links/buttons/inputs.
- Positive and negative tabindex.
- Hidden/disabled controls.
- Modal/dialog focus behavior.
- Focus trap and escape path.
- Reverse tab sequence.
- Dynamic focus changes.
- Cross-origin iframe boundary.
- Large focusable page and step cap.
- Browser timeout/cancellation.

Verify that tests never submit forms, trigger destructive buttons or type into personal data fields. Verify cleanup of browser contexts after success, failure and cancellation.

## 7.5 Acceptance gate

The simulator records actual keyboard-driven focus observations, enforces safe action limits and presents suspected issues with evidence rather than assumptions.

---

# 8. Feature 6 — Accessibility Regression Monitoring

**Priority:** High  
**Commit:** `monitoring: add historical accessibility regression detection`

## 8.1 User outcome

A user can compare a new completed scan with a selected historical baseline and identify newly introduced, resolved, persistent and changed findings. Optional scheduled scans can detect regressions over time and notify the project owner.

## 8.2 Comparison model

Never compare only total issue counts. Match findings using a stable fingerprint built from appropriate fields, such as:

- Project/page canonical URL.
- Axe rule ID.
- Normalized target/selector path.
- Relevant node identity or normalized snippet hash.
- Impact.
- WCAG tags / criterion mapping.
- Scanner and rule-set version.

The fingerprint algorithm must be versioned. A change to fingerprint logic must not silently rewrite historical outcomes.

Classifications:

- `new`: no credible baseline match.
- `resolved`: baseline finding absent in the new comparable scan.
- `persistent`: matched in both.
- `changed`: same likely issue with meaningful evidence/impact change.
- `inconclusive`: scan coverage or identity changed enough that a safe comparison is not possible.

Do not mark findings resolved if the page was not scanned, the URL changed, a scan failed, the viewport/configuration differs materially, or the baseline is not comparable. Coverage must be compared alongside results.

### Baseline selection

Allow the user to designate a successful completed scan as a baseline. A baseline must belong to the same authorized project. Record its scan ID, creation time, scanner version, axe version, crawl scope, page count and viewport configuration.

Support comparison against:
- Last successful comparable scan.
- User-pinned baseline.
- A selected historical scan.

Do not automatically replace a pinned baseline.

## 8.3 Scheduled monitoring

Add recurring scans only using the existing Celery/Redis scheduling capability if present and appropriate. Inspect current scheduler implementation first. Avoid adding a second scheduler.

Controls:
- User-defined cadence within allowed limits.
- Pause/resume/delete.
- Domain verification required.
- Re-check authorization at execution time.
- Rate/concurrency caps per tenant and domain.
- Retry policy with bounded backoff.
- Prevent overlapping runs for the same schedule unless explicitly supported.
- Record schedule owner, configuration changes and execution history.
- Respect project deletion and token/session authorization policies.

### Notifications

Use the existing notification/email/outbox mechanism if available. If no delivery integration exists, create in-app notifications first; do not claim email notifications work without a real configured provider. Notifications should summarize the regression and link to evidence, not include sensitive page content.

## 8.4 Testing

- Stable findings classify correctly.
- New/resolved/persistent/changed/inconclusive cases covered.
- Coverage reduction prevents false “resolved” classifications.
- Axe/scanner version changes are surfaced.
- URL canonicalization does not merge distinct pages incorrectly.
- Fingerprint version migrations are tested.
- Duplicate scheduled jobs are prevented.
- Pause/resume and cancellation work.
- Unverified domain schedule execution is blocked.
- Cross-tenant schedule/baseline access is denied.
- Notification delivery failure does not corrupt scan state.
- Time-zone and daylight-saving behavior is explicit; store schedule timezone and next-run UTC.
- No schedule runs after deletion/disablement.

## 8.5 Acceptance gate

Regression results are evidence-based and coverage-aware; scheduled monitoring is opt-in, bounded and securely authorized.

---

# 9. Feature 7 — GitHub Pull Request Integration

**Priority:** High  
**Commit:** `integrations: add secure GitHub pull request accessibility reviews`

## 9.1 User outcome

A user connects a GitHub repository, associates it with an authorized AccessGuard project and requests an accessibility review for a pull request. AccessGuard analyzes the relevant changed pages/code context where safely possible and posts a concise evidence-backed review comment or check result.

The integration must be useful without automatically changing code, approving or merging PRs.

## 9.2 Integration strategy

Use the official GitHub App model where practical for a multi-user product. Inspect current repository/deployment constraints before selecting GitHub App versus OAuth App. Do not implement both unless there is a concrete requirement.

Prefer least-privilege GitHub App permissions:
- Repository metadata: read.
- Pull requests: read, and write only if posting comments/checks is enabled.
- Checks: write only if creating check runs is required.
- Contents: read only if source files must be inspected.
Do not request organization administration or broad account scopes.

Use a GitHub App installation token or supported OAuth token flow, not a long-lived personal access token stored in plaintext.

### Connection and mapping

- User explicitly initiates repository connection.
- Validate callback state and OAuth/App installation authenticity.
- Store installation/repository identifiers and encrypted credential references.
- Map repository to an existing AccessGuard project.
- Require project ownership/authorization and verified website domain before crawling the target site.
- Allow repository disconnect and credential revocation.
- Do not infer a production URL from arbitrary README content or PR text.

### PR workflow

1. Receive GitHub webhook.
2. Verify signature against raw request body using constant-time comparison.
3. Enforce delivery ID idempotency.
4. Validate event/action/repository/installation and permission state.
5. Queue a bounded background job.
6. Fetch only required PR metadata and changed files using authorized API calls.
7. Treat repository content and PR text as untrusted.
8. Associate PR with an explicitly configured target URL or project mapping.
9. Run an authorized scan only if domain verification and project permissions pass.
10. Optionally analyze changed source snippets as supplementary static context; do not equate source diff analysis with rendered accessibility verification.
11. Create a check/comment with finding summaries, evidence links and manual-review caveats.
12. Persist the review and API response metadata without secrets.

### Comment design

Post a single concise summary, preferably updated rather than repeatedly spamming new comments. Include:
- Scan run and target URL.
- New and persistent high-impact findings.
- WCAG references where grounded.
- Links to AccessGuard evidence.
- Coverage limitations.
- Clear statement that this is an automated review, not certification.
- No full DOM snapshots, secrets, personal data or excessive page content.

Do not post AI-generated inline code suggestions as if they were verified fixes. If inline comments are supported, each must map to a real changed line and a verified finding; otherwise use a summary comment/check.

### Security

- Verify webhook signatures and replay/idempotency.
- Enforce installation/repository ownership on every request.
- Handle revoked/uninstalled apps.
- Restrict outbound requests to official GitHub API endpoints through the approved HTTP client.
- Validate all redirect behavior.
- Encrypt credentials and redact logs.
- Bound API pagination, file size, job concurrency and rate limits.
- Handle GitHub rate limiting with `Retry-After` and bounded retries.
- Never run repository scripts or build commands on the API server.
- If code execution/build validation is ever needed, it requires a separate hardened sandbox and is out of scope for this feature.

## 9.3 Testing

- Valid and invalid webhook signatures.
- Replay of same delivery ID is idempotent.
- Wrong installation/repository cannot access another tenant.
- Revoked installation handled safely.
- Missing/insufficient permission produces clear status.
- GitHub API timeout/rate-limit/retry behavior.
- PR with no changed files and oversized diff.
- Malicious PR description/file content prompt injection.
- Unverified target domain blocks website scan.
- Repository-to-project mapping cannot be changed by unauthorized user.
- Comment/check creation is idempotent and does not spam.
- No token appears in logs, error responses or frontend bundles.
- Mocked GitHub API tests run in CI; live tests require dedicated test-app secrets and are opt-in.

## 9.4 Acceptance gate

A user can securely connect and disconnect a repository, trigger or receive a PR review, and see real AccessGuard evidence in GitHub without automatic code changes or merge actions.

---

# 10. Feature 8 — Conversational Accessibility Assistant

**Priority:** Medium  
**Commit:** `ai: add evidence-grounded conversational accessibility assistant`

## 10.1 User outcome

Users can ask questions about their own project, scan, findings and remediation history, such as:
- “Why was this navigation flagged?”
- “Which critical findings are still unresolved?”
- “Explain this contrast result in simple terms.”
- “Show me the evidence for this recommendation.”
- “What should I fix first?”

The assistant answers from authorized application data and the existing WCAG knowledge base. It must distinguish observed facts from general guidance and uncertainty.

## 10.2 Architecture

Reuse the current LLM provider abstraction and RAG retrieval service. Do not create a second unrelated chatbot stack.

### Context resolution

Every request must be scoped to an authenticated user and explicitly selected project/scan context. Server-side authorization must run before retrieval. The model must never choose arbitrary tenant IDs or query unrestricted database records.

Allowed context sources:
- Current project metadata.
- Authorized scan and page records.
- Authorized findings and evidence references.
- Remediation proposals and their terminal/current status.
- Keyboard/screen-reader-preview/agent results when those features have records.
- Retrieved official WCAG/WAI knowledge chunks.

Do not send entire databases, raw browser profiles, secrets, password fields, GitHub tokens or unnecessary page contents to the model.

### Answer format

Use structured output with:
- Answer text.
- Evidence references to AccessGuard records.
- WCAG knowledge citations.
- Distinction between measured observation and interpretation.
- Suggested next action.
- Limitations / manual-review notice where relevant.

The server must validate every reference and citation before returning the response. An invalid reference must be removed or cause safe regeneration; never render fabricated citations.

### Tool design

If using tools, expose narrow read-only functions:
- Get authorized finding details.
- List authorized findings with filters.
- Get scan summary.
- Retrieve approved WCAG knowledge.
- Get remediation status.
- Get stored test-run results.

No assistant tool may:
- Start a scan without explicit user action.
- Approve/reject a remediation.
- Modify a website.
- Change a GitHub repository setting.
- Delete audit records.
- Access another tenant.
- Execute arbitrary code or arbitrary SQL.

For write-like actions, the assistant may explain and direct the user to the corresponding UI. Explicit confirmation workflows can be designed later, but are not required here.

### Conversation persistence

Persist only necessary conversation metadata and messages under tenant ownership. Define retention and deletion behavior. Avoid storing full sensitive DOM snapshots in chat history. Provide a way to clear conversation history if consistent with product policy.

### Streaming and failure behavior

Use existing streaming infrastructure only if already supported. Otherwise use a normal bounded request rather than adding complex transport. Handle provider timeouts, rate limits and invalid outputs gracefully. If no provider key is configured, show a clear unavailable state while keeping search/filter workflows functional.

## 10.3 UI

A contextual assistant panel on project/scan/finding pages. It must show:
- Current context label.
- Conversation messages.
- Evidence chips/links.
- WCAG citations.
- “Observed” versus “Guidance” labels.
- Loading, unavailable and error states.
- Clear conversation action according to retention policy.

Do not show generic prefilled claims or fabricated sample conversations in production.

## 10.4 Testing

- Cross-tenant context access denied before model invocation.
- Assistant answers only from authorized context.
- Prompt injection inside website content cannot expand tool permissions.
- WCAG citations resolve to retrieved sources.
- Finding links resolve to authorized records.
- Model hallucinated IDs are rejected.
- No mutation tool exists in the assistant tool registry.
- No API key configured is handled cleanly.
- Provider timeouts and malformed JSON handled.
- Retention/deletion and pagination enforced.
- User input is escaped/rendered safely; no HTML/script execution.
- Token and request budgets are enforced.

## 10.5 Acceptance gate

Assistant responses are grounded, cited, tenant-scoped and read-only. The assistant never invents scan facts or silently performs consequential actions.

---

# 11. Feature 9 — Responsive Accessibility Testing

**Priority:** Medium  
**Commit:** `scanner: add multi-viewport accessibility test matrix`

## 11.1 User outcome

A user can test a website at selected desktop, tablet and mobile viewport profiles and compare accessibility findings across those profiles. The product identifies issues that occur only at particular viewport sizes.

## 11.2 Technical design

Reuse the existing Playwright scanner and axe-core pipeline. Add a viewport matrix to scan configuration, not a separate scanner implementation.

### Viewport profiles

Provide a small documented default set, for example:
- Desktop: 1440 × 900 CSS pixels.
- Tablet: 768 × 1024 CSS pixels.
- Mobile: 390 × 844 CSS pixels.

These are test profiles, not universal device specifications. Allow custom dimensions only within hard safety bounds. Record CSS viewport, device scale factor, browser version and any mobile emulation flags.

Do not claim that a viewport width exactly represents all devices. Do not conflate viewport emulation with real hardware testing.

### Execution

- Use the same authorized page scope and crawl limits for each viewport.
- Create isolated browser contexts per viewport.
- Reuse the same scan lifecycle/cancellation mechanism.
- Run axe-core separately for each viewport.
- Store findings with viewport/run identity.
- Capture screenshots for evidence where configured.
- Bound total page × viewport combinations and concurrency.
- Ensure cookie/session state is controlled and does not leak across tenants or projects.
- Do not let one viewport’s failure silently mark the whole matrix passed.
- Return per-viewport and aggregate status.

### Comparison

Display:
- Findings shared across all viewports.
- Findings specific to one or more viewports.
- Severity changes.
- Pages not tested at a given viewport.
- Failed/partial viewport runs.
- Responsive layout observations from deterministic measurements (overflow, clipped target, horizontal scrolling) only when implemented and tested.

Do not classify every horizontal scroll as a WCAG failure. Use specific criteria and manual-review language. axe-core may not detect all reflow, zoom or touch-target issues; state that limitation.

## 11.3 API and UI

Extend scan configuration with a validated viewport profile list. Preserve defaults for existing API clients. Show a responsive matrix in scan details with per-viewport counts and evidence. Provide links to the existing finding detail view.

## 11.4 Testing

- Correct browser context dimensions per profile.
- Axe runs separately for each viewport.
- Findings retain viewport association.
- Identical findings across viewports are grouped without losing source records.
- Viewport-specific findings remain distinct.
- One viewport failure produces partial status.
- Cancellation closes all contexts.
- Concurrency and total combinations are capped.
- Invalid/extreme custom dimensions are rejected.
- Existing single-viewport scan requests remain backward compatible.
- UI works at narrow widths and is keyboard accessible.

## 11.5 Acceptance gate

A scan can run across multiple documented viewport profiles and accurately report shared, unique, partial and failed results without breaking the existing single-viewport scan flow.

---

# 12. Feature 10 — Accessibility Compliance Passport

**Priority:** Medium  
**Commit:** `reports: add versioned accessibility evidence passport`

## 12.1 User outcome

A user can generate a versioned evidence document for a project, containing the scan history and current state of automated checks, findings, resolved items, outstanding risks, WCAG references, manual-review limitations and evidence links.

The passport is an auditable snapshot of evidence, not a legal certificate or proof of full WCAG conformance.

## 12.2 Data and generation model

Create a passport snapshot from immutable references to completed scans and their evidence. Record:
- Passport ID and version.
- Project identity and authorized domain.
- Generation timestamp and generating user.
- Selected scan/baseline range.
- Scanner and axe-core versions.
- Crawl scope and page coverage.
- Viewport profiles tested.
- Total pages attempted/completed/failed.
- Findings grouped by severity and rule.
- New/resolved/persistent regression classifications where available.
- Remediation proposal statuses (proposed, approved, rejected, validation outcome).
- Snapshot re-audit results.
- Agent investigation results and limitations, if included.
- Keyboard and screen-reader-oriented preview results, with exact test type labels.
- GitHub PR review references, if configured and authorized.
- WCAG 2.2 criteria and retrieved source references.
- Manual review checklist and known untested areas.
- Artifact hashes and stable evidence references.
- Data provenance and generation version.

Only include evidence that exists and is authorized. Missing evidence must be represented as “Not tested”, “Unavailable” or “Not included”, never as a passing result.

### Versioning and integrity

- Every generated passport is an immutable version.
- Regeneration creates a new version; it does not rewrite old content.
- Store canonical structured payload and content hash.
- Hash generation must be deterministic for the same canonical payload and generator version.
- Use a documented canonicalization method before hashing.
- Do not claim cryptographic authenticity beyond what is actually implemented.
- If digital signatures are not implemented, call the field an integrity hash, not a digital signature.
- Retain source record IDs and timestamps to support audit traceability.
- Define retention and deletion behavior consistently with project privacy rules.

### Output formats

At minimum:
- Human-readable PDF.
- Machine-readable JSON.

PDF should be generated using the existing report/export stack where possible. Include:
- Cover and project metadata.
- Executive evidence summary.
- Scope and methodology.
- Findings and severity breakdown.
- Regression history.
- Remediation and validation evidence.
- WCAG references.
- Manual review and limitations.
- Evidence manifest with hashes/IDs.
- Generation/version metadata.

Do not overcrowd PDF tables or truncate important caveats. Large reports should paginate. Include page numbers and generation timestamp.

### Honest status language

Use status such as:
- “Automated evidence available”
- “No automated findings in tested scope”
- “Outstanding automated findings”
- “Manual review required”
- “Insufficient scan coverage”
- “Evidence not available”

Never use “Certified”, “Compliant”, “Passed WCAG” or a legal assurance claim based on automated results.

## 12.3 API and UI

Add passport create/list/detail/download endpoints using current report conventions. Enforce tenant and project authorization for every endpoint and artifact. Add a “Compliance Passport” section to project reports with version history and generation state.

## 12.4 Testing

- Snapshot contains only authorized project records.
- Missing scans and zero-scan projects do not receive a perfect score.
- Version generation is immutable.
- Canonical hash is deterministic.
- Any payload change changes the hash.
- PDF and JSON contain matching key totals and caveats.
- PDF handles large finding lists and page breaks.
- Artifact download is tenant-protected.
- Formula injection is prevented in any CSV/worksheet-like export.
- HTML in page titles/URLs is escaped in PDF/HTML rendering.
- Deleted/restricted source evidence is represented according to retention policy.
- Repeated generation is idempotent only when the same request key is used; otherwise a new version is explicit.
- No certification claim appears in UI, PDF, metadata or API.

## 12.5 Acceptance gate

A user can generate and retrieve immutable, traceable PDF/JSON evidence versions with accurate scope and limitations. No automated result is represented as legal certification.

---

# 13. Cross-feature end-to-end validation

Run this after all ten feature commits are integrated. It is a release gate, not an additional commit.

## 13.1 Golden end-to-end fixture

Create or reuse a deterministic local test website with:
- An unlabeled button.
- A form control with a missing label.
- A low-contrast text example.
- A semantic landmark/heading structure.
- A keyboard focus sequence and a deliberately trapped-focus test fixture.
- A responsive layout issue at a selected viewport.
- A component that changes after interaction, for safe observation only.
- A page with a valid remediation patch target.
- A page with an ambiguous selector or unavailable geometry case.

Use only local fixtures for CI. Do not depend on public websites, live GitHub, live DNS or paid LLM APIs for deterministic acceptance tests.

## 13.2 Required integrated journey

1. Register/login using the existing authentication flow.
2. Create a project and complete the existing domain-verification flow for the local fixture using the test harness’s approved mechanism.
3. Run a normal scan and verify existing scan lifecycle and findings.
4. Open the heatmap and navigate from marker to finding.
5. Open an existing remediation proposal and run isolated before/after comparison.
6. Run specialist agents using deterministic model doubles and verify evidence grounding.
7. Open the screen-reader-oriented reading preview.
8. Run keyboard navigation testing and inspect the real focus sequence.
9. Select a baseline, run a comparable scan and verify regression classification.
10. Exercise scheduled monitoring with a controllable clock/queue in tests.
11. Exercise GitHub webhook and PR workflow with mocked GitHub API responses.
12. Ask the conversational assistant a question about an authorized finding and validate citations.
13. Run desktop/tablet/mobile viewport matrix and compare results.
14. Generate PDF and JSON passport versions.
15. Attempt cross-tenant access to every new resource and artifact; verify denial.
16. Verify cancellation and cleanup of browser/worker resources.
17. Verify the original project overview, findings, remediation, reports, auth and settings still work.

## 13.3 Core non-regression suite

Re-run all existing suites covering:
- Authentication, refresh, logout and session revocation.
- Project ownership and tenant isolation.
- DNS verification and unverified-domain scan blocking.
- SSRF, redirect, DNS rebinding and prohibited IP protections.
- Scan queueing, progress, cancellation and event replay.
- Playwright lifecycle and axe normalization.
- Finding persistence and evidence retrieval.
- RAG retrieval and citation grounding.
- AI provider abstraction and structured output.
- LangGraph workflow routing and prompt-injection defenses.
- Remediation approval/rejection terminal-state rules.
- Safe snapshot patching and isolated re-audit.
- Reports, score semantics and CSV formula-injection defense.
- Frontend routes, auth guards, responsive layout, themes and accessibility.

Do not remove or weaken a test because a new feature changes a UI or response. Update tests only for a deliberate, documented contract change that preserves the underlying security invariant.

---

# 14. Quality gates, observability and operational behavior

## 14.1 Test pyramid

For every feature, add:
- Unit tests for pure logic and validation.
- Service tests for authorization, persistence and state transitions.
- API tests for request/response contracts and error handling.
- Frontend component tests for loading/empty/error/success states.
- E2E tests for the most important user journey.
- Security tests for tenant isolation, injection, SSRF and secret handling where relevant.

Prefer deterministic local fixtures and mocked external APIs. Live provider/GitHub integration tests must be opt-in and must not make CI depend on personal credentials.

## 14.2 Type and quality checks

Run the actual configured commands for:
- Backend lint and formatting.
- Backend type checking where configured.
- Frontend ESLint.
- TypeScript type checking.
- Frontend unit tests.
- Frontend production build.
- Backend unit/integration tests.
- Migration validation.
- Docker/Compose config validation where available.
- Dependency/security checks already configured.

Do not relax compiler flags, lint rules or type checking to get a green build. Do not add widespread `Any`, broad type ignores, disabled rules or blanket test skips. If a new dependency has a known vulnerability, do not suppress it without review and a documented reason.

## 14.3 Performance budgets

Measure before setting numerical targets. Enforce reasonable caps for:
- Pages per scan.
- Viewports per scan.
- Concurrent browser contexts.
- Keyboard steps per page.
- DOM snapshot nodes/bytes.
- Screenshot dimensions/bytes.
- Agent calls and tokens.
- Assistant context size.
- GitHub file/page pagination.
- Scheduled runs per tenant.
- Passport record count and PDF generation time.

Record observed runtime in test artifacts; do not invent benchmark claims.

## 14.4 Logging and monitoring

Use structured logs with correlation IDs and resource IDs. Never log secrets or sensitive page content. Record:
- Feature run ID and status.
- Duration and retry count.
- Browser cleanup status.
- Provider/GitHub API error category (not secret payload).
- Artifact write/read failures.
- Cancellation and timeout reason.
- Tenant-scoped actor/resource metadata appropriate to audit policy.

---

# 15. Ten-commit execution plan

The implementation must produce one meaningful commit for each feature, with tests and docs included in that commit. The following are the only planned feature commits:

| Order | Feature | Commit message |
|---:|---|---|
| 1 | Visual Accessibility Heatmap | `accessibility: add evidence-linked visual accessibility heatmap` |
| 2 | Live Before-and-After Comparison | `accessibility: add isolated before-and-after remediation comparison` |
| 3 | Autonomous Accessibility Agents | `ai: add evidence-grounded specialized accessibility agents` |
| 4 | Screen Reader Simulator | `accessibility: add screen-reader-oriented page reading simulator` |
| 5 | Keyboard Navigation Simulator | `accessibility: add deterministic keyboard navigation testing` |
| 6 | Accessibility Regression Monitoring | `monitoring: add historical accessibility regression detection` |
| 7 | GitHub Pull Request Integration | `integrations: add secure GitHub pull request accessibility reviews` |
| 8 | Conversational Accessibility Assistant | `ai: add evidence-grounded conversational accessibility assistant` |
| 9 | Responsive Accessibility Testing | `scanner: add multi-viewport accessibility test matrix` |
| 10 | Accessibility Compliance Passport | `reports: add versioned accessibility evidence passport` |

### 15.1 Rules for each commit

Before committing a feature:

- Inspect `git diff` and `git status`.
- Confirm only files relevant to that feature and its tests/docs are staged.
- Run focused tests and required quality checks.
- Run the core regression tests most likely to be affected.
- Check for secrets, generated private artifacts and unrelated formatting churn.
- Confirm migrations are forward-only and valid.
- Confirm no unrelated core behavior was changed.
- Write a concise implementation note with exact commands and actual results.
- Commit only after the feature acceptance gate passes.

After each commit:
- Record the real commit SHA.
- Verify the working tree state.
- Confirm the app still starts and the existing core journey remains functional.
- Do not proceed if the commit contains a known regression.

**No extra commits:** Do not create a preliminary baseline commit, shared-foundation commit, final polish commit or release commit. Include shared schema/service support in the feature commit that first needs it. If a shared change cannot logically belong to one feature, place it in the earliest dependent feature and document why.

---

# 16. Definition of done

Phase 19 is complete only when all of the following are true:

## Product
- All ten features exist in the real application.
- Each feature is connected to real backend data and existing workflows.
- No production route displays fabricated sample results.
- All limitations are visible and understandable.
- Existing core features remain available and functional.

## Engineering
- Exactly ten feature commits exist on `main`, one per feature.
- Each commit contains implementation, tests and relevant documentation.
- No empty commits or unapproved extra commits exist.
- Migrations work from clean and upgraded databases.
- All new API contracts are typed and documented.
- Background jobs are bounded, cancellable where applicable and idempotent where required.
- Browser and worker resources are cleaned up after success/failure/cancellation.

## Security
- Tenant-isolation tests cover every new resource.
- Existing SSRF and verified-domain protections remain intact.
- GitHub credentials are securely stored and redacted.
- Webhooks are signature-verified and idempotent.
- Untrusted content cannot expand LLM tool permissions.
- No feature applies changes to a live website or merges PRs.
- Artifacts and exports are access-controlled.

## Quality
- Focused tests pass.
- Full backend and frontend regression suites pass, or each blocked test is explicitly reported with evidence.
- Lint, formatting, type checks and production build pass under the repository’s existing standards.
- No existing tests were deleted/weakened to accommodate the features.
- E2E golden journey passes in the supported local test environment.
- Browser console and API logs have no new uncaught errors or secret leaks.

## Evidence and handoff
- A Phase 19 implementation report records each commit SHA, changed modules, migrations, API additions, tests run and exact results.
- Known limitations and unverified external integrations are listed.
- Screenshots are genuine captures from the running application.
- No claim of WCAG certification or complete conformance is made.

---

# 17. Required final implementation report

At the end, produce `docs/phase-19/FINAL_IMPLEMENTATION_REPORT.md` (or the repository’s established equivalent) containing:

1. Final verdict: complete, partially complete or blocked.
2. The ten feature-by-feature implementation summaries.
3. Exactly ten commit messages and real SHAs, if all ten were completed.
4. Files/modules changed per feature.
5. Database migrations and rollback notes.
6. API endpoints and schemas added/extended.
7. Frontend routes/components added/extended.
8. External configuration required (GitHub App, provider key, scheduler, artifact storage).
9. Exact test commands and actual output summaries.
10. Security checks and cross-tenant test results.
11. Performance observations and resource limits.
12. Known limitations and manual test requirements.
13. Deployment/configuration steps.
14. Any blocked items, with the reason and evidence.

Never fill the report with assumed values. If a feature was not implemented or a test did not run, say so plainly.

---

# 18. Master instruction for the implementation agent

Read this complete specification and the current repository documentation before changing code. Inspect the actual repository and current `main` state first. The existing AccessGuard AI application is already implemented; your job is to extend it, not recreate it.

Implement the ten features in the exact order in Section 15. Create exactly one meaningful commit per feature and no more than ten commits total. Include that feature’s backend, frontend, persistence, tests, security checks and documentation in its one commit. Do not create empty commits. Do not start a feature until the previous feature’s acceptance gate passes.

Preserve the existing FastAPI/React architecture, Playwright/axe-core scanner, RAG/LangGraph provider architecture, authentication, tenant isolation, verified-domain requirement, SSRF defenses, scan lifecycle, remediation approval state machine, isolated snapshot patching and reporting behavior. Reuse existing abstractions whenever possible. Inspect actual code and installed package APIs rather than assuming names or capabilities.

Do not invent test results, data, screenshots, provider behavior, GitHub responses or compliance status. Do not replace real functionality with mock data. Mocks are allowed only in deterministic automated tests. Do not weaken lint/type/compiler settings or existing tests. Do not execute arbitrary website/repository code. Do not let AI agents modify live websites or merge pull requests. Do not claim that the screen-reader preview is equivalent to NVDA/JAWS/VoiceOver. Do not claim automated scans certify WCAG conformance.

After each feature, run its tests, relevant core regression tests, lint/type/build checks and inspect the diff before committing. If a requirement cannot be implemented safely within the ten-commit constraint, stop and report the exact blocker instead of silently violating the constraint.

At the end, deliver the report specified in Section 17 with actual commit SHAs and exact verification evidence. A green UI alone is not completion; the feature must be real, secure, tested and integrated end to end.

---

# 19. Technical references to verify during implementation

Use official documentation for the exact installed versions. Do not copy API calls from an outdated blog post.

- W3C Web Content Accessibility Guidelines (WCAG) 2.2: https://www.w3.org/TR/WCAG22/
- W3C WAI-ARIA 1.2: https://www.w3.org/TR/wai-aria-1.2/
- WAI-ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
- axe-core project and rule documentation: https://github.com/dequelabs/axe-core
- Playwright documentation: https://playwright.dev/docs/intro
- FastAPI documentation: https://fastapi.tiangolo.com/
- SQLAlchemy documentation: https://docs.sqlalchemy.org/
- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- GitHub Apps documentation: https://docs.github.com/en/apps
- GitHub webhook security: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- GitHub REST API: https://docs.github.com/en/rest
- PDF generation library documentation already used by the repository.

Documentation links are starting points, not proof that a particular method exists in the installed package version. Check the package lock/versions and official version-specific docs before implementation.
