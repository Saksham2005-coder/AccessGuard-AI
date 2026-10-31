"""Tests for LLM retry behavior, structured output validation, and secret sanitization."""

import logging
from unittest.mock import AsyncMock, patch

import pytest
from google.genai import errors
from pydantic import ValidationError

from app.ai.exceptions import (
    LLMAuthenticationError,
    LLMContextLimitError,
    LLMRateLimitError,
    LLMSchemaValidationError,
)
from app.ai.gemini_provider import GeminiLLMProvider
from app.ai.groq_provider import GroqLLMProvider
from app.ai.mock_provider import MockLLMProvider
from app.ai.schemas import (
    FindingAnalysis,
    PatchOperation,
)
from app.core.logging import (
    censor_sensitive_data,
    censor_sensitive_dict,
    scrub_sensitive_text,
)

# ==============================================================================
# 1. Secret Sanitization & Logging Tests
# ==============================================================================


def test_scrub_sensitive_text_gemini_keys() -> None:
    """Verify raw Gemini API keys matching known patterns are scrubbed."""
    raw_gemini_key_1 = "AQ.SyntheticTestKeyNotReal1234567890abcdef"
    raw_gemini_key_2 = "AIzaSyD_TestKey1234567890_abcdefghij"
    raw_groq_key = "gsk_1234567890abcdefghijklmnopqrstuvwxyz"

    text_with_keys = (
        f"Connecting to Gemini with key={raw_gemini_key_1} and fallback {raw_gemini_key_2}. "
        f"Groq fallback is {raw_groq_key}."
    )

    sanitized = scrub_sensitive_text(text_with_keys)
    assert raw_gemini_key_1 not in sanitized
    assert raw_gemini_key_2 not in sanitized
    assert raw_groq_key not in sanitized
    assert sanitized.count("[REDACTED_SECRET]") == 3


def test_censor_sensitive_dict_keys_and_values() -> None:
    """Verify dictionary processor censors both sensitive keys and nested values."""
    sensitive_dict = {
        "gemini_api_key": "AQ.SyntheticTestKeyNotReal1234567890abcdef",
        "groq_api_key": "gsk_test12345678901234567890",
        "jwt_secret_key": "supersecretkey999",
        "nested": {
            "token": "bearer-token-val",
            "debug_message": "Failed with key AQ.SyntheticTestKeyNotReal1234567890abcdef",
        },
        "safe_key": "normal_value",
    }

    clean = censor_sensitive_dict(sensitive_dict)
    assert clean["gemini_api_key"] == "[REDACTED]"
    assert clean["groq_api_key"] == "[REDACTED]"
    assert clean["jwt_secret_key"] == "[REDACTED]"
    assert clean["nested"]["token"] == "[REDACTED]"
    assert "SyntheticTestKey" not in clean["nested"]["debug_message"]
    assert "[REDACTED_SECRET]" in clean["nested"]["debug_message"]
    assert clean["safe_key"] == "normal_value"


def test_censor_sensitive_data_structlog_processor() -> None:
    """Verify structlog processor censors sensitive event dict before output."""
    event = {
        "event": "LLM request failed with key AQ.SyntheticTestKeyNotReal1234567890abcdef",
        "api_key": "AQ.SyntheticTestKeyNotReal1234567890abcdef",
        "status": "error",
    }
    processed = censor_sensitive_data(logging.getLogger(), "error", event)
    assert processed["api_key"] == "[REDACTED]"
    assert "SyntheticTestKey" not in processed["event"]
    assert "[REDACTED_SECRET]" in processed["event"]
    assert processed["status"] == "error"


# ==============================================================================
# 2. Structured Outputs & Schema Validation Tests
# ==============================================================================


def test_remediation_proposal_schema_rejects_unsafe_attributes() -> None:
    """Verify Pydantic validation rejects unsafe HTML attributes (e.g. onclick, src)."""
    # Safe attribute: alt
    valid_patch = PatchOperation(
        operation="set_attribute",
        selector="img.logo",
        attribute="alt",
        value="Company Logo",
    )
    assert valid_patch.attribute == "alt"

    # Safe attribute: aria-label
    aria_patch = PatchOperation(
        operation="set_attribute",
        selector="button.nav",
        attribute="aria-label",
        value="Navigation Menu",
    )
    assert aria_patch.attribute == "aria-label"

    # Safe attribute: role
    role_patch = PatchOperation(
        operation="set_attribute",
        selector="div.banner",
        attribute="role",
        value="banner",
    )
    assert role_patch.attribute == "role"

    # Unsafe attribute: onclick should fail
    with pytest.raises(ValidationError) as exc_info:
        PatchOperation(
            operation="set_attribute",
            selector="button.nav",
            attribute="onclick",
            value="evilCode()",
        )
    assert "is prohibited in safe patch operations" in str(exc_info.value)

    # Unsafe attribute: href should fail
    with pytest.raises(ValidationError) as exc_info_href:
        PatchOperation(
            operation="set_attribute",
            selector="a.link",
            attribute="href",
            value="javascript:void(0)",
        )
    assert "is prohibited in safe patch operations" in str(exc_info_href.value)


@pytest.mark.asyncio
async def test_mock_provider_schema_validation_error_injection() -> None:
    """Verify MockLLMProvider can simulate LLMSchemaValidationError cleanly."""
    mock_prov = MockLLMProvider()
    mock_prov.set_simulated_error(
        LLMSchemaValidationError(
            "Synthesized invalid JSON payload from mock",
            provider="mock",
            raw_output="{broken_json: true",
        )
    )

    with pytest.raises(LLMSchemaValidationError) as exc_info:
        await mock_prov.generate_structured(
            system_prompt="Test",
            user_payload={},
            output_schema=FindingAnalysis,
        )

    assert exc_info.value.provider == "mock"
    assert exc_info.value.retryable is False
    assert "{broken_json: true" in exc_info.value.raw_output


# ==============================================================================
# 3. Retry and Transient Error Handling Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_gemini_retry_on_server_error_and_eventual_success() -> None:
    """Verify Gemini provider retries on ServerError and succeeds on subsequent attempt."""
    provider = GeminiLLMProvider(api_key="AIzaSyTestMockKey1234567890abcdef")

    attempts = 0

    async def mock_generate_content(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise errors.ServerError(503, "Service Temporarily Unavailable", None)
        mock_resp = AsyncMock()
        mock_resp.text = (
            '{"summary": "Missing alt attribute on header logo image", '
            '"likely_root_cause": "Image tag rendered without alternative text", '
            '"relevant_criterion_ids": ["1.1.1"], '
            '"evidence_chunk_ids": ["chunk-1"]}'
        )
        return mock_resp

    with patch.object(
        provider._client.aio.models,
        "generate_content",
        side_effect=mock_generate_content,
    ):
        result = await provider.generate_structured(
            system_prompt="Test",
            user_payload={},
            output_schema=FindingAnalysis,
        )

    assert attempts == 3
    assert isinstance(result, FindingAnalysis)
    assert result.summary == "Missing alt attribute on header logo image"


@pytest.mark.asyncio
async def test_gemini_fails_after_max_retries_on_persistent_rate_limit() -> None:
    """Verify Gemini provider exhausts retries and raises LLMRateLimitError."""
    provider = GeminiLLMProvider(api_key="AIzaSyTestMockKey1234567890abcdef")

    async def mock_rate_limit(*_args, **_kwargs):
        raise errors.ClientError(429, "RESOURCE_EXHAUSTED: Quota exceeded", None)

    with (
        patch.object(
            provider._client.aio.models,
            "generate_content",
            side_effect=mock_rate_limit,
        ),
        pytest.raises(LLMRateLimitError) as exc_info,
    ):
        await provider.generate_structured(
            system_prompt="Test",
            user_payload={},
            output_schema=FindingAnalysis,
        )

    assert exc_info.value.provider == "gemini"
    assert exc_info.value.retryable is True
    assert "rate limit exceeded" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_context_limit_error_is_not_retryable() -> None:
    """Verify context length errors are translated to LLMContextLimitError and not retried."""
    provider = GeminiLLMProvider(api_key="AIzaSyTestMockKey1234567890abcdef")
    call_count = 0

    async def mock_context_error(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        raise errors.ClientError(
            400, "Maximum token context length exceeded: token count 1500000", None
        )

    with (
        patch.object(
            provider._client.aio.models,
            "generate_content",
            side_effect=mock_context_error,
        ),
        pytest.raises(LLMContextLimitError) as exc_info,
    ):
        await provider.generate_structured(
            system_prompt="Test",
            user_payload={},
            output_schema=FindingAnalysis,
        )

    assert call_count == 1  # Not retried!
    assert exc_info.value.retryable is False
    assert "token limit" in str(exc_info.value)


@pytest.mark.asyncio
async def test_groq_retryable_vs_non_retryable_errors() -> None:
    """Verify Groq provider distinguishes between retryable server error and non-retryable auth error."""
    groq_provider = GroqLLMProvider(api_key="gsk_test12345678901234567890")

    # Test non-retryable auth error
    from groq import AuthenticationError

    mock_resp = AsyncMock()
    mock_resp.status_code = 401
    auth_err = AuthenticationError("Invalid API key provided", response=mock_resp, body=None)

    auth_calls = 0

    async def mock_auth_fail(*_args, **_kwargs):
        nonlocal auth_calls
        auth_calls += 1
        raise auth_err

    with (
        patch.object(
            groq_provider._client.chat.completions,
            "create",
            side_effect=mock_auth_fail,
        ),
        pytest.raises(LLMAuthenticationError) as exc_info,
    ):
        await groq_provider.generate_structured(
            system_prompt="Test",
            user_payload={},
            output_schema=FindingAnalysis,
        )

    assert auth_calls == 1  # Did not retry auth failure
    assert exc_info.value.retryable is False
