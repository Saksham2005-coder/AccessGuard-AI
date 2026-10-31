"""Local Sentence Transformers embedding service for WCAG knowledge retrieval."""

import hashlib
import math
from typing import Any

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("rag_embeddings")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


class EmbeddingService:
    """Produces normalized local dense vector embeddings for documents and queries."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL, use_mock: bool = False) -> None:
        self.model_name = model_name
        self.dimension = EMBEDDING_DIMENSION
        self.use_mock = use_mock
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None and not self.use_mock:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading local SentenceTransformer model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(
                    "Failed to load SentenceTransformer weights, falling back to deterministic vectors",
                    error=str(e),
                )
                self.use_mock = True
        return self._model

    def _deterministic_mock_vector(self, text: str) -> list[float]:
        """Generate a deterministic 384-dimensional unit vector from text hash for tests/fallbacks."""
        # Seed from sha256
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec: list[float] = []
        for i in range(self.dimension):
            byte_val = h[i % len(h)]
            # Pseudo-random float between -1.0 and 1.0 based on byte and index
            val = ((byte_val ^ (i & 0xFF)) / 128.0) - 1.0
            vec.append(val)

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute normalized vector embeddings for a list of document strings."""
        if not texts:
            return []

        if self.use_mock:
            return [self._deterministic_mock_vector(t) for t in texts]

        model = self._get_model()
        if self.use_mock or model is None:
            return [self._deterministic_mock_vector(t) for t in texts]

        try:
            embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error(
                "Embedding generation failed, falling back to deterministic vectors", error=str(e)
            )
            return [self._deterministic_mock_vector(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        """Compute normalized vector embedding for a single query string."""
        results = self.embed_texts([query])
        return results[0]


_embedding_service: EmbeddingService | None = None


def get_embedding_service(force_mock: bool | None = None) -> EmbeddingService:
    """Return singleton embedding service instance."""
    global _embedding_service
    settings = get_settings()

    should_mock = (
        force_mock
        if force_mock is not None
        else (settings.APP_ENV == "test" and settings.LLM_PROVIDER == "mock")
    )
    if _embedding_service is None or (
        _embedding_service.use_mock != should_mock and force_mock is not None
    ):
        _embedding_service = EmbeddingService(
            model_name=DEFAULT_EMBEDDING_MODEL,
            use_mock=should_mock,
        )
    return _embedding_service
