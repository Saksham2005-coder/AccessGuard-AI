"""Integration and unit tests for Gemini and Groq model adapters and prompt loading."""

import pytest

from app.ai.exceptions import LLMAuthenticationError
from app.ai.gemini_provider import GeminiLLMProvider
from app.ai.groq_provider import GroqLLMProvider
from app.ai.prompts import load_prompt
from app.ai.schemas import FindingAnalysis
from app.config import get_settings


def test_load_prompt_templates() -> None:
    """Verify system prompt templates load successfully with security constraints."""
    analysis_prompt = load_prompt("finding_analysis_v1")
    assert "Lead Accessibility Specialist" in analysis_prompt
    assert "UNTRUSTED DATA" in analysis_prompt

    remediation_prompt = load_prompt("remediation_proposal_v1")
    assert "Senior Front-End Accessibility Engineer" in remediation_prompt
    assert "allowlisted operation" in remediation_prompt

    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_prompt_xyz")


def test_groq_provider_requires_api_key() -> None:
    """Verify GroqLLMProvider raises LLMAuthenticationError when initialized with empty key."""
    with pytest.raises(LLMAuthenticationError) as exc_info:
        GroqLLMProvider(api_key="")
    assert "GROQ_API_KEY must be provided" in str(exc_info.value)
    assert exc_info.value.provider == "groq"


def test_gemini_provider_requires_api_key() -> None:
    """Verify GeminiLLMProvider raises LLMAuthenticationError when initialized with empty key."""
    with pytest.raises(LLMAuthenticationError) as exc_info:
        GeminiLLMProvider(api_key="")
    assert "GEMINI_API_KEY must be provided" in str(exc_info.value)
    assert exc_info.value.provider == "gemini"


@pytest.mark.asyncio
async def test_gemini_provider_rejects_invalid_api_key() -> None:
    """Verify GeminiLLMProvider translates upstream 400/401/403 into LLMAuthenticationError."""
    provider = GeminiLLMProvider(api_key="AIzaSyFakeKeyInvalidForTesting123456789")
    with pytest.raises(LLMAuthenticationError) as exc_info:
        await provider.generate_structured(
            system_prompt="Test prompt",
            user_payload={"test": "data"},
            output_schema=FindingAnalysis,
        )
    assert exc_info.value.provider == "gemini"
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_gemini_provider_live_structured_generation() -> None:
    """Verify live Gemini API call generates valid structured FindingAnalysis with configured key."""
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY is not configured; skipping live provider call.")

    provider = GeminiLLMProvider(
        api_key=settings.GEMINI_API_KEY,
        default_model=settings.GEMINI_MODEL or "gemini-3.5-flash",
    )
    prompt = load_prompt("finding_analysis_v1")
    evidence_chunk_id = "00000000-0000-0000-0000-000000000001"
    payload = {
        "axe_rule_id": "image-alt",
        "selector": "img.brand-logo",
        "html_snippet": '<img src="logo.png" class="brand-logo">',
        "retrieved_evidence": [
            {
                "chunk_id": evidence_chunk_id,
                "criterion_id": "1.1.1",
                "title": "1.1.1 Non-text Content",
                "excerpt": "All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
            }
        ],
    }

    result = await provider.generate_structured(
        system_prompt=prompt,
        user_payload=payload,
        output_schema=FindingAnalysis,
    )

    assert isinstance(result, FindingAnalysis)
    assert len(result.summary) >= 10
    assert len(result.likely_root_cause) >= 10
    assert "1.1.1" in result.relevant_criterion_ids
    assert evidence_chunk_id in result.evidence_chunk_ids
