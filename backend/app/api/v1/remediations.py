"""API endpoints for remediation proposals, human approvals, and snapshot validations."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, DbDep
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.remediation import Remediation
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.remediation import (
    ComparisonResponse,
    RemediationDecisionRequest,
    RemediationResponse,
    ValidationResultResponse,
)
from app.services.comparison_service import (
    generate_remediation_comparison,
    get_remediation_comparison,
)
from app.services.remediation_service import (
    create_or_run_remediation_proposal,
    get_remediation_and_check_ownership,
    record_approval_decision,
    run_remediation_snapshot_validation,
)
from app.services.storage_service import resolve_artifact_path

router = APIRouter(tags=["remediations"])


@router.get(
    "/remediations",
    response_model=list[RemediationResponse],
    status_code=status.HTTP_200_OK,
)
async def list_remediations(
    current_user: CurrentUserDep,
    db: DbDep,
    finding_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None),
) -> list[RemediationResponse]:
    """List remediation proposals belonging to the authenticated tenant."""
    query = (
        select(Remediation)
        .options(
            selectinload(Remediation.approvals),
            selectinload(Remediation.validation_results),
        )
        .join(Finding, Remediation.finding_id == Finding.id)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .join(Project, Scan.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    if finding_id:
        query = query.where(Remediation.finding_id == finding_id)
    if status_filter:
        query = query.where(Remediation.status == status_filter)

    query = query.order_by(Remediation.created_at.desc())
    result = await db.execute(query)
    remediations = result.scalars().all()
    return [RemediationResponse.model_validate(r) for r in remediations]


@router.post(
    "/findings/{finding_id}/remediations",
    response_model=RemediationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_remediation_proposal(
    finding_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RemediationResponse:
    """Generate or retrieve an evidence-grounded remediation proposal for an accessibility finding."""
    remediation = await create_or_run_remediation_proposal(
        db=db,
        finding_id=finding_id,
        user_id=current_user.id,
    )
    return RemediationResponse.model_validate(remediation)


@router.get(
    "/remediations/{remediation_id}",
    response_model=RemediationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_remediation_proposal(
    remediation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RemediationResponse:
    """Retrieve proposed remediation details, before/after snippets, and approval audit trail."""
    remediation, _finding, _project = await get_remediation_and_check_ownership(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
    )
    return RemediationResponse.model_validate(remediation)


@router.post(
    "/remediations/{remediation_id}/approve",
    response_model=RemediationResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_remediation_proposal(
    remediation_id: uuid.UUID,
    decision_payload: RemediationDecisionRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RemediationResponse:
    """Approve a remediation proposal, record human reviewer audit, and trigger snapshot validation."""
    remediation = await record_approval_decision(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
        decision="approved",
        comments=decision_payload.comments,
    )
    return RemediationResponse.model_validate(remediation)


@router.post(
    "/remediations/{remediation_id}/reject",
    response_model=RemediationResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_remediation_proposal(
    remediation_id: uuid.UUID,
    decision_payload: RemediationDecisionRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RemediationResponse:
    """Reject a remediation proposal and record reviewer explanation without validating."""
    remediation = await record_approval_decision(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
        decision="rejected",
        comments=decision_payload.comments,
    )
    return RemediationResponse.model_validate(remediation)


@router.post(
    "/remediations/{remediation_id}/validate",
    response_model=RemediationResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_remediation_snapshot(
    remediation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RemediationResponse:
    """Queue or execute isolated snapshot validation for an approved remediation proposal."""
    remediation = await run_remediation_snapshot_validation(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
    )
    return RemediationResponse.model_validate(remediation)


@router.get(
    "/remediations/{remediation_id}/validation",
    response_model=list[ValidationResultResponse],
    status_code=status.HTTP_200_OK,
)
async def get_remediation_validation_history(
    remediation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> list[ValidationResultResponse]:
    """Retrieve isolated snapshot validation history and violation diffs."""
    remediation, _finding, _project = await get_remediation_and_check_ownership(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
    )
    return [ValidationResultResponse.model_validate(vr) for vr in remediation.validation_results]


@router.post(
    "/remediations/{remediation_id}/compare",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
)
async def run_remediation_comparison(
    remediation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ComparisonResponse:
    """Generate isolated before-and-after snapshot comparison, visual rendering, and re-audit."""
    comparison = await generate_remediation_comparison(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
    )
    return ComparisonResponse.model_validate(comparison)


@router.get(
    "/remediations/{remediation_id}/comparison",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
)
async def get_remediation_comparison_endpoint(
    remediation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ComparisonResponse:
    """Retrieve isolated before-and-after snapshot comparison metadata and re-audit diff."""
    comparison = await get_remediation_comparison(
        db=db,
        remediation_id=remediation_id,
        user_id=current_user.id,
    )
    return ComparisonResponse.model_validate(comparison)


@router.get(
    "/remediations/{remediation_id}/screenshots/{variant}",
    status_code=status.HTTP_200_OK,
)
async def get_remediation_screenshot(
    remediation_id: uuid.UUID,
    variant: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> FileResponse:
    """Stream before or after isolated screenshot artifact for an authorized remediation."""
    if variant not in ("before", "after"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Screenshot variant must be 'before' or 'after'.",
        )

    # Tenant ownership check
    await get_remediation_and_check_ownership(db, remediation_id, current_user.id)

    storage_key = f"remediations/{remediation_id}/{variant}.png"
    file_path = resolve_artifact_path(storage_key)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Remediation screenshot '{variant}' is not yet generated or available.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=f"remediation-{remediation_id}-{variant}.png",
    )

