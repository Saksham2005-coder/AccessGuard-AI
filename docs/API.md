# AccessGuard AI — REST API Specification

Base URL: `/api/v1`

All requests and responses use JSON format (`application/json`) unless otherwise noted (SSE and PDF report downloads).

---

## 1. Conventions & Error Handling

Standard error envelope:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {},
    "request_id": "req_01h7x..."
  }
}
```

Standard HTTP Status Codes:
- `200 OK` — Successful query or operation
- `201 Created` — Successful resource creation
- `204 No Content` — Successful deletion or action without return body
- `400 Bad Request` — Invalid input schema or business rule violation
- `401 Unauthorized` — Missing or expired authentication token
- `403 Forbidden` — Access denied (resource owned by another user)
- `404 Not Found` — Resource not found or inaccessible
- `422 Unprocessable Entity` — Schema validation error
- `429 Too Many Requests` — Rate limit exceeded
- `500 Internal Server Error` — Unexpected server failure (sanitized; stack traces never leaked)

---

## 2. API Endpoints

### 2.1 Health Checks (Root Path)
- `GET /health/live` — Liveness probe (returns status `alive`)
- `GET /health/ready` — Readiness probe (checks PostgreSQL, Redis, Qdrant connectivity)

### 2.2 Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Create user account
- `POST /api/v1/auth/login` — Authenticate and receive JWT access token + refresh cookie
- `POST /api/v1/auth/refresh` — Refresh access token via active refresh session
- `POST /api/v1/auth/logout` — Revoke active refresh session
- `GET /api/v1/auth/me` — Retrieve authenticated user profile

### 2.3 Projects & Domain Ownership (`/api/v1/projects`)
- `POST /api/v1/projects` — Create project
- `GET /api/v1/projects` — List user's projects
- `GET /api/v1/projects/{project_id}` — Get project details
- `PATCH /api/v1/projects/{project_id}` — Update project name
- `DELETE /api/v1/projects/{project_id}` — Archive project
- `POST /api/v1/projects/{project_id}/domain-verification` — Generate DNS verification token
- `POST /api/v1/projects/{project_id}/domain-verification/check` — Verify DNS TXT record

### 2.4 Scans (`/api/v1/scans`)
- `POST /api/v1/scans` — Queue a new scan
- `GET /api/v1/scans` — List user's scans
- `GET /api/v1/scans/{scan_id}` — Get scan overview and totals
- `GET /api/v1/scans/{scan_id}/status` — Get scan execution state
- `GET /api/v1/scans/{scan_id}/events` — Server-Sent Events (SSE) progress stream
- `GET /api/v1/scans/{scan_id}/pages` — List audited pages for scan
- `POST /api/v1/scans/{scan_id}/cancel` — Request scan cancellation

### 2.5 Findings (`/api/v1/findings`)
- `GET /api/v1/scans/{scan_id}/findings` — List findings for scan (with filtering & pagination)
- `GET /api/v1/findings/{finding_id}` — Get finding details with target nodes and snippets

### 2.6 Remediations & Approvals (`/api/v1/remediations`)
- `POST /api/v1/findings/{finding_id}/remediations` — Trigger LangGraph multi-agent remediation
- `GET /api/v1/findings/{finding_id}/remediations` — List remediations for finding
- `GET /api/v1/remediations/{remediation_id}` — Get remediation proposal and citations
- `POST /api/v1/remediations/{remediation_id}/approve` — Human approval to execute snapshot validation
- `POST /api/v1/remediations/{remediation_id}/reject` — Human rejection with reviewer comments
- `GET /api/v1/remediations/{remediation_id}/validations` — Get DOM snapshot validation results

### 2.7 Knowledge Base (`/api/v1/knowledge`)
- `GET /api/v1/knowledge/sources` — List official W3C knowledge sources and chunk counts
- `GET /api/v1/knowledge/search` — Search WCAG chunks via hybrid dense-lexical retrieval

### 2.8 Reports (`/api/v1/reports`)
- `POST /api/v1/scans/{scan_id}/reports` — Generate PDF or JSON report
- `GET /api/v1/reports/{report_id}/download` — Authorized download of generated report file
