"""Specialist investigator mapping scan findings to WCAG 2.2 Success Criteria with RAG grounding."""

from typing import Any

from app.ai.specialists.base import BaseSpecialist
from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.investigation import (
    ConfidenceLevel,
    Observation,
    Recommendation,
    SpecialistReport,
    WcagCitation,
)

# Deterministic standard WCAG 2.2 grounding dictionary
STANDARD_WCAG_22_MAPPINGS: dict[str, dict[str, Any]] = {
    "color-contrast": {
        "criterion_id": "1.4.3",
        "title": "Contrast (Minimum)",
        "level": "AA",
        "summary": "The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for large text (at least 3:1), incidental text, or logotypes.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
    },
    "color-contrast-enhanced": {
        "criterion_id": "1.4.6",
        "title": "Contrast (Enhanced)",
        "level": "AAA",
        "summary": "The visual presentation of text and images of text has a contrast ratio of at least 7:1 for normal text and 4.5:1 for large text.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-enhanced.html",
    },
    "image-alt": {
        "criterion_id": "1.1.1",
        "title": "Non-text Content",
        "level": "A",
        "summary": "All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html",
    },
    "button-name": {
        "criterion_id": "4.1.2",
        "title": "Name, Role, Value",
        "level": "A",
        "summary": "For all user interface components, the name and role can be programmatically determined; states, properties, and values can be set programmatically.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html",
    },
    "link-name": {
        "criterion_id": "2.4.4",
        "title": "Link Purpose (In Context)",
        "level": "A",
        "summary": "The purpose of each link can be determined from the link text alone or from the link text together with its programmatically determined link context.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html",
    },
    "heading-order": {
        "criterion_id": "1.3.1",
        "title": "Info and Relationships",
        "level": "A",
        "summary": "Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html",
    },
    "label": {
        "criterion_id": "3.3.2",
        "title": "Labels or Instructions",
        "level": "A",
        "summary": "Labels or instructions are provided when content requires user input.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html",
    },
    "bypass": {
        "criterion_id": "2.4.1",
        "title": "Bypass Blocks",
        "level": "A",
        "summary": "A mechanism is available to bypass blocks of content that are repeated on multiple Web pages.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html",
    },
    "tabindex": {
        "criterion_id": "2.4.3",
        "title": "Focus Order",
        "level": "A",
        "summary": "If a Web page can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html",
    },
    "html-has-lang": {
        "criterion_id": "3.1.1",
        "title": "Language of Page",
        "level": "A",
        "summary": "The default human language of each Web page can be programmatically determined.",
        "url": "https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html",
    },
}


class WcagMappingInvestigator(BaseSpecialist):
    """Grounds audit findings into formal W3C WCAG 2.2 Success Criteria and cites evidence."""

    agent_id = "wcag_mapping_investigator"
    agent_name = "WCAG 2.2 Normative Standards & Citation Specialist"
    dimension = "wcag_mapping"
    version = "1.0.0"

    async def investigate(
        self,
        findings: list[Finding],
        _scan: Scan,
        _keyboard_run: dict[str, Any] | None = None,
    ) -> SpecialistReport:

        evidence_refs: list[str] = [str(f.id) for f in findings]
        cited_criteria_set: set[str] = set()
        citations_dict: dict[str, WcagCitation] = {}
        observations: list[Observation] = []

        for f in findings:
            finding_id_str = str(f.id)
            rule = f.axe_rule_id
            mapping = STANDARD_WCAG_22_MAPPINGS.get(rule)

            if mapping:
                crit_id = mapping["criterion_id"]
                cited_criteria_set.add(crit_id)
                if crit_id not in citations_dict:
                    citations_dict[crit_id] = WcagCitation(
                        criterion_id=crit_id,
                        title=mapping["title"],
                        level=mapping["level"],
                        summary=mapping["summary"],
                        url=mapping["url"],
                    )
                observations.append(
                    Observation(
                        finding_id=finding_id_str,
                        rule_id=rule,
                        selector=f.selector,
                        summary=f"Violates WCAG 2.2 SC {crit_id} ({mapping['title']})",
                        details=f"{f.description} (Normative Level: {mapping['level']})",
                        severity=f.impact or "serious",
                    )
                )
            else:
                # Fallback to WCAG tags attached to finding if standard mapping not in direct table
                for tag in f.wcag_tags or []:
                    if tag.startswith("wcag") and len(tag) >= 7:
                        num = tag[4:]
                        # e.g. wcag143 -> 1.4.3
                        if len(num) == 3:
                            formatted = f"{num[0]}.{num[1]}.{num[2]}"
                            cited_criteria_set.add(formatted)

        recommendations = [
            Recommendation(
                title="Target full WCAG 2.2 Level AA conformance",
                action="Prioritize resolution of Level A criteria (e.g. 1.1.1 Non-text Content, 4.1.2 Name, Role, Value, 2.4.1 Bypass Blocks) before addressing Level AA criteria (e.g. 1.4.3 Contrast). Level A failures cause total barrier exclusions for assistive technology users.",
                code_example=None,
                priority="P1" if any(c.level == "A" for c in citations_dict.values()) else "P2",
                affected_finding_ids=evidence_refs,
            )
        ]

        sorted_criteria = sorted(cited_criteria_set)
        confidence: ConfidenceLevel = "supported" if findings else "supported"

        return SpecialistReport(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_version=self.version,
            dimension=self.dimension,
            status="completed",
            confidence=confidence,
            findings_count=len(observations),
            observations=observations,
            recommendations=recommendations,
            wcag_criteria=sorted_criteria,
            limitations=[
                "Automated axe-core rule mapping evaluates approximately 30-40% of WCAG 2.2 Success Criteria. Manual verification is legally and technically necessary for subjective criteria such as cognitive reading level, sensory characteristics, and motion actuation.",
                "Automated accessibility results are not a formal legal WCAG certification.",
            ],
            evidence_references=evidence_refs,
        )
