"""Specialist investigator analyzing native HTML semantics versus ARIA overrides."""

from typing import Any

from app.ai.specialists.base import BaseSpecialist
from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.investigation import (
    ConfidenceLevel,
    Observation,
    Recommendation,
    SpecialistReport,
)

SEMANTIC_HTML_RULES = {
    "aria-allowed-role",
    "aria-roles",
    "aria-valid-attr-value",
    "aria-valid-attr",
    "landmark-one-main",
    "region",
    "button-name",
    "link-name",
    "label",
    "select-name",
    "nested-interactive",
}


class SemanticHtmlInvestigator(BaseSpecialist):
    """Inspects native HTML5 element semantics, native versus ARIA balance, and form relationships."""

    agent_id = "semantic_html_investigator"
    agent_name = "Semantic HTML & Native Architecture Investigator"
    dimension = "semantic_html"
    version = "1.0.0"

    async def investigate(
        self,
        findings: list[Finding],
        _scan: Scan,
        _keyboard_run: dict[str, Any] | None = None,
    ) -> SpecialistReport:

        semantic_findings = [f for f in findings if f.axe_rule_id in SEMANTIC_HTML_RULES]

        observations: list[Observation] = []
        recommendations: list[Recommendation] = []
        evidence_refs: list[str] = []

        div_button_refs: list[str] = []
        label_refs: list[str] = []

        for f in semantic_findings:
            finding_id_str = str(f.id)
            evidence_refs.append(finding_id_str)
            snippet = (f.html_snippet or "").lower()

            if ("<div" in snippet or "<span" in snippet) and ("button" in snippet or "role" in snippet):
                div_button_refs.append(finding_id_str)
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=f.axe_rule_id,
                        selector=f.selector,
                        summary="Non-semantic generic container used for interactive widget",
                        details=f"Detected <div> or <span> emulating interactive behavior. Lacks native keyboard trigger and accessibility semantics: {f.description}",
                        severity=f.impact or "serious",
                    )
                )
            elif f.axe_rule_id in ("label", "select-name"):
                label_refs.append(finding_id_str)
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=f.axe_rule_id,
                        selector=f.selector,
                        summary=f"Form control missing programmatic native label: {f.description}",
                        details="Native <label for='...'> association provides click-to-focus hit target expansion and screen reader binding.",
                        severity=f.impact or "critical",
                    )
                )
            else:
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=f.axe_rule_id,
                        selector=f.selector,
                        summary=f.description,
                        details=f.failure_summary,
                        severity=f.impact or "moderate",
                    )
                )

        if div_button_refs:
            recommendations.append(
                Recommendation(
                    title="Replace faux-interactive <div> elements with native <button>",
                    action="First rule of ARIA: Do not use ARIA when native HTML can achieve the same result. Native <button> automatically handles Space/Enter key actuation, tab focusability, and disabled state.",
                    code_example="<!-- Before -->\n<div role=\"button\" tabindex=\"0\" onclick=\"submit()\">Submit</div>\n\n<!-- After -->\n<button type=\"button\" onclick=\"submit()\">Submit</button>",
                    priority="P2",
                    affected_finding_ids=div_button_refs,
                )
            )

        if label_refs:
            recommendations.append(
                Recommendation(
                    title="Associate input controls with explicit native <label> elements",
                    action="Enclose inputs in a <label> or bind them using for and id attributes to ensure native touch and assistive technology focus.",
                    code_example='<label for="user-email">Email Address</label>\n<input id="user-email" type="email" name="email" required />',
                    priority="P1",
                    affected_finding_ids=label_refs,
                )
            )

        confidence: ConfidenceLevel = "supported" if semantic_findings else "supported"

        return SpecialistReport(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            dimension=self.dimension,
            status="completed",
            confidence=confidence,
            findings_count=len(semantic_findings),
            observations=observations,
            recommendations=recommendations,
            wcag_criteria=["1.3.1", "3.3.2", "4.1.2"],
            limitations=[
                "Static HTML inspection flags missing semantic elements and improper ARIA usage, but cannot evaluate custom web components (Shadow DOM) without shadow root piercing.",
            ],
            evidence_references=evidence_refs,
        )
