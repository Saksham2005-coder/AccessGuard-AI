"""Unit tests for bounded source fetcher and W3C document parser."""

from pathlib import Path

import pytest
import respx
from bs4 import BeautifulSoup

from app.core.errors import PolicyViolationError
from app.rag.fetcher import SourceFetcher
from app.rag.parser import (
    clean_html_tree,
    extract_clean_text,
    parse_source_document,
    parse_w3c_tr_wcag,
)


@pytest.mark.asyncio
async def test_fetcher_rejects_non_allowlisted_domain() -> None:
    """Verify fetcher enforces strict W3C official publisher domain boundaries."""
    fetcher = SourceFetcher()
    with pytest.raises(PolicyViolationError) as exc_info:
        await fetcher.fetch("https://attacker.com/malicious_guidelines.html")
    assert "not in the official W3C allowlist" in str(exc_info.value)
    assert exc_info.value.code == "DOMAIN_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_fetcher_rejects_insecure_http_protocol() -> None:
    """Verify fetcher enforces TLS (HTTPS) on all official resources."""
    fetcher = SourceFetcher()
    with pytest.raises(PolicyViolationError) as exc_info:
        await fetcher.fetch("http://www.w3.org/TR/WCAG22/")
    assert "must use HTTPS" in str(exc_info.value)
    assert exc_info.value.code == "INVALID_PROTOCOL"


@pytest.mark.asyncio
@respx.mock
async def test_fetcher_enforces_size_limit(tmp_path: Path) -> None:
    """Verify fetcher bounds download payload size."""
    oversized = b"A" * (1024 * 1024 + 10)  # 1MB + 10 bytes
    respx.get("https://www.w3.org/TR/WCAG22/").respond(200, content=oversized)

    fetcher = SourceFetcher(raw_storage_dir=tmp_path, max_bytes=1024 * 1024)
    with pytest.raises(PolicyViolationError) as exc_info:
        await fetcher.fetch("https://www.w3.org/TR/WCAG22/")
    assert "exceeds size limit" in str(exc_info.value)
    assert exc_info.value.code == "DOCUMENT_TOO_LARGE"


@pytest.mark.asyncio
@respx.mock
async def test_fetcher_caches_to_local_raw_storage(tmp_path: Path) -> None:
    """Verify successful fetch writes raw copy to disk and reuses on subsequent call."""
    html_content = "<html><body><h1>WCAG 2.2 Standard</h1></body></html>"
    respx.get("https://www.w3.org/TR/WCAG22/").respond(200, text=html_content)

    fetcher = SourceFetcher(raw_storage_dir=tmp_path)
    doc1 = await fetcher.fetch("https://www.w3.org/TR/WCAG22/", source_key="wcag_test")
    assert doc1.from_cache is False
    assert (tmp_path / "wcag_test.html").exists()

    # Second fetch should load from cache without HTTP request
    doc2 = await fetcher.fetch(
        "https://www.w3.org/TR/WCAG22/", source_key="wcag_test", use_cache=True
    )
    assert doc2.from_cache is True
    assert doc2.checksum == doc1.checksum


def test_clean_html_tree_removes_noise() -> None:
    """Verify scripts, styles, navigation, and footers are cleanly decomposed."""
    markup = """
    <html>
        <head><style>.ad { color: red; }</style></head>
        <body>
            <nav><a href="#top">Skip to content</a></nav>
            <main>
                <h1>Main Heading</h1>
                <p>Informative content.</p>
            </main>
            <footer><p>Copyright 2026</p></footer>
            <script>console.log("tracking");</script>
        </body>
    </html>
    """
    soup = BeautifulSoup(markup, "html.parser")
    clean_html_tree(soup)

    assert soup.find("nav") is None
    assert soup.find("footer") is None
    assert soup.find("script") is None
    assert soup.find("style") is None
    text = extract_clean_text(soup)
    assert "Main Heading Informative content." in text


def test_parse_w3c_tr_wcag_sections() -> None:
    """Verify parser extracts structured criteria with levels and principles."""
    sample_wcag = """
    <!DOCTYPE html>
    <html lang="en">
    <body>
        <h2>Principle 1 - Perceivable</h2>
        <h3>Guideline 1.1 Text Alternatives</h3>
        <section class="sc" id="non-text-content">
            <h4>1.1.1 Non-text Content (Level A)</h4>
            <p>All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.</p>
        </section>
        <section class="sc" id="contrast-minimum">
            <h4>1.4.3 Contrast (Minimum) (Level AA)</h4>
            <p>The visual presentation of text and images of text has a contrast ratio of at least 4.5:1.</p>
        </section>
        <h2>Principle 2 - Operable</h2>
        <section class="sc" id="keyboard">
            <h4>2.1.1 Keyboard (Level A)</h4>
            <p>All functionality of the content is operable through a keyboard interface.</p>
        </section>
    </body>
    </html>
    """
    sections = parse_w3c_tr_wcag(sample_wcag, "https://www.w3.org/TR/WCAG22/", "wcag22_rec")
    assert len(sections) == 3

    sc1 = sections[0]
    assert sc1.criterion_id == "1.1.1"
    assert sc1.criterion_level == "A"
    assert sc1.principle == "Perceivable"
    assert "Non-text Content" in sc1.section_title
    assert "https://www.w3.org/TR/WCAG22/#non-text-content" in sc1.source_url

    sc2 = sections[1]
    assert sc2.criterion_id == "1.4.3"
    assert sc2.criterion_level == "AA"
    assert sc2.principle == "Perceivable"

    sc3 = sections[2]
    assert sc3.criterion_id == "2.1.1"
    assert sc3.criterion_level == "A"
    assert sc3.principle == "Operable"


def test_parse_source_document_dispatcher() -> None:
    """Verify parser dispatcher routes correctly based on declared parser_type."""
    html = """
    <html>
        <body>
            <main>
                <h2>Button Pattern</h2>
                <p>A button is a widget that enables users to trigger an action or event.</p>
                <h2>Dialog (Modal) Pattern</h2>
                <p>A dialog is a window overlaid on either the primary window or another dialog window.</p>
            </main>
        </body>
    </html>
    """
    sections = parse_source_document(html, "https://www.w3.org/WAI/ARIA/apg/", "apg", "w3c_wai_apg")
    assert len(sections) == 2
    assert sections[0].content_type == "pattern"
    assert "Button Pattern" in sections[0].section_title
    assert "Dialog" in sections[1].section_title
