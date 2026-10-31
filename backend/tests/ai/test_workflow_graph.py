"""Unit tests for LangGraph investigation workflow, routing, and evidence gates."""

import pytest

from app.ai.exceptions import LLMRateLimitError
from app.ai.mock_provider import MockLLMProvider
from app.ai.workflow.graph import build_remediation_graph
from app.ai.workflow.state import AccessGuardGraphState


@pytest.fixture
def sample_finding_state() -> AccessGuardGraphState:
    """Fixture providing clean initial graph state with preloaded grounding evidence."""
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
            "selector": "img.logo",
            "html_snippet": '<img src="logo.png" class="logo">',
            "failure_summary": "Fix all of the following: Element does not have an alt attribute",
            "is_incomplete": False,
        },
        "retrieved_evidence": [
            {
                "chunk_id": "00000000-0000-0000-0000-000000000010",
                "criterion_id": "1.1.1",
                "criterion_level": "A",
                "title": "1.1.1 Non-text Content",
                "source_title": "WCAG 2.2 Recommendation",
                "source_url": "https://www.w3.org/TR/WCAG22/#non-text-content",
                "excerpt": "All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
                "score": 0.88,
            }
        ],
        "evidence_sufficient": True,
        "status": "pending",
        "attempt_count": 0,
        "errors": [],
        "metadata": {},
    }


def test_graph_compiles_successfully() -> None:
    """Verify build_remediation_graph constructs a runnable compiled graph."""
    mock_llm = MockLLMProvider()
    graph = build_remediation_graph(provider=mock_llm)
    assert graph is not None
    assert hasattr(graph, "ainvoke")


@pytest.mark.asyncio
async def test_graph_executes_investigation_with_sufficient_evidence(
    sample_finding_state: AccessGuardGraphState,
) -> None:
    """Verify workflow executes from context -> retrieval -> analysis -> finalize."""
    mock_llm = MockLLMProvider()
    graph = build_remediation_graph(provider=mock_llm)

    result = await graph.ainvoke(sample_finding_state)

    assert result["status"] == "review_passed"
    assert result["evidence_sufficient"] is True
    assert result["analysis"] is not None
    assert result["remediation_proposal"] is not None
    assert "image-alt" in result["analysis"]["summary"].lower()
    assert "1.1.1" in result["analysis"]["relevant_criterion_ids"]
    assert result["metadata"]["analysis_provider"] == "mock"
    assert "analysis_duration_ms" in result["metadata"]
    assert "finalized_at" in result["metadata"]


@pytest.mark.asyncio
async def test_graph_routes_to_manual_review_when_evidence_insufficient() -> None:
    """Verify graph abstains and routes to manual review when no grounding evidence exists."""
    mock_llm = MockLLMProvider()
    graph = build_remediation_graph(provider=mock_llm)

    state_without_evidence: AccessGuardGraphState = {
        "scan_id": "00000000-0000-0000-0000-000000000001",
        "finding_id": "00000000-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000003",
        "target_url": "https://example.com/checkout",
        "finding": {
            "axe_rule_id": "obscure-custom-rule",
            "impact": "minor",
            "description": "Obscure custom rule with no WCAG mapping",
            "html_snippet": "<div>custom</div>",
            "is_incomplete": False,
        },
        "retrieved_evidence": [],  # Empty evidence!
        "evidence_sufficient": False,
        "status": "pending",
        "attempt_count": 0,
        "errors": [],
        "metadata": {},
    }

    result = await graph.ainvoke(state_without_evidence)

    assert result["status"] == "manual_review_required"
    assert result["evidence_sufficient"] is False
    assert result.get("analysis") is None  # Analysis bypassed!
    assert len(result["errors"]) >= 1
    assert "knowledge_retrieval" in result["errors"][0]["node"]


@pytest.mark.asyncio
async def test_graph_routes_incomplete_finding_to_manual_review() -> None:
    """Verify axe findings marked incomplete are routed directly to human review without LLM call."""
    mock_llm = MockLLMProvider()
    graph = build_remediation_graph(provider=mock_llm)

    incomplete_state: AccessGuardGraphState = {
        "scan_id": "00000000-0000-0000-0000-000000000001",
        "finding_id": "00000000-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000003",
        "target_url": "https://example.com/checkout",
        "finding": {
            "axe_rule_id": "color-contrast",
            "impact": "serious",
            "description": "Element has background image; contrast could not be tested automatically",
            "html_snippet": '<span class="text-bg">Incomplete Check</span>',
            "is_incomplete": True,  # Incomplete!
        },
        "retrieved_evidence": [],
        "evidence_sufficient": False,
        "status": "pending",
        "attempt_count": 0,
        "errors": [],
        "metadata": {},
    }

    result = await graph.ainvoke(incomplete_state)

    assert result["status"] == "manual_review_required"
    assert result.get("analysis") is None
    assert len(mock_llm.call_history) == 0  # Did not invoke LLM!
    assert "scan_context" in result["errors"][0]["node"]


@pytest.mark.asyncio
async def test_graph_handles_llm_failure_gracefully(
    sample_finding_state: AccessGuardGraphState,
) -> None:
    """Verify provider error transitions state to manual review while preserving finding data."""
    mock_llm = MockLLMProvider()
    mock_llm.set_simulated_error(
        LLMRateLimitError("Simulated provider rate limit exceeded", provider="mock")
    )

    graph = build_remediation_graph(provider=mock_llm)
    result = await graph.ainvoke(sample_finding_state)

    assert result["status"] == "manual_review_required"
    assert result["finding"]["axe_rule_id"] == "image-alt"  # Original finding preserved!
    assert any("finding_analysis" in err.get("node", "") for err in result["errors"])
