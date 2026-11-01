"""Base classes and utility functions for specialized accessibility investigation agents."""

import html
import re
from abc import ABC, abstractmethod
from typing import Any

from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.investigation import SpecialistReport

UNTRUSTED_CONTENT_TAG = "UNTRUSTED_CONTENT"


def escape_untrusted_content(text: str | None, max_len: int = 1500) -> str:
    """Sanitize and delimit untrusted DOM/page text to prevent prompt injection."""
    if not text:
        return ""
    # Strip potential control characters and truncate to max_len
    clean = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", str(text))
    truncated = clean[:max_len]
    escaped = html.escape(truncated, quote=True)
    return f"<{UNTRUSTED_CONTENT_TAG}>\n{escaped}\n</{UNTRUSTED_CONTENT_TAG}>"


class BaseSpecialist(ABC):
    """Abstract base class for all bounded accessibility specialist investigators."""

    agent_id: str
    agent_name: str
    dimension: str
    version: str = "1.0.0"

    @abstractmethod
    async def investigate(
        self,
        findings: list[Finding],
        scan: Scan,
        keyboard_run: dict[str, Any] | None = None,
    ) -> SpecialistReport:
        """Execute specialist bounded investigation over verified findings and scan metadata."""
        raise NotImplementedError
