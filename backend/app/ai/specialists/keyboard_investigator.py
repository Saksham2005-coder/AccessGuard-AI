"""Specialist investigator analyzing keyboard navigation, focusability, and tab sequences."""

from typing import Any

from app.ai.specialists.base import BaseSpecialist
from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.investigation import (
    ConfidenceLevel,
    InvestigationStatus,
    Observation,
    Recommendation,
    SpecialistReport,
)

KEYBOARD_STATIC_RULES = {
    "tabindex",
    "focus-order-semantics",
    "bypass",
    "region",
    "skip-link",
    "accesskeys",
}


class KeyboardInvestigator(BaseSpecialist):
    """Evaluates keyboard accessibility, requiring interactive sessions for dynamic flow."""

    agent_id = "keyboard_investigator"
    agent_name = "Keyboard Navigation & Focus Trap Investigator"
    dimension = "keyboard_accessibility"
    version = "1.0.0"

    async def investigate(
        self,
        findings: list[Finding],
        scan: Scan,
        keyboard_run: dict[str, Any] | None = None,
    ) -> SpecialistReport:
        # Check if an interactive keyboard session was executed
        config_session = scan.config.get("keyboard_session") if scan.config else None
        session_data = keyboard_run or config_session

        kb_static_findings = [f for f in findings if f.axe_rule_id in KEYBOARD_STATIC_RULES]
        evidence_refs = [str(f.id) for f in kb_static_findings]

        if not session_data:
            # Deterministic requirement: MUST NOT claim keyboard testing occurred if no keyboard run exists!
            observations: list[Observation] = []
            if kb_static_findings:
                for f in kb_static_findings:
                    observations.append(
                        Observation(
                            finding_id=str(f.id),
                            rule_id=f.axe_rule_id,
                            selector=f.selector,
                            summary=f"Static DOM indicator: {f.description}",
                            details="Flagged by static axe rule; dynamic focus order requires interactive keyboard test session.",
                            severity=f.impact or "moderate",
                        )
                    )

            return SpecialistReport(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                agent_version=self.version,
                dimension=self.dimension,
                status="skipped",
                confidence="insufficient_evidence",
                findings_count=len(kb_static_findings),
                observations=observations,
                recommendations=[
                    Recommendation(
                        title="Execute interactive keyboard navigation test session",
                        action="Run AccessGuard AI Keyboard Navigation Simulator (Feature 5) to test for modal focus traps, sequential tab order, reverse-tab navigation, and visible focus indicators.",
                        code_example=None,
                        priority="P3",
                        affected_finding_ids=evidence_refs,
                    )
                ],
                wcag_criteria=["2.1.1", "2.1.2", "2.4.3", "2.4.7"],
                limitations=[
                    "No deterministic keyboard navigation session was recorded for this scan. Automated DOM analysis cannot determine focus trap, tab navigation order, or skip links without an interactive keyboard test run.",
                    "Static HTML analysis cannot evaluate dynamic JavaScript focus management (e.g. element.focus() on modal open/close).",
                ],
                evidence_references=evidence_refs,
            )

        # Keyboard run session exists
        status: InvestigationStatus = "completed"
        confidence: ConfidenceLevel = "supported"
        observations = []
        recommendations = []

        traps = session_data.get("focus_traps", [])
        tab_order_issues = session_data.get("tab_order_issues", [])

        if traps:
            for trap in traps:
                observations.append(
                    Observation(
                        finding_id=None,
                        rule_id="keyboard-trap",
                        selector=trap.get("selector"),
                        summary=f"Keyboard focus trap detected at {trap.get('selector')}",
                        details="Focus cannot escape container using Tab or Shift+Tab keys.",
                        severity="critical",
                    )
                )
            recommendations.append(
                Recommendation(
                    title="Remove keyboard focus trap",
                    action="Ensure keyboard users can exit all interactive components using standard Tab, Shift+Tab, or Escape keys without getting locked in a loop.",
                    priority="P1",
                    affected_finding_ids=[],
                )
            )

        for issue in tab_order_issues:
            observations.append(
                Observation(
                    finding_id=None,
                    rule_id="tab-order-disruption",
                    selector=issue.get("selector"),
                    summary=issue.get("message", "Unnatural tab index jump"),
                    details=issue.get("details"),
                    severity="serious",
                )
            )

        return SpecialistReport(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            dimension=self.dimension,
            status=status,
            confidence=confidence,
            findings_count=len(observations),
            observations=observations,
            recommendations=recommendations,
            wcag_criteria=["2.1.1", "2.1.2", "2.4.3", "2.4.7"],
            limitations=[
                "Interactive keyboard testing evaluates automated key events in headless Chromium. Custom platform-specific keyboard shortcuts or assistive technology key chords (e.g., NVDA browse mode) should be verified manually.",
            ],
            evidence_references=evidence_refs,
        )
