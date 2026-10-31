"""RAG retrieval evaluation benchmark computing Recall@5, Precision@5, MRR, nDCG@5, and Hit Rate."""

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.knowledge import KnowledgeChunk
from app.db.session import get_session_maker
from app.rag.citation_validator import CitationValidator
from app.rag.retriever import HybridRetriever

logger = get_logger("evaluate_rag")


def compute_dcg(relevance_scores: list[int], k: int = 5) -> float:
    """Compute Discounted Cumulative Gain at rank k."""
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k], start=1):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def compute_ndcg(retrieved_relevance: list[int], k: int = 5) -> float:
    """Compute Normalized Discounted Cumulative Gain at rank k."""
    dcg = compute_dcg(retrieved_relevance, k)
    ideal_relevance = sorted(retrieved_relevance, reverse=True)
    idcg = compute_dcg(ideal_relevance, k)
    return (dcg / idcg) if idcg > 0.0 else 0.0


async def evaluate_retrieval_mode(
    cases: list[dict[str, Any]],
    mode: str,
    db: AsyncSession,
    retriever: HybridRetriever,
    k: int = 5,
) -> dict[str, Any]:
    """Run evaluation for a specific retrieval mode (dense, lexical, or hybrid)."""
    recalls: list[float] = []
    precisions: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    criterion_hits: list[float] = []
    source_accuracies: list[float] = []
    abstention_matches: list[float] = []

    for case in cases:
        query = case["query"]
        expected_cid = case.get("expected_criterion_id")
        should_abstain = case.get("should_abstain", False)

        evidence, _total_candidates, system_abstained = await retriever.search(
            db=db,
            query=query,
            limit=k,
            mode=mode,
        )

        abstain_by_threshold = CitationValidator.check_abstention_threshold(evidence)
        final_abstain = system_abstained or abstain_by_threshold

        if should_abstain:
            abstention_matches.append(1.0 if final_abstain else 0.0)
            continue

        if final_abstain or not evidence:
            recalls.append(0.0)
            precisions.append(0.0)
            reciprocal_ranks.append(0.0)
            ndcgs.append(0.0)
            criterion_hits.append(0.0)
            source_accuracies.append(0.0)
            continue

        # Evaluate relevance
        retrieved_cids = [item.criterion_id for item in evidence]
        relevance = [
            1 if (cid and expected_cid and cid == expected_cid) else 0 for cid in retrieved_cids
        ]

        # Criterion Hit Rate@k: at least 1 match in top k
        hit = 1.0 if any(r == 1 for r in relevance) else 0.0
        criterion_hits.append(hit)

        # Precision@k: fraction of top k that match
        precision = sum(relevance) / float(len(evidence))
        precisions.append(precision)

        # Recall@k (binary single-criterion relevance)
        recall = 1.0 if hit > 0.0 else 0.0
        recalls.append(recall)

        # MRR: reciprocal rank of first relevant match
        mrr = 0.0
        for rank_idx, rel in enumerate(relevance, start=1):
            if rel > 0:
                mrr = 1.0 / rank_idx
                break
        reciprocal_ranks.append(mrr)

        # nDCG@k
        ndcgs.append(compute_ndcg(relevance, k=k))

        # Citation Source Accuracy: verify official w3.org domain
        valid_sources = [1.0 if ("w3.org" in item.source_url.lower()) else 0.0 for item in evidence]
        source_accuracies.append(
            sum(valid_sources) / float(len(valid_sources)) if valid_sources else 0.0
        )

    def avg(lst: list[float]) -> float:
        return round(sum(lst) / len(lst), 4) if lst else 0.0

    return {
        "mode": mode,
        "sample_count": len(cases),
        "recall_at_k": avg(recalls),
        "precision_at_k": avg(precisions),
        "mrr": avg(reciprocal_ranks),
        "ndcg_at_k": avg(ndcgs),
        "criterion_hit_rate": avg(criterion_hits),
        "citation_source_accuracy": avg(source_accuracies),
        "abstention_accuracy": avg(abstention_matches),
    }


async def run_evaluation_suite(
    dataset_path: Path,
    db: AsyncSession | None = None,
    k: int = 5,
) -> dict[str, Any]:
    """Execute evaluation across Dense, Lexical, and Hybrid RRF modes."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {dataset_path}")

    cases = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    retriever = HybridRetriever()

    async def _evaluate_with_session(session: AsyncSession) -> dict[str, Any]:
        if retriever.vector_store.count() == 0:
            chunks_res = await session.execute(select(KnowledgeChunk))
            db_chunks = chunks_res.scalars().all()
            if db_chunks:
                logger.info(
                    "Syncing knowledge chunks to vector store for evaluation", count=len(db_chunks)
                )
                chunk_texts = [f"{c.section_title or ''} {c.content}" for c in db_chunks]
                vectors = retriever.embedding_service.embed_texts(chunk_texts)
                points_to_upsert = [
                    (c.id, vec, {"criterion_id": c.criterion_id, "chunk_key": c.chunk_key})
                    for c, vec in zip(db_chunks, vectors, strict=True)
                ]
                retriever.vector_store.upsert_chunks(points_to_upsert)

        dense_metrics = await evaluate_retrieval_mode(cases, "dense", session, retriever, k=k)
        lexical_metrics = await evaluate_retrieval_mode(cases, "lexical", session, retriever, k=k)
        hybrid_metrics = await evaluate_retrieval_mode(cases, "hybrid", session, retriever, k=k)

        return {
            "dataset_version": dataset_path.name,
            "total_cases": len(cases),
            "top_k": k,
            "modes": {
                "dense": dense_metrics,
                "lexical": lexical_metrics,
                "hybrid_rrf": hybrid_metrics,
            },
        }

    if db is not None:
        return await _evaluate_with_session(db)
    else:
        session_maker = get_session_maker()
        async with session_maker() as session:
            return await _evaluate_with_session(session)


def main() -> None:
    """CLI entrypoint for running RAG retrieval benchmarks."""
    parser = argparse.ArgumentParser(description="Evaluate WCAG Hybrid RAG Retrieval Quality")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).parent.parent.parent
        / "knowledge_base"
        / "evaluation"
        / "retrieval_cases.jsonl",
        help="Path to evaluation cases JSONL",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to output JSON benchmark report",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Top-K cutoff for Recall, Precision, and nDCG (default: 5)",
    )

    args = parser.parse_args()
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    results = asyncio.run(run_evaluation_suite(dataset_path=args.dataset, k=args.k))

    print("\n================== AccessGuard AI — RAG Evaluation Report ==================")
    print(
        f" Dataset: {results['dataset_version']} | Total Cases: {results['total_cases']} | Cutoff @k: {results['top_k']}"
    )
    print("-" * 76)
    print(f" {'Metric':<26} | {'Dense':<12} | {'Lexical':<12} | {'Hybrid (RRF)':<14}")
    print("-" * 76)

    m = results["modes"]
    metrics_to_show = [
        ("Criterion Hit Rate@5", "criterion_hit_rate"),
        ("Recall@5", "recall_at_k"),
        ("Precision@5", "precision_at_k"),
        ("MRR (Mean Reciprocal Rank)", "mrr"),
        ("nDCG@5", "ndcg_at_k"),
        ("Citation Source Accuracy", "citation_source_accuracy"),
        ("Abstention Accuracy", "abstention_accuracy"),
    ]

    for label, key in metrics_to_show:
        d_val = f"{m['dense'][key]:.4f}"
        l_val = f"{m['lexical'][key]:.4f}"
        h_val = f"{m['hybrid_rrf'][key]:.4f}"
        print(f" {label:<26} | {d_val:<12} | {l_val:<12} | {h_val:<14}")

    print("=" * 76 + "\n")

    if args.report_json:
        with open(args.report_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Report written to {args.report_json}")


if __name__ == "__main__":
    main()
