"""Integration tests for knowledge ingestion idempotency, database persistence, and vector indexing."""

from pathlib import Path

import pytest
import yaml
from qdrant_client import QdrantClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import QdrantVectorStore
from scripts.ingest_knowledge import run_ingestion


@pytest.fixture
def test_knowledge_sources_file(tmp_path: Path) -> tuple[Path, Path]:
    """Create a temporary sources.yaml and pre-cached HTML fixture."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Write sample WCAG HTML to raw cache
    html_content = """<!DOCTYPE html>
    <html lang="en">
    <head><title>WCAG 2.2 Test</title></head>
    <body>
        <h2>Principle 1 - Perceivable</h2>
        <section class="sc" id="non-text-content">
            <h4>1.1.1 Non-text Content (Level A)</h4>
            <p>All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.</p>
        </section>
        <section class="sc" id="contrast-minimum">
            <h4>1.4.3 Contrast (Minimum) (Level AA)</h4>
            <p>The visual presentation of text and images of text has a contrast ratio of at least 4.5:1.</p>
        </section>
    </body>
    </html>
    """
    (raw_dir / "test_wcag.html").write_text(html_content, encoding="utf-8")

    sources_yaml = tmp_path / "sources.yaml"
    data = {
        "sources": [
            {
                "source_key": "test_wcag",
                "title": "WCAG 2.2 Test Spec",
                "source_url": "https://www.w3.org/TR/WCAG22/",
                "publisher": "W3C",
                "standard_version": "WCAG 2.2",
                "parser_type": "w3c_tr_single",
                "is_active": True,
            }
        ]
    }
    with open(sources_yaml, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    return sources_yaml, raw_dir


@pytest.mark.asyncio
async def test_ingestion_idempotency_and_vector_indexing(
    db_session: AsyncSession,
    test_knowledge_sources_file: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify first ingestion indexes records and second ingestion produces zero duplicates."""
    sources_yaml, raw_dir = test_knowledge_sources_file

    # Use in-memory Qdrant and mock embedder for fast test execution
    in_mem_qdrant = QdrantVectorStore(client=QdrantClient(":memory:"))
    monkeypatch.setattr("scripts.ingest_knowledge.get_vector_store", lambda: in_mem_qdrant)
    monkeypatch.setattr(
        "scripts.ingest_knowledge.get_embedding_service",
        lambda: EmbeddingService(use_mock=True),
    )

    # --- Run 1: Initial Ingestion ---
    stats_1 = await run_ingestion(
        sources_yaml_path=sources_yaml,
        dry_run=False,
        use_cache=True,
        db=db_session,
        raw_storage_dir=raw_dir,
    )
    assert stats_1["sources_processed"] == 1
    assert stats_1["total_sections_parsed"] == 2
    assert stats_1["chunks_persisted"] == 2
    assert stats_1["vectors_upserted"] == 2
    assert stats_1["chunks_skipped_unchanged"] == 0

    # Verify DB state
    src_count = (await db_session.execute(select(func.count(KnowledgeSource.id)))).scalar_one()
    assert src_count == 1

    chunks_count = (await db_session.execute(select(func.count(KnowledgeChunk.id)))).scalar_one()
    assert chunks_count == 2

    # Verify Qdrant points count
    assert in_mem_qdrant.count() == 2

    # Verify Qdrant point references corresponding PostgreSQL chunk
    chunks_res = await db_session.execute(select(KnowledgeChunk))
    db_chunks = chunks_res.scalars().all()
    chunk_map = {str(c.id): c for c in db_chunks}

    search_res = in_mem_qdrant.search(
        query_vector=[0.1] * 384,
        limit=5,
    )
    assert len(search_res) == 2
    for item in search_res:
        assert str(item.chunk_id) in chunk_map
        db_chunk = chunk_map[str(item.chunk_id)]
        assert item.payload["criterion_id"] == db_chunk.criterion_id

    # --- Run 2: Second Ingestion (Idempotency Check) ---
    stats_2 = await run_ingestion(
        sources_yaml_path=sources_yaml,
        dry_run=False,
        use_cache=True,
        db=db_session,
        raw_storage_dir=raw_dir,
    )
    assert stats_2["sources_processed"] == 1
    assert stats_2["chunks_persisted"] == 0
    assert stats_2["chunks_skipped_unchanged"] == 2
    assert stats_2["vectors_upserted"] == 0

    # Assert no duplicate records in PostgreSQL or Qdrant
    assert (await db_session.execute(select(func.count(KnowledgeSource.id)))).scalar_one() == 1
    assert (await db_session.execute(select(func.count(KnowledgeChunk.id)))).scalar_one() == 2
    assert in_mem_qdrant.count() == 2


@pytest.mark.asyncio
async def test_ingestion_dry_run_leaves_db_untouched(
    db_session: AsyncSession,
    test_knowledge_sources_file: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify --dry-run parses documents without committing any rows or vectors."""
    sources_yaml, raw_dir = test_knowledge_sources_file
    in_mem_qdrant = QdrantVectorStore(client=QdrantClient(":memory:"))
    monkeypatch.setattr("scripts.ingest_knowledge.get_vector_store", lambda: in_mem_qdrant)
    monkeypatch.setattr(
        "scripts.ingest_knowledge.get_embedding_service",
        lambda: EmbeddingService(use_mock=True),
    )

    stats = await run_ingestion(
        sources_yaml_path=sources_yaml,
        dry_run=True,
        use_cache=True,
        db=db_session,
        raw_storage_dir=raw_dir,
    )
    assert stats["dry_run"] is True
    assert stats["total_sections_parsed"] == 2
    assert stats["chunks_persisted"] == 0
    assert stats["vectors_upserted"] == 0

    assert (await db_session.execute(select(func.count(KnowledgeSource.id)))).scalar_one() == 0
    assert (await db_session.execute(select(func.count(KnowledgeChunk.id)))).scalar_one() == 0
    assert in_mem_qdrant.count() == 0
