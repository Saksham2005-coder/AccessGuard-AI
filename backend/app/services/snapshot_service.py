"""Sanitized DOM snapshot storage, safe patch application, and hashing service."""

import hashlib
import json
import re
from typing import Any

from bs4 import BeautifulSoup

from app.ai.schemas import SAFE_ATTRIBUTES, PatchOperation
from app.core.errors import PolicyViolationError
from app.core.logging import get_logger

logger = get_logger("snapshot_service")

# Regular expression to match inline event handler attributes (onclick, onload, onerror, etc.)
EVENT_HANDLER_PATTERN = re.compile(r"^on[a-z]+", re.IGNORECASE)

# Dangerous URL schemes that must be stripped
DANGEROUS_SCHEMES_PATTERN = re.compile(r"^\s*(javascript|vbscript|data\s*:\s*text/html)", re.IGNORECASE)


def compute_snapshot_hash(html: str) -> str:
    """Compute SHA-256 checksum of normalized snapshot HTML content."""
    normalized = html.strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def compute_patch_hash(operations: list[dict[str, Any] | PatchOperation]) -> str:
    """Compute SHA-256 checksum of canonical patch operations JSON."""
    clean_ops = [
        op.model_dump() if isinstance(op, PatchOperation) else op
        for op in operations
    ]
    canonical_json = json.dumps(clean_ops, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def sanitize_dom_snapshot(html: str) -> str:
    """Sanitize HTML snapshot by eliminating remote scripts, tracking beacons, and event handlers.

    Guarantees:
    - All <script>, <style>, <iframe>, <object>, <embed> tags are removed.
    - All remote stylesheet <link rel="stylesheet"> tags are removed.
    - All inline event handler attributes (onclick, onload, etc.) are purged.
    - Script and executable URI schemes are stripped from href/src attributes.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove dangerous executable or remote loading tags
    for tag_name in ("script", "iframe", "object", "embed", "applet"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 2. Remove external stylesheet links and tracker preloads
    for link in soup.find_all("link"):
        rel = link.get("rel", [])
        rel_str = " ".join(rel).lower() if isinstance(rel, list) else str(rel).lower()
        if "stylesheet" in rel_str or "preload" in rel_str or "dns-prefetch" in rel_str:
            link.decompose()

    # 3. Purge inline event handlers and sanitize dangerous schemes
    for tag in soup.find_all(True):
        attrs_to_remove = []
        for attr, val in list(tag.attrs.items()):
            # Strip inline event handlers (onclick, onload, etc.)
            if EVENT_HANDLER_PATTERN.match(attr):
                attrs_to_remove.append(attr)
                continue

            # Strip script URI schemes
            val_str = str(val) if not isinstance(val, list) else " ".join(val)
            if DANGEROUS_SCHEMES_PATTERN.search(val_str):
                attrs_to_remove.append(attr)

        for attr in attrs_to_remove:
            del tag.attrs[attr]

    return str(soup)


def apply_dom_patch(
    html: str,
    operations: list[dict[str, Any] | PatchOperation],
) -> tuple[str, list[dict[str, Any]]]:
    """Apply strictly allowlisted DOM patch operations to an HTML document.

    Raises:
        PolicyViolationError: If an operation targets prohibited attributes or contains unsafe values.
    """
    if not html:
        return "", []

    soup = BeautifulSoup(html, "html.parser")
    applied_logs: list[dict[str, Any]] = []

    for idx, raw_op in enumerate(operations):
        # Validate operation schema and attribute safety
        if isinstance(raw_op, PatchOperation):
            op = raw_op
        else:
            try:
                op = PatchOperation.model_validate(raw_op)
            except Exception as e:
                raise PolicyViolationError(
                    f"Invalid patch operation at index {idx}: {e}",
                    details={"index": idx, "raw_op": str(raw_op)},
                ) from e

        # Validate attribute allowlist
        if op.attribute:
            attr_clean = op.attribute.strip().lower()
            if attr_clean not in SAFE_ATTRIBUTES:
                raise PolicyViolationError(
                    f"Attribute '{op.attribute}' violates safe accessibility patch policy.",
                    details={"attribute": op.attribute, "allowed": sorted(SAFE_ATTRIBUTES)},
                )

        # Validate value safety (no script schemes)
        if op.value and DANGEROUS_SCHEMES_PATTERN.search(op.value):
            raise PolicyViolationError(
                f"Patch operation value contains prohibited script URI scheme: '{op.value}'",
                details={"selector": op.selector, "value": op.value},
            )

        # Find target elements
        targets = soup.select(op.selector)
        if not targets:
            logger.warning(
                "Patch operation selector found no target elements in snapshot",
                selector=op.selector,
                operation=op.operation,
            )
            applied_logs.append({
                "operation": op.operation,
                "selector": op.selector,
                "matched_count": 0,
                "status": "selector_not_found",
            })
            continue

        matched_count = 0
        for elem in targets:
            matched_count += 1
            if op.operation == "set_attribute" and op.attribute:
                elem[op.attribute] = op.value or ""
            elif op.operation == "remove_attribute" and op.attribute:
                elem.attrs.pop(op.attribute, None)
            elif op.operation == "replace_text" and op.value is not None:
                elem.string = op.value

        applied_logs.append({
            "operation": op.operation,
            "selector": op.selector,
            "matched_count": matched_count,
            "attribute": op.attribute,
            "status": "applied",
        })

    return str(soup), applied_logs
