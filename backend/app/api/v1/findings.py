"""API endpoints for exploring accessibility findings, element selectors, and WCAG tags."""

import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, DbDep
from app.core.errors import NotFoundError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.finding import (
    FindingDetailResponse,
    FindingListResponse,
    FindingResponse,
)

router = APIRouter(tags=["findings"])


@router.get(
    "/findings",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_findings(
    current_user: CurrentUserDep,
    db: DbDep,
    project_id: uuid.UUID | None = Query(default=None),
    scan_id: uuid.UUID | None = Query(default=None),
    impact: str | None = Query(default=None),
    axe_rule_id: str | None = Query(default=None),
) -> FindingListResponse:
    """List accessibility findings across tenant projects with optional filtering."""
    query = (
        select(Finding)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .join(Project, Scan.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )

    if project_id:
        query = query.where(Project.id == project_id)
    if scan_id:
        query = query.where(Scan.id == scan_id)
    if impact:
        query = query.where(Finding.impact == impact)
    if axe_rule_id:
        query = query.where(Finding.axe_rule_id == axe_rule_id)

    query = query.order_by(Finding.created_at.desc())

    result = await db.execute(query)
    findings = result.scalars().all()
    items = [FindingResponse.model_validate(f) for f in findings]
    return FindingListResponse(items=items, total=len(items))


@router.get(
    "/findings/{finding_id}",
    response_model=FindingDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_finding_by_id(
    finding_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> FindingDetailResponse:
    """Retrieve detailed accessibility finding with DOM element targets and nodes."""
    query = (
        select(Finding)
        .options(selectinload(Finding.nodes))
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .join(Project, Scan.project_id == Project.id)
        .where(Finding.id == finding_id, Project.owner_id == current_user.id)
    )

    result = await db.execute(query)
    finding = result.scalar_one_or_none()
    if not finding:
        raise NotFoundError("Finding not found or access unauthorized.")

    return FindingDetailResponse.model_validate(finding)


@router.get(
    "/scans/{scan_id}/findings",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_scan_findings(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> FindingListResponse:
    """Retrieve all accessibility findings detected during a specific scan execution."""
    query = (
        select(Finding)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .join(Project, Scan.project_id == Project.id)
        .where(Scan.id == scan_id, Project.owner_id == current_user.id)
        .order_by(Finding.created_at.desc())
    )

    result = await db.execute(query)
    findings = result.scalars().all()
    items = [FindingResponse.model_validate(f) for f in findings]
    return FindingListResponse(items=items, total=len(items))
