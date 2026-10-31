"""Playwright browser lifecycle and hardened execution context manager."""

import asyncio
import contextlib
import urllib.parse
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    Route,
    async_playwright,
)

from app.core.logging import get_logger
from app.scanner.target_policy import classify_ip_address

logger = get_logger("browser_context")

# Canonical desktop viewport for deterministic auditing
DEFAULT_VIEWPORT = {"width": 1365, "height": 900}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 AccessGuard-Audit/1.0"
)

# Standard network timeouts in milliseconds
DEFAULT_NAVIGATION_TIMEOUT_MS = 15_000
DEFAULT_PAGE_TIMEOUT_MS = 25_000


class BrowserManager:
    """Manages ephemeral, hardened Playwright Chromium browser instances."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        current_loop = asyncio.get_running_loop()
        if self._loop != current_loop:
            self._loop = current_loop
            self._lock = asyncio.Lock()
            # Loop has changed (e.g. new test or worker thread), discard old references
            self._browser = None
            self._playwright = None
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get_browser(self) -> Browser:
        """Lazily initialize or retrieve shared headless Chromium browser process."""
        lock = self._get_lock()
        async with lock:
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            if self._browser is None or not self._browser.is_connected():
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-extensions",
                    ],
                )
                logger.info("Launched headless Chromium browser process")
            return self._browser

    async def close(self) -> None:
        """Close browser process and stop Playwright subsystem."""
        lock = self._get_lock()
        async with lock:
            if self._browser and self._browser.is_connected():
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Closed headless Chromium browser subsystem")


# Singleton browser process manager
browser_manager = BrowserManager()


async def _handle_route_interception(route: Route, allow_loopback: bool = False) -> None:
    """Validate each outbound subrequest and block forbidden schemes or SSRF destinations."""
    request = route.request
    req_url = request.url

    try:
        parsed = urllib.parse.urlsplit(req_url)
    except Exception:
        await route.abort()
        return

    scheme = parsed.scheme.lower()

    # Block data, file, ftp, javascript, and other non-HTTP schemes
    if scheme not in ("http", "https"):
        await route.abort()
        return

    # If host is an IP literal, validate directly
    host = parsed.hostname or ""
    try:
        is_safe, _ = classify_ip_address(host, allow_loopback=allow_loopback)
        if not is_safe:
            await route.abort()
            return
    except Exception:
        # Not an IP literal, continue with standard network request
        pass

    await route.continue_()


@asynccontextmanager
async def create_isolated_browser_context(
    allow_loopback: bool = False,
    navigation_timeout_ms: int = DEFAULT_NAVIGATION_TIMEOUT_MS,
    page_timeout_ms: int = DEFAULT_PAGE_TIMEOUT_MS,
) -> AsyncGenerator[BrowserContext, None]:
    """Provide a pristine, ephemeral, hardened BrowserContext for a single scan task."""
    browser = await browser_manager.get_browser()

    context = await browser.new_context(
        viewport=DEFAULT_VIEWPORT,
        user_agent=DEFAULT_USER_AGENT,
        locale="en-US",
        timezone_id="UTC",
        accept_downloads=False,
        bypass_csp=False,
        ignore_https_errors=False,
        java_script_enabled=True,
    )

    # Set default timeouts
    context.set_default_navigation_timeout(navigation_timeout_ms)
    context.set_default_timeout(page_timeout_ms)

    # Reject unexpected popups and secondary tabs beyond the primary crawling page
    primary_page_holder: list[object] = []

    async def _on_unexpected_page(new_page: object) -> None:
        if not primary_page_holder:
            primary_page_holder.append(new_page)
            return
        logger.warning(
            "Closed unexpected secondary window or popup tab",
            url=getattr(new_page, "url", ""),
        )
        with contextlib.suppress(Exception):
            await new_page.close()  # type: ignore[attr-defined]

    context.on("page", lambda p: asyncio.create_task(_on_unexpected_page(p)))

    # Intercept all outbound requests for SSRF and protocol safety
    await context.route(
        "**/*", lambda r: _handle_route_interception(r, allow_loopback=allow_loopback)
    )

    try:
        yield context
    finally:
        try:
            await context.close()
        except Exception as e:
            logger.info("Context close cleanup note", error=str(e))
