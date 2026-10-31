"""Factory for instantiating configured LLM provider adapters."""

from app.ai.exceptions import LLMAuthenticationError
from app.ai.mock_provider import MockLLMProvider
from app.ai.provider import LLMProvider
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("ai_factory")

_cached_provider: LLMProvider | None = None


def get_llm_provider(force_new: bool = False, provider_override: str | None = None) -> LLMProvider:
    """Return configured LLM provider instance based on application settings.

    Args:
        force_new: If True, bypass cached singleton and create fresh instance.
        provider_override: Optional override for provider type ('mock', 'gemini', 'groq').
    """
    global _cached_provider
    if _cached_provider is not None and not force_new and provider_override is None:
        return _cached_provider

    settings = get_settings()
    provider_type = (provider_override or settings.LLM_PROVIDER).lower()

    if provider_type == "mock":
        provider = MockLLMProvider()
    elif provider_type == "gemini":
        if not settings.GEMINI_API_KEY:
            raise LLMAuthenticationError(
                "GEMINI_API_KEY is not configured in backend/.env. Please configure a valid key to use Gemini.",
                provider="gemini",
            )
        from app.ai.gemini_provider import GeminiLLMProvider

        provider = GeminiLLMProvider(
            api_key=settings.GEMINI_API_KEY,
            default_model=settings.GEMINI_MODEL or "gemini-3.5-flash",
        )
    elif provider_type == "groq":
        if not settings.GROQ_API_KEY:
            raise LLMAuthenticationError(
                "GROQ_API_KEY is not configured in backend/.env. Please configure a valid key to use Groq.",
                provider="groq",
            )
        from app.ai.groq_provider import GroqLLMProvider

        provider = GroqLLMProvider(
            api_key=settings.GROQ_API_KEY,
            default_model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
        )
    else:
        logger.warning(
            "Unrecognized LLM_PROVIDER in settings; falling back to mock provider",
            provider=provider_type,
        )
        provider = MockLLMProvider()

    if provider_override is None and not force_new:
        _cached_provider = provider

    return provider
