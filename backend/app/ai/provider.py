"""Abstract Protocol definition for AI model providers."""

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    """Protocol defining standard contract for structured generation across LLM providers."""

    @property
    def provider_name(self) -> str:
        """Return identifier string for this provider (e.g. 'gemini', 'groq', 'mock')."""
        ...

    @property
    def default_model(self) -> str:
        """Return default model identifier string."""
        ...

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate validated Pydantic model from system prompt and user payload.

        Args:
            system_prompt: System-level instruction specifying role and constraints.
            user_payload: Untrusted data payload (finding details, DOM snippets, evidence).
            output_schema: Expected Pydantic model class to validate and return.
            model: Optional model identifier override.
            temperature: Sampling temperature (0.0 for deterministic structured reasoning).

        Returns:
            An instance of output_schema.

        Raises:
            LLMAuthenticationError: When API key is missing or invalid.
            LLMRateLimitError: When provider rate limit is exceeded.
            LLMServerUnavailableError: When provider is temporarily down.
            LLMSchemaValidationError: When response cannot be parsed into output_schema.
            LLMContextLimitError: When input exceeds maximum context window.
        """
        ...
