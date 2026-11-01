"""Specialist investigator analyzing color contrast, luminous ratios, and background complexities."""

import re
from typing import Any

from app.ai.specialists.base import BaseSpecialist
from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.investigation import (
    ConfidenceLevel,
    InvestigationStatus,
    Observation,
    PriorityLevel,
    Recommendation,
    SpecialistReport,
)

CONTRAST_RULES = {"color-contrast", "color-contrast-enhanced", "link-in-text-block"}


class ContrastInvestigator(BaseSpecialist):
    """Evaluates axe color contrast findings and checks for background image or gradient limitations."""

    agent_id = "contrast_investigator"
    agent_name = "Contrast & Visual Acoustics Investigator"
    dimension = "color_contrast"
    version = "1.0.0"

    async def investigate(
        self,
        findings: list[Finding],
        _scan: Scan,
        _keyboard_run: dict[str, Any] | None = None,
    ) -> SpecialistReport:

        contrast_findings = [f for f in findings if f.axe_rule_id in CONTRAST_RULES]

        if not contrast_findings:
            return SpecialistReport(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                agent_version=self.version,
                dimension=self.dimension,
                status="completed",
                confidence="supported",
                findings_count=0,
                observations=[],
                recommendations=[],
                wcag_criteria=["1.4.3"],
                limitations=[
                    "No automated color contrast violations were detected by axe-core. However, text positioned over CSS gradients, video backgrounds, or canvas elements cannot be deterministically evaluated by static CSS queries and requires manual verification.",
                ],
                evidence_references=[],
            )

        observations: list[Observation] = []
        recommendations: list[Recommendation] = []
        evidence_refs: list[str] = []
        has_gradient_or_image = False

        for f in contrast_findings:
            finding_id_str = str(f.id)
            evidence_refs.append(finding_id_str)

            # Check for background image or gradient in failure summary or snippet
            summary_lower = (f.failure_summary or "").lower()
            snippet_lower = (f.html_snippet or "").lower()
            if any(term in summary_lower or term in snippet_lower for term in ("gradient", "background-image", "canvas", "opacity", "transparent")):
                has_gradient_or_image = True

            # Extract contrast ratio if present
            ratio_match = re.search(r"(\d+(?:\.\d+)?):1", f.failure_summary or "")
            ratio_str = f" (measured ratio {ratio_match.group(1)}:1)" if ratio_match else ""

            observations.append(
                Observation(
                    finding_id=finding_id_str,
                    rule_id=f.axe_rule_id,
                    selector=f.selector,
                    summary=f"Insufficient contrast ratio on element{ratio_str}",
                    details=f.failure_summary or f.description,
                    severity=f.impact or "serious",
                )
            )

        # Build prioritized recommendation
        critical_count = sum(1 for f in contrast_findings if f.impact in ("critical", "serious"))
        rec_priority: PriorityLevel = "P1" if critical_count > 0 else "P2"


        recommendations.append(
            Recommendation(
                title="Increase foreground-to-background luminance contrast",
                action="Adjust CSS text color or container background color to satisfy WCAG 2.2 Level AA requirement of at least 4.5:1 for normal text (< 18pt / < 14pt bold) and 3:1 for large text.",
                code_example="/* Example remediation */\n.insufficient-contrast {\n  color: #111827; /* Dark charcoal */\n  background-color: #FFFFFF; /* High contrast ratio 16.1:1 */\n}",
                priority=rec_priority,
                affected_finding_ids=evidence_refs,
            )
        )

        limitations = [
            "Computed color contrast is based on static CSS styles. Elements positioned over CSS gradients, background images, HTML5 canvas, or semi-transparent overlays must be manually verified with a calibrated color contrast analyzer.",
            "Dynamic hover, focus, and active pseudo-class states require manual interaction verification to ensure contrast compliance across all user interaction states.",
        ]
        if has_gradient_or_image:
            limitations.insert(
                0,
                "FLAGGED FOR MANUAL REVIEW: One or more elements appear to use CSS gradients, background images, or opacity. Automated static sampling cannot guarantee contrast across variable backgrounds.",
            )

        confidence: ConfidenceLevel = "supported" if all(f.failure_summary for f in contrast_findings) else "tentative"
        status: InvestigationStatus = "completed"

        return SpecialistReport(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            dimension=self.dimension,
            status=status,
            confidence=confidence,
            findings_count=len(contrast_findings),
            observations=observations,
            recommendations=recommendations,
            wcag_criteria=["1.4.3", "1.4.6"],
            limitations=limitations,
            evidence_references=evidence_refs,
        )
