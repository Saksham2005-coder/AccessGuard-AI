"""API endpoints for Accessibility Regression Monitoring, Scheduled Audits, and Notifications.

Phase 19 Feature 6: Historical regression analysis, pinned baselines,
scheduled audits, and in-app notifications.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.regression import (
    InAppNotificationResponse,
    ProjectBaselineResponse,
    RegressionComparisonReport,
    ScanScheduleCreate,
    ScanScheduleResponse,
    SetBaselineRequest,
)
from app.services import regression_service

router = APIRouter(tags=["regression"])


@router.get(
    "/projects/{project_id}/regression/compare",
    response_model=RegressionComparisonReport,
    status_code=status.HTTP_200_OK,
)
async def compare_scan_regression(
    project_id: uuid.UUID,
    current_scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    baseline_scan_id: uuid.UUID | None = Query(None, description="Explicit baseline scan ID to compare against"),
) -> RegressionComparisonReport:
    """Compare a scan with a baseline to detect new, resolved, persistent, and changed findings."""
    if baseline_scan_id:
        baseline_scan, baseline_type = await regression_service.get_scan(db, baseline_scan_id, current_user.id), "custom_selection"
    else:
        baseline_scan, baseline_type = await regression_service.get_or_determine_baseline(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            reference_scan_id=current_scan_id,
        )

    return await regression_service.compare_scans(
        db=db,
        project_id=project_id,
        current_scan_id=current_scan_id,
        baseline_scan_id=baseline_scan.id,
        user_id=current_user.id,
        baseline_type=baseline_type,
    )


@router.get(
    "/projects/{project_id}/baseline",
    response_model=ProjectBaselineResponse | None,
    status_code=status.HTTP_200_OK,
)
async def get_project_baseline(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ProjectBaselineResponse | None:
    """Retrieve designated project baseline scan details if set."""
    return await regression_service.get_project_baseline_info(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )


@router.post(
    "/projects/{project_id}/baseline",
    response_model=ProjectBaselineResponse,
    status_code=status.HTTP_200_OK,
)
async def set_project_baseline(
    project_id: uuid.UUID,
    payload: SetBaselineRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ProjectBaselineResponse:
    """Designate a successfully completed scan as the project baseline."""
    return await regression_service.set_project_baseline(
        db=db,
        project_id=project_id,
        scan_id=uuid.UUID(payload.scan_id),
        user_id=current_user.id,
        notes=payload.notes,
    )


@router.get(
    "/projects/{project_id}/schedules",
    response_model=list[ScanScheduleResponse],
    status_code=status.HTTP_200_OK,
)
async def list_schedules(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> list[ScanScheduleResponse]:
    """List recurring audit schedules configured for a project."""
    return await regression_service.list_project_schedules(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )


@router.post(
    "/projects/{project_id}/schedules",
    response_model=ScanScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    project_id: uuid.UUID,
    payload: ScanScheduleCreate,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ScanScheduleResponse:
    """Create a recurring scheduled audit for an authorized verified domain."""
    return await regression_service.create_scan_schedule(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        data=payload,
    )


@router.patch(
    "/projects/{project_id}/schedules/{schedule_id}",
    response_model=ScanScheduleResponse,
    status_code=status.HTTP_200_OK,
)
async def toggle_schedule(
    project_id: uuid.UUID,
    schedule_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    is_active: bool = Query(..., description="Activate or pause the recurring schedule"),
) -> ScanScheduleResponse:
    """Pause or resume a recurring audit schedule."""
    return await regression_service.toggle_scan_schedule(
        db=db,
        project_id=project_id,
        schedule_id=schedule_id,
        user_id=current_user.id,
        is_active=is_active,
    )


@router.delete(
    "/projects/{project_id}/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_schedule(
    project_id: uuid.UUID,
    schedule_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> None:
    """Delete a recurring audit schedule permanently."""
    await regression_service.delete_scan_schedule(
        db=db,
        project_id=project_id,
        schedule_id=schedule_id,
        user_id=current_user.id,
    )


@router.get(
    "/notifications",
    response_model=list[InAppNotificationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_notifications(
    current_user: CurrentUserDep,
    db: DbDep,
    unread_only: bool = Query(default=False),
) -> list[InAppNotificationResponse]:
    """Retrieve in-app notifications for the authenticated user."""
    return await regression_service.list_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
    )


@router.patch(
    "/notifications/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> None:
    """Mark an in-app notification as read."""
    await regression_service.mark_notification_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
