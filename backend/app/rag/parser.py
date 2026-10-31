"""HTML parser and structural extractor for official WCAG and WAI documents."""

import re
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from app.core.logging import get_logger

logger = get_logger("rag_parser")

# Regex pattern for WCAG success criterion headers: e.g. "1.1.1 Non-text Content (Level A)"
CRITERION_HEADER_RE = re.compile(
    r"(?:Success\s+Criterion\s+)?(\d+\.\d+\.\d+)\s+([^(]+?)(?:\s*\((?:Level\s+)?(A{1,3})\))?",
    re.IGNORECASE,
)

# Regex pattern for WCAG guidelines: e.g. "Guideline 1.1 Text Alternatives"
GUIDELINE_HEADER_RE = re.compile(
    r"Guideline\s+(\d+\.\d+)\s*[-:]?\s*(.+)",
    re.IGNORECASE,
)

# Regex pattern for WCAG principles: e.g. "Principle 1 - Perceivable"
PRINCIPLE_HEADER_RE = re.compile(
    r"Principle\s+(\d+)\s*[-:]?\s*([A-Za-z]+)",
    re.IGNORECASE,
)

PRINCIPLE_MAPPING = {
    "1": "Perceivable",
    "2": "Operable",
    "3": "Understandable",
    "4": "Robust",
}

CRITERION_ID_RE = re.compile(r"(?:Success\s+Criterion\s+)?(\d+\.\d+\.\d+)", re.IGNORECASE)
CRITERION_LEVEL_RE = re.compile(r"\((?:Level\s+)?(A{1,3})\)", re.IGNORECASE)


def extract_criterion_header_parts(heading_text: str) -> tuple[str, str, str | None] | None:
    """Extract (criterion_id, clean_title, level) from heading text, or None if not a criterion."""
    m_id = CRITERION_ID_RE.search(heading_text)
    if not m_id:
        return None
    criterion_id = m_id.group(1).strip()

    m_lvl = CRITERION_LEVEL_RE.search(heading_text)
    level = m_lvl.group(1).strip().upper() if m_lvl else None

    clean_title = re.sub(
        r"^(?:Success\s+Criterion\s+)?\d+\.\d+\.\d+\s*", "", heading_text, flags=re.IGNORECASE
    )
    clean_title = re.sub(
        r"\s*\((?:Level\s+)?(A{1,3})\)\s*$", "", clean_title, flags=re.IGNORECASE
    ).strip()

    return criterion_id, clean_title, level


class ParsedSection:
    """Canonical section extracted from official accessibility documentation."""

    def __init__(
        self,
        section_key: str,
        section_title: str,
        content: str,
        source_url: str,
        content_type: str = "normative_criterion",
        criterion_id: str | None = None,
        criterion_level: str | None = None,
        principle: str | None = None,
        guideline_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.section_key = section_key
        self.section_title = section_title
        self.content = content
        self.source_url = source_url
        self.content_type = content_type
        self.criterion_id = criterion_id
        self.criterion_level = criterion_level
        self.principle = principle
        self.guideline_id = guideline_id
        self.metadata = metadata or {}


def clean_html_tree(soup: BeautifulSoup) -> None:
    """Strip navigation, footers, scripts, styles, and non-content chrome."""
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Remove generic navigation and skip links
    for el in soup.find_all(
        class_=re.compile(r"(nav|menu|toc|breadcrumb|skip-link|pagination)", re.I)
    ):
        el.decompose()


def extract_clean_text(tag: Tag) -> str:
    """Extract clean whitespace-normalized text from an HTML subtree."""
    text = tag.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def parse_w3c_tr_wcag(html: str, base_url: str, source_key: str) -> list[ParsedSection]:
    """Parse single-page W3C WCAG 2.2 Recommendation HTML into structured criterion sections."""
    soup = BeautifulSoup(html, "html.parser")
    clean_html_tree(soup)

    sections: list[ParsedSection] = []
    current_principle: str | None = None
    current_guideline: str | None = None

    # WCAG TR documents structure criteria inside <section class="sc"> or under h3/h4 headings
    criterion_containers = soup.find_all(["section", "div"], class_=re.compile(r"\bsc\b"))

    if criterion_containers:
        for container in criterion_containers:
            heading = container.find(["h2", "h3", "h4", "h5"])
            if not heading:
                continue

            heading_text = heading.get_text(" ", strip=True)
            parts_info = extract_criterion_header_parts(heading_text)
            if not parts_info:
                continue

            criterion_id, section_title, level = parts_info

            # Infer principle and guideline from criterion ID
            parts = criterion_id.split(".")
            principle = PRINCIPLE_MAPPING.get(parts[0], f"Principle {parts[0]}")
            guideline_id = f"{parts[0]}.{parts[1]}"

            anchor_id = (
                container.get("id") or heading.get("id") or f"sc-{criterion_id.replace('.', '-')}"
            )
            section_url = urllib.parse.urljoin(base_url, f"#{anchor_id}")

            content_text = extract_clean_text(container)
            if not content_text:
                continue

            section_key = f"{source_key}_{criterion_id.replace('.', '_')}"
            sections.append(
                ParsedSection(
                    section_key=section_key,
                    section_title=f"{criterion_id} {section_title}"
                    + (f" (Level {level})" if level else ""),
                    content=content_text,
                    source_url=section_url,
                    content_type="normative_criterion",
                    criterion_id=criterion_id,
                    criterion_level=level,
                    principle=principle,
                    guideline_id=guideline_id,
                    metadata={
                        "source_key": source_key,
                        "anchor_id": str(anchor_id),
                        "heading": heading_text,
                    },
                )
            )
        return sections

    # Fallback to heading traversal if no explicit .sc containers
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        heading_text = heading.get_text(" ", strip=True)

        p_match = PRINCIPLE_HEADER_RE.search(heading_text)
        if p_match:
            current_principle = p_match.group(2).strip()
            continue

        g_match = GUIDELINE_HEADER_RE.search(heading_text)
        if g_match:
            current_guideline = g_match.group(1).strip()
            continue

        parts_info = extract_criterion_header_parts(heading_text)
        if parts_info:
            criterion_id, section_title, level = parts_info

            # Collect subsequent siblings until next heading
            content_nodes: list[str] = [heading_text]
            curr = heading.next_sibling
            while curr:
                if isinstance(curr, Tag) and curr.name in ["h1", "h2", "h3", "h4", "h5"]:
                    break
                if isinstance(curr, Tag):
                    text = extract_clean_text(curr)
                    if text:
                        content_nodes.append(text)
                elif isinstance(curr, NavigableString):
                    t = curr.strip()
                    if t:
                        content_nodes.append(t)
                curr = curr.next_sibling

            content_text = " ".join(content_nodes)
            anchor_id = heading.get("id") or f"sc-{criterion_id.replace('.', '-')}"
            section_url = urllib.parse.urljoin(base_url, f"#{anchor_id}")

            parts = criterion_id.split(".")
            principle = current_principle or PRINCIPLE_MAPPING.get(
                parts[0], f"Principle {parts[0]}"
            )
            guideline = current_guideline or f"{parts[0]}.{parts[1]}"

            section_key = f"{source_key}_{criterion_id.replace('.', '_')}"
            sections.append(
                ParsedSection(
                    section_key=section_key,
                    section_title=f"{criterion_id} {section_title}"
                    + (f" (Level {level})" if level else ""),
                    content=content_text,
                    source_url=section_url,
                    content_type="normative_criterion",
                    criterion_id=criterion_id,
                    criterion_level=level,
                    principle=principle,
                    guideline_id=guideline,
                    metadata={"source_key": source_key, "anchor_id": str(anchor_id)},
                )
            )

    return sections


def parse_generic_w3c_doc(
    html: str, base_url: str, source_key: str, default_content_type: str = "guidance"
) -> list[ParsedSection]:
    """Parse generic W3C documentation, APG patterns, or Understanding pages by top-level section headings."""
    soup = BeautifulSoup(html, "html.parser")
    clean_html_tree(soup)

    sections: list[ParsedSection] = []
    main_el = soup.find(["main", "article"]) or soup.body or soup

    headings = main_el.find_all(["h2", "h3"])
    for idx, heading in enumerate(headings):
        heading_text = heading.get_text(" ", strip=True)
        if len(heading_text) < 3 or heading_text.lower() in (
            "table of contents",
            "navigation",
            "references",
        ):
            continue

        anchor_id = heading.get("id") or f"sec-{idx}"
        section_url = urllib.parse.urljoin(base_url, f"#{anchor_id}")

        content_nodes: list[str] = [heading_text]
        curr = heading.next_sibling
        while curr:
            if isinstance(curr, Tag) and curr.name in ["h2", "h3"]:
                break
            if isinstance(curr, Tag):
                text = extract_clean_text(curr)
                if text:
                    content_nodes.append(text)
            elif isinstance(curr, NavigableString):
                t = curr.strip()
                if t:
                    content_nodes.append(t)
            curr = curr.next_sibling

        content = " ".join(content_nodes)
        if len(content) < 50:
            continue

        parts_info = extract_criterion_header_parts(heading_text)
        criterion_id = parts_info[0] if parts_info else None
        level = parts_info[2] if parts_info else None

        section_key = (
            f"{source_key}_{re.sub(r'[^a-zA-Z0-9]+', '_', heading_text).strip('_').lower()[:60]}"
        )
        sections.append(
            ParsedSection(
                section_key=section_key,
                section_title=heading_text,
                content=content,
                source_url=section_url,
                content_type=default_content_type,
                criterion_id=criterion_id,
                criterion_level=level,
                metadata={"source_key": source_key, "heading": heading_text},
            )
        )

    return sections


def parse_source_document(
    html: str, base_url: str, source_key: str, parser_type: str
) -> list[ParsedSection]:
    """Dispatch document parsing based on declared parser type in sources.yaml."""
    if parser_type == "w3c_tr_single":
        return parse_w3c_tr_wcag(html, base_url, source_key)
    elif parser_type == "w3c_wai_understanding":
        return parse_generic_w3c_doc(
            html, base_url, source_key, default_content_type="understanding"
        )
    elif parser_type == "w3c_wai_techniques":
        return parse_generic_w3c_doc(html, base_url, source_key, default_content_type="technique")
    elif parser_type == "w3c_wai_apg":
        return parse_generic_w3c_doc(html, base_url, source_key, default_content_type="pattern")
    else:
        return parse_generic_w3c_doc(html, base_url, source_key, default_content_type="guidance")
