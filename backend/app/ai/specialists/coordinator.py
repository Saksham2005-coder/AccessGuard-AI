"""Investigation coordinator running specialist agents and synthesizing multi-agent findings."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from app.ai.specialists.contrast_investigator import ContrastInvestigator
from app.ai.specialists.keyboard_investigator import KeyboardInvestigator
from app.ai.specialists.screen_reader_semantics_investigator import (
    ScreenReaderSemanticsInvestigator,
)
from app.ai.specialists.semantic_html_investigator import SemanticHtmlInvestigator
from app.ai.specialists.wcag_mapping_investigator import (
    STANDARD_WCAG_22_MAPPINGS,
    WcagMappingInvestigator,
)
from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.investigation import (
    ConfidenceLevel,
    InvestigationReport,
    InvestigationStatus,
    PriorityLevel,
    RemediationMatrixItem,
    SpecialistReport,
    WcagCitation,
)


class InvestigationCoordinator:
    """Orchestrates multi-agent specialist investigations, deduplication, and executive synthesis."""

    def __init__(self) -> None:
        self.specialists = [
            ContrastInvestigator(),
            KeyboardInvestigator(),
            ScreenReaderSemanticsInvestigator(),
            SemanticHtmlInvestigator(),
            WcagMappingInvestigator(),
        ]

    async def run_investigation(
        self,
        scan: Scan,
        findings: list[Finding],
        keyboard_run: dict[str, Any] | None = None,
        investigation_id: str | None = None,
    ) -> InvestigationReport:
        inv_id = investigation_id or str(uuid.uuid4())
        created_at_iso = datetime.now(UTC).isoformat()

        # 1. Run specialists in parallel
        tasks = [
            s.investigate(findings, scan, keyboard_run)
            for s in self.specialists
        ]

        results: list[SpecialistReport] = await asyncio.gather(*tasks)

        specialists_dict: dict[str, SpecialistReport] = {
            r.agent_id: r for r in results
        }

        # 2. Synthesize Prioritized Remediation Matrix across all recommendations
        remediation_matrix: list[RemediationMatrixItem] = []
        seen_rec_titles: set[str] = set()

        # Collect and prioritize recommendations
        for report in results:
            for rec in report.recommendations:
                if rec.title in seen_rec_titles:
                    continue
                seen_rec_titles.add(rec.title)

                priority: PriorityLevel = rec.priority
                remediation_matrix.append(
                    RemediationMatrixItem(
                        priority=priority,
                        title=rec.title,
                        description=rec.action,
                        dimension=report.dimension,
                        affected_findings=rec.affected_finding_ids,
                        remediation_hint=rec.code_example or "Inspect finding nodes in DOM and apply safe attribute modifications.",
                    )
                )

        # Sort matrix by priority: P1, P2, P3, P4
        priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        remediation_matrix.sort(key=lambda item: priority_order.get(item.priority, 5))

        # 3. Deduplicate manual verification checklist
        manual_checklist: list[str] = []
        seen_limitations: set[str] = set()
        for report in results:
            for lim in report.limitations:
                if lim not in seen_limitations:
                    seen_limitations.add(lim)
                    manual_checklist.append(lim)

        # 4. Aggregate WCAG citations
        wcag_citations: list[WcagCitation] = []
        seen_criteria: set[str] = set()
        for f in findings:
            mapping = STANDARD_WCAG_22_MAPPINGS.get(f.axe_rule_id)
            if mapping:
                cid = mapping["criterion_id"]
                if cid not in seen_criteria:
                    seen_criteria.add(cid)
                    wcag_citations.append(
                        WcagCitation(
                            criterion_id=cid,
                            title=mapping["title"],
                            level=mapping["level"],
                            summary=mapping["summary"],
                            url=mapping["url"],
                        )
                    )

        # 5. Determine overall investigation status and confidence
        statuses = [r.status for r in results]
        overall_status: InvestigationStatus = (
            "completed" if all(st == "completed" for st in statuses) else "partial"
        )

        # If keyboard specialist is skipped, overall confidence is tentative to reflect dynamic flow absence
        keyboard_report = specialists_dict.get("keyboard_investigator")
        if keyboard_report and keyboard_report.status == "skipped":
            overall_confidence: ConfidenceLevel = "tentative"
        elif any(r.confidence == "insufficient_evidence" for r in results):
            overall_confidence = "tentative"
        else:
            overall_confidence = "supported"

        # 6. Generate grounded executive summary
        total_findings = len(findings)
        p1_count = sum(1 for m in remediation_matrix if m.priority == "P1")
        p2_count = sum(1 for m in remediation_matrix if m.priority == "P2")

        exec_summary_parts = [
            f"Autonomous multi-agent investigation completed for scan {scan.id} across {len(self.specialists)} bounded dimensions.",
            f"Evaluated {total_findings} verified accessibility findings from target URL: {scan.target_url}.",
        ]

        if p1_count > 0:
            exec_summary_parts.append(
                f"Identified {p1_count} Critical (P1) barrier(s) that immediately disrupt assistive technology navigation."
            )
        if p2_count > 0:
            exec_summary_parts.append(
                f"Identified {p2_count} High (P2) barrier(s) requiring prompt structural remediation."
            )

        if keyboard_report and keyboard_report.status == "skipped":
            exec_summary_parts.append(
                "NOTE: Interactive keyboard navigation test was not recorded for this scan; dynamic focus management and modal focus traps require manual or simulated keyboard execution."
            )

        exec_summary_parts.append(
            "All findings are grounded in deterministic axe-core evidence and mapped to normative WCAG 2.2 criteria. Automated audits are not legal certifications."
        )

        executive_summary = " ".join(exec_summary_parts)

        return InvestigationReport(
            investigation_id=inv_id,
            scan_id=str(scan.id),
            status=overall_status,
            overall_confidence=overall_confidence,
            executive_summary=executive_summary,
            specialists=specialists_dict,
            remediation_matrix=remediation_matrix,
            manual_verification_checklist=manual_checklist,
            wcag_citations=wcag_citations,
            duration_ms=None,
            created_at=created_at_iso,
        )
