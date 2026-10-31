"""Project and domain verification REST endpoints."""

import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.project import (
    DomainVerificationResponse,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    VerificationCheckResponse,
)
from app.services.project_service import (
    archive_project,
    create_project,
    get_project,
    list_projects,
    perform_verification_check,
    refresh_verification_token,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    request: ProjectCreateRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ProjectResponse:
    """Create a new project and initialize domain verification challenge."""
    return await create_project(db, current_user.id, request)


@router.get("", response_model=ProjectListResponse)
async def list_user_projects(
    current_user: CurrentUserDep,
    db: DbDep,
) -> ProjectListResponse:
    """List all active projects owned by the authenticated tenant."""
    items = await list_projects(db, current_user.id)
    return ProjectListResponse(items=items, total=len(items))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ProjectResponse:
    """Retrieve details of a project owned by the authenticated tenant."""
    _, response = await get_project(db, project_id, current_user.id)
    return response


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_by_id(
    project_id: uuid.UUID,
    request: ProjectUpdateRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ProjectResponse:
    """Update metadata of an existing project."""
    return await update_project(db, project_id, current_user.id, request)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> Response:
    """Archive / soft-delete a project."""
    await archive_project(db, project_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/domain-verification",
    response_model=DomainVerificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def regenerate_domain_verification(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> DomainVerificationResponse:
    """Generate a fresh DNS verification token for the project's base domain."""
    return await refresh_verification_token(db, project_id, current_user.id)


@router.post(
    "/{project_id}/domain-verification/check",
    response_model=VerificationCheckResponse,
)
async def check_project_domain_verification(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> VerificationCheckResponse:
    """Perform on-demand DNS TXT lookup to verify domain ownership."""
    is_verified, message, verification = await perform_verification_check(
        db, project_id, current_user.id
    )
    return VerificationCheckResponse(
        verified=is_verified,
        message=message,
        status=verification.status,
        verification=verification,
    )
