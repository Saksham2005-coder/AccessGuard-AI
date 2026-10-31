"""axe-core injection, execution, finding normalization, and fingerprinting engine."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.errors import InfrastructureUnavailableError
from app.core.logging import get_logger

logger = get_logger("axe_runner")

# Maximum string length for stored HTML snippets to prevent oversized database records
MAX_SNIPPET_LENGTH = 2000

# Default WCAG tags executed during accessibility evaluation
DEFAULT_AXE_TAGS = [
    "wcag2a",
    "wcag2aa",
    "wcag21a",
    "wcag21aa",
    "wcag22aa",
    "best-practice",
]


class AxeNodeResult(BaseModel):
    """Normalized representation of a single DOM node violating an accessibility rule."""

    target: list[str] = Field(default_factory=list, description="CSS selector path array")
    html_snippet: str = Field(default="", description="Sanitized and bounded HTML snippet")
    failure_summary: str = Field(default="", description="Summary of specific failed checks")


class AxeFindingItem(BaseModel):
    """Normalized accessibility finding parsed from axe-core result item."""

    rule_id: str
    impact: str | None = None  # minor, moderate, serious, critical
    description: str
    help_text: str = ""
    help_url: str = ""
    tags: list[str] = Field(default_factory=list)
    wcag_tags: list[str] = Field(default_factory=list)
    is_best_practice: bool = False
    is_incomplete: bool = False
    fingerprint: str
    primary_selector: str = ""
    nodes: list[AxeNodeResult] = Field(default_factory=list)


class AxeAuditResult(BaseModel):
    """Aggregate findings and summary from executing axe-core on a page."""

    url: str
    axe_version: str
    test_engine: str = "axe-core"
    violations: list[AxeFindingItem] = Field(default_factory=list)
    incomplete: list[AxeFindingItem] = Field(default_factory=list)
    passes_count: int = 0
    inapplicable_count: int = 0


def get_repo_root() -> Path:
    """Return the repository root directory."""
    # Current file is backend/app/scanner/axe_runner.py -> repo root is 4 levels up
    return Path(__file__).resolve().parent.parent.parent.parent


def get_axe_bundle_path() -> Path:
    """Locate the pinned local axe-core bundle file."""
    env_path = os.getenv("AXE_BUNDLE_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    repo_root = get_repo_root()
    bundle_path = repo_root / "tools" / "axe" / "node_modules" / "axe-core" / "axe.min.js"
    if not bundle_path.exists():
        fallback_path = Path("/app/tools/axe/node_modules/axe-core/axe.min.js")
        if fallback_path.exists():
            return fallback_path
        raise InfrastructureUnavailableError(
            f"Local axe-core bundle not found at '{bundle_path}'. "
            "Please run 'npm install' in tools/axe to provision the pinned axe-core bundle."
        )
    return bundle_path


def get_axe_version() -> str:
    """Discover pinned axe-core version from package metadata."""
    env_path = os.getenv("AXE_BUNDLE_PATH")
    if env_path and Path(env_path).exists():
        pkg_path = Path(env_path).parent / "package.json"
        if pkg_path.exists():
            try:
                with open(pkg_path, encoding="utf-8") as f:
                    data = json.load(f)
                    return str(data.get("version", "4.14.0"))
            except Exception:
                pass

    repo_root = get_repo_root()
    pkg_path = repo_root / "tools" / "axe" / "node_modules" / "axe-core" / "package.json"
    if not pkg_path.exists():
        fallback_pkg = Path("/app/tools/axe/node_modules/axe-core/package.json")
        if fallback_pkg.exists():
            pkg_path = fallback_pkg

    if pkg_path.exists():
        try:
            with open(pkg_path, encoding="utf-8") as f:
                data = json.load(f)
                return str(data.get("version", "4.14.0"))
        except Exception:
            pass
    return "4.14.0"


def compute_finding_fingerprint(
    normalized_url: str,
    rule_id: str,
    selector: str,
    snippet: str,
) -> str:
    """Compute a stable, deterministic SHA-256 fingerprint for a finding.

    Fingerprint guarantees:
    - Stable across identical runs on the same DOM element.
    - Changes if target selector or element HTML structure changes.
    """
    raw_key = f"{normalized_url.strip()}|{rule_id.strip()}|{selector.strip()}|{snippet.strip()}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:32]


def filter_wcag_tags(tags: list[str]) -> tuple[list[str], bool]:
    """Separate official WCAG success criterion tags from best-practice tags."""
    wcag_tags: list[str] = []
    is_best_practice = False

    for tag in tags:
        tag_lower = tag.lower().strip()
        if tag_lower == "best-practice":
            is_best_practice = True
        elif (
            tag_lower.startswith("wcag")
            or tag_lower.startswith("section508")
            or tag_lower.startswith("act")
        ):
            wcag_tags.append(tag_lower)

    return wcag_tags, is_best_practice


def normalize_axe_item(
    item: dict[str, Any],
    page_url: str,
    is_incomplete: bool = False,
) -> AxeFindingItem:
    """Normalize raw axe-core item into structured AxeFindingItem with length bounds."""
    rule_id = str(item.get("id", "unknown-rule"))
    impact = item.get("impact")
    description = str(item.get("description", ""))
    help_text = str(item.get("help", ""))
    help_url = str(item.get("helpUrl", ""))
    tags = [str(t) for t in item.get("tags", [])]

    wcag_tags, is_best_practice = filter_wcag_tags(tags)

    raw_nodes = item.get("nodes", [])
    normalized_nodes: list[AxeNodeResult] = []
    primary_selector = ""
    primary_snippet = ""

    for node in raw_nodes:
        targets = [str(t) for t in node.get("target", [])]
        html_raw = str(node.get("html", ""))
        # Enforce snippet length bound
        if len(html_raw) > MAX_SNIPPET_LENGTH:
            html_snippet = html_raw[:MAX_SNIPPET_LENGTH] + "... [truncated]"
        else:
            html_snippet = html_raw

        failure_summary = str(node.get("failureSummary", ""))

        if not primary_selector and targets:
            primary_selector = targets[0]
            primary_snippet = html_snippet

        normalized_nodes.append(
            AxeNodeResult(
                target=targets,
                html_snippet=html_snippet,
                failure_summary=failure_summary,
            )
        )

    fingerprint = compute_finding_fingerprint(
        normalized_url=page_url,
        rule_id=rule_id,
        selector=primary_selector,
        snippet=primary_snippet,
    )

    return AxeFindingItem(
        rule_id=rule_id,
        impact=str(impact) if impact else None,
        description=description,
        help_text=help_text,
        help_url=help_url,
        tags=tags,
        wcag_tags=wcag_tags,
        is_best_practice=is_best_practice,
        is_incomplete=is_incomplete,
        fingerprint=fingerprint,
        primary_selector=primary_selector,
        nodes=normalized_nodes,
    )


async def execute_axe_audit(
    page: Any,
    rule_tags: list[str] | None = None,
) -> AxeAuditResult:
    """Inject local axe-core bundle into page and evaluate accessibility rules."""
    bundle_path = get_axe_bundle_path()
    axe_version = get_axe_version()
    effective_tags = rule_tags if rule_tags is not None else DEFAULT_AXE_TAGS

    # Inject axe-core directly into the Playwright page DOM
    await page.add_script_tag(path=str(bundle_path))

    # Execute axe.run() with requested tags
    axe_options = {
        "runOnly": {
            "type": "tag",
            "values": effective_tags,
        }
    }

    raw_results = await page.evaluate(
        """(options) => {
            return window.axe.run(document, options);
        }""",
        axe_options,
    )

    page_url = page.url

    # Normalize confirmed violations
    violations: list[AxeFindingItem] = [
        normalize_axe_item(v, page_url=page_url, is_incomplete=False)
        for v in raw_results.get("violations", [])
    ]

    # Normalize incomplete (needs review) items separately
    incomplete: list[AxeFindingItem] = [
        normalize_axe_item(inc, page_url=page_url, is_incomplete=True)
        for inc in raw_results.get("incomplete", [])
    ]

    passes_count = len(raw_results.get("passes", []))
    inapplicable_count = len(raw_results.get("inapplicable", []))

    logger.info(
        "axe-core audit completed",
        url=page_url,
        violations_count=len(violations),
        incomplete_count=len(incomplete),
        passes_count=passes_count,
    )

    return AxeAuditResult(
        url=page_url,
        axe_version=axe_version,
        violations=violations,
        incomplete=incomplete,
        passes_count=passes_count,
        inapplicable_count=inapplicable_count,
    )
