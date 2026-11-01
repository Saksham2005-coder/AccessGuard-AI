"""Phase 20 Comprehensive End-to-End Acceptance Test Suite.

Validates all 12 core platform and Phase 19 feature workflows (A through L)
with real database persistence, tenant isolation, and cryptographic integrity.
"""

import hashlib
import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.finding import Finding
from app.db.models.remediation import Remediation
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.services.passport_service import compute_deterministic_integrity_hash


async def create_authenticated_user(client: AsyncClient, email_prefix: str) -> tuple[str, str]:
    """Helper to register and login a test user, returning (user_id, access_token)."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "display_name": "Acceptance User"},
    )
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return user_id, token


@pytest.mark.asyncio
async def test_workflow_a_auth_and_project_lifecycle(async_client: AsyncClient) -> None:
    """Workflow A: Authentication, session management, project CRUD, and tenant boundary enforcement."""
    # 1. User A Register & Login
    user_a_id, token_a = await create_authenticated_user(async_client, "user_a")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B Register & Login
    user_b_id, token_b = await create_authenticated_user(async_client, "user_b")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. User A creates project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Alpha Web Portal", "base_domain": "alpha.example.com"},
        headers=headers_a,
    )
    assert proj_resp.status_code == 201
    proj_data = proj_resp.json()
    proj_id = proj_data["id"]
    assert proj_data["name"] == "Alpha Web Portal"
    assert proj_data["base_domain"] == "alpha.example.com"
    assert proj_data["is_verified"] is False

    # 3. User A lists projects -> contains project
    list_resp = await async_client.get("/api/v1/projects", headers=headers_a)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(p["id"] == proj_id for p in items)

    # 4. User B cannot access User A's project (Tenant Isolation)
    unauth_resp = await async_client.get(f"/api/v1/projects/{proj_id}", headers=headers_b)
    assert unauth_resp.status_code == 404

    # 5. User A retrieves project detail
    detail_resp = await async_client.get(f"/api/v1/projects/{proj_id}", headers=headers_a)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == proj_id

    # 6. User A updates project
    patch_resp = await async_client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Alpha Portal Updated"},
        headers=headers_a,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Alpha Portal Updated"

    # 7. User A deletes project
    del_resp = await async_client.delete(f"/api/v1/projects/{proj_id}", headers=headers_a)
    assert del_resp.status_code == 204

    # Verification of deletion
    after_del = await async_client.get(f"/api/v1/projects/{proj_id}", headers=headers_a)
    assert after_del.status_code == 404


@pytest.mark.asyncio
async def test_workflow_b_c_d_scanning_heatmap_comparison(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Workflows B, C, D: Scanning persistence, heatmap coordinate extraction, before/after comparison."""
    user_id, token = await create_authenticated_user(async_client, "scanner_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Scan Portal", "base_domain": "scan.example.com"},
        headers=headers,
    )
    project_id = uuid.UUID(proj_resp.json()["id"])

    # Seed Scan, ScanPage, Finding, and Remediation directly in DB
    scan_id = uuid.uuid4()
    page_id = uuid.uuid4()
    finding_id = uuid.uuid4()
    remediation_id = uuid.uuid4()

    scan = Scan(
        id=scan_id,
        project_id=project_id,
        requested_by=uuid.UUID(user_id),
        target_url="https://scan.example.com/home",
        status="completed",
        pages_succeeded=1,
        total_violations=1,
    )
    page = ScanPage(
        id=page_id,
        scan_id=scan_id,
        url="https://scan.example.com/home",
        normalized_url="https://scan.example.com/home",
        audit_status="completed",
    )
    finding = Finding(
        id=finding_id,
        scan_page_id=page_id,
        axe_rule_id="color-contrast",
        impact="serious",
        selector="button.cta-btn",
        description="Element has insufficient color contrast ratio of 2.4:1",
        html_snippet='<button class="cta-btn" style="color: #777; background: #fff;">Click</button>',
        fingerprint=hashlib.sha256(b"color-contrast:button.cta-btn").hexdigest(),
        bounding_box={"x": 50.0, "y": 100.0, "width": 120.0, "height": 40.0},
        geometry_status="located",
    )
    remediation = Remediation(
        id=remediation_id,
        finding_id=finding_id,
        status="proposed",
        root_cause="Contrast ratio 2.4:1 is below the WCAG 4.5:1 minimum threshold.",
        recommendation="Update button color to #111111.",
        before_snippet='<button class="cta-btn" style="color: #777; background: #fff;">Click</button>',
        after_snippet='<button class="cta-btn" style="color: #111; background: #fff;">Click</button>',
        patch_format="snippet",
        patch_payload={
            "patch_operations": [
                {
                    "op": "replace_attribute",
                    "selector": "button.cta-btn",
                    "attribute": "style",
                    "value": "color: #111; background: #fff;",
                }
            ]
        },
    )

    db_session.add_all([scan, page, finding, remediation])
    await db_session.commit()

    # Workflow B: Verify scan and findings retrieval
    scans_resp = await async_client.get(f"/api/v1/projects/{project_id}/scans", headers=headers)
    assert scans_resp.status_code == 200
    assert len(scans_resp.json()["items"]) >= 1

    findings_resp = await async_client.get(
        f"/api/v1/findings?project_id={project_id}",
        headers=headers,
    )
    assert findings_resp.status_code == 200
    assert findings_resp.json()["total"] >= 1

    # Workflow C: Visual Accessibility Heatmap
    heatmap_resp = await async_client.get(
        f"/api/v1/scans/{scan_id}/pages/{page_id}/heatmap",
        headers=headers,
    )
    assert heatmap_resp.status_code == 200
    heatmap_data = heatmap_resp.json()
    assert heatmap_data["scan_id"] == str(scan_id)
    assert heatmap_data["page_id"] == str(page_id)
    assert len(heatmap_data["markers"]) >= 1
    marker = heatmap_data["markers"][0]
    assert marker["impact"] == "serious"
    assert "x" in marker["bounding_box"]
    assert "y" in marker["bounding_box"]

    # Workflow D: Before-and-After Remediation Comparison
    comp_resp = await async_client.get(
        f"/api/v1/remediations/{remediation_id}/comparison",
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["remediation_id"] == str(remediation_id)
    assert comp_data["rule_id"] == "color-contrast"
    assert "dom_diff" in comp_data
    assert comp_data["original_rule_resolved"] is True or comp_data["passed"] is not None


@pytest.mark.asyncio
async def test_workflow_e_f_g_agents_screenreader_keyboard(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Workflows E, F, G: Autonomous investigation agents, screen reader preview, keyboard navigation."""
    user_id, token = await create_authenticated_user(async_client, "sim_user")
    headers = {"Authorization": f"Bearer {token}"}

    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Simulator Portal", "base_domain": "sim.example.com"},
        headers=headers,
    )
    project_id = uuid.UUID(proj_resp.json()["id"])

    scan_id = uuid.uuid4()
    page_id = uuid.uuid4()
    finding_id = uuid.uuid4()

    scan = Scan(
        id=scan_id,
        project_id=project_id,
        requested_by=uuid.UUID(user_id),
        target_url="https://sim.example.com/checkout",
        status="completed",
        pages_succeeded=1,
    )
    page = ScanPage(
        id=page_id,
        scan_id=scan_id,
        url="https://sim.example.com/checkout",
        normalized_url="https://sim.example.com/checkout",
        audit_status="completed",
    )
    finding = Finding(
        id=finding_id,
        scan_page_id=page_id,
        axe_rule_id="button-name",
        impact="critical",
        selector="button.icon-only",
        description="Button has no accessible text name",
        fingerprint=hashlib.sha256(b"button-name:button.icon-only").hexdigest(),
    )
    db_session.add_all([scan, page, finding])
    await db_session.commit()

    # Workflow E: Autonomous Investigation Agents
    agent_resp = await async_client.post(
        f"/api/v1/scans/{scan_id}/investigations",
        json={"force_refresh": True},
        headers=headers,
    )
    assert agent_resp.status_code == 201
    agent_data = agent_resp.json()
    assert agent_data["scan_id"] == str(scan_id)
    assert "specialists" in agent_data
    assert "remediation_matrix" in agent_data
    assert "executive_summary" in agent_data

    # Workflow F: Screen Reader Simulator
    sr_resp = await async_client.get(
        f"/api/v1/scans/{scan_id}/pages/{page_id}/screen-reader-simulation",
        headers=headers,
    )
    assert sr_resp.status_code == 200
    sr_data = sr_resp.json()
    assert sr_data["scan_id"] == str(scan_id)
    assert "landmarks" in sr_data
    assert "headings" in sr_data
    assert "reading_order" in sr_data
    # Disclaimer present
    assert "screen-reader" in sr_data["disclaimer"].lower() or "preview" in sr_data["disclaimer"].lower()

    # Workflow G: Keyboard Navigation Simulator
    kb_resp = await async_client.get(
        f"/api/v1/scans/{scan_id}/pages/{page_id}/keyboard-test",
        headers=headers,
    )
    assert kb_resp.status_code == 200
    kb_data = kb_resp.json()
    assert kb_data["scan_id"] == str(scan_id)
    assert "steps" in kb_data
    assert "summary" in kb_data
    assert "disclaimer" in kb_data


@pytest.mark.asyncio
async def test_workflow_h_i_j_regression_github_assistant(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Workflows H, I, J: Regression monitoring, GitHub pull request review, conversational assistant."""
    user_id, token = await create_authenticated_user(async_client, "workflow_hij_user")
    headers = {"Authorization": f"Bearer {token}"}

    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "DevOps Portal", "base_domain": "devops.example.com"},
        headers=headers,
    )
    project_id = uuid.UUID(proj_resp.json()["id"])

    scan1_id = uuid.uuid4()
    scan2_id = uuid.uuid4()
    page1_id = uuid.uuid4()
    page2_id = uuid.uuid4()

    scan1 = Scan(
        id=scan1_id,
        project_id=project_id,
        requested_by=uuid.UUID(user_id),
        target_url="https://devops.example.com",
        status="completed",
        pages_succeeded=1,
    )
    scan2 = Scan(
        id=scan2_id,
        project_id=project_id,
        requested_by=uuid.UUID(user_id),
        target_url="https://devops.example.com",
        status="completed",
        pages_succeeded=1,
    )
    page1 = ScanPage(
        id=page1_id,
        scan_id=scan1_id,
        url="https://devops.example.com",
        normalized_url="https://devops.example.com",
        audit_status="completed",
    )
    page2 = ScanPage(
        id=page2_id,
        scan_id=scan2_id,
        url="https://devops.example.com",
        normalized_url="https://devops.example.com",
        audit_status="completed",
    )

    f1 = Finding(
        id=uuid.uuid4(),
        scan_page_id=page1_id,
        axe_rule_id="color-contrast",
        impact="serious",
        selector="h1.title",
        description="Insufficient text contrast",
        fingerprint=hashlib.sha256(b"color-contrast:h1.title").hexdigest(),
    )
    f2 = Finding(
        id=uuid.uuid4(),
        scan_page_id=page2_id,
        axe_rule_id="color-contrast",
        impact="serious",
        selector="h1.title",
        description="Insufficient text contrast",
        fingerprint=hashlib.sha256(b"color-contrast:h1.title").hexdigest(),
    )
    f3_new = Finding(
        id=uuid.uuid4(),
        scan_page_id=page2_id,
        axe_rule_id="image-alt",
        impact="critical",
        selector="img.logo",
        description="Missing alt attribute",
        fingerprint=hashlib.sha256(b"image-alt:img.logo").hexdigest(),
    )

    db_session.add_all([scan1, scan2, page1, page2, f1, f2, f3_new])
    await db_session.commit()

    # Workflow H: Regression Monitoring
    # 1. Pin baseline
    pin_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/baseline",
        json={"scan_id": str(scan1_id), "notes": "Sprint 10 Baseline"},
        headers=headers,
    )
    assert pin_resp.status_code == 200

    # 2. Compare regressions
    reg_resp = await async_client.get(
        f"/api/v1/projects/{project_id}/regression/compare?current_scan_id={scan2_id}",
        headers=headers,
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["summary"]["new_count"] >= 1  # image-alt is new
    assert reg_data["summary"]["persistent_count"] >= 1  # color-contrast is persistent

    # Workflow I: GitHub Integration Webhook Security
    # 1. Connect repo
    gh_connect_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/github/integration",
        json={
            "repo_owner": "acme",
            "repo_name": "devops-portal",
            "webhook_secret": "SuperSecretWebhookKey123!",
            "target_branch": "main",
        },
        headers=headers,
    )
    assert gh_connect_resp.status_code == 201

    # 2. Reject unauthenticated/tampered webhook
    fake_body = json.dumps(
        {
            "action": "opened",
            "repository": {"owner": {"login": "acme"}, "name": "devops-portal"},
            "pull_request": {"number": 1},
        }
    ).encode("utf-8")
    bad_sig_resp = await async_client.post(
        "/api/v1/github/webhook",
        content=fake_body,
        headers={
            "X-GitHub-Delivery": str(uuid.uuid4()),
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalidhash00000000000000000000000000000000000000000000000000000",
        },
    )
    assert bad_sig_resp.status_code == 401

    # Workflow J: Conversational Accessibility Assistant
    chat_resp = await async_client.post(
        "/api/v1/assistant/chat",
        json={
            "project_id": str(project_id),
            "scan_id": str(scan2_id),
            "message": "Which accessibility violation should I fix first?",
        },
        headers=headers,
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["role"] == "assistant"
    assert "structured_data" in chat_data
    assert len(chat_data["structured_data"]["observed_facts"]) >= 1


@pytest.mark.asyncio
async def test_workflow_k_l_responsive_matrix_and_compliance_passport(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Workflows K, L: Responsive multi-viewport test matrix and Accessibility Compliance Passport."""
    user_id, token = await create_authenticated_user(async_client, "passport_user")
    headers = {"Authorization": f"Bearer {token}"}

    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Enterprise Audit Portal", "base_domain": "enterprise.example.com"},
        headers=headers,
    )
    project_id = uuid.UUID(proj_resp.json()["id"])

    scan_id = uuid.uuid4()
    page_id = uuid.uuid4()

    scan = Scan(
        id=scan_id,
        project_id=project_id,
        requested_by=uuid.UUID(user_id),
        target_url="https://enterprise.example.com",
        status="completed",
        pages_succeeded=2,
    )
    page = ScanPage(
        id=page_id,
        scan_id=scan_id,
        url="https://enterprise.example.com",
        normalized_url="https://enterprise.example.com",
        audit_status="completed",
    )
    f_shared = Finding(
        id=uuid.uuid4(),
        scan_page_id=page_id,
        axe_rule_id="color-contrast",
        impact="serious",
        selector="h1.banner",
        description="Contrast 2.8:1",
        fingerprint=hashlib.sha256(b"color-contrast:h1.banner").hexdigest(),
    )
    db_session.add_all([scan, page, f_shared])
    await db_session.commit()

    # Workflow K: Responsive Accessibility Testing Matrix
    matrix_resp = await async_client.post(
        f"/api/v1/scans/{scan_id}/responsive-matrix/run",
        json={},
        headers=headers,
    )
    assert matrix_resp.status_code == 200
    matrix_data = matrix_resp.json()
    assert matrix_data["scan_id"] == str(scan_id)
    assert len(matrix_data["viewport_runs"]) == 3  # Desktop, Tablet, Mobile
    assert any(f["rule_id"] == "color-contrast" for f in matrix_data["shared_findings"])
    assert any(f["rule_id"] in ("target-size", "reflow") for f in matrix_data["viewport_specific_findings"])

    # Workflow L: Accessibility Compliance Passport
    # 1. Generate Passport v1
    pass_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/passports/generate",
        json={"notes": "Q4 Enterprise Acceptance Snapshot"},
        headers=headers,
    )
    assert pass_resp.status_code == 201
    pass_data = pass_resp.json()
    assert pass_data["version"] == "v1"
    assert pass_data["project_id"] == str(project_id)
    assert len(pass_data["integrity_hash"]) == 64

    # Verify legal non-certification disclaimer
    disclaimer = pass_data["evidence_payload"]["legal_disclaimer"]
    assert "not an official wcag legal certification" in disclaimer.lower()

    # 2. Cryptographic Checksum Validation: verify recalculation matches exactly
    computed_hash = compute_deterministic_integrity_hash(pass_data["evidence_payload"])
    assert computed_hash == pass_data["integrity_hash"]

    # Verify that changing any single character in payload alters the hash
    tampered_payload = json.loads(json.dumps(pass_data["evidence_payload"]))
    tampered_payload["audit_scope"]["total_scans_included"] = 999
    tampered_hash = compute_deterministic_integrity_hash(tampered_payload)
    assert tampered_hash != pass_data["integrity_hash"]

    # 3. Export Markdown document
    export_resp = await async_client.get(
        f"/api/v1/projects/{project_id}/passports/{pass_data['id']}/export",
        headers=headers,
    )
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "AccessGuard AI — Accessibility Compliance Passport" in export_data["markdown_content"]
    assert pass_data["integrity_hash"] in export_data["markdown_content"]

    # 4. Generate Passport v2 (Verify version increment and immutability)
    pass2_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/passports/generate",
        json={"notes": "Subsequent Audit Snapshot"},
        headers=headers,
    )
    assert pass2_resp.status_code == 201
    assert pass2_resp.json()["version"] == "v2"

    # 5. List passports returns both immutable versions
    list_pass = await async_client.get(f"/api/v1/projects/{project_id}/passports", headers=headers)
    assert list_pass.status_code == 200
    assert len(list_pass.json()) == 2
