"""Integration tests for knowledge search, sources, and criterion inspection API endpoints."""

import pytest
from httpx import AsyncClient
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import QdrantVectorStore


async def create_user_and_token(
    client: AsyncClient, email: str = "rag.user@example.com", password: str = "SecurePass123!"
) -> tuple[dict, str]:
    """Helper to register and login a test user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "RAG User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = login_resp.json()
    return data["user"], data["access_token"]


@pytest.fixture
async def seeded_api_knowledge(db_session: AsyncSession) -> KnowledgeSource:
    """Seed test knowledge source and chunk."""
    source = KnowledgeSource(
        source_key="wcag22_api_test",
        title="Web Content Accessibility Guidelines 2.2",
        source_url="https://www.w3.org/TR/WCAG22/",
        publisher="W3C",
        standard_version="WCAG 2.2",
    )
    db_session.add(source)
    await db_session.flush()

    chunk = KnowledgeChunk(
        source_id=source.id,
        chunk_key="wcag22_sc_1_4_3_api",
        criterion_id="1.4.3",
        criterion_level="AA",
        section_title="1.4.3 Contrast (Minimum) (Level AA)",
        content_type="normative_criterion",
        content="The visual presentation of text and images of text has a contrast ratio of at least 4.5:1.",
        source_url="https://www.w3.org/TR/WCAG22/#contrast-minimum",
        chunk_metadata={"source_key": "wcag22_api_test"},
        content_hash="hash_143",
        embedding_model="mock",
    )
    db_session.add(chunk)
    await db_session.commit()
    return source


@pytest.mark.asyncio
async def test_list_knowledge_sources_endpoint(
    async_client: AsyncClient,
    seeded_api_knowledge: KnowledgeSource,
) -> None:
    """Verify GET /api/v1/knowledge/sources returns active official sources."""
    assert seeded_api_knowledge.id is not None
    resp = await async_client.get("/api/v1/knowledge/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    source_keys = [s["source_key"] for s in data]
    assert "wcag22_api_test" in source_keys


@pytest.mark.asyncio
async def test_search_knowledge_requires_authentication(
    async_client: AsyncClient,
) -> None:
    """Verify POST /api/v1/knowledge/search rejects unauthenticated calls."""
    resp = await async_client.post(
        "/api/v1/knowledge/search",
        json={"query": "color contrast ratio", "retrieval_mode": "hybrid"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_search_knowledge_authenticated_success(
    async_client: AsyncClient,
    seeded_api_knowledge: KnowledgeSource,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify authenticated user can perform knowledge searches and receive structured evidence."""
    assert seeded_api_knowledge.id is not None
    _, token = await create_user_and_token(async_client, "searcher@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Use in-memory Qdrant and mock embedder for test
    in_mem_qdrant = QdrantVectorStore(client=QdrantClient(":memory:"))
    test_retriever = HybridRetriever(
        vector_store=in_mem_qdrant,
        embedding_service=EmbeddingService(use_mock=True),
    )
    monkeypatch.setattr("app.api.v1.knowledge._retriever", test_retriever)

    resp = await async_client.post(
        "/api/v1/knowledge/search",
        json={"query": "contrast minimum 4.5:1", "retrieval_mode": "lexical", "limit": 3},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "contrast minimum 4.5:1"
    assert data["retrieval_mode"] == "lexical"
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["criterion_id"] == "1.4.3"


@pytest.mark.asyncio
async def test_get_criterion_details_endpoint(
    async_client: AsyncClient,
    seeded_api_knowledge: KnowledgeSource,
) -> None:
    """Verify GET /api/v1/knowledge/criteria/{id} returns criterion details."""
    assert seeded_api_knowledge.id is not None
    resp = await async_client.get("/api/v1/knowledge/criteria/1.4.3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["criterion_id"] == "1.4.3"
    assert "https://www.w3.org/TR/WCAG22/#contrast-minimum" in data[0]["source_url"]


@pytest.mark.asyncio
async def test_get_criterion_details_not_found(
    async_client: AsyncClient,
    seeded_api_knowledge: KnowledgeSource,
) -> None:
    """Verify non-existent criterion returns 404 Not Found."""
    assert seeded_api_knowledge.id is not None
    resp = await async_client.get("/api/v1/knowledge/criteria/9.9.9")
    assert resp.status_code == 404
