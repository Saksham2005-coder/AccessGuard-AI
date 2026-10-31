"""Categorized LLM provider exceptions for error handling, retries, and reporting."""


class LLMError(Exception):
    """Base exception for all AI/LLM provider interactions."""

    def __init__(self, message: str, provider: str = "unknown", retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.retryable = retryable


class LLMAuthenticationError(LLMError):
    """Raised when provider API key is missing, invalid, or expired (non-retryable)."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(message, provider=provider, retryable=False)


class LLMRateLimitError(LLMError):
    """Raised when provider returns HTTP 429 or quota exhaustion (retryable with backoff)."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message, provider=provider, retryable=True)
        self.retry_after_seconds = retry_after_seconds


class LLMServerUnavailableError(LLMError):
    """Raised when provider returns HTTP 500, 502, 503, or connection timeouts (retryable)."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(message, provider=provider, retryable=True)


class LLMSchemaValidationError(LLMError):
    """Raised when model output does not conform to the expected Pydantic schema."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        raw_output: str | None = None,
    ) -> None:
        super().__init__(message, provider=provider, retryable=False)
        self.raw_output = raw_output


class LLMContextLimitError(LLMError):
    """Raised when prompt token count exceeds the model's context window limit."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(message, provider=provider, retryable=False)
