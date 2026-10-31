"""Project management service enforcing strict multi-tenant authorization."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.db.base import utc_now
from app.db.models.domain_verification import ProjectDomainVerification
from app.db.models.project import Project
from app.schemas.project import (
    DomainVerificationResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.verification_service import (
    create_domain_verification,
    verify_domain_txt_record,
)

logger = get_logger("project_service")


async def get_project_verification_status(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[bool, ProjectDomainVerification | None]:
    """Determine whether project has an active verified record and retrieve latest record."""
    result = await db.execute(
        select(ProjectDomainVerification)
        .where(ProjectDomainVerification.project_id == project_id)
        .order_by(ProjectDomainVerification.created_at.desc())
    )
    verifications = result.scalars().all()
    if not verifications:
        return False, None

    is_verified = any(v.status == "verified" for v in verifications)
    return is_verified, verifications[0]


def build_project_response(
    project: Project,
    is_verified: bool,
    latest_verification: ProjectDomainVerification | None,
) -> ProjectResponse:
    """Helper to convert Project model and verification state into ProjectResponse."""
    return ProjectResponse(
        id=project.id,
        name=project.name,
        base_domain=project.base_domain,
        is_verified=is_verified,
        latest_verification=(
            DomainVerificationResponse.from_model(latest_verification)
            if latest_verification
            else None
        ),
        created_at=project.created_at,
        updated_at=project.updated_at,
        archived_at=project.archived_at,
    )


async def create_project(
    db: AsyncSession, user_id: uuid.UUID, request: ProjectCreateRequest
) -> ProjectResponse:
    """Create a new project and initialize its first domain verification challenge."""
    # Check if active project with duplicate name already exists for this tenant
    duplicate_check = await db.execute(
        select(Project).where(
            Project.owner_id == user_id,
            Project.name == request.name,
            Project.archived_at.is_(None),
        )
    )
    if duplicate_check.scalar_one_or_none() is not None:
        raise ConflictError(f"A project named '{request.name}' already exists in your workspace.")

    project = Project(
        owner_id=user_id,
        name=request.name,
        base_domain=request.base_domain,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    # Automatically generate first verification challenge token
    verification = await create_domain_verification(db, project)

    logger.info(
        "Project created",
        project_id=str(project.id),
        owner_id=str(user_id),
        domain=project.base_domain,
    )

    return build_project_response(project, is_verified=False, latest_verification=verification)


async def list_projects(db: AsyncSession, user_id: uuid.UUID) -> list[ProjectResponse]:
    """List all non-archived projects belonging to the authenticated tenant."""
    result = await db.execute(
        select(Project)
        .where(
            Project.owner_id == user_id,
            Project.archived_at.is_(None),
        )
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    responses: list[ProjectResponse] = []
    for project in projects:
        is_verified, latest_verification = await get_project_verification_status(db, project.id)
        responses.append(build_project_response(project, is_verified, latest_verification))

    return responses


async def get_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Project, ProjectResponse]:
    """Retrieve an active project ensuring tenant isolation."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == user_id,
            Project.archived_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        # Check if project exists under another tenant to avoid leaking existence
        raise NotFoundError("Project not found.")

    is_verified, latest_verification = await get_project_verification_status(db, project.id)
    response = build_project_response(project, is_verified, latest_verification)
    return project, response


async def update_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    request: ProjectUpdateRequest,
) -> ProjectResponse:
    """Update project metadata while enforcing tenant ownership."""
    project, _ = await get_project(db, project_id, user_id)

    if request.name is not None and request.name != project.name:
        # Check duplicate name collision for this owner
        dup = await db.execute(
            select(Project).where(
                Project.owner_id == user_id,
                Project.name == request.name,
                Project.id != project_id,
                Project.archived_at.is_(None),
            )
        )
        if dup.scalar_one_or_none() is not None:
            raise ConflictError(f"A project named '{request.name}' already exists.")
        project.name = request.name

    await db.flush()
    await db.refresh(project)

    is_verified, latest_verification = await get_project_verification_status(db, project.id)
    return build_project_response(project, is_verified, latest_verification)


async def archive_project(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Soft-delete / archive a project."""
    project, _ = await get_project(db, project_id, user_id)
    project.archived_at = utc_now()
    await db.flush()
    logger.info("Project archived", project_id=str(project_id), owner_id=str(user_id))


async def refresh_verification_token(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> DomainVerificationResponse:
    """Generate a new DNS verification challenge token for an existing project."""
    project, _ = await get_project(db, project_id, user_id)
    verification = await create_domain_verification(db, project)
    return DomainVerificationResponse.from_model(verification)


async def perform_verification_check(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[bool, str, DomainVerificationResponse]:
    """Execute on-demand DNS TXT lookup and update verification state."""
    project, _ = await get_project(db, project_id, user_id)
    is_verified, verification, message = await verify_domain_txt_record(db, project)
    return is_verified, message, DomainVerificationResponse.from_model(verification)
