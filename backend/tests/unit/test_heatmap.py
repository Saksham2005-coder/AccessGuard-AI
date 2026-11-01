"""Unit tests for visual accessibility heatmap geometry, density calculation, and tenant isolation."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.db.models.user import User
from app.scanner.geometry import (
    BoundingBox,
    ElementGeometryResult,
    calculate_density_hotspots,
)
from app.services.heatmap_service import get_page_heatmap, list_scan_pages
from app.services.storage_service import save_page_screenshot


def test_density_hotspot_calculation() -> None:
    """Verify density calculation weights critical findings higher and sets appropriate radius."""
    markers = [
        {
            "finding_id": "f1",
            "impact": "critical",
            "bounding_box": {"x": 100, "y": 200, "width": 50, "height": 40},
        },
        {
            "finding_id": "f2",
            "impact": "minor",
            "bounding_box": {"x": 300, "y": 400, "width": 100, "height": 20},
        },
    ]

    hotspots = calculate_density_hotspots(markers)
    assert len(hotspots) == 2

    critical_point = next(h for h in hotspots if h.impact == "critical")
    assert critical_point.x == 125.0  # 100 + 50/2
    assert critical_point.y == 220.0  # 200 + 40/2
    assert critical_point.intensity == 1.0
    assert critical_point.radius == 65.0

    minor_point = next(h for h in hotspots if h.impact == "minor")
    assert minor_point.x == 350.0  # 300 + 100/2
    assert minor_point.y == 410.0  # 400 + 20/2
    assert minor_point.intensity == 0.25
    assert minor_point.radius == 30.0


def test_element_geometry_result_pydantic_validation() -> None:
    """Verify ElementGeometryResult parses located, ambiguous, and not_located states cleanly."""
    located = ElementGeometryResult(
        selector="#main-btn",
        status="located",
        bounding_box=BoundingBox(x=10, y=20, width=100, height=30),
        match_count=1,
    )
    assert located.status == "located"
    assert located.bounding_box is not None
    assert located.bounding_box.width == 100

    ambiguous = ElementGeometryResult(
        selector=".card",
        status="ambiguous",
        bounding_box=BoundingBox(x=0, y=50, width=200, height=150),
        match_count=4,
    )
    assert ambiguous.status == "ambiguous"
    assert ambiguous.match_count == 4

    missing = ElementGeometryResult(
        selector="#nonexistent",
        status="not_located",
        bounding_box=None,
        match_count=0,
    )
    assert missing.status == "not_located"
    assert missing.bounding_box is None


@pytest.mark.asyncio
async def test_heatmap_tenant_isolation(
    db_session: AsyncSession,
) -> None:
    """Verify user cannot view heatmap or screenshot for scans owned by another tenant."""
    # 1. Create Tenant A
    user_a = User(
        email="tenant_a_heatmap@example.com",
        password_hash="hashed_pass_a",
        display_name="Tenant A",
    )
    # 2. Create Tenant B
    user_b = User(
        email="tenant_b_heatmap@example.com",
        password_hash="hashed_pass_b",
        display_name="Tenant B",
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    project_a = Project(
        owner_id=user_a.id,
        name="Project A",
        base_domain="project-a.example.com",
    )
    db_session.add(project_a)
    await db_session.flush()

    scan_a = Scan(
        project_id=project_a.id,
        requested_by=user_a.id,
        target_url="https://project-a.example.com",
        status="completed",
        config={},
    )
    db_session.add(scan_a)
    await db_session.flush()

    page_a = ScanPage(
        scan_id=scan_a.id,
        url="https://project-a.example.com",
        normalized_url="https://project-a.example.com",
        audit_status="completed",
        viewport_width=1280,
        viewport_height=800,
        device_pixel_ratio=1.0,
    )
    db_session.add(page_a)
    await db_session.flush()

    finding_a = Finding(
        scan_page_id=page_a.id,
        axe_rule_id="image-alt",
        impact="critical",
        description="Images must have alternate text",
        selector="img.logo",
        fingerprint="fp123456",
        bounding_box={"x": 50, "y": 60, "width": 120, "height": 40},
        geometry_status="located",
    )
    db_session.add(finding_a)
    await db_session.commit()

    # Tenant B tries to query Tenant A's heatmap directly
    from app.core.errors import NotFoundError

    with pytest.raises(NotFoundError):
        await get_page_heatmap(
            db=db_session,
            scan_id=scan_a.id,
            page_id=page_a.id,
            user_id=user_b.id,
        )

    with pytest.raises(NotFoundError):
        await list_scan_pages(
            db=db_session,
            scan_id=scan_a.id,
            user_id=user_b.id,
        )

    # Tenant A succeeds
    heatmap_res = await get_page_heatmap(
        db=db_session,
        scan_id=scan_a.id,
        page_id=page_a.id,
        user_id=user_a.id,
    )
    assert heatmap_res.scan_id == str(scan_a.id)
    assert heatmap_res.page_id == str(page_a.id)
    assert heatmap_res.total_findings == 1
    assert heatmap_res.located_findings == 1
    assert len(heatmap_res.markers) == 1
    assert heatmap_res.markers[0].rule_id == "image-alt"
    assert heatmap_res.markers[0].bounding_box == {"x": 50, "y": 60, "width": 120, "height": 40}
    assert len(heatmap_res.density_points) == 1


@pytest.mark.asyncio
async def test_heatmap_screenshot_lifecycle() -> None:
    """Verify screenshot saving, linking, and storage retrieval."""
    scan_id = uuid.uuid4()
    page_id = uuid.uuid4()
    dummy_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"

    storage_key = save_page_screenshot(scan_id, page_id, dummy_png_bytes)
    assert storage_key == f"screenshots/{scan_id}/{page_id}.png"

    from app.services.storage_service import resolve_artifact_path

    resolved = resolve_artifact_path(storage_key)
    assert resolved is not None
    assert resolved.exists()
    assert resolved.read_bytes() == dummy_png_bytes

    # Path traversal attempts must return None
    assert resolve_artifact_path("../../../etc/passwd") is None
    assert resolve_artifact_path("/absolute/path") is None
