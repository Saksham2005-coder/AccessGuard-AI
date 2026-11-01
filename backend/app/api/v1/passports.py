"""API routes for Accessibility Compliance Passport.

Phase 19 Feature 10: Versioned, tamper-evident audit evidence package with deterministic
SHA-256 integrity hash, multi-engine telemetry breakdown, and audit traceability.
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.passport import (
    CompliancePassportDetail,
    CompliancePassportSummary,
    GeneratePassportRequest,
    PassportExportDocument,
)
from app.services.passport_service import (
    export_compliance_passport_markdown,
    generate_compliance_passport,
    get_compliance_passport_detail,
    list_compliance_passports,
)

router = APIRouter(prefix="/projects/{project_id}/passports", tags=["passports"])


@router.post(
    "/generate",
    response_model=CompliancePassportDetail,
    status_code=status.HTTP_201_CREATED,
)
async def generate_passport_endpoint(
    project_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
    request: GeneratePassportRequest | None = None,
) -> CompliancePassportDetail:
    """Generate a new immutable compliance passport version for a project."""
    notes = request.notes if request else None
    passport = await generate_compliance_passport(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        notes=notes,
    )
    return CompliancePassportDetail.model_validate(passport)


@router.get("", response_model=list[CompliancePassportSummary])
async def list_passports_endpoint(
    project_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
) -> list[CompliancePassportSummary]:
    """List all compliance passport versions generated for a project."""
    return await list_compliance_passports(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )


@router.get("/{passport_id}", response_model=CompliancePassportDetail)
async def get_passport_endpoint(
    project_id: uuid.UUID,
    passport_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
) -> CompliancePassportDetail:
    """Retrieve full compliance passport details and evidence payload."""
    passport = await get_compliance_passport_detail(
        db=db,
        project_id=project_id,
        passport_id=passport_id,
        user_id=current_user.id,
    )
    return CompliancePassportDetail.model_validate(passport)


@router.get("/{passport_id}/export", response_model=PassportExportDocument)
async def export_passport_document_endpoint(
    project_id: uuid.UUID,
    passport_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
) -> PassportExportDocument:
    """Export human-readable Markdown/audit document representation of passport."""
    passport = await get_compliance_passport_detail(
        db=db,
        project_id=project_id,
        passport_id=passport_id,
        user_id=current_user.id,
    )
    markdown_content = export_compliance_passport_markdown(passport)
    return PassportExportDocument(
        passport_id=passport.id,
        version=passport.version,
        integrity_hash=passport.integrity_hash,
        markdown_content=markdown_content,
        generated_at=datetime.utcnow(),
    )


@router.get("/{passport_id}/download")
async def download_passport_json_endpoint(
    project_id: uuid.UUID,
    passport_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUserDep,
) -> Response:
    """Download canonical JSON evidence bundle with checksum header."""
    passport = await get_compliance_passport_detail(
        db=db,
        project_id=project_id,
        passport_id=passport_id,
        user_id=current_user.id,
    )
    json_bytes = json.dumps(passport.evidence_payload, indent=2).encode("utf-8")
    filename = f"compliance-passport-{passport.version}-{str(project_id)[:8]}.json"

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Integrity-SHA256": passport.integrity_hash,
        },
    )
