"""Unit tests for criterion-aware chunker, metadata schema, and local embeddings."""

import math

from app.rag.chunker import chunk_section, compute_content_hash
from app.rag.embeddings import EmbeddingService
from app.rag.parser import ParsedSection


def test_chunker_preserves_criterion_integrity() -> None:
    """Verify criterion-aware chunker attaches criterion ID and canonical metadata."""
    sec = ParsedSection(
        section_key="wcag22_rec_1_1_1",
        section_title="1.1.1 Non-text Content (Level A)",
        content="All non-text content that is presented to the user has a text alternative.",
        source_url="https://www.w3.org/TR/WCAG22/#non-text-content",
        content_type="normative_criterion",
        criterion_id="1.1.1",
        criterion_level="A",
        principle="Perceivable",
        guideline_id="1.1",
    )
    meta = {
        "source_key": "wcag22_recommendation",
        "title": "WCAG 2.2",
        "publisher": "W3C",
        "standard_version": "WCAG 2.2",
    }
    chunks = chunk_section(sec, meta)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.chunk_key == "wcag22_rec_1_1_1_normative"
    assert c.criterion_id == "1.1.1"
    assert c.criterion_level == "A"
    assert c.principle == "Perceivable"
    assert c.content_hash == compute_content_hash(sec.content)
    assert c.metadata["publisher"] == "W3C"
    assert c.metadata["criterion_id"] == "1.1.1"


def test_chunker_splits_long_section_with_repeated_context() -> None:
    """Verify long sections split into multiple parts while repeating context."""
    long_paragraphs = [
        f"Paragraph {i}: Detailed explanation of accessibility requirement number {i} with sufficient context."
        for i in range(25)
    ]
    long_text = "\n\n".join(long_paragraphs)
    sec = ParsedSection(
        section_key="wcag22_und_contrast",
        section_title="Understanding Contrast Minimum",
        content=long_text,
        source_url="https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum",
        content_type="understanding",
        criterion_id="1.4.3",
        criterion_level="AA",
        principle="Perceivable",
    )
    meta = {"source_key": "wcag22_und", "title": "Understanding"}
    chunks = chunk_section(sec, meta, chunk_size=300)
    assert len(chunks) > 1

    # Every sub-chunk must retain criterion_id and context
    for c in chunks:
        assert c.criterion_id == "1.4.3"
        assert c.criterion_level == "AA"
        assert "Understanding Contrast Minimum" in c.content


def test_content_hash_is_deterministic() -> None:
    """Verify compute_content_hash produces identical SHA256 regardless of surrounding whitespace."""
    t1 = "Non-text content requires an equivalent text alternative."
    t2 = "  Non-text content   requires an equivalent text alternative. \n "
    assert compute_content_hash(t1) == compute_content_hash(t2)


def test_embedding_service_dimensions_and_normalization() -> None:
    """Verify embedding service produces 384-dimensional unit vectors."""
    embedder = EmbeddingService(use_mock=True)
    assert embedder.dimension == 384

    query = "How to provide accessible name for icon buttons?"
    vec = embedder.embed_query(query)
    assert len(vec) == 384

    # Unit length check (L2 norm should be approximately 1.0)
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-3


def test_embedding_service_batch_consistency() -> None:
    """Verify embed_texts produces same vector as individual embed_query."""
    embedder = EmbeddingService(use_mock=True)
    texts = ["Image alternative text", "Color contrast ratio"]
    batch = embedder.embed_texts(texts)

    assert len(batch) == 2
    v1 = embedder.embed_query("Image alternative text")
    v2 = embedder.embed_query("Color contrast ratio")

    assert batch[0] == v1
    assert batch[1] == v2
    assert v1 != v2
