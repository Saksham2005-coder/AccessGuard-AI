"""Unit and tenant isolation tests for isolated before-and-after snapshot comparisons."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthorizationError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.remediation import Remediation
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.db.models.user import User
from app.services.comparison_service import (
    generate_dom_diff,
    generate_remediation_comparison,
    get_remediation_comparison,
    wrap_for_render,
)


def test_generate_dom_diff_produces_unified_diff() -> None:
    before = '<button class="btn">Submit</button>'
    after = '<button class="btn" aria-label="Submit Form">Submit</button>'
    diff = generate_dom_diff(before, after)

    assert "Original Snapshot (Isolated)" in diff
    assert "Proposed Patch (Isolated)" in diff
    assert "+<button" in diff
    assert "aria-label=" in diff


def test_wrap_for_render_creates_compliant_html5() -> None:
    raw = "<button>Click Me</button>"
    wrapped = wrap_for_render(raw)

    assert "<!DOCTYPE html>" in wrapped
    assert '<html lang="en">' in wrapped
    assert "<main>" in wrapped
    assert raw in wrapped


@pytest.mark.asyncio
async def test_comparison_service_lifecycle_and_tenant_boundary(
    db_session: AsyncSession,
) -> None:
    # 1. Create Tenant 1 and Project
    user1 = User(
        email=f"tenant1-{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mockhash",
        display_name="Tenant 1",
    )
    user2 = User(
        email=f"tenant2-{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mockhash",
        display_name="Tenant 2",
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    project1 = Project(
        name="Project 1",
        base_domain="proj1.example.com",
        owner_id=user1.id,
    )
    db_session.add(project1)
    await db_session.commit()
    await db_session.refresh(project1)

    scan1 = Scan(
        project_id=project1.id,
        target_url="https://proj1.example.com",
        requested_by=user1.id,
        status="completed",
    )
    db_session.add(scan1)
    await db_session.commit()
    await db_session.refresh(scan1)

    page1 = ScanPage(
        scan_id=scan1.id,
        url="https://proj1.example.com",
        normalized_url="https://proj1.example.com",
        audit_status="completed",
    )
    db_session.add(page1)
    await db_session.commit()
    await db_session.refresh(page1)

    finding1 = Finding(
        scan_page_id=page1.id,
        axe_rule_id="image-alt",
        impact="critical",
        description="Images must have alternate text",
        html_snippet='<img src="logo.png">',
        fingerprint="fp-test-image-alt-001",
    )
    db_session.add(finding1)
    await db_session.commit()
    await db_session.refresh(finding1)

    remediation1 = Remediation(
        finding_id=finding1.id,
        status="proposed",
        root_cause="Missing alt attribute on informative image",
        recommendation="Add descriptive alt attribute",
        patch_format="dom_operations",
        patch_payload={
            "patch_operations": [
                {
                    "op": "set_attribute",
                    "selector": "img",
                    "attribute": "alt",
                    "value": "Company Logo",
                }
            ]
        },
        before_snippet='<img src="logo.png">',
        after_snippet='<img src="logo.png" alt="Company Logo">',
    )
    db_session.add(remediation1)
    await db_session.commit()
    await db_session.refresh(remediation1)

    # Tenant 1 generates comparison
    result = await generate_remediation_comparison(
        db=db_session,
        remediation_id=remediation1.id,
        user_id=user1.id,
    )

    assert result["remediation_id"] == str(remediation1.id)
    assert result["finding_id"] == str(finding1.id)
    assert result["rule_id"] == "image-alt"
    assert "alt=" in result["after_html"]
    assert "Original Snapshot" in result["dom_diff"]

    # Retrieval from cache works
    cached = await get_remediation_comparison(
        db=db_session,
        remediation_id=remediation1.id,
        user_id=user1.id,
    )
    assert cached["remediation_id"] == str(remediation1.id)

    # Cross-tenant access by User 2 must raise AuthorizationError (tenant isolation boundary)
    with pytest.raises(AuthorizationError):
        await get_remediation_comparison(
            db=db_session,
            remediation_id=remediation1.id,
            user_id=user2.id,
        )
