"""Unit and integration tests for evidence-grounded remediation proposal generation and review."""

from typing import Any

import pytest

from app.ai.mock_provider import MockLLMProvider
from app.ai.schemas import PatchOperation, RemediationProposal
from app.ai.workflow.graph import build_remediation_graph
from app.ai.workflow.nodes import review_node
from app.ai.workflow.state import AccessGuardGraphState


@pytest.fixture
def sample_grounded_state() -> AccessGuardGraphState:
    """Fixture providing clean initial state with grounded WCAG evidence."""
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
            "selector": "img.logo",
            "html_snippet": '<img src="logo.png" class="logo">',
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
                "excerpt": "All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
                "score": 0.92,
            }
        ],
        "evidence_sufficient": True,
        "status": "pending",
        "attempt_count": 0,
        "errors": [],
        "metadata": {},
    }


@pytest.mark.asyncio
async def test_end_to_end_remediation_workflow_success(
    sample_grounded_state: AccessGuardGraphState,
) -> None:
    """Verify full graph execution produces a verified, evidence-grounded remediation proposal."""
    mock_llm = MockLLMProvider()
    graph = build_remediation_graph(provider=mock_llm)

    result = await graph.ainvoke(sample_grounded_state)

    assert result["status"] == "review_passed"
    assert result["remediation_proposal"] is not None
    proposal = result["remediation_proposal"]
    assert "alt" in proposal["recommendation"].lower()
    assert len(proposal["patch_operations"]) >= 1
    assert proposal["patch_operations"][0]["attribute"] == "alt"
    assert "00000000-0000-0000-0000-000000000010" in proposal["evidence_chunk_ids"]

    # Verify review result
    assert result["review_result"] is not None
    assert result["review_result"]["accepted_for_human_review"] is True
    assert "citation_grounding" in result["review_result"]["policy_checks_passed"]
    assert "safe_patch_policy" in result["review_result"]["policy_checks_passed"]

    # Verify audit metadata
    assert result["metadata"]["remediation_provider"] == "mock"
    assert "remediation_duration_ms" in result["metadata"]


def test_review_node_rejects_hallucinated_citations() -> None:
    """Verify review_node rejects proposals citing evidence chunks not in retrieved_evidence."""
    state: AccessGuardGraphState = {
        "retrieved_evidence": [
            {"chunk_id": "00000000-0000-0000-0000-000000000001", "criterion_id": "1.1.1"}
        ],
        "remediation_proposal": {
            "problem": "Missing alt attribute",
            "recommendation": "Add alt='logo'",
            "patch_format": "dom_operations",
            "patch_operations": [
                {
                    "operation": "set_attribute",
                    "selector": "img",
                    "attribute": "alt",
                    "value": "logo",
                }
            ],
            "expected_effect": "Screen reader announces logo",
            "manual_checks": ["Inspect image"],
            "evidence_chunk_ids": ["99999999-9999-9999-9999-999999999999"],  # Hallucinated ID!
        },
    }

    review = review_node(state)
    assert review["status"] == "review_rejected"
    assert review["review_result"]["accepted_for_human_review"] is False
    assert review["review_result"]["evidence_complete"] is False
    assert "citation_grounding" in review["review_result"]["policy_checks_failed"]
    assert any(
        "ungrounded evidence chunks" in r for r in review["review_result"]["rejection_reasons"]
    )


def test_review_node_rejects_unsafe_attributes_and_script_schemes() -> None:
    """Verify review_node rejects disallowed DOM attributes and script schemes."""
    state: AccessGuardGraphState = {
        "retrieved_evidence": [
            {"chunk_id": "00000000-0000-0000-0000-000000000001", "criterion_id": "1.1.1"}
        ],
        "remediation_proposal": {
            "problem": "Barrier on button",
            "recommendation": "Add inline script",
            "patch_format": "dom_operations",
            "patch_operations": [
                {
                    "operation": "set_attribute",
                    "selector": "button",
                    "attribute": "onclick",
                    "value": "alert(1)",
                },
                {
                    "operation": "set_attribute",
                    "selector": "a",
                    "attribute": "aria-label",
                    "value": "javascript:void(0)",
                },
            ],
            "expected_effect": "None",
            "manual_checks": [],
            "evidence_chunk_ids": ["00000000-0000-0000-0000-000000000001"],
        },
    }

    review = review_node(state)
    assert review["status"] == "review_rejected"
    assert review["review_result"]["accepted_for_human_review"] is False
    assert "safe_patch_policy" in review["review_result"]["policy_checks_failed"]


class TwoAttemptMockProvider(MockLLMProvider):
    """Mock provider that generates an ungrounded proposal on attempt 1 and a valid one on attempt 2."""

    def __init__(self, valid_chunk_id: str) -> None:
        super().__init__()
        self.valid_chunk_id = valid_chunk_id
        self.call_count = 0

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: type[Any],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> Any:
        if output_schema == RemediationProposal:
            self.call_count += 1
            if self.call_count == 1:
                # Attempt 1: ungrounded citation to trigger review rejection
                return RemediationProposal(
                    problem="Missing image text barrier",
                    recommendation="Add descriptive alternative text",
                    patch_format="dom_operations",
                    patch_operations=[
                        PatchOperation(
                            operation="set_attribute",
                            selector="img.logo",
                            attribute="alt",
                            value="Company Logo",
                        )
                    ],
                    expected_effect="Screen reader announces logo",
                    manual_checks=["Verify image alt"],
                    evidence_chunk_ids=["00000000-0000-0000-0000-000000000099"],  # Hallucinated!
                )
            # Attempt 2: valid grounded citation
            return RemediationProposal(
                problem="Missing image text barrier",
                recommendation="Add descriptive alternative text",
                patch_format="dom_operations",
                patch_operations=[
                    PatchOperation(
                        operation="set_attribute",
                        selector="img.logo",
                        attribute="alt",
                        value="Company Logo",
                    )
                ],
                expected_effect="Screen reader announces logo",
                manual_checks=["Verify image alt"],
                evidence_chunk_ids=[self.valid_chunk_id],  # Correct chunk!
            )
        return await super().generate_structured(
            system_prompt=system_prompt,
            user_payload=user_payload,
            output_schema=output_schema,
            model=model,
            temperature=temperature,
        )


@pytest.mark.asyncio
async def test_bounded_regeneration_recovers_on_second_attempt(
    sample_grounded_state: AccessGuardGraphState,
) -> None:
    """Verify graph executes bounded regeneration once and passes when proposal is corrected."""
    chunk_id = "00000000-0000-0000-0000-000000000010"
    two_attempt_provider = TwoAttemptMockProvider(valid_chunk_id=chunk_id)

    graph = build_remediation_graph(provider=two_attempt_provider)
    result = await graph.ainvoke(sample_grounded_state)

    assert result["status"] == "review_passed"
    assert two_attempt_provider.call_count == 2  # Exactly 2 attempts!
    assert result["attempt_count"] == 2
    assert result["review_result"]["accepted_for_human_review"] is True


class PersistentFailingMockProvider(MockLLMProvider):
    """Mock provider that always produces ungrounded citations."""

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: type[Any],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> Any:
        if output_schema == RemediationProposal:
            return RemediationProposal(
                problem="Persistent barrier",
                recommendation="Persistent recommendation",
                patch_format="dom_operations",
                patch_operations=[
                    PatchOperation(
                        operation="set_attribute",
                        selector="img.logo",
                        attribute="alt",
                        value="Logo",
                    )
                ],
                expected_effect="Announced",
                manual_checks=[],
                evidence_chunk_ids=["00000000-0000-0000-0000-000000000099"],  # Always hallucinated!
            )
        return await super().generate_structured(
            system_prompt=system_prompt,
            user_payload=user_payload,
            output_schema=output_schema,
            model=model,
            temperature=temperature,
        )


@pytest.mark.asyncio
async def test_bounded_regeneration_escalates_to_manual_review_after_max_attempts(
    sample_grounded_state: AccessGuardGraphState,
) -> None:
    """Verify graph stops after 1 retry (2 total attempts) and marks manual review required."""
    failing_provider = PersistentFailingMockProvider()
    graph = build_remediation_graph(provider=failing_provider)

    result = await graph.ainvoke(sample_grounded_state)

    assert result["status"] == "manual_review_required"
    assert result["attempt_count"] == 2
    assert result["review_result"]["accepted_for_human_review"] is False
