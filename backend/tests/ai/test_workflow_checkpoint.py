"""Unit tests for LangGraph checkpoint persistence, human approval interrupt, and resume."""

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.ai.mock_provider import MockLLMProvider
from app.ai.workflow.graph import build_remediation_graph
from app.ai.workflow.state import AccessGuardGraphState


@pytest.fixture
def sample_finding_state() -> AccessGuardGraphState:
    """Fixture providing clean state for workflow checkpointing tests."""
    chunk_id = "00000000-0000-0000-0000-000000000010"
    return {
        "scan_id": "00000000-0000-0000-0000-000000000001",
        "finding_id": "00000000-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000003",
        "target_url": "https://example.com/checkout",
        "finding": {
            "axe_rule_id": "image-alt",
            "impact": "critical",
            "description": "Images must have alternate text",
            "help_url": "https://dequeuniversity.com/rules/axe/4.14/image-alt",
            "wcag_tags": ["wcag2a", "wcag111"],
            "selector": "img.hero-banner",
            "html_snippet": '<img src="banner.jpg" class="hero-banner">',
            "failure_summary": "Fix all of the following: Element does not have an alt attribute",
            "is_incomplete": False,
        },
        "retrieved_evidence": [
            {
                "chunk_id": chunk_id,
                "criterion_id": "1.1.1",
                "criterion_level": "A",
                "title": "1.1.1 Non-text Content",
                "source_title": "WCAG 2.2 Recommendation",
                "source_url": "https://www.w3.org/TR/WCAG22/#non-text-content",
                "excerpt": "All non-text content that is presented to the user has a text alternative.",
                "score": 0.95,
            }
        ],
        "evidence_sufficient": True,
        "status": "pending",
        "attempt_count": 0,
        "errors": [],
        "metadata": {},
    }


@pytest.mark.asyncio
async def test_workflow_interrupts_at_human_approval(
    sample_finding_state: AccessGuardGraphState,
) -> None:
    """Verify workflow compiles with checkpointer, generates proposal, and halts at approval gate."""
    mock_llm = MockLLMProvider()
    checkpointer = MemorySaver()
    graph = build_remediation_graph(
        provider=mock_llm,
        checkpointer=checkpointer,
        require_human_approval=True,
    )

    thread_id = "test-thread-interrupt-1"
    config = {"configurable": {"thread_id": thread_id}}

    res = await graph.ainvoke(sample_finding_state, config=config)

    # Graph halted at human_approval interrupt
    assert "__interrupt__" in res
    assert len(res["__interrupt__"]) >= 1
    interrupt_payload = res["__interrupt__"][0].value
    assert "Awaiting human approval" in interrupt_payload["message"]
    assert interrupt_payload["finding_id"] == "00000000-0000-0000-0000-000000000002"
    assert res["remediation_proposal"] is not None


@pytest.mark.asyncio
async def test_workflow_resumes_on_human_approval_to_validation(
    sample_finding_state: AccessGuardGraphState,
) -> None:
    """Verify workflow resumes from checkpoint on human approval and completes snapshot validation."""
    mock_llm = MockLLMProvider()
    checkpointer = MemorySaver()
    graph = build_remediation_graph(
        provider=mock_llm,
        checkpointer=checkpointer,
        require_human_approval=True,
    )

    thread_id = "test-thread-resume-approve"
    config = {"configurable": {"thread_id": thread_id}}

    # Initial invoke pauses at human approval
    res1 = await graph.ainvoke(sample_finding_state, config=config)
    assert "__interrupt__" in res1

    # Resume graph with approval decision
    resume_payload = {
        "decision": "approved",
        "reviewer_id": "00000000-0000-0000-0000-000000000099",
        "comments": "Patch operations verified safe and correct.",
    }
    res2 = await graph.ainvoke(Command(resume=resume_payload), config=config)

    assert res2["status"] == "validated"
    assert res2["human_decision"]["decision"] == "approved"
    assert res2["validation_result"] is not None
    assert res2["validation_result"]["passed"] is True
    assert "approval_decided_at" in res2["metadata"]
    assert "finalized_at" in res2["metadata"]


@pytest.mark.asyncio
async def test_workflow_resumes_on_rejection_without_validation(
    sample_finding_state: AccessGuardGraphState,
) -> None:
    """Verify workflow resumes on human rejection and finalizes without running snapshot validation."""
    mock_llm = MockLLMProvider()
    checkpointer = MemorySaver()
    graph = build_remediation_graph(
        provider=mock_llm,
        checkpointer=checkpointer,
        require_human_approval=True,
    )

    thread_id = "test-thread-resume-reject"
    config = {"configurable": {"thread_id": thread_id}}

    # Initial invoke pauses at human approval
    await graph.ainvoke(sample_finding_state, config=config)

    # Resume graph with rejection decision
    resume_payload = {
        "decision": "rejected",
        "reviewer_id": "00000000-0000-0000-0000-000000000099",
        "comments": "Developer prefers manual code refactoring.",
    }
    res2 = await graph.ainvoke(Command(resume=resume_payload), config=config)

    assert res2["status"] == "rejected"
    assert res2["human_decision"]["decision"] == "rejected"
    assert res2.get("validation_result") is None
    assert "approval_decided_at" in res2["metadata"]
    assert "finalized_at" in res2["metadata"]
