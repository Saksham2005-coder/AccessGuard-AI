"""Google Gemini LLM provider adapter using the modern google-genai SDK."""

import json
from typing import Any, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.exceptions import (
    LLMAuthenticationError,
    LLMContextLimitError,
    LLMRateLimitError,
    LLMSchemaValidationError,
    LLMServerUnavailableError,
)
from app.ai.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger("gemini_provider")

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(LLMProvider):
    """Adapter for Google Gemini models with native structured Pydantic outputs."""

    def __init__(
        self,
        api_key: str,
        default_model: str = "gemini-3.5-flash",
    ) -> None:
        if not api_key:
            raise LLMAuthenticationError(
                "GEMINI_API_KEY must be provided to instantiate GeminiLLMProvider.",
                provider="gemini",
            )
        self._api_key = api_key
        self._default_model = default_model
        self._client = genai.Client(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

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
        """Generate structured Pydantic output using Gemini native JSON schema enforcement."""
        selected_model = model or self._default_model

        # Build contents from user payload
        payload_text = json.dumps(user_payload, indent=2, default=str)
        prompt_content = f"{system_prompt}\n\nInput Payload:\n{payload_text}"

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=output_schema,
            temperature=temperature,
        )

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1.0, min=1.0, max=8.0),
            retry=retry_if_exception_type((LLMRateLimitError, LLMServerUnavailableError)),
        )
        async def _call_api() -> str:
            try:
                response = await self._client.aio.models.generate_content(
                    model=selected_model,
                    contents=prompt_content,
                    config=config,
                )
                if not response.text:
                    raise LLMSchemaValidationError(
                        "Gemini returned an empty response.",
                        provider="gemini",
                        raw_output="",
                    )
                return response.text
            except errors.ClientError as e:
                err_msg = str(e)
                code = getattr(e, "code", None)
                if code in (401, 403) or "API_KEY_INVALID" in err_msg or "unauthenticated" in err_msg.lower():
                    raise LLMAuthenticationError(
                        f"Gemini API authentication failed: {err_msg}",
                        provider="gemini",
                    ) from e
                if code == 429 or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    raise LLMRateLimitError(
                        f"Gemini rate limit exceeded: {err_msg}",
                        provider="gemini",
                        retry_after_seconds=5.0,
                    ) from e
                if "context" in err_msg.lower() or "token" in err_msg.lower():
                    raise LLMContextLimitError(
                        f"Gemini prompt exceeds token limit: {err_msg}",
                        provider="gemini",
                    ) from e
                raise LLMSchemaValidationError(
                    f"Gemini client error: {err_msg}",
                    provider="gemini",
                    raw_output=err_msg,
                ) from e
            except errors.ServerError as e:
                err_msg = str(e)
                raise LLMServerUnavailableError(
                    f"Gemini server unavailable: {err_msg}",
                    provider="gemini",
                ) from e
            except TimeoutError as e:
                raise LLMServerUnavailableError(
                    "Gemini API request timed out.",
                    provider="gemini",
                ) from e

        raw_text = await _call_api()

        try:
            return output_schema.model_validate_json(raw_text)
        except ValidationError as e:
            logger.error(
                "Gemini response failed Pydantic schema validation",
                schema=output_schema.__name__,
                error=str(e),
                raw_preview=raw_text[:200],
            )
            raise LLMSchemaValidationError(
                f"Model output failed schema validation for {output_schema.__name__}: {e}",
                provider="gemini",
                raw_output=raw_text,
            ) from e
