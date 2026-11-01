"""Qdrant vector store management and semantic candidate retrieval for WCAG RAG."""

import uuid
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("rag_vector_store")

COLLECTION_NAME = "wcag_knowledge"
VECTOR_DIMENSION = 384


@dataclass
class VectorSearchResult:
    """Standardized scored search result from Qdrant vector store."""

    chunk_id: uuid.UUID
    score: float
    payload: dict[str, Any]


class QdrantVectorStore:
    """Manages Qdrant collection lifecycle and cosine vector similarity searches."""

    def __init__(
        self,
        client: QdrantClient | None = None,
        collection_name: str = COLLECTION_NAME,
        vector_dim: int = VECTOR_DIMENSION,
    ) -> None:
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        if client is not None:
            self.client = client
        else:
            settings = get_settings()
            if (
                settings.APP_ENV == "test" and "localhost" in settings.QDRANT_URL
            ) or settings.QDRANT_URL in (":memory:", "memory"):
                # Use in-memory Qdrant client for test isolation or explicit memory mode
                self.client = QdrantClient(":memory:")
            else:
                try:
                    c = QdrantClient(url=settings.QDRANT_URL, timeout=2)
                    c.collection_exists(self.collection_name)
                    self.client = c
                except Exception as e:
                    logger.warning(
                        "External Qdrant service unreachable; falling back to local in-memory vector store",
                        url=settings.QDRANT_URL,
                        error=str(e),
                    )
                    self.client = QdrantClient(":memory:")

    def ensure_collection_exists(self) -> None:
        """Create the WCAG collection with cosine distance if it does not already exist."""
        if not self.client.collection_exists(self.collection_name):
            logger.info(
                "Creating Qdrant collection", collection=self.collection_name, dim=self.vector_dim
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_dim,
                    distance=models.Distance.COSINE,
                ),
            )

    def recreate_collection(self) -> None:
        """Delete and recreate the knowledge collection for clean reindexing."""
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self.ensure_collection_exists()

    def upsert_chunks(self, chunks: list[tuple[uuid.UUID, list[float], dict[str, Any]]]) -> int:
        """Upsert a batch of (chunk_id, embedding_vector, metadata_payload) points."""
        if not chunks:
            return 0

        self.ensure_collection_exists()
        points: list[models.PointStruct] = []
        for chunk_id, vector, payload in chunks:
            points.append(
                models.PointStruct(
                    id=str(chunk_id),
                    vector=vector,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return len(points)

    def search(
        self,
        query_vector: list[float],
        limit: int = 20,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Perform dense vector search with cosine similarity and optional metadata filters."""
        self.ensure_collection_exists()

        query_filter: models.Filter | None = None
        if filter_dict:
            must_conditions: list[models.Condition] = []
            for key, val in filter_dict.items():
                if val is not None:
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=val),
                        )
                    )
            if must_conditions:
                query_filter = models.Filter(must=must_conditions)

        res = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )

        results: list[VectorSearchResult] = []
        for point in res.points:
            try:
                c_uuid = uuid.UUID(str(point.id))
            except ValueError:
                c_uuid = uuid.uuid5(uuid.NAMESPACE_URL, str(point.id))

            results.append(
                VectorSearchResult(
                    chunk_id=c_uuid,
                    score=float(point.score),
                    payload=point.payload or {},
                )
            )

        return results

    def delete_chunk(self, chunk_id: uuid.UUID) -> None:
        """Remove a point from the vector store."""
        if self.client.collection_exists(self.collection_name):
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[str(chunk_id)]),
            )

    def count(self) -> int:
        """Return total number of points in the collection."""
        if not self.client.collection_exists(self.collection_name):
            return 0
        info = self.client.get_collection(self.collection_name)
        return info.points_count or 0


_vector_store: QdrantVectorStore | None = None


def get_vector_store(in_memory: bool = False) -> QdrantVectorStore:
    """Return singleton or isolated in-memory vector store instance."""
    global _vector_store
    if in_memory:
        return QdrantVectorStore(client=QdrantClient(":memory:"))

    if _vector_store is None:
        _vector_store = QdrantVectorStore()
    return _vector_store
