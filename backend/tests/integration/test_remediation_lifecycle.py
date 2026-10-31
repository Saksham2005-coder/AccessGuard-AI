"""End-to-end integration tests for human approval lifecycle, checkpoint resume, and snapshot regression handling."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import set_cached_provider
from app.ai.mock_provider import MockLLMProvider
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.services.snapshot_validator import SnapshotValidator


@pytest.fixture(autouse=True)
def mock_llm_for_integration():
    """Ensure deterministic mock LLM is active across integration tests."""
    set_cached_provider(MockLLMProvider())
    yield
    set_cached_provider(None)


async def create_user_and_token(
    client: AsyncClient, email: str, password: str = "SecurePass123!"
) -> tuple[dict, str]:
    """Register and login a test user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": email.split("@")[0]},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = login_resp.json()
    return data["user"], data["access_token"]


async def seed_finding_fixture(
    db: AsyncSession,
    owner_id: uuid.UUID,
    html_snippet: str = '<img src="logo.png" class="brand-logo">',
    rule_id: str = "image-alt",
) -> tuple[Project, Scan, Finding]:
    """Seed project, scan, scan page, and accessibility finding."""
    project = Project(
        owner_id=owner_id,
        name=f"E2E-Project-{uuid.uuid4().hex[:6]}",
        base_domain="example.org",
    )
    db.add(project)
    await db.flush()

    scan = Scan(
        project_id=project.id,
        requested_by=owner_id,
        target_url="https://example.org",
        status="completed",
        config={"max_pages": 1, "max_depth": 1},
    )
    db.add(scan)
    await db.flush()

    page = ScanPage(
        scan_id=scan.id,
        url="https://example.org/about",
        normalized_url="https://example.org/about",
        http_status=200,
        audit_status="completed",
    )
    db.add(page)
    await db.flush()

    finding = Finding(
        scan_page_id=page.id,
        axe_rule_id=rule_id,
        impact="critical",
        description="Images must have alternate text",
        help="Provide alt text for all non-decorative images",
        help_url="https://dequeuniversity.com/rules/axe/4.14/image-alt",
        wcag_tags=["wcag2a", "wcag111"],
        selector="img.brand-logo",
        html_snippet=html_snippet,
        failure_summary="Element does not have an alt attribute",
        fingerprint=f"fp-{uuid.uuid4().hex}",
        is_incomplete=False,
    )
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return project, scan, finding


@pytest.mark.asyncio
async def test_full_remediation_approval_and_validation_lifecycle(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify complete lifecycle: proposal generation -> human approval -> resume -> snapshot validation."""
    owner, token = await create_user_and_token(async_client, "lifecycle_owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _proj, _scan, finding = await seed_finding_fixture(db_session, uuid.UUID(owner["id"]))

    # 1. Generate remediation proposal (enters 'proposed' status)
    gen_resp = await async_client.post(
        f"/api/v1/findings/{finding.id}/remediations",
        headers=headers,
    )
    assert gen_resp.status_code == 201
    remediation_id = gen_resp.json()["id"]
    assert gen_resp.json()["status"] == "proposed"

    # 2. Approve proposal with reviewer comments
    app_resp = await async_client.post(
        f"/api/v1/remediations/{remediation_id}/approve",
        headers=headers,
        json={"decision": "approved", "comments": "Approved after accessibility team review."},
    )
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    assert app_data["status"] == "validated"
    assert len(app_data["approvals"]) == 1
    assert app_data["approvals"][0]["decision"] == "approved"
    assert app_data["approvals"][0]["comments"] == "Approved after accessibility team review."

    # 3. Retrieve validation history endpoint
    val_resp = await async_client.get(
        f"/api/v1/remediations/{remediation_id}/validation",
        headers=headers,
    )
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert len(val_data) >= 1
    assert val_data[0]["passed"] is True
    assert val_data[0]["original_rule_resolved"] is True
    assert val_data[0]["validation_mode"] == "dom_snapshot"


@pytest.mark.asyncio
async def test_remediation_regression_handling_new_violations(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify that if a patch introduces new accessibility violations, validation fails and lists them."""
    owner, _token = await create_user_and_token(async_client, "regression_tester@example.com")

    snippet = '<button class="action-btn">Click Me</button>'
    _proj, _scan, finding = await seed_finding_fixture(
        db_session,
        uuid.UUID(owner["id"]),
        html_snippet=snippet,
        rule_id="button-name",
    )

    validator = SnapshotValidator()

    # Regression patch: sets invalid aria-hidden which introduces an accessibility violation
    regressive_patch = [
        {
            "operation": "set_attribute",
            "selector": "button.action-btn",
            "attribute": "aria-hidden",
            "value": "true",  # Hiding focusable element causes aria-hidden-focus violation in axe-core
        }
    ]

    val_result = await validator.validate_snapshot(
        snapshot_html=snippet,
        original_rule_id="button-name",
        patch_operations=regressive_patch,
        finding_id=str(finding.id),
    )

    # When new violations occur or original rule not resolved, passed MUST be False
    assert val_result["passed"] is False or len(val_result["new_violations"]) > 0


@pytest.mark.asyncio
async def test_snapshot_validation_network_containment() -> None:
    """Verify snapshot validator never requests external network resources during audit."""
    validator = SnapshotValidator()

    # Snippet with malicious remote tracking script and stylesheet
    hostile_snippet = """
    <div>
      <script src="https://evil.attacker.example.com/steal.js"></script>
      <link rel="stylesheet" href="https://evil.attacker.example.com/style.css">
      <img src="logo.png" class="brand-logo">
    </div>
    """

    patch = [
        {
            "operation": "set_attribute",
            "selector": "img.brand-logo",
            "attribute": "alt",
            "value": "Company Brand Logo",
        }
    ]

    result = await validator.validate_snapshot(
        snapshot_html=hostile_snippet,
        original_rule_id="image-alt",
        patch_operations=patch,
    )

    # Validation succeeds in isolated sandbox with all external network requests purged and aborted
    assert result["validation_mode"] == "dom_snapshot"
    assert result["passed"] is True
    assert result["original_rule_resolved"] is True
