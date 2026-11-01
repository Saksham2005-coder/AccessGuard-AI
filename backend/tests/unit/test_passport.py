"""Unit tests for Accessibility Compliance Passport.

Phase 19 Feature 10: Versioned, tamper-evident audit evidence package with deterministic
SHA-256 integrity hash, multi-engine telemetry breakdown, and audit traceability.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import NotFoundError
from app.db.models.finding import Finding
from app.db.models.passport import CompliancePassport
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.services import passport_service
from app.services.passport_service import (
    compute_deterministic_integrity_hash,
    export_compliance_passport_markdown,
    generate_compliance_passport,
    get_compliance_passport_detail,
)


def test_deterministic_integrity_hash() -> None:
    """Verify SHA-256 hash is deterministic and key-order independent."""
    dict_a = {
        "project": "portal",
        "violations": 4,
        "nested": {"status": "ok", "count": 2},
    }
    dict_b = {
        "nested": {"count": 2, "status": "ok"},
        "violations": 4,
        "project": "portal",
    }
    hash_a = compute_deterministic_integrity_hash(dict_a)
    hash_b = compute_deterministic_integrity_hash(dict_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64

    # Any mutation alters hash
    dict_c = dict(dict_a)
    dict_c["violations"] = 5
    hash_c = compute_deterministic_integrity_hash(dict_c)
    assert hash_c != hash_a


@pytest.mark.asyncio
async def test_passport_tenant_isolation() -> None:
    """Verify accessing or generating passport across tenants raises NotFoundError."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    with pytest.raises(NotFoundError) as exc_info:
        await generate_compliance_passport(
            db=db,
            project_id=project_id,
            user_id=user_id,
        )

    assert "unauthorized" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_generate_compliance_passport_evidence_structure_and_disclaimer() -> None:
    """Verify generated passport contains version, evidence breakdown, hash, and non-certification disclaimer."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    scan_id = uuid.uuid4()
    page_id = uuid.uuid4()

    project = Project(
        id=project_id,
        owner_id=user_id,
        name="Enterprise Portal",
        base_domain="portal.example.com",
    )
    scan = Scan(
        id=scan_id,
        project_id=project_id,
        target_url="https://portal.example.com",
        status="completed",
        pages_succeeded=3,
    )
    finding = Finding(
        id=uuid.uuid4(),
        scan_page_id=page_id,
        axe_rule_id="color-contrast",
        impact="serious",
        selector="h1.header",
        description="Text contrast 2.5:1",
    )

    # Mock DB executions:
    # 1. get_authorized_project -> project
    # 2. scans -> [scan]
    # 3. findings -> [finding]
    # 4. remediations -> []
    # 5. viewport_runs -> []
    # 6. baseline -> None
    # 7. existing_passports -> []
    mock_proj = MagicMock()
    mock_proj.scalar_one_or_none.return_value = project

    mock_scans = MagicMock()
    mock_scans.scalars().all.return_value = [scan]

    mock_findings = MagicMock()
    mock_findings.scalars().all.return_value = [finding]

    mock_remed = MagicMock()
    mock_remed.scalars().all.return_value = []

    mock_vp = MagicMock()
    mock_vp.scalars().all.return_value = []

    mock_base = MagicMock()
    mock_base.scalar_one_or_none.return_value = None

    mock_passports = MagicMock()
    mock_passports.scalars().all.return_value = []

    db.execute.side_effect = [
        mock_proj,
        mock_scans,
        mock_findings,
        mock_remed,
        mock_vp,
        mock_base,
        mock_passports,
    ]

    passport = await generate_compliance_passport(
        db=db,
        project_id=project_id,
        user_id=user_id,
        notes="Q4 Release Evidence Audit",
    )

    assert passport.version == "v1"
    assert len(passport.integrity_hash) == 64
    assert passport.project_id == project_id

    payload = passport.evidence_payload
    assert payload["passport_metadata"]["project_name"] == "Enterprise Portal"
    assert payload["audit_scope"]["total_scans_included"] == 1
    assert payload["compliance_evaluation"]["status_label"] == "Outstanding automated findings"
    assert payload["compliance_evaluation"]["severity_breakdown"]["serious"] == 1

    # Legal disclaimer must clearly deny official certification
    disclaimer = payload["legal_disclaimer"]
    assert "not an official wcag legal certification" in disclaimer.lower()
    assert db.add.called
    assert db.commit.called


def test_export_compliance_passport_markdown() -> None:
    """Verify Markdown export includes all required audit sections and integrity hash."""
    passport = CompliancePassport(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        version="v2",
        status="completed",
        integrity_hash="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        evidence_payload={
            "passport_metadata": {
                "project_name": "Audit Portal",
                "base_domain": "audit.example.com",
            },
            "audit_scope": {
                "total_scans_included": 2,
                "total_pages_audited": 10,
                "scanner_engine": "axe-core with Playwright Chromium",
                "axe_version": "4.14.0",
            },
            "compliance_evaluation": {
                "status_label": "No automated findings in tested scope",
                "total_violations": 0,
                "severity_breakdown": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
                "remediations_summary": {"total_proposals": 1, "resolved_or_verified": 1, "pending_or_proposed": 0},
            },
            "multi_engine_evidence": {
                "multi_viewport_testing": {"runs_recorded": 3},
                "keyboard_simulator": {"status": "Verified"},
                "screen_reader_preview": {"status": "Verified"},
            },
            "manual_review_checklist": [
                {
                    "item": "Captions",
                    "guideline": "WCAG 1.2.2",
                    "status": "Manual Review Required",
                    "notes": "Ensure all video has synchronized captions.",
                }
            ],
            "legal_disclaimer": "This compliance passport is an auditable record of automated testing and engineering evidence. It is not an official WCAG legal certification.",
        },
    )

    doc = export_compliance_passport_markdown(passport)

    assert "# AccessGuard AI — Accessibility Compliance Passport (v2)" in doc
    assert "abcdef0123456789abcdef0123456789" in doc
    assert "Audit Portal" in doc
    assert "No automated findings in tested scope" in doc
    assert "Captions" in doc
    assert "not an official wcag legal certification" in doc.lower()
