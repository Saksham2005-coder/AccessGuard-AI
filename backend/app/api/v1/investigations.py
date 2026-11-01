"""API routes for autonomous accessibility agent investigations and reports."""

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, DbDep
from app.core.errors import NotFoundError
from app.schemas.investigation import (
    InvestigationListResponse,
    InvestigationReport,
    TriggerInvestigationRequest,
)
from app.services.investigation_service import (
    get_investigation_by_id,
    get_latest_scan_investigation,
    list_scan_investigations,
    run_scan_investigation,
)

router = APIRouter(prefix="/scans/{scan_id}/investigations", tags=["investigations"])


@router.post(
    "",
    response_model=InvestigationReport,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_investigation(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    payload: TriggerInvestigationRequest | None = None,
) -> InvestigationReport:
    """Trigger an autonomous multi-agent investigation across all findings in a scan."""
    # Check if latest already exists and force_refresh is False
    if payload and not payload.force_refresh:
        existing = await get_latest_scan_investigation(
            db, scan_id=scan_id, user_id=current_user.id
        )
        if existing:
            return existing

    return await run_scan_investigation(
        db,
        scan_id=scan_id,
        user_id=current_user.id,
    )


@router.get(
    "",
    response_model=InvestigationListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_investigations(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> InvestigationListResponse:
    """List historical autonomous multi-agent investigations for an authorized scan."""
    items = await list_scan_investigations(
        db,
        scan_id=scan_id,
        user_id=current_user.id,
    )
    return InvestigationListResponse(items=items, total=len(items))


@router.get(
    "/latest",
    response_model=InvestigationReport,
    status_code=status.HTTP_200_OK,
)
async def get_latest_investigation(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> InvestigationReport:
    """Retrieve the most recent autonomous multi-agent investigation report."""
    report = await get_latest_scan_investigation(
        db,
        scan_id=scan_id,
        user_id=current_user.id,
    )
    if not report:
        raise NotFoundError("No investigation report found for this scan")
    return report


@router.get(
    "/{investigation_id}",
    response_model=InvestigationReport,
    status_code=status.HTTP_200_OK,
)
async def get_investigation(
    scan_id: uuid.UUID,
    investigation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> InvestigationReport:
    """Retrieve a specific autonomous multi-agent investigation report by ID."""
    return await get_investigation_by_id(
        db,
        scan_id=scan_id,
        investigation_id=investigation_id,
        user_id=current_user.id,
    )
