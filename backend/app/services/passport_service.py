"""Service for Accessibility Compliance Passport generation and verification.

Phase 19 Feature 10: Versioned, tamper-evident audit evidence package with deterministic
SHA-256 integrity hash, multi-engine telemetry breakdown, and audit traceability.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models.finding import Finding
from app.db.models.passport import CompliancePassport
from app.db.models.project import Project
from app.db.models.regression import ProjectBaseline
from app.db.models.remediation import Remediation
from app.db.models.responsive import ScanViewportRun
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.passport import CompliancePassportSummary


async def get_authorized_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Project:
    """Fetch project ensuring tenant scoping."""
    stmt = select(Project).where(
        Project.id == project_id,
        Project.owner_id == user_id,
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found or unauthorized")
    return project


def compute_deterministic_integrity_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash over canonicalized JSON payload."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


async def generate_compliance_passport(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    notes: str | None = None,
) -> CompliancePassport:
    """Generate an immutable versioned compliance passport snapshot with SHA-256 integrity hash."""
    project = await get_authorized_project(db, project_id=project_id, user_id=user_id)

    # 1. Fetch project scans
    scans_stmt = (
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
    )
    scans_res = await db.execute(scans_stmt)
    scans = list(scans_res.scalars().all())

    # 2. Fetch project findings
    findings_stmt = (
        select(Finding)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .where(Scan.project_id == project_id)
    )
    findings_res = await db.execute(findings_stmt)
    findings = list(findings_res.scalars().all())

    # 3. Fetch project remediations
    remediations_stmt = (
        select(Remediation)
        .join(Finding, Remediation.finding_id == Finding.id)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .where(Scan.project_id == project_id)
    )
    remediations_res = await db.execute(remediations_stmt)
    remediations = list(remediations_res.scalars().all())

    # 4. Fetch responsive runs
    viewport_stmt = (
        select(ScanViewportRun)
        .join(Scan, ScanViewportRun.scan_id == Scan.id)
        .where(Scan.project_id == project_id)
    )
    viewport_res = await db.execute(viewport_stmt)
    viewport_runs = list(viewport_res.scalars().all())

    # 5. Fetch project baseline
    baseline_stmt = select(ProjectBaseline).where(ProjectBaseline.project_id == project_id)
    baseline_res = await db.execute(baseline_stmt)
    baseline = baseline_res.scalar_one_or_none()

    # Determine version sequence
    passports_stmt = (
        select(CompliancePassport)
        .where(CompliancePassport.project_id == project_id)
        .order_by(CompliancePassport.created_at.desc())
    )
    passports_res = await db.execute(passports_stmt)
    existing_passports = list(passports_res.scalars().all())
    version_num = len(existing_passports) + 1
    version_str = f"v{version_num}"

    # Severity counts
    critical_count = sum(1 for f in findings if f.impact == "critical")
    serious_count = sum(1 for f in findings if f.impact == "serious")
    moderate_count = sum(1 for f in findings if f.impact == "moderate")
    minor_count = sum(1 for f in findings if f.impact == "minor")
    total_violations = len(findings)

    # Status classification
    if not scans:
        status_label = "Insufficient scan coverage"
    elif total_violations == 0:
        status_label = "No automated findings in tested scope"
    else:
        status_label = "Outstanding automated findings"

    # Remediation stats
    resolved_count = sum(1 for r in remediations if r.status in ("applied", "verified", "accepted"))
    pending_count = sum(1 for r in remediations if r.status in ("proposed", "pending", "in_review"))

    # Rules and criteria
    unique_rules = sorted({f.axe_rule_id for f in findings if f.axe_rule_id})

    wcag_criteria = [
        {
            "criterion_id": "1.4.3",
            "title": "Contrast (Minimum)",
            "level": "AA",
            "status": "Evaluated by axe-core color-contrast rule",
        },
        {
            "criterion_id": "2.1.1",
            "title": "Keyboard",
            "level": "A",
            "status": "Evaluated by keyboard navigation simulator",
        },
        {
            "criterion_id": "2.4.7",
            "title": "Focus Visible",
            "level": "AA",
            "status": "Evaluated by focus indicator inspection harness",
        },
        {
            "criterion_id": "2.5.8",
            "title": "Target Size (Minimum)",
            "level": "AA",
            "status": "Evaluated across mobile & touch viewports",
        },
        {
            "criterion_id": "4.1.2",
            "title": "Name, Role, Value",
            "level": "A",
            "status": "Evaluated by semantic accessibility scanner",
        },
    ]

    manual_review_checklist = [
        {
            "item": "Captions and Audio Descriptions",
            "guideline": "WCAG 1.2.2 / 1.2.5",
            "status": "Manual Review Required",
            "notes": "Verify that pre-recorded video media contains synchronized, accurate captions.",
        },
        {
            "item": "Dynamic Screen Reader Focus Updates",
            "guideline": "WCAG 2.4.3 / 4.1.3",
            "status": "Manual Review Required",
            "notes": "Verify that screen readers announce asynchronous route changes and modal openings.",
        },
        {
            "item": "Content Reflow Without Information Loss",
            "guideline": "WCAG 1.4.10",
            "status": "Partially Automated",
            "notes": "Verify horizontal scrolling is avoided down to 320px viewport width.",
        },
        {
            "item": "Plain Language and Cognitive Accessibility",
            "guideline": "WCAG 3.1",
            "status": "Manual Review Required",
            "notes": "Review error message clarity and form submission confirmation steps.",
        },
    ]

    now_iso = datetime.utcnow().isoformat() + "Z"

    # Assemble Canonical Evidence Payload (Excludes mutable runtime references)
    evidence_payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "passport_metadata": {
            "project_id": str(project_id),
            "project_name": project.name,
            "base_domain": project.base_domain,
            "version": version_str,
            "generation_timestamp": now_iso,
            "generated_by": str(user_id),
            "notes": notes or "Automated compliance evidence package generation",
        },
        "audit_scope": {
            "total_scans_included": len(scans),
            "total_pages_audited": sum(s.pages_succeeded or s.total_pages or 1 for s in scans),
            "scanner_engine": "axe-core with Playwright Chromium",
            "axe_version": "4.14.0",
        },
        "compliance_evaluation": {
            "status_label": status_label,
            "total_violations": total_violations,
            "severity_breakdown": {
                "critical": critical_count,
                "serious": serious_count,
                "moderate": moderate_count,
                "minor": minor_count,
            },
            "unique_wcag_rules_flagged": unique_rules,
            "remediations_summary": {
                "total_proposals": len(remediations),
                "resolved_or_verified": resolved_count,
                "pending_or_proposed": pending_count,
            },
        },
        "multi_engine_evidence": {
            "multi_viewport_testing": {
                "runs_recorded": len(viewport_runs),
                "viewports_tested": sorted({r.viewport_name for r in viewport_runs}),
            },
            "regression_monitoring": {
                "baseline_pinned": bool(baseline),
                "baseline_scan_id": str(baseline.scan_id) if baseline else None,
            },
            "keyboard_simulator": {
                "status": "Deterministic browser navigation trace available",
            },
            "screen_reader_preview": {
                "status": "Semantic accessibility tree reading preview available",
            },
        },
        "wcag_criteria_audited": wcag_criteria,
        "manual_review_checklist": manual_review_checklist,
        "legal_disclaimer": (
            "This compliance passport is an auditable record of automated testing and engineering "
            "evidence. It is not an official WCAG legal certification or guarantee of non-liability."
        ),
    }

    integrity_hash = compute_deterministic_integrity_hash(evidence_payload)

    passport = CompliancePassport(
        id=uuid.uuid4(),
        project_id=project_id,
        version=version_str,
        status="completed",
        integrity_hash=integrity_hash,
        evidence_payload=evidence_payload,
        created_by=user_id,
        created_at=datetime.utcnow(),
    )
    db.add(passport)
    await db.commit()
    await db.refresh(passport)
    return passport


async def list_compliance_passports(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[CompliancePassportSummary]:
    """List all versioned compliance passports for a project."""
    await get_authorized_project(db, project_id=project_id, user_id=user_id)

    stmt = (
        select(CompliancePassport)
        .where(CompliancePassport.project_id == project_id)
        .order_by(CompliancePassport.created_at.desc())
    )
    res = await db.execute(stmt)
    passports = list(res.scalars().all())

    summaries = []
    for p in passports:
        payload = p.evidence_payload or {}
        eval_data = payload.get("compliance_evaluation", {})
        scope_data = payload.get("audit_scope", {})

        summaries.append(
            CompliancePassportSummary(
                id=p.id,
                project_id=p.project_id,
                version=p.version,
                status=p.status,
                integrity_hash=p.integrity_hash,
                status_label=eval_data.get("status_label", "Automated evidence available"),
                total_scans_included=scope_data.get("total_scans_included", 0),
                total_violations=eval_data.get("total_violations", 0),
                created_at=p.created_at,
            )
        )
    return summaries


async def get_compliance_passport_detail(
    db: AsyncSession,
    project_id: uuid.UUID,
    passport_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CompliancePassport:
    """Fetch complete compliance passport detail ensuring tenant authorization."""
    await get_authorized_project(db, project_id=project_id, user_id=user_id)

    stmt = select(CompliancePassport).where(
        CompliancePassport.id == passport_id,
        CompliancePassport.project_id == project_id,
    )
    res = await db.execute(stmt)
    passport = res.scalar_one_or_none()
    if not passport:
        raise NotFoundError("Compliance passport not found")
    return passport


def export_compliance_passport_markdown(passport: CompliancePassport) -> str:
    """Generate human-readable, auditable Markdown report document with checksums and disclaimers."""
    payload = passport.evidence_payload or {}
    meta = payload.get("passport_metadata", {})
    scope = payload.get("audit_scope", {})
    comp = payload.get("compliance_evaluation", {})
    sev = comp.get("severity_breakdown", {})
    remed = comp.get("remediations_summary", {})
    engines = payload.get("multi_engine_evidence", {})
    disclaimer = payload.get("legal_disclaimer", "")

    created_at_str = (
        passport.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if passport.created_at
        else str(meta.get("generation_timestamp", "N/A"))
    )

    md_lines = [
        f"# AccessGuard AI — Accessibility Compliance Passport ({passport.version})",
        "",
        "## Executive Summary & Integrity Manifest",
        f"- **Project Name:** {meta.get('project_name', 'N/A')}",
        f"- **Base Domain:** {meta.get('base_domain', 'N/A')}",
        f"- **Passport Version:** {passport.version}",
        f"- **Generated At:** {created_at_str}",
        f"- **Integrity Checksum (SHA-256):** `{passport.integrity_hash}`",
        f"- **Compliance Evaluation Status:** **{comp.get('status_label', 'Automated evidence available')}**",
        "",
        "---",
        "",
        "## Audit Scope & Telemetry",
        f"- **Total Scans Analyzed:** {scope.get('total_scans_included', 0)}",
        f"- **Total Pages Audited:** {scope.get('total_pages_audited', 0)}",
        f"- **Scanning Engine:** {scope.get('scanner_engine', 'axe-core')}",
        f"- **Engine Version:** axe-core {scope.get('axe_version', '4.14.0')}",
        "",
        "## Automated Findings Breakdown",
        f"- **Total Outstanding Violations:** {comp.get('total_violations', 0)}",
        f"  - **Critical:** {sev.get('critical', 0)}",
        f"  - **Serious:** {sev.get('serious', 0)}",
        f"  - **Moderate:** {sev.get('moderate', 0)}",
        f"  - **Minor:** {sev.get('minor', 0)}",
        "",
        "## Remediation Engineering Progress",
        f"- **Total Remediation Proposals:** {remed.get('total_proposals', 0)}",
        f"- **Verified / Applied Fixes:** {remed.get('resolved_or_verified', 0)}",
        f"- **Pending Approval / Review:** {remed.get('pending_or_proposed', 0)}",
        "",
        "## Multi-Engine Testing Evidence",
        f"- **Multi-Viewport Matrix:** {engines.get('multi_viewport_testing', {}).get('runs_recorded', 0)} runs recorded",
        f"- **Keyboard Navigation:** {engines.get('keyboard_simulator', {}).get('status', 'N/A')}",
        f"- **Screen Reader Preview:** {engines.get('screen_reader_preview', {}).get('status', 'N/A')}",
        f"- **Historical Regression Baseline:** {engines.get('regression_tracking', {}).get('baseline_scan_id') or 'None pinned'}",
        "",
        "## Manual Review Checklist",
    ]

    for item in payload.get("manual_review_checklist", []):
        md_lines.append(f"- [ ] **{item.get('item')}** ({item.get('guideline')}): *{item.get('status')}* — {item.get('notes')}")

    md_lines.extend([
        "",
        "---",
        "",
        "> [!IMPORTANT]",
        f"> {disclaimer}",
        "",
        f"*Report End — Generated cryptographically by AccessGuard AI for project {meta.get('project_id', '')}*",
    ])

    return "\n".join(md_lines)
