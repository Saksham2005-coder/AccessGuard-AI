"""Deterministic in-memory Mock LLM provider for fast, reproducible testing without network calls."""

import uuid
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.exceptions import LLMError
from app.ai.provider import LLMProvider
from app.ai.schemas import FindingAnalysis, PatchOperation, RemediationProposal, ReviewResult

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic mock model provider for unit tests and local pipeline execution."""

    def __init__(self, simulated_error: LLMError | None = None) -> None:
        self._simulated_error = simulated_error
        self.call_history: list[dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "deterministic-mock-v1"

    @property
    def model_name(self) -> str:
        return self.default_model

    def set_simulated_error(self, error: LLMError | None) -> None:
        """Inject a simulated error to test failure handling and retries."""
        self._simulated_error = error

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        """Return deterministic Pydantic instance based on payload inputs."""
        self.call_history.append(
            {
                "system_prompt": system_prompt,
                "user_payload": user_payload,
                "output_schema": output_schema.__name__,
                "model": model or self.default_model,
                "temperature": temperature,
            }
        )

        if self._simulated_error is not None:
            raise self._simulated_error

        # Extract context from payload
        rule_id = str(user_payload.get("axe_rule_id") or "accessibility-issue").lower()
        selector = str(user_payload.get("selector") or "body")
        snippet = str(user_payload.get("html_snippet") or "<div>")
        evidence = user_payload.get("retrieved_evidence") or []
        evidence_ids = [
            str(e.get("chunk_id")) for e in evidence if isinstance(e, dict) and e.get("chunk_id")
        ]
        if not evidence_ids:
            # Fallback UUID string if no evidence passed
            evidence_ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, rule_id))]

        # 1. FindingAnalysis Mock
        if issubclass(output_schema, FindingAnalysis):
            crit_ids = (
                ["1.1.1"]
                if "alt" in rule_id or "image" in rule_id
                else ["1.4.3" if "contrast" in rule_id else "4.1.2"]
            )
            result = FindingAnalysis(
                summary=f"Automated finding for '{rule_id}': element requires accessible markup.",
                likely_root_cause=f"The element matching '{selector}' violates WCAG requirements for {rule_id}.",
                affected_element_type="img" if "alt" in rule_id else "interactive_control",
                relevant_criterion_ids=crit_ids,
                needs_manual_review=False,
                limitations=["Automated rule test only", "Color perception varies across monitors"],
                evidence_chunk_ids=evidence_ids,
            )
            return result  # type: ignore[return-value]

        # 2. RemediationProposal Mock
        if issubclass(output_schema, RemediationProposal):
            patch_ops: list[PatchOperation] = []
            patch_fmt = "snippet"

            if "alt" in rule_id or "image" in rule_id:
                patch_ops.append(
                    PatchOperation(
                        operation="set_attribute",
                        selector=selector if selector and selector != "body" else "img",
                        attribute="alt",
                        value="Descriptive accessibility label",
                    )
                )
                patch_fmt = "dom_operations"
                after_snippet = (
                    snippet.replace(">", ' alt="Descriptive accessibility label">')
                    if ">" in snippet
                    else '<img src="sample.png" alt="Descriptive accessibility label">'
                )
            elif "button" in rule_id or "name" in rule_id:
                patch_ops.append(
                    PatchOperation(
                        operation="set_attribute",
                        selector=selector if selector and selector != "body" else "button",
                        attribute="aria-label",
                        value="Action button",
                    )
                )
                patch_fmt = "dom_operations"
                after_snippet = '<button aria-label="Action button">Submit</button>'
            else:
                after_snippet = f"<!-- Adjusted for {rule_id} -->\n{snippet}"

            result = RemediationProposal(
                problem=f"Assistive technology cannot properly parse element matching '{selector}'.",
                recommendation=f"Add necessary attributes to conform with accessibility requirements for {rule_id}.",
                before_snippet=snippet,
                after_snippet=after_snippet,
                patch_format=patch_fmt,  # type: ignore[arg-type]
                patch_operations=patch_ops,
                expected_effect="Screen readers announce the element correctly and accessible tree is valid.",
                manual_checks=[
                    "Verify screen reader announces the updated accessible text",
                    "Verify visual layout is unaffected",
                ],
                evidence_chunk_ids=evidence_ids,
                model_confidence=0.95,
            )
            return result  # type: ignore[return-value]

        # 3. ReviewResult Mock
        if issubclass(output_schema, ReviewResult):
            has_rejection = bool(user_payload.get("simulate_rejection", False))
            result = ReviewResult(
                accepted_for_human_review=not has_rejection,
                rejection_reasons=["Simulated policy rejection"] if has_rejection else [],
                evidence_complete=bool(evidence_ids),
                policy_checks_passed=[
                    "safe_dom_attributes",
                    "grounded_citations",
                    "bounded_snippet",
                ],
                policy_checks_failed=["disallowed_attributes"] if has_rejection else [],
            )
            return result  # type: ignore[return-value]

        # Generic Pydantic fallback instantiation
        return output_schema.model_validate({})
