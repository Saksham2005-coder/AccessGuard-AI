"""Screen-reader-oriented semantic tree extraction engine using sandboxed browser DOM inspection."""

import contextlib
from datetime import UTC, datetime
from typing import Any

from playwright.async_api import Route, async_playwright

from app.core.logging import get_logger
from app.db.models.finding import Finding
from app.schemas.screen_reader import (
    HeadingOutlineItem,
    LandmarkOutlineItem,
    ReviewHint,
    ScreenReaderSimulationResponse,
    SemanticNode,
)

logger = get_logger("screen_reader_extractor")

EXTRACT_SEMANTICS_JS = r"""
(() => {

    const results = [];
    let sequenceIndex = 0;

    const LANDMARK_ROLES = new Set([
        "banner", "navigation", "main", "complementary", "contentinfo", "region", "form", "search"
    ]);
    const INTERACTIVE_ROLES = new Set([
        "button", "link", "checkbox", "radio", "combobox", "textbox", "searchbox", "menuitem", "tab", "switch"
    ]);

    function getHeadingLevel(el) {
        const tag = el.tagName.toUpperCase();
        if (/^H[1-6]$/.test(tag)) return parseInt(tag.charAt(1), 10);
        if (el.getAttribute("role") === "heading") {
            const level = parseInt(el.getAttribute("aria-level"), 10);
            return isNaN(level) ? 2 : level;
        }
        return null;
    }

    function getLandmarkType(el) {
        const explicitRole = (el.getAttribute("role") || "").toLowerCase();
        if (LANDMARK_ROLES.has(explicitRole)) return explicitRole;
        const tag = el.tagName.toLowerCase();
        if (tag === "header") return "banner";
        if (tag === "nav") return "navigation";
        if (tag === "main") return "main";
        if (tag === "footer") return "contentinfo";
        if (tag === "aside") return "complementary";
        if (tag === "form" && (el.getAttribute("aria-label") || el.getAttribute("aria-labelledby"))) return "form";
        return null;
    }

    function getRole(el) {
        const explicit = el.getAttribute("role");
        if (explicit) return explicit.toLowerCase();
        const tag = el.tagName.toLowerCase();
        if (/^h[1-6]$/.test(tag)) return "heading";
        if (tag === "button") return "button";
        if (tag === "a" && el.hasAttribute("href")) return "link";
        if (tag === "input") {
            const type = (el.getAttribute("type") || "text").toLowerCase();
            if (["button", "submit", "reset"].includes(type)) return "button";
            if (type === "checkbox") return "checkbox";
            if (type === "radio") return "radio";
            return "textbox";
        }
        if (tag === "select") return "combobox";
        if (tag === "textarea") return "textbox";
        if (tag === "img") return "image";
        const landmark = getLandmarkType(el);
        if (landmark) return landmark;
        return null;
    }

    function getAccessibleName(el) {
        if (el.getAttribute("aria-label")) return el.getAttribute("aria-label").trim();
        if (el.getAttribute("aria-labelledby")) {
            const ids = el.getAttribute("aria-labelledby").split(/\s+/);
            const textParts = ids.map(id => {
                const target = document.getElementById(id);
                return target ? (target.innerText || target.textContent || "") : "";
            }).filter(Boolean);
            if (textParts.length > 0) return textParts.join(" ").trim();
        }
        if (el.tagName.toLowerCase() === "img") {
            return (el.getAttribute("alt") !== null) ? el.getAttribute("alt").trim() : null;
        }
        if (["input", "select", "textarea"].includes(el.tagName.toLowerCase())) {
            const id = el.id;
            if (id) {
                const label = document.querySelector(`label[for="${id}"]`);
                if (label) return (label.innerText || label.textContent || "").trim();
            }
            const parentLabel = el.closest("label");
            if (parentLabel) {
                return (parentLabel.innerText || parentLabel.textContent || "").trim();
            }
            if (el.getAttribute("placeholder")) return el.getAttribute("placeholder").trim();
        }
        if (el.innerText && el.innerText.trim()) return el.innerText.trim();
        if (el.getAttribute("title")) return el.getAttribute("title").trim();
        return null;
    }

    function isVisible(el) {
        if (!el || el.nodeType !== 1) return false;
        const style = window.getComputedStyle(el);
        if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") return false;
        if (el.hasAttribute("aria-hidden") && el.getAttribute("aria-hidden") === "true") return false;
        return true;
    }

    function getCssSelector(el) {
        if (el.id) return `#${el.id}`;
        let path = [];
        let curr = el;
        while (curr && curr.nodeType === 1 && curr.tagName.toLowerCase() !== "body") {
            let tag = curr.tagName.toLowerCase();
            let parent = curr.parentElement;
            if (!parent) break;
            let siblings = Array.from(parent.children).filter(c => c.tagName.toLowerCase() === tag);
            let idx = siblings.indexOf(curr) + 1;
            path.unshift(siblings.length > 1 ? `${tag}:nth-of-type(${idx})` : tag);
            curr = parent;
        }
        return path.join(" > ") || el.tagName.toLowerCase();
    }

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT, {
        acceptNode(node) {
            if (!isVisible(node)) return NodeFilter.FILTER_REJECT;
            const role = getRole(node);
            const isHeading = !!getHeadingLevel(node);
            const isLandmark = !!getLandmarkType(node);
            if (role || isHeading || isLandmark) return NodeFilter.FILTER_ACCEPT;
            return NodeFilter.FILTER_SKIP;
        }
    });

    let currentNode = walker.nextNode();
    while (currentNode && results.length < 500) {
        const role = getRole(currentNode);
        const headingLevel = getHeadingLevel(currentNode);
        const landmarkType = getLandmarkType(currentNode);
        const accessibleName = getAccessibleName(currentNode);
        const selector = getCssSelector(currentNode);
        const isInteractive = INTERACTIVE_ROLES.has(role) || ["a", "button", "input", "select", "textarea"].includes(currentNode.tagName.toLowerCase());

        // Privacy defense: NEVER record input values or passwords
        results.push({
            sequence_index: sequenceIndex++,
            role: role || (headingLevel ? "heading" : "generic"),
            accessible_name: accessibleName,
            heading_level: headingLevel,
            landmark_type: landmarkType,
            is_interactive: isInteractive,
            selector: selector,
            tag_name: currentNode.tagName.toLowerCase(),
            has_name: !!accessibleName,
            attributes: {
                role: currentNode.getAttribute("role") || null,
                aria_expanded: currentNode.getAttribute("aria-expanded"),
                aria_checked: currentNode.getAttribute("aria-checked"),
                aria_disabled: currentNode.getAttribute("aria-disabled"),
                aria_required: currentNode.getAttribute("aria-required"),
            }
        });

        currentNode = walker.nextNode();
    }

    return results;
})()
"""


async def _abort_route(route: Route) -> None:
    with contextlib.suppress(Exception):
        await route.abort()


def _wrap_in_html5(raw_html: str) -> str:
    if "<!DOCTYPE html>" in raw_html or "<html" in raw_html.lower():
        return raw_html
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Screen Reader Preview</title>
</head>
<body>
    <main>
        {raw_html}
    </main>
</body>
</html>"""


async def extract_semantic_tree_from_html(
    html_content: str,
    findings: list[Finding] | None = None,
    page_url: str = "",
    scan_id: str = "",
    page_id: str = "",
) -> ScreenReaderSimulationResponse:
    """Evaluate DOM accessibility semantics, reading order, and review hints in a sandbox."""
    sanitized_html = _wrap_in_html5(html_content)
    raw_nodes: list[dict[str, Any]] = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1.0,
            )
            page = await context.new_page()
            await page.route("**/*", _abort_route)

            try:
                await page.set_content(sanitized_html, timeout=5000, wait_until="domcontentloaded")
            except Exception as e:
                logger.warning("DOM snapshot content loading timed out; continuing with partial", error=str(e))

            raw_nodes = await page.evaluate(EXTRACT_SEMANTICS_JS)
            await context.close()
            await browser.close()
    except Exception as e:
        logger.error("Failed to execute Playwright semantic extraction; falling back", error=str(e))
        raw_nodes = []

    # Map findings by selector or rule for correlation
    findings_by_selector: dict[str, Finding] = {}
    if findings:
        for f in findings:
            if f.selector:
                findings_by_selector[f.selector.strip().lower()] = f

    reading_order: list[SemanticNode] = []
    headings: list[HeadingOutlineItem] = []
    landmarks: list[LandmarkOutlineItem] = []
    interactive_elements: list[SemanticNode] = []
    review_hints: list[ReviewHint] = []

    prev_heading_level: int | None = None
    seen_interactive_names: dict[str, int] = {}

    for node_dict in raw_nodes:
        seq_idx = node_dict["sequence_index"]
        sel = node_dict["selector"]
        role = node_dict["role"]
        name = node_dict["accessible_name"]
        h_level = node_dict["heading_level"]
        l_type = node_dict["landmark_type"]
        is_interactive = node_dict["is_interactive"]

        # Check for correlated axe finding
        associated_f = findings_by_selector.get(sel.lower())
        associated_f_id = str(associated_f.id) if associated_f else None

        potential_issue = None
        if is_interactive and not name:
            potential_issue = "Missing accessible name"
            review_hints.append(
                ReviewHint(
                    category="missing_name",
                    message=f"Interactive control <{node_dict['tag_name']}> lacks an accessible name.",
                    severity="warning",
                    sequence_index=seq_idx,
                    selector=sel,
                    associated_finding_id=associated_f_id,
                )
            )

        sem_node = SemanticNode(
            sequence_index=seq_idx,
            role=role,
            accessible_name=name,
            heading_level=h_level,
            landmark_type=l_type,
            is_interactive=is_interactive,
            selector=sel,
            tag_name=node_dict["tag_name"],
            has_name=node_dict["has_name"],
            attributes=node_dict["attributes"],
            associated_finding_id=associated_f_id,
            potential_issue=potential_issue,
        )
        reading_order.append(sem_node)

        # Headings Outline
        if h_level is not None:
            is_skipped = False
            if prev_heading_level is not None and h_level > prev_heading_level + 1:
                is_skipped = True
                review_hints.append(
                    ReviewHint(
                        category="heading_skip",
                        message=f"Heading level skipped from H{prev_heading_level} directly to H{h_level}.",
                        severity="advisory",
                        sequence_index=seq_idx,
                        selector=sel,
                        associated_finding_id=associated_f_id,
                    )
                )
            prev_heading_level = h_level
            headings.append(
                HeadingOutlineItem(
                    level=h_level,
                    text=name or "(Unlabeled heading)",
                    sequence_index=seq_idx,
                    selector=sel,
                    is_skipped=is_skipped,
                )
            )

        # Landmarks Outline
        if l_type is not None:
            landmarks.append(
                LandmarkOutlineItem(
                    landmark_type=l_type,
                    accessible_name=name,
                    sequence_index=seq_idx,
                    selector=sel,
                )
            )

        # Interactive Controls
        if is_interactive:
            interactive_elements.append(sem_node)
            if name:
                key = f"{role}:{name.lower()}"
                seen_interactive_names[key] = seen_interactive_names.get(key, 0) + 1
                if seen_interactive_names[key] == 2:
                    review_hints.append(
                        ReviewHint(
                            category="duplicate_name",
                            message=f"Multiple {role} elements share the identical accessible name: '{name}'.",
                            severity="advisory",
                            sequence_index=seq_idx,
                            selector=sel,
                            associated_finding_id=associated_f_id,
                        )
                    )

    limitations = [
        "Static DOM interpretation aid based on standard browser accessibility semantics, not an NVDA, JAWS, or VoiceOver execution.",
        "Assistive technology speech output depends on specific screen reader versions, speech synthesis engines, punctuation verbosity, and operating system accessibility APIs.",
        "Form field values, passwords, credit card inputs, and sensitive attributes are completely redacted by policy.",
    ]

    return ScreenReaderSimulationResponse(
        scan_id=scan_id,
        page_id=page_id,
        page_url=page_url,
        nodes_count=len(reading_order),
        reading_order=reading_order,
        headings=headings,
        landmarks=landmarks,
        interactive_elements=interactive_elements,
        review_hints=review_hints,
        limitations=limitations,
        captured_at=datetime.now(UTC).isoformat(),
    )
