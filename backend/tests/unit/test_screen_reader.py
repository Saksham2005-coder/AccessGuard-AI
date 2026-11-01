"""Unit and security tests for screen-reader-oriented page reading simulator."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.db.models.user import User
from app.scanner.screen_reader_extractor import extract_semantic_tree_from_html
from app.services.screen_reader_service import get_or_create_page_simulation


@pytest.mark.asyncio
async def test_semantic_extraction_roles_names_and_landmarks() -> None:
    html = """
    <header role="banner">
        <h1>Website Title</h1>
        <nav role="navigation" aria-label="Primary Navigation">
            <a href="/home">Home</a>
            <a href="/services">Services</a>
        </nav>
    </header>
    <main role="main">
        <h2>About Section</h2>
        <p>Welcome to our platform.</p>
        <form aria-label="Contact Form">
            <label for="full-name">Your Name</label>
            <input id="full-name" type="text" value="Secret User Data" />
            <button type="submit" aria-label="Send Message">Send</button>
            <button class="icon-only"><span class="icon"></span></button>
        </form>
    </main>
    <footer role="contentinfo">
        <p>&copy; 2026 AccessGuard</p>
    </footer>
    """

    res = await extract_semantic_tree_from_html(
        html_content=html,
        page_url="https://example.com/test",
        scan_id="scan-001",
        page_id="page-001",
    )

    assert res.nodes_count >= 6
    roles = [node.role for node in res.reading_order]
    assert "banner" in roles
    assert "heading" in roles
    assert "navigation" in roles
    assert "main" in roles
    assert "button" in roles

    # Verify landmarks
    landmark_types = [lm.landmark_type for lm in res.landmarks]
    assert "banner" in landmark_types
    assert "navigation" in landmark_types
    assert "main" in landmark_types
    assert "contentinfo" in landmark_types

    # Verify heading outline
    assert len(res.headings) >= 2
    assert res.headings[0].level == 1
    assert res.headings[0].text == "Website Title"
    assert res.headings[1].level == 2

    # Verify Privacy: password/value is NOT in node attributes
    for node in res.reading_order:
        assert "Secret User Data" not in str(node.attributes)

    # Verify missing accessible name review hint for icon-only button
    missing_name_hints = [h for h in res.review_hints if h.category == "missing_name"]
    assert len(missing_name_hints) >= 1
    assert any("button" in h.message.lower() for h in missing_name_hints)

    # Mandatory enterprise disclaimer
    assert "Screen-reader-oriented reading and navigation preview" in res.disclaimer
    assert "does NOT emulate NVDA, JAWS, or VoiceOver" in res.disclaimer


@pytest.mark.asyncio
async def test_heading_order_and_skip_detection() -> None:
    html = """
    <h1>Level 1 Title</h1>
    <h3>Skipped Level 3 Subtitle</h3>
    """

    res = await extract_semantic_tree_from_html(
        html_content=html,
        page_url="https://example.com/headings",
        scan_id="scan-002",
        page_id="page-002",
    )

    assert len(res.headings) == 2
    assert res.headings[0].level == 1
    assert res.headings[1].level == 3
    assert res.headings[1].is_skipped is True

    skip_hints = [h for h in res.review_hints if h.category == "heading_skip"]
    assert len(skip_hints) == 1
    assert "H1 directly to H3" in skip_hints[0].message


@pytest.mark.asyncio
async def test_screen_reader_service_and_tenant_boundary(db_session: AsyncSession) -> None:
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

    project = Project(
        name="Project SR",
        base_domain="tenant1-sr.example.com",
        owner_id=user1.id,
    )
    db_session.add(project)
    await db_session.commit()

    scan = Scan(
        project_id=project.id,
        requested_by=user1.id,
        target_url="https://tenant1-sr.example.com",
        status="completed",
        config={},
    )
    db_session.add(scan)
    await db_session.commit()

    page = ScanPage(
        scan_id=scan.id,
        url="https://tenant1-sr.example.com/about",
        normalized_url="https://tenant1-sr.example.com/about",
        page_title="About Us",
        audit_status="completed",
    )
    db_session.add(page)
    await db_session.commit()

    finding = Finding(
        scan_page_id=page.id,
        axe_rule_id="button-name",
        impact="critical",
        description="Button without accessible name",
        selector="button.icon-only",
        html_snippet='<button class="icon-only"></button>',
        fingerprint="fp-sr-01",
    )
    db_session.add(finding)
    await db_session.commit()

    # 1. Tenant 1 retrieves / generates simulation
    sim1 = await get_or_create_page_simulation(
        db_session,
        scan_id=scan.id,
        page_id=page.id,
        user_id=user1.id,
    )
    assert sim1.scan_id == str(scan.id)
    assert sim1.page_id == str(page.id)
    assert sim1.nodes_count > 0
    assert len(sim1.review_hints) >= 1

    # 2. Cached retrieval on second call
    sim2 = await get_or_create_page_simulation(
        db_session,
        scan_id=scan.id,
        page_id=page.id,
        user_id=user1.id,
    )
    assert sim2.nodes_count == sim1.nodes_count

    # 3. Tenant 2 access is blocked by non-disclosing NotFoundError
    with pytest.raises(NotFoundError):
        await get_or_create_page_simulation(
            db_session,
            scan_id=scan.id,
            page_id=page.id,
            user_id=user2.id,
        )
