"""Groq LLM provider adapter using the official groq SDK with JSON-mode structured outputs."""

import json
from typing import Any, TypeVar

from groq import (
    APIConnectionError,
    AsyncGroq,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMSchemaValidationError,
    LLMServerUnavailableError,
)
from app.ai.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger("groq_provider")

T = TypeVar("T", bound=BaseModel)


class GroqLLMProvider(LLMProvider):
    """Adapter for Groq API models with JSON mode and Pydantic schema validation."""

    def __init__(
        self,
        api_key: str,
        default_model: str = "llama-3.3-70b-versatile",
    ) -> None:
        if not api_key:
            raise LLMAuthenticationError(
                "GROQ_API_KEY must be provided to instantiate GroqLLMProvider.",
                provider="groq",
            )
        self._api_key = api_key
        self._default_model = default_model
        self._client = AsyncGroq(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def default_model(self) -> str:
        return self._default_model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output using Groq JSON mode and validate with Pydantic."""
        selected_model = model or self._default_model

        # Augment system prompt with JSON schema definition to guide model formatting
        schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
        full_system_prompt = (
            f"{system_prompt}\n\n"
            f"You MUST return a valid JSON object matching this schema exactly:\n{schema_json}"
        )
        payload_text = json.dumps(user_payload, indent=2, default=str)

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1.0, min=1.0, max=8.0),
            retry=retry_if_exception_type((LLMRateLimitError, LLMServerUnavailableError)),
        )
        async def _call_api() -> str:
            try:
                response = await self._client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": f"Input Data:\n{payload_text}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )
                choice = response.choices[0] if response.choices else None
                if not choice or not choice.message.content:
                    raise LLMSchemaValidationError(
                        "Groq returned an empty completion content.",
                        provider="groq",
                        raw_output="",
                    )
                return choice.message.content
            except AuthenticationError as e:
                raise LLMAuthenticationError(
                    f"Groq API authentication failed: {e}",
                    provider="groq",
                ) from e
            except RateLimitError as e:
                raise LLMRateLimitError(
                    f"Groq rate limit exceeded: {e}",
                    provider="groq",
                    retry_after_seconds=5.0,
                ) from e
            except (InternalServerError, APIConnectionError) as e:
                raise LLMServerUnavailableError(
                    f"Groq service unavailable or network error: {e}",
                    provider="groq",
                ) from e

        raw_text = await _call_api()

        try:
            return output_schema.model_validate_json(raw_text)
        except ValidationError as e:
            logger.error(
                "Groq response failed Pydantic schema validation",
                schema=output_schema.__name__,
                error=str(e),
                raw_preview=raw_text[:200],
            )
            raise LLMSchemaValidationError(
                f"Model output failed schema validation for {output_schema.__name__}: {e}",
                provider="groq",
                raw_output=raw_text,
            ) from e
