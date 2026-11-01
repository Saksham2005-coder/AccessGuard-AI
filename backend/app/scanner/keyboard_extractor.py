"""Deterministic Keyboard Navigation Testing Engine.

Phase 19 Feature 5: Real browser-driven keyboard navigation harness using
Playwright to test Tab and Shift+Tab focus traversal, focus indicator visibility,
and keyboard traps under isolated conditions.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from playwright.async_api import async_playwright

from app.schemas.keyboard_test import (
    BoundingBox,
    ComputedFocusStyle,
    KeyboardIssue,
    KeyboardNavigationReport,
    KeyboardNavigationSummary,
    KeyboardStep,
)

logger = logging.getLogger(__name__)

# Script evaluated in page context to inspect activeElement semantics and computed focus styles
INSPECT_ACTIVE_ELEMENT_JS = r"""() => {
    const active = document.activeElement;
    if (!active || active === document.body || active === document.documentElement) {
        return {
            isBodyOrHtml: true,
            tagName: active ? active.tagName.toLowerCase() : "body",
            selector: active ? (active.id ? "#" + active.id : active.tagName.toLowerCase()) : "body",
            role: null,
            accessibleName: "",
            tabindex: null,
            boundingBox: null,
            isClippedOrOffscreen: false,
            focusStyle: null,
            hasVisibleFocusIndicator: false
        };
    }

    // Build stable CSS selector
    function buildSelector(el) {
        if (el.id) return `#${CSS.escape(el.id)}`;
        let path = [];
        let curr = el;
        while (curr && curr.nodeType === Node.ELEMENT_NODE && curr !== document.body) {
            let tag = curr.tagName.toLowerCase();
            let siblingIndex = 1;
            let sibling = curr.previousElementSibling;
            while (sibling) {
                if (sibling.tagName.toLowerCase() === tag) siblingIndex++;
                sibling = sibling.previousElementSibling;
            }
            path.unshift(`${tag}:nth-of-type(${siblingIndex})`);
            curr = curr.parentElement;
        }
        return path.length > 0 ? path.join(" > ") : el.tagName.toLowerCase();
    }

    // Compute accessible name without leaking sensitive input values
    function getAccessibleName(el) {
        const type = (el.getAttribute("type") || "").toLowerCase();
        if (type === "password" || el.autocomplete === "cc-number" || el.autocomplete === "current-password") {
            return "[REDACTED_SECURE_FIELD]";
        }

        const ariaLabel = el.getAttribute("aria-label");
        if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

        const labelledBy = el.getAttribute("aria-labelledby");
        if (labelledBy) {
            const labelEl = document.getElementById(labelledBy.trim());
            if (labelEl && labelEl.textContent && labelEl.textContent.trim()) {
                return labelEl.textContent.trim();
            }
        }

        if (el.tagName.toLowerCase() === "input" && (type === "submit" || type === "button" || type === "reset")) {
            return (el.value || "").trim();
        }

        const title = el.getAttribute("title");
        if (title && title.trim()) return title.trim();

        const alt = el.getAttribute("alt");
        if (alt && alt.trim()) return alt.trim();

        const placeholder = el.getAttribute("placeholder");
        if (placeholder && placeholder.trim()) return placeholder.trim();

        // Standard text content for buttons, links, etc.
        const text = el.innerText || el.textContent || "";
        return text.replace(/\s+/g, " ").trim().slice(0, 150);
    }

    // Determine explicit or implicit role
    function getRole(el) {
        const explicit = el.getAttribute("role");
        if (explicit && explicit.trim()) return explicit.trim().toLowerCase();

        const tag = el.tagName.toLowerCase();
        if (tag === "a" && el.hasAttribute("href")) return "link";
        if (tag === "button") return "button";
        if (tag === "select") return "combobox";
        if (tag === "textarea") return "textbox";
        if (tag === "input") {
            const type = (el.getAttribute("type") || "text").toLowerCase();
            if (["button", "submit", "reset"].includes(type)) return "button";
            if (type === "checkbox") return "checkbox";
            if (type === "radio") return "radio";
            return "textbox";
        }
        return tag;
    }

    const rect = active.getBoundingClientRect();
    const style = window.getComputedStyle(active);

    const outlineStyle = style.outlineStyle || "none";
    const outlineWidth = style.outlineWidth || "0px";
    const outlineColor = style.outlineColor || "";
    const outlineOffset = style.outlineOffset || "0px";
    const boxShadow = style.boxShadow || "none";
    const borderStyle = style.borderStyle || "none";
    const borderWidth = style.borderWidth || "0px";
    const borderColor = style.borderColor || "";

    const outlineVisible = outlineStyle !== "none" && outlineWidth !== "0px";
    const shadowVisible = boxShadow !== "none" && boxShadow !== "" && !boxShadow.includes("0px 0px 0px 0px");
    const borderVisible = borderStyle !== "none" && borderWidth !== "0px";

    const hasVisibleFocusIndicator = outlineVisible || shadowVisible || borderVisible;

    const isClippedOrOffscreen = (
        rect.width === 0 ||
        rect.height === 0 ||
        rect.bottom < 0 ||
        rect.top > window.innerHeight ||
        rect.right < 0 ||
        rect.left > window.innerWidth ||
        style.visibility === "hidden" ||
        style.opacity === "0"
    );

    const rawTabindex = active.getAttribute("tabindex");
    const tabindex = rawTabindex !== null ? parseInt(rawTabindex, 10) : null;

    return {
        isBodyOrHtml: false,
        tagName: active.tagName.toLowerCase(),
        selector: buildSelector(active),
        role: getRole(active),
        accessibleName: getAccessibleName(active),
        tabindex: isNaN(tabindex) ? null : tabindex,
        boundingBox: {
            x: Math.round(rect.x * 10) / 10,
            y: Math.round(rect.y * 10) / 10,
            width: Math.round(rect.width * 10) / 10,
            height: Math.round(rect.height * 10) / 10
        },
        isClippedOrOffscreen,
        focusStyle: {
            outline_style: outlineStyle,
            outline_width: outlineWidth,
            outline_color: outlineColor,
            outline_offset: outlineOffset,
            box_shadow: boxShadow,
            border_style: borderStyle,
            border_width: borderWidth,
            border_color: borderColor
        },
        hasVisibleFocusIndicator
    };
};
"""


async def run_keyboard_navigation_test(
    html_content: str,
    page_url: str,
    scan_id: uuid.UUID | None = None,
    page_id: uuid.UUID | None = None,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    max_forward_steps: int = 50,
    max_reverse_steps: int = 15,
) -> KeyboardNavigationReport:
    """Execute a deterministic keyboard navigation test using Playwright in an isolated context."""
    scan_id_str = str(scan_id or uuid.uuid4())
    page_id_str = str(page_id or uuid.uuid4())

    forward_steps: list[KeyboardStep] = []
    reverse_steps: list[KeyboardStep] = []
    issues: list[KeyboardIssue] = []
    visited_selectors: list[str] = []
    has_potential_trap = False
    completion_status = "completed"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
            ],
        )
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            java_script_enabled=True,
        )

        try:
            page = await context.new_page()

            # Abort all external network requests for complete isolation & security
            await page.route("**/*", lambda route: route.abort())

            # Load the HTML content
            await page.set_content(html_content, wait_until="domcontentloaded", timeout=15000)

            # Establish initial neutral focus state
            await page.evaluate("() => { if (document.body) { document.body.focus(); } }")

            consecutive_same_element_count = 0
            last_selector = ""

            # 1. Forward Tab Traversal
            for step_num in range(1, max_forward_steps + 1):
                await page.keyboard.press("Tab")
                active_info: dict[str, Any] = await page.evaluate(INSPECT_ACTIVE_ELEMENT_JS)

                if active_info.get("isBodyOrHtml"):
                    # Focus returned to body or html; either empty or wrapped around
                    if len(forward_steps) > 0:
                        # Reached end of page focus order
                        break
                    continue

                selector = active_info.get("selector", "")
                tag = active_info.get("tagName", "")
                role = active_info.get("role")
                accessible_name = active_info.get("accessibleName")
                tabindex = active_info.get("tabindex")
                is_clipped = active_info.get("isClippedOrOffscreen", False)
                has_indicator = active_info.get("hasVisibleFocusIndicator", False)
                raw_bbox = active_info.get("boundingBox")
                bbox = BoundingBox(**raw_bbox) if raw_bbox else None
                raw_style = active_info.get("focusStyle")
                f_style = ComputedFocusStyle(**raw_style) if raw_style else None

                step = KeyboardStep(
                    step_index=step_num,
                    action="Tab",
                    selector=selector,
                    tag_name=tag,
                    role=role,
                    accessible_name=accessible_name,
                    tabindex=tabindex,
                    bounding_box=bbox,
                    is_clipped_or_offscreen=is_clipped,
                    has_visible_focus_indicator=has_indicator,
                    focus_style=f_style,
                    focus_notes=None,
                )
                forward_steps.append(step)
                visited_selectors.append(selector)

                # Trap detection: stuck on same element
                if selector == last_selector:
                    consecutive_same_element_count += 1
                else:
                    consecutive_same_element_count = 0
                last_selector = selector

                if consecutive_same_element_count >= 3:
                    # Focus failed to advance after 3 Tabs
                    has_potential_trap = True
                    # Test if Escape releases focus
                    await page.keyboard.press("Escape")
                    escape_active: dict[str, Any] = await page.evaluate(INSPECT_ACTIVE_ELEMENT_JS)
                    escaped = escape_active.get("selector") != selector

                    issues.append(
                        KeyboardIssue(
                            issue_type="potential_focus_trap",
                            severity="critical",
                            step_index=step_num,
                            selector=selector,
                            message=(
                                f"Focus appears trapped on element '{selector}'. "
                                f"Tab key does not advance focus. "
                                f"{'Escape key successfully broke trap.' if escaped else 'Escape key failed to release focus.'}"
                            ),
                            recommendation="Ensure keyboard focus can always advance or escape using Tab, Shift+Tab, or Escape.",
                            wcag_criteria=["2.1.2 No Keyboard Trap"],
                        )
                    )
                    break

                if step_num == max_forward_steps:
                    completion_status = "capped"

            # 2. Reverse Shift+Tab Traversal (if any elements were focused)
            if forward_steps:
                for rev_num in range(1, min(max_reverse_steps, len(forward_steps)) + 1):
                    await page.keyboard.press("Shift+Tab")
                    active_info = await page.evaluate(INSPECT_ACTIVE_ELEMENT_JS)

                    if active_info.get("isBodyOrHtml"):
                        break

                    selector = active_info.get("selector", "")
                    tag = active_info.get("tagName", "")
                    role = active_info.get("role")
                    accessible_name = active_info.get("accessibleName")
                    tabindex = active_info.get("tabindex")
                    is_clipped = active_info.get("isClippedOrOffscreen", False)
                    has_indicator = active_info.get("hasVisibleFocusIndicator", False)
                    raw_bbox = active_info.get("boundingBox")
                    bbox = BoundingBox(**raw_bbox) if raw_bbox else None
                    raw_style = active_info.get("focusStyle")
                    f_style = ComputedFocusStyle(**raw_style) if raw_style else None

                    rev_step = KeyboardStep(
                        step_index=rev_num,
                        action="Shift+Tab",
                        selector=selector,
                        tag_name=tag,
                        role=role,
                        accessible_name=accessible_name,
                        tabindex=tabindex,
                        bounding_box=bbox,
                        is_clipped_or_offscreen=is_clipped,
                        has_visible_focus_indicator=has_indicator,
                        focus_style=f_style,
                        focus_notes=None,
                    )
                    reverse_steps.append(rev_step)

            # 3. Analyze Observed Steps for Accessibility Issues
            seen_issue_selectors: set[str] = set()

            for step in forward_steps:
                s_key = step.selector

                # Missing Focus Indicator
                if not step.has_visible_focus_indicator and f"no_indicator_{s_key}" not in seen_issue_selectors:
                    seen_issue_selectors.add(f"no_indicator_{s_key}")
                    issues.append(
                        KeyboardIssue(
                            issue_type="missing_focus_indicator",
                            severity="serious",
                            step_index=step.step_index,
                            selector=step.selector,
                            message=(
                                f"Element '{step.selector}' does not present a discernible focus indicator. "
                                f"(outline: {step.focus_style.outline_style if step.focus_style else 'none'}, "
                                f"box-shadow: {step.focus_style.box_shadow if step.focus_style else 'none'})"
                            ),
                            recommendation="Provide a high-contrast focus indicator (e.g. outline: 2px solid #2563eb; outline-offset: 2px;).",
                            wcag_criteria=["2.4.7 Focus Visible", "2.4.11 Focus Appearance"],
                        )
                    )

                # Missing Accessible Name
                interactive_roles = {"button", "link", "combobox", "textbox", "checkbox", "radio", "menuitem"}
                is_interactive = (
                    step.tag_name in {"a", "button", "input", "select", "textarea"}
                    or (step.role and step.role in interactive_roles)
                )
                if (
                    is_interactive
                    and not (step.accessible_name and step.accessible_name.strip())
                    and f"no_name_{s_key}" not in seen_issue_selectors
                ):
                    seen_issue_selectors.add(f"no_name_{s_key}")
                    issues.append(
                        KeyboardIssue(
                            issue_type="missing_accessible_name",
                            severity="critical",
                            step_index=step.step_index,
                            selector=step.selector,
                            message=f"Interactive focusable element '{step.selector}' has no discernible accessible name.",
                            recommendation="Provide an accessible label using aria-label, aria-labelledby, or visible inner text.",
                            wcag_criteria=["4.1.2 Name, Role, Value"],
                        )
                    )

                # Positive Tabindex
                if (
                    step.tabindex is not None
                    and step.tabindex > 0
                    and f"pos_tabindex_{s_key}" not in seen_issue_selectors
                ):
                    seen_issue_selectors.add(f"pos_tabindex_{s_key}")
                    issues.append(
                        KeyboardIssue(
                            issue_type="positive_tabindex",
                            severity="moderate",
                            step_index=step.step_index,
                            selector=step.selector,
                            message=f"Element '{step.selector}' specifies tabindex='{step.tabindex}'. Positive tabindex disrupts natural navigation order.",
                            recommendation="Avoid positive tabindex values. Use natural DOM source ordering or tabindex='0' / '-1'.",
                            wcag_criteria=["2.4.3 Focus Order"],
                        )
                    )

                # Offscreen or Clipped Focus
                if step.is_clipped_or_offscreen and f"offscreen_{s_key}" not in seen_issue_selectors:
                    seen_issue_selectors.add(f"offscreen_{s_key}")
                    issues.append(
                        KeyboardIssue(
                            issue_type="offscreen_focus",
                            severity="review_hint",
                            step_index=step.step_index,
                            selector=step.selector,
                            message=f"Element '{step.selector}' received keyboard focus while clipped or outside current viewport bounds.",
                            recommendation="Ensure focused elements scroll smoothly into view or are visible to sighted keyboard users.",
                            wcag_criteria=["2.4.7 Focus Visible", "2.4.3 Focus Order"],
                        )
                    )

        except Exception as e:
            logger.error("Error during keyboard navigation test: %s", e)
            completion_status = "failed"
        finally:
            await context.close()
            await browser.close()

    unique_selectors = set(visited_selectors)
    summary = KeyboardNavigationSummary(
        total_steps=len(forward_steps) + len(reverse_steps),
        forward_steps=len(forward_steps),
        reverse_steps=len(reverse_steps),
        unique_elements=len(unique_selectors),
        issues_count=len(issues),
        has_potential_trap=has_potential_trap,
        missing_indicator_count=sum(1 for i in issues if i.issue_type == "missing_focus_indicator"),
        missing_name_count=sum(1 for i in issues if i.issue_type == "missing_accessible_name"),
        positive_tabindex_count=sum(1 for i in issues if i.issue_type == "positive_tabindex"),
        completion_status=completion_status,
    )

    return KeyboardNavigationReport(
        scan_id=scan_id_str,
        page_id=page_id_str,
        page_url=page_url,
        viewport={"width": viewport_width, "height": viewport_height},
        summary=summary,
        steps=forward_steps,
        reverse_steps=reverse_steps,
        issues=issues,
        tested_at=datetime.now(UTC).isoformat(),
    )
