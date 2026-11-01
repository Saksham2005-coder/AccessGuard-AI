"""Specialist investigator analyzing screen reader semantics, accessible names, and landmark structures."""

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

SCREEN_READER_RULES = {
    "image-alt",
    "image-redundant-alt",
    "button-name",
    "link-name",
    "input-button-title",
    "label",
    "aria-label",
    "aria-labelledby",
    "aria-hidden-body",
    "aria-hidden-focus",
    "heading-order",
    "page-has-heading-one",
    "landmark-one-main",
    "landmark-unique",
    "landmark-main-is-top-level",
    "region",
}


class ScreenReaderSemanticsInvestigator(BaseSpecialist):
    """Examines DOM accessibility tree semantics, accessible names, and structural landmarks."""

    agent_id = "screen_reader_semantics_investigator"
    agent_name = "Screen Reader Semantics & ARIA Tree Investigator"
    dimension = "screen_reader_semantics"
    version = "1.0.0"

    async def investigate(
        self,
        findings: list[Finding],
        _scan: Scan,
        _keyboard_run: dict[str, Any] | None = None,
    ) -> SpecialistReport:

        sr_findings = [f for f in findings if f.axe_rule_id in SCREEN_READER_RULES]

        observations: list[Observation] = []
        recommendations: list[Recommendation] = []
        evidence_refs: list[str] = []

        missing_names: list[str] = []
        heading_issues: list[str] = []
        image_alt_issues: list[str] = []

        for f in sr_findings:
            finding_id_str = str(f.id)
            evidence_refs.append(finding_id_str)

            rule = f.axe_rule_id
            if rule in ("button-name", "link-name", "input-button-title", "label"):
                missing_names.append(finding_id_str)
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=rule,
                        selector=f.selector,
                        summary=f"Interactive element lacks accessible name: {f.description}",
                        details="Screen readers will announce generic role (e.g. 'button') without communicating purpose.",
                        severity=f.impact or "critical",
                    )
                )
            elif rule in ("image-alt", "image-redundant-alt"):
                image_alt_issues.append(finding_id_str)
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=rule,
                        selector=f.selector,
                        summary=f"Non-text content accessibility violation: {f.description}",
                        details="Images without descriptive alt text force screen readers to vocalize raw filenames or skip content.",
                        severity=f.impact or "serious",
                    )
                )
            elif rule in ("heading-order", "page-has-heading-one"):
                heading_issues.append(finding_id_str)
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=rule,
                        selector=f.selector,
                        summary=f"Heading outline irregularity: {f.description}",
                        details="Skipping heading levels confuses blind users navigating by headings (H key).",
                        severity=f.impact or "moderate",
                    )
                )
            else:
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=rule,
                        selector=f.selector,
                        summary=f.description,
                        details=f.failure_summary,
                        severity=f.impact or "moderate",
                    )
                )

        if missing_names:
            recommendations.append(
                Recommendation(
                    title="Provide programmatic accessible names for interactive controls",
                    action="Add visible text content, an aria-label attribute, or an aria-labelledby reference so assistive tech can articulate the element's function.",
                    code_example='<!-- Before -->\n<button class="icon-search"><svg>...</svg></button>\n\n<!-- After -->\n<button class="icon-search" aria-label="Search site">\n  <svg aria-hidden="true">...</svg>\n</button>',
                    priority="P1",
                    affected_finding_ids=missing_names,
                )
            )

        if image_alt_issues:
            recommendations.append(
                Recommendation(
                    title="Add descriptive alternative text for informative images",
                    action="Set alt attribute with concise, meaningful description for informational images, or alt='' for purely decorative graphics.",
                    code_example='<!-- Informative -->\n<img src="/chart.png" alt="Quarterly accessibility audit score trend up 15%">\n\n<!-- Decorative -->\n<img src="/glow-bg.svg" alt="" aria-hidden="true">',
                    priority="P2",
                    affected_finding_ids=image_alt_issues,
                )
            )

        if heading_issues:
            recommendations.append(
                Recommendation(
                    title="Structure headings into a sequential logical hierarchy",
                    action="Ensure pages begin with a single top-level <h1>, and nested sections increment by exactly one level without skipping (e.g. h1 -> h2 -> h3).",
                    code_example="<h1>Main Title</h1>\n  <h2>Sub-section</h2>\n    <h3>Detail Block</h3>",
                    priority="P3",
                    affected_finding_ids=heading_issues,
                )
            )

        confidence: ConfidenceLevel = "supported" if sr_findings else "supported"

        return SpecialistReport(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            dimension=self.dimension,
            status="completed",
            confidence=confidence,
            findings_count=len(sr_findings),
            observations=observations,
            recommendations=recommendations,
            wcag_criteria=["1.1.1", "1.3.1", "2.4.6", "4.1.2"],
            limitations=[
                "Static DOM interpretation aid, not an NVDA/JAWS/VoiceOver execution. Real screen reader announcements depend on assistive technology settings, browser engines, and operating system speech synthesizers.",
                "Semantic tree calculations cannot verify the phonetic pronunciation of domain-specific acronyms or the cognitive clarity of generated alt text.",
            ],
            evidence_references=evidence_refs,
        )
