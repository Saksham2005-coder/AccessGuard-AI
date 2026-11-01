"""API endpoints for Responsive Accessibility Testing.

Phase 19 Feature 9: Multi-viewport audit execution, profile testing,
shared vs unique violation diffs, and responsive matrix comparison.
"""

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.responsive import (
    ResponsiveMatrixReport,
    RunResponsiveMatrixRequest,
)
from app.services import responsive_service

router = APIRouter(tags=["responsive"])


@router.get(
    "/scans/{scan_id}/responsive-matrix",
    response_model=ResponsiveMatrixReport,
    status_code=status.HTTP_200_OK,
)
async def get_scan_responsive_matrix(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ResponsiveMatrixReport:
    """Retrieve responsive multi-viewport accessibility matrix report for a scan."""
    return await responsive_service.get_responsive_matrix_report(
        db=db,
        scan_id=scan_id,
        user_id=current_user.id,
    )


@router.post(
    "/scans/{scan_id}/responsive-matrix/run",
    response_model=ResponsiveMatrixReport,
    status_code=status.HTTP_200_OK,
)
async def run_scan_responsive_matrix(
    scan_id: uuid.UUID,
    data: RunResponsiveMatrixRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ResponsiveMatrixReport:
    """Trigger or re-evaluate multi-viewport accessibility matrix for a scan."""
    return await responsive_service.compute_or_execute_responsive_matrix(
        db=db,
        scan_id=scan_id,
        user_id=current_user.id,
        profiles=data.viewports,
    )
