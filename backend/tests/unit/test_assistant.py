"""Unit tests for Conversational Accessibility Assistant.

Phase 19 Feature 8: Grounded reasoning, tenant authorization, WCAG citations,
and conversation persistence.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import NotFoundError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.schemas.assistant import AssistantChatRequest
from app.services import assistant_service
from app.services.assistant_service import synthesize_grounded_response


@pytest.mark.asyncio
async def test_assistant_chat_blocks_unauthorized_project() -> None:
    """Verify cross-tenant project context access is blocked with NotFoundError."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    foreign_project_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    req = AssistantChatRequest(
        project_id=foreign_project_id,
        message="What are my top issues?",
    )

    with pytest.raises(NotFoundError) as exc_info:
        await assistant_service.process_assistant_chat(
            db=db,
            user_id=user_id,
            req=req,
        )

    assert "unauthorized" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_synthesize_grounded_response_prioritizes_critical_barriers() -> None:
    """Verify asking 'what to fix first' grounds answer in critical findings and WCAG criteria."""
    project = Project(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        name="Portal Pro",
        base_domain="portal.example.com",
    )
    scan = Scan(
        id=uuid.uuid4(),
        project_id=project.id,
        target_url="https://portal.example.com/login",
        status="completed",
    )
    scan_page_id = uuid.uuid4()
    findings = [
        Finding(
            id=uuid.uuid4(),
            scan_page_id=scan_page_id,
            axe_rule_id="button-name",
            impact="critical",
            selector="button.icon-only",
            description="Button element has no accessible name",
        ),
        Finding(
            id=uuid.uuid4(),
            scan_page_id=scan_page_id,
            axe_rule_id="color-contrast",
            impact="serious",
            selector="span.subtext",
            description="Insufficient text contrast ratio 3.2:1",
        ),
        Finding(
            id=uuid.uuid4(),
            scan_page_id=scan_page_id,
            axe_rule_id="image-alt",
            impact="minor",
            selector="img.avatar",
            description="Avatar missing alt attribute",
        ),
    ]

    db = AsyncMock()
    mock_k = MagicMock()
    mock_k.scalars().all.return_value = []
    db.execute.return_value = mock_k

    answer, structured_data = await synthesize_grounded_response(
        query="What should I fix first?",
        project=project,
        scan=scan,
        findings=findings,
        db=db,
    )

    assert "Recommended Remediation Priority" in answer
    assert "button-name" in answer
    assert "critical" in answer.lower()
    assert len(structured_data.evidence_findings) >= 1
    assert structured_data.evidence_findings[0].rule_id == "button-name"
    assert any(c.criterion_id == "4.1.2" for c in structured_data.wcag_citations)
    assert len(structured_data.observed_facts) >= 1
    assert "3 total recorded violations" in structured_data.observed_facts[0]


@pytest.mark.asyncio
async def test_synthesize_grounded_response_contrast_query() -> None:
    """Verify contrast question grounds answer in WCAG 1.4.3 and contrast findings."""
    project = Project(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        name="Store App",
        base_domain="store.example.com",
    )
    scan = Scan(
        id=uuid.uuid4(),
        project_id=project.id,
        target_url="https://store.example.com",
        status="completed",
    )
    scan_page_id = uuid.uuid4()
    findings = [
        Finding(
            id=uuid.uuid4(),
            scan_page_id=scan_page_id,
            axe_rule_id="color-contrast",
            impact="serious",
            selector="div.hero p.lead",
            description="Elements must have sufficient color contrast",
        ),
    ]

    db = AsyncMock()
    mock_k = MagicMock()
    mock_k.scalars().all.return_value = []
    db.execute.return_value = mock_k

    answer, structured_data = await synthesize_grounded_response(
        query="Can you explain the contrast issues?",
        project=project,
        scan=scan,
        findings=findings,
        db=db,
    )

    assert "Color Contrast Evaluation" in answer
    assert "4.5:1" in answer
    assert any(c.criterion_id == "1.4.3" for c in structured_data.wcag_citations)
    assert len(structured_data.evidence_findings) == 1
    assert structured_data.evidence_findings[0].rule_id == "color-contrast"
