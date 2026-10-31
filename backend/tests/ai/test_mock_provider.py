"""Unit tests for MockLLMProvider, structured schemas, safety allowlists, and factory."""

import pytest
from pydantic import ValidationError

from app.ai.exceptions import LLMAuthenticationError, LLMRateLimitError
from app.ai.factory import get_llm_provider
from app.ai.mock_provider import MockLLMProvider
from app.ai.schemas import (
    FindingAnalysis,
    PatchOperation,
    RemediationProposal,
    ReviewResult,
)


@pytest.mark.asyncio
async def test_mock_provider_generates_finding_analysis() -> None:
    """Verify MockLLMProvider generates valid FindingAnalysis instance grounded in payload."""
    provider = MockLLMProvider()
    payload = {
        "axe_rule_id": "image-alt",
        "selector": "img.logo",
        "html_snippet": '<img src="logo.png">',
        "retrieved_evidence": [{"chunk_id": "chunk-123", "criterion_id": "1.1.1"}],
    }
    res = await provider.generate_structured(
        system_prompt="Analyze finding",
        user_payload=payload,
        output_schema=FindingAnalysis,
    )
    assert isinstance(res, FindingAnalysis)
    assert "image-alt" in res.summary
    assert "1.1.1" in res.relevant_criterion_ids
    assert "chunk-123" in res.evidence_chunk_ids
    assert res.needs_manual_review is False
    assert len(provider.call_history) == 1


@pytest.mark.asyncio
async def test_mock_provider_generates_remediation_proposal() -> None:
    """Verify MockLLMProvider produces safe, constrained patch operations and snippets."""
    provider = MockLLMProvider()
    payload = {
        "axe_rule_id": "image-alt",
        "selector": "img.logo",
        "html_snippet": '<img src="logo.png">',
        "retrieved_evidence": [{"chunk_id": "chunk-123"}],
    }
    res = await provider.generate_structured(
        system_prompt="Propose remediation",
        user_payload=payload,
        output_schema=RemediationProposal,
    )
    assert isinstance(res, RemediationProposal)
    assert res.patch_format == "dom_operations"
    assert len(res.patch_operations) >= 1
    assert res.patch_operations[0].operation == "set_attribute"
    assert res.patch_operations[0].attribute == "alt"
    assert res.model_confidence is not None and res.model_confidence >= 0.90


@pytest.mark.asyncio
async def test_mock_provider_generates_review_result() -> None:
    """Verify MockLLMProvider returns valid ReviewResult indicating policy conformance."""
    provider = MockLLMProvider()
    payload = {
        "retrieved_evidence": [{"chunk_id": "chunk-123"}],
        "simulate_rejection": False,
    }
    res = await provider.generate_structured(
        system_prompt="Review proposal",
        user_payload=payload,
        output_schema=ReviewResult,
    )
    assert isinstance(res, ReviewResult)
    assert res.accepted_for_human_review is True
    assert len(res.policy_checks_passed) >= 1


@pytest.mark.asyncio
async def test_mock_provider_simulated_error() -> None:
    """Verify simulated errors in mock provider raise typed LLMError."""
    provider = MockLLMProvider(simulated_error=LLMRateLimitError("Quota exceeded", provider="mock"))
    with pytest.raises(LLMRateLimitError) as exc_info:
        await provider.generate_structured(
            system_prompt="Test",
            user_payload={},
            output_schema=FindingAnalysis,
        )
    assert exc_info.value.retryable is True
    assert exc_info.value.provider == "mock"


def test_patch_operation_allows_safe_attributes() -> None:
    """Verify PatchOperation accepts standard accessibility attributes."""
    op = PatchOperation(
        operation="set_attribute",
        selector="button#toggle",
        attribute="aria-expanded",
        value="true",
    )
    assert op.attribute == "aria-expanded"
    assert op.value == "true"


def test_patch_operation_rejects_dangerous_attributes() -> None:
    """Verify PatchOperation rejects event handlers and arbitrary scripts."""
    with pytest.raises(ValidationError):
        PatchOperation(
            operation="set_attribute",
            selector="button#btn",
            attribute="onclick",
            value="alert(1)",
        )

    with pytest.raises(ValidationError):
        PatchOperation(
            operation="set_attribute",
            selector="a",
            attribute="href",
            value="javascript:void(0)",
        )

    with pytest.raises(ValidationError):
        PatchOperation(
            operation="set_attribute",
            selector="div",
            attribute="aria-label",
            value="javascript:exploit()",
        )


def test_llm_factory_instantiates_mock_provider() -> None:
    """Verify factory returns MockLLMProvider when requested."""
    provider = get_llm_provider(force_new=True, provider_override="mock")
    assert provider.provider_name == "mock"
    assert provider.default_model == "deterministic-mock-v1"


def test_llm_factory_missing_gemini_key_raises_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify factory raises LLMAuthenticationError when Gemini key is not configured."""
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    with pytest.raises(LLMAuthenticationError) as exc_info:
        get_llm_provider(force_new=True, provider_override="gemini")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
