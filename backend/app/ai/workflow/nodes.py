"""LangGraph workflow node functions for accessibility investigation."""

import time
from typing import Any

from app.ai.factory import get_llm_provider
from app.ai.prompts import load_prompt
from app.ai.provider import LLMProvider
from app.ai.schemas import FindingAnalysis
from app.ai.workflow.state import AccessGuardGraphState
from app.core.logging import get_logger

logger = get_logger("workflow_nodes")


def scan_context_node(state: AccessGuardGraphState) -> dict[str, Any]:
    """Validate and normalize finding context for downstream investigation."""
    finding = state.get("finding") or {}
    if not finding:
        logger.warning("Empty finding provided in graph state", finding_id=state.get("finding_id"))
        return {
            "status": "manual_review_required",
            "errors": state.get("errors", []) + [{"node": "scan_context", "error": "No finding data provided"}],
        }

    is_incomplete = bool(finding.get("is_incomplete", False))
    rule_id = str(finding.get("axe_rule_id") or "unknown-rule")

    logger.info(
        "Loaded finding context into workflow state",
        finding_id=state.get("finding_id"),
        rule_id=rule_id,
        is_incomplete=is_incomplete,
    )

    updates: dict[str, Any] = {
        "status": "context_loaded",
        "attempt_count": state.get("attempt_count", 0),
        "errors": state.get("errors", []),
        "metadata": state.get("metadata", {}),
    }

    if is_incomplete:
        updates["status"] = "manual_review_required"
        updates["errors"].append({
            "node": "scan_context",
            "error": "Automated scan marked finding as incomplete; human verification required.",
        })

    return updates


async def knowledge_retrieval_node(
    state: AccessGuardGraphState,
    retriever: Any = None,
    db: Any = None,
) -> dict[str, Any]:
    """Retrieve grounded WCAG guidelines and techniques using hybrid search."""
    finding = state.get("finding", {})
    rule_id = finding.get("axe_rule_id", "")
    description = finding.get("description", "")
    wcag_tags = finding.get("wcag_tags", [])

    # If evidence is already supplied in state (e.g. from upstream fixture or caller), use it
    preloaded_evidence = state.get("retrieved_evidence")
    if preloaded_evidence:
        logger.info(
            "Using preloaded knowledge evidence",
            count=len(preloaded_evidence),
            finding_id=state.get("finding_id"),
        )
        return {
            "retrieved_evidence": preloaded_evidence,
            "evidence_sufficient": True,
            "status": "evidence_retrieved",
        }

    # If retriever and DB session are available, query RAG
    if retriever is not None and db is not None:
        query = f"{rule_id} {description} {' '.join(wcag_tags)}".strip()
        try:
            evidence_items, _total, abstain = await retriever.search(
                db=db,
                query=query,
                limit=5,
                mode="hybrid",
            )
            if abstain or not evidence_items:
                logger.info("Retriever abstained or returned empty evidence", query=query)
                return {
                    "retrieved_evidence": [],
                    "evidence_sufficient": False,
                    "status": "manual_review_required",
                    "errors": state.get("errors", []) + [{
                        "node": "knowledge_retrieval",
                        "error": "Insufficient grounding evidence retrieved; abstaining from automated proposal.",
                    }],
                }

            formatted_evidence = [
                {
                    "chunk_id": str(item.chunk_id),
                    "criterion_id": item.criterion_id,
                    "criterion_level": item.criterion_level,
                    "title": item.title,
                    "source_title": item.source_title,
                    "source_url": item.source_url,
                    "excerpt": item.excerpt,
                    "score": item.score,
                }
                for item in evidence_items
            ]

            return {
                "retrieved_evidence": formatted_evidence,
                "evidence_sufficient": True,
                "status": "evidence_retrieved",
            }
        except Exception as e:
            logger.error("Knowledge retrieval failed in graph node", error=str(e))
            return {
                "retrieved_evidence": [],
                "evidence_sufficient": False,
                "status": "manual_review_required",
                "errors": state.get("errors", []) + [{"node": "knowledge_retrieval", "error": str(e)}],
            }

    # If no retriever provided and no preloaded evidence, route to manual review
    logger.warning("No retriever service available; marking manual review", finding_id=state.get("finding_id"))
    return {
        "retrieved_evidence": [],
        "evidence_sufficient": False,
        "status": "manual_review_required",
        "errors": state.get("errors", []) + [{
            "node": "knowledge_retrieval",
            "error": "No RAG retriever configured for finding investigation.",
        }],
    }


async def finding_analysis_node(
    state: AccessGuardGraphState,
    provider: LLMProvider | None = None,
) -> dict[str, Any]:
    """Execute LLM analysis on the finding using retrieved evidence and prompt injection guards."""
    finding = state.get("finding", {})
    retrieved_evidence = state.get("retrieved_evidence", [])

    llm = provider or get_llm_provider()

    # Structure payload isolating untrusted DOM snippet
    user_payload = {
        "axe_rule_id": finding.get("axe_rule_id"),
        "impact": finding.get("impact"),
        "description": finding.get("description"),
        "help_url": finding.get("help_url"),
        "selector": finding.get("selector"),
        "html_snippet": finding.get("html_snippet"),
        "failure_summary": finding.get("failure_summary"),
        "retrieved_evidence": retrieved_evidence,
    }

    start_time = time.monotonic()
    system_prompt = load_prompt("finding_analysis_v1")

    try:
        analysis: FindingAnalysis = await llm.generate_structured(
            system_prompt=system_prompt,
            user_payload=user_payload,
            output_schema=FindingAnalysis,
        )
        duration_ms = int((time.monotonic() - start_time) * 1000)

        metadata = dict(state.get("metadata", {}))
        metadata.update({
            "analysis_provider": llm.provider_name,
            "analysis_model": llm.default_model,
            "analysis_prompt_version": "finding_analysis_v1",
            "analysis_duration_ms": duration_ms,
        })

        analysis_dict = analysis.model_dump()
        next_status = "manual_review_required" if analysis.needs_manual_review else "analysis_completed"

        return {
            "analysis": analysis_dict,
            "status": next_status,
            "metadata": metadata,
        }
    except Exception as e:
        logger.error("Finding analysis node failed", error=str(e), provider=llm.provider_name)
        return {
            "status": "manual_review_required",
            "errors": state.get("errors", []) + [{"node": "finding_analysis", "error": str(e)}],
        }


def mark_manual_review_node(state: AccessGuardGraphState) -> dict[str, Any]:
    """Explicit terminal fallback node when evidence is insufficient or manual check is needed."""
    return {
        "status": "manual_review_required",
        "metadata": {
            **state.get("metadata", {}),
            "manual_review_marked_at": time.time(),
        },
    }


def finalize_node(state: AccessGuardGraphState) -> dict[str, Any]:
    """Persist final metadata and clean terminal status for the investigation workflow."""
    current_status = state.get("status", "completed")
    errors = state.get("errors", [])

    return {
        "status": current_status,
        "metadata": {
            **state.get("metadata", {}),
            "finalized_at": time.time(),
            "has_errors": bool(errors),
        },
    }
