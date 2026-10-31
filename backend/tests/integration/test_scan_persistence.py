"""Integration tests for scan job, page, finding, and finding node database persistence."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.db.models.project import Project
from app.db.models.user import User
from app.scanner.axe_runner import AxeAuditResult, AxeFindingItem, AxeNodeResult
from app.services.scan_persistence_service import (
    create_scan_record,
    get_scan,
    get_scan_findings,
    persist_page_audit_results,
)


@pytest.fixture
async def test_user_and_project(db_session: AsyncSession) -> tuple[User, Project]:
    """Helper fixture creating an active user and project."""
    user = User(
        email="auditor@example.com",
        password_hash="argon2_fake_hash",
        display_name="Auditor",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    project = Project(
        owner_id=user.id,
        name="Audited Storefront",
        base_domain="store.example.com",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(user)
    await db_session.refresh(project)

    return user, project


@pytest.mark.asyncio
async def test_scan_and_findings_persistence_lifecycle(
    db_session: AsyncSession, test_user_and_project: tuple[User, Project]
) -> None:
    """Verify persisting a scan job, crawled pages, axe violations, and finding nodes."""
    user, project = test_user_and_project

    # 1. Create scan job record
    scan = await create_scan_record(
        db_session,
        project=project,
        user=user,
        target_url="https://store.example.com/",
        scan_config={"max_pages": 10},
        axe_version="4.14.0",
        browser_version="Chromium 124",
    )
    assert scan.id is not None
    assert scan.status == "pending"
    assert scan.total_violations == 0

    # 2. Build mock audit result with 1 violation and 1 incomplete finding
    mock_audit = AxeAuditResult(
        url="https://store.example.com/",
        axe_version="4.14.0",
        violations=[
            AxeFindingItem(
                rule_id="image-alt",
                impact="critical",
                description="Images must have alternative text",
                help_text="Element must have an alt attribute",
                help_url="https://dequeuniversity.com/rules/axe/4.14/image-alt",
                tags=["wcag2a", "wcag111"],
                wcag_tags=["wcag2a", "wcag111"],
                fingerprint="fingerprint_img_123",
                primary_selector="#main-hero img",
                nodes=[
                    AxeNodeResult(
                        target=["#main-hero img"],
                        html_snippet='<img src="hero.jpg">',
                        failure_summary="Fix any of the following: Element does not have an alt attribute",
                    )
                ],
            )
        ],
        incomplete=[
            AxeFindingItem(
                rule_id="color-contrast",
                impact="serious",
                description="Elements must meet minimum color contrast ratio",
                tags=["wcag2aa", "wcag143"],
                wcag_tags=["wcag2aa", "wcag143"],
                is_incomplete=True,
                fingerprint="fingerprint_contrast_456",
                primary_selector=".hero-subtext",
                nodes=[
                    AxeNodeResult(
                        target=[".hero-subtext"],
                        html_snippet='<span class="hero-subtext">Sale</span>',
                        failure_summary="Element's background could not be determined",
                    )
                ],
            )
        ],
        passes_count=15,
    )

    # 3. Persist page results
    page = await persist_page_audit_results(
        db_session,
        scan_id=scan.id,
        url="https://store.example.com/",
        normalized_url="https://store.example.com/",
        page_title="Store Home",
        http_status=200,
        load_duration_ms=450,
        audit_result=mock_audit,
    )
    assert page.id is not None
    assert page.audit_status == "completed"

    # 4. Verify scan aggregate counters updated
    updated_scan = await get_scan(db_session, scan.id, user.id)
    assert updated_scan.total_pages == 1
    assert updated_scan.pages_succeeded == 1
    assert updated_scan.total_violations == 1

    # 5. Verify findings retrieval
    confirmed_findings = await get_scan_findings(
        db_session, scan.id, user.id, include_incomplete=False
    )
    assert len(confirmed_findings) == 1
    assert confirmed_findings[0].axe_rule_id == "image-alt"
    assert len(confirmed_findings[0].nodes) == 1
    assert confirmed_findings[0].nodes[0].html_snippet == '<img src="hero.jpg">'

    all_findings = await get_scan_findings(db_session, scan.id, user.id, include_incomplete=True)
    assert len(all_findings) == 2


@pytest.mark.asyncio
async def test_duplicate_page_on_same_scan_rejected(
    db_session: AsyncSession, test_user_and_project: tuple[User, Project]
) -> None:
    """Verify persisting duplicate normalized_url on same scan raises ConflictError."""
    user, project = test_user_and_project
    scan = await create_scan_record(
        db_session, project=project, user=user, target_url="https://store.example.com/"
    )

    empty_audit = AxeAuditResult(url="https://store.example.com/", axe_version="4.14.0")

    await persist_page_audit_results(
        db_session,
        scan_id=scan.id,
        url="https://store.example.com/",
        normalized_url="https://store.example.com/",
        audit_result=empty_audit,
    )

    # Attempting to persist same normalized URL again
    with pytest.raises(ConflictError):
        await persist_page_audit_results(
            db_session,
            scan_id=scan.id,
            url="https://store.example.com/?ref=dup",
            normalized_url="https://store.example.com/",
            audit_result=empty_audit,
        )


@pytest.mark.asyncio
async def test_scan_tenant_isolation(
    db_session: AsyncSession, test_user_and_project: tuple[User, Project]
) -> None:
    """Verify User B cannot access User A's scan data (IDOR protection)."""
    user_a, project_a = test_user_and_project

    # Create User B
    user_b = User(email="intruder@example.com", password_hash="hash_b", display_name="Intruder")
    db_session.add(user_b)
    await db_session.flush()

    scan = await create_scan_record(
        db_session, project=project_a, user=user_a, target_url="https://store.example.com/"
    )

    # User B attempts to access scan -> raises NotFoundError
    with pytest.raises(NotFoundError):
        await get_scan(db_session, scan.id, user_b.id)

    with pytest.raises(NotFoundError):
        await get_scan_findings(db_session, scan.id, user_b.id)
