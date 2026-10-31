"""StateGraph construction and conditional routing for AccessGuard AI."""

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.ai.provider import LLMProvider
from app.ai.workflow.nodes import (
    finalize_node,
    finding_analysis_node,
    human_approval_node,
    knowledge_retrieval_node,
    mark_manual_review_node,
    remediation_proposal_node,
    review_node,
    scan_context_node,
    snapshot_validation_node,
)
from app.ai.workflow.state import AccessGuardGraphState


def route_after_scan_context(
    state: AccessGuardGraphState,
) -> Literal["mark_manual_review", "knowledge_retrieval"]:
    """Route to manual review if finding is incomplete or invalid; else proceed to RAG."""
    if state.get("status") == "manual_review_required":
        return "mark_manual_review"
    return "knowledge_retrieval"


def route_after_knowledge_retrieval(
    state: AccessGuardGraphState,
) -> Literal["mark_manual_review", "finding_analysis"]:
    """Route to manual review if grounding evidence is absent; else proceed to analysis."""
    if not state.get("evidence_sufficient", False) or state.get("status") == "manual_review_required":
        return "mark_manual_review"
    return "finding_analysis"


def route_after_finding_analysis(
    state: AccessGuardGraphState,
) -> Literal["mark_manual_review", "remediation_proposal"]:
    """Route to manual review if analysis requires human verification; else generate remediation."""
    if state.get("status") == "manual_review_required":
        return "mark_manual_review"
    return "remediation_proposal"


def route_after_remediation_proposal(
    state: AccessGuardGraphState,
) -> Literal["mark_manual_review", "review"]:
    """Route to manual review if proposal failed; else proceed to deterministic review."""
    if state.get("status") == "manual_review_required":
        return "mark_manual_review"
    return "review"


def route_after_human_approval(
    state: AccessGuardGraphState,
) -> Literal["snapshot_validation", "finalize"]:
    """Route to snapshot validation on approval, or finalize directly on rejection."""
    if state.get("status") == "approved":
        return "snapshot_validation"
    return "finalize"


def build_remediation_graph(
    *,
    provider: LLMProvider | None = None,
    retriever: Any = None,
    validator: Any = None,
    db: Any = None,
    checkpointer: Any = None,
    require_human_approval: bool = False,
) -> Any:
    """Construct and compile the typed LangGraph investigation workflow."""
    workflow = StateGraph(AccessGuardGraphState)

    # 1. Define nodes with injected dependencies
    workflow.add_node("scan_context", scan_context_node)

    async def _retrieval_step(state: AccessGuardGraphState) -> dict[str, Any]:
        return await knowledge_retrieval_node(state, retriever=retriever, db=db)

    workflow.add_node("knowledge_retrieval", _retrieval_step)

    async def _analysis_step(state: AccessGuardGraphState) -> dict[str, Any]:
        return await finding_analysis_node(state, provider=provider)

    workflow.add_node("finding_analysis", _analysis_step)

    async def _remediation_step(state: AccessGuardGraphState) -> dict[str, Any]:
        return await remediation_proposal_node(state, provider=provider)

    workflow.add_node("remediation_proposal", _remediation_step)
    workflow.add_node("review", review_node)
    workflow.add_node("mark_manual_review", mark_manual_review_node)

    if require_human_approval:
        workflow.add_node("human_approval", human_approval_node)

        async def _validation_step(state: AccessGuardGraphState) -> dict[str, Any]:
            return await snapshot_validation_node(state, validator=validator)

        workflow.add_node("snapshot_validation", _validation_step)

    workflow.add_node("finalize", finalize_node)

    # 2. Add edges and conditional routing
    workflow.add_edge(START, "scan_context")

    workflow.add_conditional_edges(
        "scan_context",
        route_after_scan_context,
        {
            "mark_manual_review": "mark_manual_review",
            "knowledge_retrieval": "knowledge_retrieval",
        },
    )

    workflow.add_conditional_edges(
        "knowledge_retrieval",
        route_after_knowledge_retrieval,
        {
            "mark_manual_review": "mark_manual_review",
            "finding_analysis": "finding_analysis",
        },
    )

    workflow.add_conditional_edges(
        "finding_analysis",
        route_after_finding_analysis,
        {
            "mark_manual_review": "mark_manual_review",
            "remediation_proposal": "remediation_proposal",
        },
    )

    workflow.add_conditional_edges(
        "remediation_proposal",
        route_after_remediation_proposal,
        {
            "mark_manual_review": "mark_manual_review",
            "review": "review",
        },
    )

    def route_after_review(
        state: AccessGuardGraphState,
    ) -> Literal["human_approval", "finalize", "remediation_proposal", "mark_manual_review"]:
        if state.get("status") == "review_passed":
            return "human_approval" if require_human_approval else "finalize"
        if state.get("attempt_count", 0) <= 1:
            return "remediation_proposal"
        return "mark_manual_review"

    review_destinations = {
        "remediation_proposal": "remediation_proposal",
        "mark_manual_review": "mark_manual_review",
    }
    if require_human_approval:
        review_destinations["human_approval"] = "human_approval"
    else:
        review_destinations["finalize"] = "finalize"

    workflow.add_conditional_edges(
        "review",
        route_after_review,
        review_destinations,
    )

    if require_human_approval:
        workflow.add_conditional_edges(
            "human_approval",
            route_after_human_approval,
            {
                "snapshot_validation": "snapshot_validation",
                "finalize": "finalize",
            },
        )
        workflow.add_edge("snapshot_validation", "finalize")

    workflow.add_edge("mark_manual_review", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile(checkpointer=checkpointer)
