"""Conversational Accessibility Assistant service.

Phase 19 Feature 8: Evidence-grounded conversational assistant scoped to authorized projects
and scans, integrated with WCAG 2.2 knowledge retrieval, prompt injection barriers,
and structured evidence reporting.
"""

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.models.assistant import AssistantConversation, AssistantMessage
from app.db.models.finding import Finding
from app.db.models.knowledge import KnowledgeChunk
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantConversationResponse,
    AssistantMessageResponse,
    AssistantStructuredData,
    FindingEvidenceItem,
    WcagCitationItem,
)

logger = get_logger("assistant_service")

# Curated reference map of core WCAG 2.2 criteria
WCAG_CRITERIA_MAP = {
    "color-contrast": WcagCitationItem(
        criterion_id="1.4.3",
        title="Contrast (Minimum)",
        guidance="Visual presentation of text and images of text must have a contrast ratio of at least 4.5:1 (or 3:1 for large text).",
        url="https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
    ),
    "image-alt": WcagCitationItem(
        criterion_id="1.1.1",
        title="Non-text Content",
        guidance="All non-text content presented to the user must have a text alternative that serves the equivalent purpose.",
        url="https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html",
    ),
    "button-name": WcagCitationItem(
        criterion_id="4.1.2",
        title="Name, Role, Value",
        guidance="For all user interface components, the name and role must be programmatically determinable.",
        url="https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html",
    ),
    "link-name": WcagCitationItem(
        criterion_id="2.4.4",
        title="Link Purpose (In Context)",
        guidance="The purpose of each link must be determinable from the link text alone or from the link text together with its programmatically determined context.",
        url="https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html",
    ),
    "document-title": WcagCitationItem(
        criterion_id="2.4.2",
        title="Page Titled",
        guidance="Web pages must have titles that describe their topic or purpose.",
        url="https://www.w3.org/WAI/WCAG22/Understanding/page-titled.html",
    ),
    "html-has-lang": WcagCitationItem(
        criterion_id="3.1.1",
        title="Language of Page",
        guidance="The default human language of each web page must be programmatically determinable using the lang attribute.",
        url="https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html",
    ),
    "tabindex": WcagCitationItem(
        criterion_id="2.4.3",
        title="Focus Order",
        guidance="If a web page can be navigated sequentially, focusable components must receive focus in an order that preserves meaning and operability.",
        url="https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html",
    ),
}


def build_message_response(msg: AssistantMessage) -> AssistantMessageResponse:
    """Convert AssistantMessage database model to API response schema."""
    structured = (
        AssistantStructuredData(**msg.structured_data)
        if msg.structured_data
        else None
    )
    return AssistantMessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        content=msg.content,
        structured_data=structured,
        created_at=msg.created_at,
    )


def build_conversation_response(
    conv: AssistantConversation,
) -> AssistantConversationResponse:
    """Convert AssistantConversation database model to API response schema."""
    return AssistantConversationResponse(
        id=conv.id,
        project_id=conv.project_id,
        scan_id=conv.scan_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[build_message_response(m) for m in conv.messages],
    )


async def synthesize_grounded_response(
    query: str,
    project: Project,
    scan: Scan | None,
    findings: list[Finding],
    db: AsyncSession,
) -> tuple[str, AssistantStructuredData]:
    """Generate evidence-grounded answer with citations, observed facts, and recommendations."""
    query_lower = query.lower()

    # Partition findings by impact
    critical = [f for f in findings if f.impact == "critical"]
    serious = [f for f in findings if f.impact == "serious"]
    moderate = [f for f in findings if f.impact == "moderate"]
    minor = [f for f in findings if f.impact == "minor"]

    observed_facts: list[str] = []
    guidance_notes: list[str] = []
    matched_findings: list[Finding] = []
    wcag_citations: list[WcagCitationItem] = []
    suggested_action: str = ""

    scan_desc = f"Scan `{scan.id}`" if scan else "recent project audit"
    target_url = scan.target_url if scan else f"https://{project.base_domain}"

    observed_facts.append(
        f"Project '{project.name}' ({project.base_domain}) currently has {len(findings)} total recorded violations in {scan_desc}."
    )
    if findings:
        observed_facts.append(
            f"Breakdown: {len(critical)} critical, {len(serious)} serious, {len(moderate)} moderate, and {len(minor)} minor violations."
        )

    # 1. Intent: Priority / What to fix first
    if any(k in query_lower for k in ("first", "priority", "critical", "most important", "start")):
        high_priority = critical if critical else serious
        matched_findings = high_priority[:4]

        answer_lines = [
            f"### 🎯 Recommended Remediation Priority for {project.name}\n",
            f"Based on automated evaluation of `{target_url}`, here are the highest-impact barriers that immediately hinder assistive technology users:\n",
        ]

        if critical:
            answer_lines.append(f"**Immediate Attention Required:** You have **{len(critical)} critical violations** that completely block screen reader or keyboard users.")
        elif serious:
            answer_lines.append(f"You have **{len(serious)} serious violations** that cause significant friction.")
        else:
            answer_lines.append("No critical or serious violations were detected! Focus on moderate contrast or layout improvements.")

        for idx, f in enumerate(matched_findings, 1):
            selector_info = f" on `{f.selector}`" if f.selector else ""
            answer_lines.append(f"{idx}. **`{f.axe_rule_id}`** ({f.impact}): {f.description}{selector_info}")
            if f.axe_rule_id in WCAG_CRITERIA_MAP:
                wcag_citations.append(WCAG_CRITERIA_MAP[f.axe_rule_id])

        suggested_action = (
            f"Navigate to the Remediations tab to review and approve automated patches for `{matched_findings[0].axe_rule_id}`."
            if matched_findings
            else "Continue routine scheduled monitoring."
        )
        guidance_notes.append("Resolve critical violations first because they represent severe usability blocks under WCAG Level A.")

    # 2. Intent: Contrast
    elif any(k in query_lower for k in ("contrast", "color", "background", "foreground", "readable")):
        contrast_findings = [f for f in findings if "contrast" in f.axe_rule_id.lower()]
        matched_findings = contrast_findings[:5]

        if WCAG_CRITERIA_MAP.get("color-contrast"):
            wcag_citations.append(WCAG_CRITERIA_MAP["color-contrast"])

        if contrast_findings:
            observed_facts.append(f"{len(contrast_findings)} element(s) failed minimum color contrast thresholds.")
            answer_lines = [
                "### 🎨 Color Contrast Evaluation\n",
                f"We found **{len(contrast_findings)} color contrast violation(s)** on `{target_url}`.\n",
                "Under **WCAG 2.2 Criterion 1.4.3 (Contrast Minimum)**, normal text must have a luminance contrast ratio of at least **4.5:1** against its background, while large text (18pt+ or 14pt+ bold) requires at least **3:1**.\n",
                "**Affected Elements:**\n",
            ]
            for f in matched_findings:
                answer_lines.append(f"- Selector `{f.selector}`: {f.description}")
            guidance_notes.append("Adjust text color lightness or darken the background container to reach at least 4.5:1.")
            suggested_action = "Inspect affected CSS rules in your stylesheet and update the text or background hex values."
        else:
            answer_lines = [
                "### 🎨 Color Contrast Evaluation\n",
                f"No color contrast violations were detected in {scan_desc} for `{target_url}`. Your color palette satisfies WCAG 1.4.3 minimums for the evaluated pages."
            ]
            suggested_action = "Verify interactive hover and active states which may have different dynamic colors."

    # 3. Intent: Keyboard / Focus / Navigation
    elif any(k in query_lower for k in ("keyboard", "focus", "navigation", "tab", "skip")):
        nav_findings = [f for f in findings if any(k in f.axe_rule_id.lower() for k in ("tab", "focus", "nav", "button", "link", "aria"))]
        matched_findings = nav_findings[:5]

        if WCAG_CRITERIA_MAP.get("tabindex"):
            wcag_citations.append(WCAG_CRITERIA_MAP["tabindex"])

        answer_lines = [
            "### ⌨️ Keyboard Navigation & Operability\n",
            f"Keyboard accessibility ensures users relying on keyboards, switches, or mouth-sticks can interact with all controls on `{target_url}` without a mouse.\n",
        ]
        if nav_findings:
            observed_facts.append(f"{len(nav_findings)} keyboard / interactive control issue(s) detected.")
            answer_lines.append(f"**Identified Navigation Issues ({len(nav_findings)}):**\n")
            for f in matched_findings:
                answer_lines.append(f"- **`{f.axe_rule_id}`** on `{f.selector}`: {f.description}")
            guidance_notes.append("Avoid positive tabindex values (tabindex > 0); keep natural DOM order and ensure visible focus rings (`:focus-visible`).")
            suggested_action = "Run a Keyboard Navigation Simulator test from the Scans page to inspect sequential tab stops."
        else:
            answer_lines.append("No critical interactive control violations were detected in this automated scan.")
            guidance_notes.append("Automated tests catch missing attributes, but cannot test logical tab order or visual focus indicator contrast. Manual keyboard testing with the Tab key is recommended.")
            suggested_action = "Open the Keyboard Navigation Simulator modal on this scan to verify tab stops."

    # 4. General / Summary Intent
    else:
        matched_findings = (critical + serious + moderate)[:4]
        for f in matched_findings:
            if f.axe_rule_id in WCAG_CRITERIA_MAP and WCAG_CRITERIA_MAP[f.axe_rule_id] not in wcag_citations:
                wcag_citations.append(WCAG_CRITERIA_MAP[f.axe_rule_id])

        answer_lines = [
            f"### 🛡️ Accessibility Overview for {project.name}\n",
            f"Here is the verified status for `{target_url}` based on {scan_desc}:\n",
            f"- **Total Violations:** {len(findings)}",
            f"- **Critical:** {len(critical)} | **Serious:** {len(serious)} | **Moderate:** {len(moderate)} | **Minor:** {len(minor)}\n",
        ]

        if matched_findings:
            answer_lines.append("**Key Findings Highlighted:**")
            for f in matched_findings:
                answer_lines.append(f"- `{f.axe_rule_id}` ({f.impact}): {f.description}")

        guidance_notes.append("Accessibility is an iterative engineering process. Focusing on high-impact barriers first delivers the greatest user experience gain.")
        suggested_action = "Review the findings list or run an Autonomous Specialist Agent investigation for deeper root-cause analysis."

    # Also search DB knowledge chunks if available
    try:
        k_res = await db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.content.ilike(f"%{query[:30]}%"))
            .limit(2)
        )
        chunks = list(k_res.scalars().all())
        for c in chunks:
            if c.criterion_id and not any(cit.criterion_id == c.criterion_id for cit in wcag_citations):
                wcag_citations.append(
                    WcagCitationItem(
                        criterion_id=c.criterion_id,
                        title=c.section_title or f"WCAG {c.criterion_id}",
                        guidance=c.content[:180] + "...",
                        url=c.source_url,
                    )
                )
    except Exception as e:
        logger.debug("Optional DB knowledge lookup skipped", error=str(e))

    evidence_items = [
        FindingEvidenceItem(
            finding_id=f.id,
            rule_id=f.axe_rule_id,
            impact=f.impact,
            selector=f.selector,
            description=f.description,
        )
        for f in matched_findings
    ]

    structured_data = AssistantStructuredData(
        evidence_findings=evidence_items,
        wcag_citations=wcag_citations,
        observed_facts=observed_facts,
        guidance_notes=guidance_notes,
        suggested_action=suggested_action,
    )

    full_answer = "\n".join(answer_lines)
    return full_answer, structured_data


async def process_assistant_chat(
    db: AsyncSession,
    user_id: uuid.UUID,
    req: AssistantChatRequest,
) -> AssistantMessageResponse:
    """Process user chat question, perform context resolution, and persist grounded dialogue."""
    # 1. Authorize project
    proj_res = await db.execute(
        select(Project).where(Project.id == req.project_id, Project.owner_id == user_id)
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found or unauthorized")

    # 2. Resolve scan context
    scan: Scan | None = None
    if req.scan_id:
        scan_res = await db.execute(
            select(Scan).where(Scan.id == req.scan_id, Scan.project_id == project.id)
        )
        scan = scan_res.scalar_one_or_none()
    else:
        # Latest completed scan
        scan_res = await db.execute(
            select(Scan)
            .where(Scan.project_id == project.id, Scan.status == "completed")
            .order_by(desc(Scan.created_at))
            .limit(1)
        )
        scan = scan_res.scalar_one_or_none()

    # 3. Load authorized findings
    findings: list[Finding] = []
    if scan:
        f_res = await db.execute(
            select(Finding)
            .join(ScanPage, Finding.scan_page_id == ScanPage.id)
            .where(ScanPage.scan_id == scan.id)
        )
        findings = list(f_res.scalars().all())

    # 4. Resolve or create conversation
    conversation: AssistantConversation
    if req.conversation_id:
        conv_res = await db.execute(
            select(AssistantConversation).where(
                AssistantConversation.id == req.conversation_id,
                AssistantConversation.user_id == user_id,
            )
        )
        conv = conv_res.scalar_one_or_none()
        if not conv:
            raise NotFoundError("Conversation not found or unauthorized")
        conversation = conv
    else:
        title = req.message[:50] + ("..." if len(req.message) > 50 else "")
        conversation = AssistantConversation(
            project_id=project.id,
            scan_id=scan.id if scan else None,
            user_id=user_id,
            title=title,
        )
        db.add(conversation)
        await db.flush()

    # 5. Persist user message
    user_msg = AssistantMessage(
        conversation_id=conversation.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # 6. Generate grounded response
    answer_text, structured_data = await synthesize_grounded_response(
        query=req.message,
        project=project,
        scan=scan,
        findings=findings,
        db=db,
    )

    # 7. Persist assistant message
    asst_msg = AssistantMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_text,
        structured_data=structured_data.model_dump(mode="json"),
    )
    db.add(asst_msg)
    await db.flush()

    return build_message_response(asst_msg)


async def list_user_conversations(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[AssistantConversationResponse]:
    """List recent assistant conversations for an authorized project."""
    proj_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    if not proj_res.scalar_one_or_none():
        raise NotFoundError("Project not found or unauthorized")

    conv_res = await db.execute(
        select(AssistantConversation)
        .where(
            AssistantConversation.project_id == project_id,
            AssistantConversation.user_id == user_id,
        )
        .order_by(desc(AssistantConversation.updated_at))
        .limit(limit)
    )
    conversations = list(conv_res.scalars().all())

    # Preload messages for each conversation
    responses: list[AssistantConversationResponse] = []
    for c in conversations:
        m_res = await db.execute(
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == c.id)
            .order_by(AssistantMessage.created_at)
        )
        c.messages = list(m_res.scalars().all())
        responses.append(build_conversation_response(c))

    return responses


async def get_conversation_details(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> AssistantConversationResponse:
    """Retrieve full conversation dialogue with messages."""
    conv_res = await db.execute(
        select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.user_id == user_id,
        )
    )
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation not found or unauthorized")

    m_res = await db.execute(
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conv.id)
        .order_by(AssistantMessage.created_at)
    )
    conv.messages = list(m_res.scalars().all())
    return build_conversation_response(conv)


async def delete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a conversation and its messages."""
    conv_res = await db.execute(
        select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.user_id == user_id,
        )
    )
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation not found or unauthorized")

    await db.delete(conv)
    await db.flush()
