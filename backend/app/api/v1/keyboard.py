"""API endpoints for Keyboard Navigation Simulator.

Phase 19 Feature 5: Deterministic keyboard-only navigation testing and focus order inspection.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.keyboard_test import KeyboardNavigationReport
from app.services.keyboard_service import get_or_run_keyboard_test

router = APIRouter(tags=["keyboard"])


@router.get(
    "/scans/{scan_id}/pages/{page_id}/keyboard-test",
    response_model=KeyboardNavigationReport,
    status_code=status.HTTP_200_OK,
)
async def get_keyboard_test(
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    force_refresh: bool = Query(default=False, description="Force a fresh keyboard navigation test run"),
) -> KeyboardNavigationReport:
    """Retrieve or run a deterministic keyboard navigation test on a scanned page."""
    return await get_or_run_keyboard_test(
        db=db,
        scan_id=scan_id,
        page_id=page_id,
        user_id=current_user.id,
        force_refresh=force_refresh,
    )


@router.post(
    "/scans/{scan_id}/pages/{page_id}/keyboard-test/run",
    response_model=KeyboardNavigationReport,
    status_code=status.HTTP_200_OK,
)
async def rerun_keyboard_test(
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> KeyboardNavigationReport:
    """Explicitly trigger a fresh keyboard navigation test on a scanned page."""
    return await get_or_run_keyboard_test(
        db=db,
        scan_id=scan_id,
        page_id=page_id,
        user_id=current_user.id,
        force_refresh=True,
    )
