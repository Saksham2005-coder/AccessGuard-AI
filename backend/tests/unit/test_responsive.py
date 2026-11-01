"""Unit tests for Responsive Multi-Viewport Accessibility Testing.

Phase 19 Feature 9: Multi-viewport audit profile validation, cross-viewport
violation diffing, shared vs specific classification, and tenant scoping.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.errors import NotFoundError, ValidationError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.schemas.responsive import ViewportProfile
from app.services import responsive_service
from app.services.responsive_service import (
    compute_or_execute_responsive_matrix,
    validate_viewport_dimensions,
)


def test_validate_viewport_dimensions_bounds() -> None:
    """Verify viewport dimensions enforce strict safety boundaries."""
    # Valid
    valid_p = ViewportProfile(name="custom", width=1280, height=800, device_scale_factor=1.0)
    validate_viewport_dimensions(valid_p)

    # Out of bounds rejected by schema validation
    with pytest.raises(PydanticValidationError):
        ViewportProfile(name="too_narrow", width=200, height=800)

    with pytest.raises(PydanticValidationError):
        ViewportProfile(name="too_wide", width=4000, height=800)

    with pytest.raises(PydanticValidationError):
        ViewportProfile(name="too_short", width=1024, height=300)

    with pytest.raises(PydanticValidationError):
        ViewportProfile(name="bad_scale", width=1024, height=768, device_scale_factor=5.0)

    # Also test validate_viewport_dimensions directly
    class OutOfBoundsProfile:
        name = "out_of_bounds"
        width = 100
        height = 800
        device_scale_factor = 1.0
    with pytest.raises(ValidationError):
        validate_viewport_dimensions(OutOfBoundsProfile())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_responsive_matrix_tenant_isolation() -> None:
    """Verify unauthorized scan ID raises NotFoundError before execution."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    scan_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.first.return_value = None
    db.execute.return_value = mock_res

    with pytest.raises(NotFoundError) as exc_info:
        await responsive_service.get_responsive_matrix_report(
            db=db,
            scan_id=scan_id,
            user_id=user_id,
        )

    assert "unauthorized" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_compute_responsive_matrix_shared_and_unique_classification() -> None:
    """Verify shared findings and viewport-specific findings are properly distinguished."""
    db = AsyncMock()
    db.add = MagicMock()
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    scan_id = uuid.uuid4()
    scan_page_id = uuid.uuid4()

    project = Project(id=project_id, owner_id=user_id, name="Mobile Portal", base_domain="m.example.com")
    scan = Scan(id=scan_id, project_id=project_id, target_url="https://m.example.com", status="completed")

    baseline_finding = Finding(
        id=uuid.uuid4(),
        scan_page_id=scan_page_id,
        axe_rule_id="color-contrast",
        impact="serious",
        selector="h1.title",
        description="Text contrast is 2.5:1",
    )

    # Mock DB executions:
    # 1. get_authorized_scan -> (scan, project)
    # 2. baseline findings -> [baseline_finding]
    # 3. existing runs check -> []
    mock_auth = MagicMock()
    mock_auth.first.return_value = (scan, project)

    mock_findings = MagicMock()
    mock_findings.scalars().all.return_value = [baseline_finding]

    mock_existing_runs = MagicMock()
    mock_existing_runs.scalars().all.return_value = []

    db.execute.side_effect = [mock_auth, mock_findings, mock_existing_runs]

    report = await compute_or_execute_responsive_matrix(
        db=db,
        scan_id=scan_id,
        user_id=user_id,
    )

    assert report.scan_id == scan_id
    assert len(report.viewport_runs) == 3  # desktop, tablet, mobile
    assert any(r.viewport_name == "desktop" for r in report.viewport_runs)
    assert any(r.viewport_name == "mobile" for r in report.viewport_runs)

    # Color contrast should be shared across all 3 viewports
    assert any(f.rule_id == "color-contrast" and f.is_shared_across_all for f in report.shared_findings)

    # Mobile-specific touch target or reflow should appear in viewport_specific_findings
    assert any(f.rule_id in ("target-size", "reflow") for f in report.viewport_specific_findings)
    assert db.add.called
