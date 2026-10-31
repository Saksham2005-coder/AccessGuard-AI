"""Integration tests for Playwright crawler using a local HTTP fixture website server."""

import asyncio
import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.scanner.crawler import crawl_website
from app.scanner.schemas import CrawlOptions


class FixtureWebsiteHandler(BaseHTTPRequestHandler):
    """Deterministic HTTP fixture website simulating complex linking structures."""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress standard HTTP server request logs in test output."""

    def do_GET(self) -> None:
        """Serve deterministic HTML pages based on path."""
        path = self.path.split("?")[0]

        if path == "/":
            body = """<!DOCTYPE html>
            <html lang="en">
            <head><title>Home Page</title></head>
            <body>
                <h1>Welcome to AccessGuard Fixture</h1>
                <a href="/about">About Us</a>
                <a href="/pricing">Pricing</a>
                <a href="/deep-1">Deep Link 1</a>
                <a href="https://external-untrusted.com/phish">External Link</a>
                <a href="/document.pdf">Download Brochure</a>
            </body>
            </html>"""
            status = 200
        elif path == "/about":
            body = """<!DOCTYPE html>
            <html lang="en">
            <head><title>About Page</title></head>
            <body>
                <h1>About Us</h1>
                <a href="/">Back Home</a>
                <a href="/team">Our Team</a>
            </body>
            </html>"""
            status = 200
        elif path == "/pricing":
            body = """<!DOCTYPE html>
            <html lang="en">
            <head><title>Pricing Page</title></head>
            <body>
                <h1>Pricing Plans</h1>
                <a href="/">Back Home</a>
            </body>
            </html>"""
            status = 200
        elif path == "/team":
            body = """<!DOCTYPE html>
            <html lang="en">
            <head><title>Team Page</title></head>
            <body>
                <h1>Engineering Team</h1>
                <a href="/about">Back to About</a>
            </body>
            </html>"""
            status = 200
        elif path == "/deep-1":
            body = """<!DOCTYPE html>
            <html lang="en"><head><title>Deep 1</title></head>
            <body><a href="/deep-2">Go to Deep 2</a></body></html>"""
            status = 200
        elif path == "/deep-2":
            body = """<!DOCTYPE html>
            <html lang="en"><head><title>Deep 2</title></head>
            <body><a href="/deep-3">Go to Deep 3</a></body></html>"""
            status = 200
        elif path == "/deep-3":
            body = """<!DOCTYPE html>
            <html lang="en"><head><title>Deep 3</title></head>
            <body><a href="/deep-4">Go to Deep 4</a></body></html>"""
            status = 200
        elif path == "/deep-4":
            body = """<!DOCTYPE html>
            <html lang="en"><head><title>Deep 4</title></head>
            <body>Final Deep Page</body></html>"""
            status = 200
        elif path == "/circular":
            body = """<!DOCTYPE html>
            <html lang="en"><head><title>Circular</title></head>
            <body><a href="/circular">Self Loop</a></body></html>"""
            status = 200
        else:
            body = "<html><body>404 Not Found</body></html>"
            status = 404

        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


@pytest.fixture(scope="module")
def fixture_server() -> Generator[tuple[str, int], None, None]:
    """Start local threaded HTTP server on loopback interface with ephemeral OS port."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureWebsiteHandler)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", port

    server.shutdown()
    server.server_close()


@pytest.mark.asyncio
async def test_crawler_discovers_same_origin_pages(fixture_server: tuple[str, int]) -> None:
    """Verify crawler traverses internal links, extracts HTML, and bounds to verified domain."""
    base_url, port = fixture_server

    options = CrawlOptions(
        max_pages=10,
        max_depth=3,
        allow_loopback=True,
        allowed_ports={port},
        navigation_timeout_ms=5000,
    )

    summary = await crawl_website(
        start_url=base_url + "/",
        base_domain="127.0.0.1",
        options=options,
    )

    assert summary.is_complete is True
    assert summary.total_pages_crawled >= 3

    crawled_urls = [p.url for p in summary.pages]
    # Internal pages should be visited
    assert any("/about" in u for u in crawled_urls)
    assert any("/pricing" in u for u in crawled_urls)

    # External domain must NOT be crawled
    assert not any("external-untrusted.com" in u for u in crawled_urls)

    # Binary file must NOT be crawled
    assert not any("document.pdf" in u for u in crawled_urls)

    # Titles and HTML should be extracted
    home_page = next(p for p in summary.pages if p.url.endswith("/"))
    assert home_page.title == "Home Page"
    assert "Welcome to AccessGuard Fixture" in home_page.html_content


@pytest.mark.asyncio
async def test_crawler_enforces_max_pages_limit(fixture_server: tuple[str, int]) -> None:
    """Verify crawler stops promptly when max_pages limit is reached."""
    base_url, port = fixture_server

    options = CrawlOptions(
        max_pages=2,
        max_depth=5,
        allow_loopback=True,
        allowed_ports={port},
    )

    summary = await crawl_website(
        start_url=base_url + "/",
        base_domain="127.0.0.1",
        options=options,
    )

    assert summary.total_pages_crawled == 2


@pytest.mark.asyncio
async def test_crawler_enforces_max_depth_limit(fixture_server: tuple[str, int]) -> None:
    """Verify crawler halts expansion when max_depth bound is exceeded."""
    base_url, port = fixture_server

    # Depth 0: /deep-1 -> Depth 1: /deep-2 -> Depth 2: /deep-3 -> Depth 3: /deep-4
    options = CrawlOptions(
        max_pages=10,
        max_depth=1,  # Only depth 0 and depth 1 allowed
        allow_loopback=True,
        allowed_ports={port},
    )

    summary = await crawl_website(
        start_url=base_url + "/deep-1",
        base_domain="127.0.0.1",
        options=options,
    )

    crawled_paths = [p.url.split(f":{port}")[1] for p in summary.pages]
    assert "/deep-1" in crawled_paths
    assert "/deep-2" in crawled_paths
    # /deep-3 would be depth 2, which exceeds max_depth=1
    assert "/deep-3" not in crawled_paths


@pytest.mark.asyncio
async def test_crawler_handles_circular_links(fixture_server: tuple[str, int]) -> None:
    """Verify circular links do not cause infinite crawling loops."""
    base_url, port = fixture_server

    options = CrawlOptions(
        max_pages=5,
        max_depth=3,
        allow_loopback=True,
        allowed_ports={port},
    )

    summary = await crawl_website(
        start_url=base_url + "/circular",
        base_domain="127.0.0.1",
        options=options,
    )

    assert summary.total_pages_crawled == 1


@pytest.mark.asyncio
async def test_crawler_cancellation(fixture_server: tuple[str, int]) -> None:
    """Verify external cancellation event halts crawler immediately."""
    base_url, port = fixture_server

    cancel_event = asyncio.Event()
    cancel_event.set()  # Signal cancellation immediately

    options = CrawlOptions(
        max_pages=10,
        allow_loopback=True,
        allowed_ports={port},
    )

    summary = await crawl_website(
        start_url=base_url + "/",
        base_domain="127.0.0.1",
        options=options,
        cancel_event=cancel_event,
    )

    assert summary.is_complete is False
    assert summary.total_pages_crawled == 0
