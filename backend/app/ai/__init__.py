"""AI provider adapters, structured schemas, and error handling for AccessGuard AI."""

from app.ai.exceptions import (
    LLMAuthenticationError,
    LLMContextLimitError,
    LLMError,
    LLMRateLimitError,
    LLMSchemaValidationError,
    LLMServerUnavailableError,
)
from app.ai.factory import get_llm_provider
from app.ai.gemini_provider import GeminiLLMProvider
from app.ai.groq_provider import GroqLLMProvider
from app.ai.mock_provider import MockLLMProvider
from app.ai.provider import LLMProvider
from app.ai.schemas import (
    SAFE_ATTRIBUTES,
    FindingAnalysis,
    PatchOperation,
    RemediationProposal,
    ReviewResult,
)

__all__ = [
    "SAFE_ATTRIBUTES",
    "FindingAnalysis",
    "GeminiLLMProvider",
    "GroqLLMProvider",
    "LLMAuthenticationError",
    "LLMContextLimitError",
    "LLMError",
    "LLMProvider",
    "LLMRateLimitError",
    "LLMSchemaValidationError",
    "LLMServerUnavailableError",
    "MockLLMProvider",
    "PatchOperation",
    "RemediationProposal",
    "ReviewResult",
    "get_llm_provider",
]
