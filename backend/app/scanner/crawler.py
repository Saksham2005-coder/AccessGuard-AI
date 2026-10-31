"""Bounded breadth-first web crawler utilizing hardened Playwright browser contexts."""

import asyncio
import time
from collections import deque
from collections.abc import Callable, Coroutine
from typing import Any

from app.core.logging import get_logger
from app.scanner.browser import create_isolated_browser_context
from app.scanner.schemas import CrawledPage, CrawlOptions, CrawlSummary
from app.scanner.target_policy import validate_target_url
from app.scanner.url_utils import is_eligible_crawl_target, normalize_url

logger = get_logger("crawler")

PageCallback = Callable[[CrawledPage], Coroutine[Any, Any, None]]


async def crawl_website(
    start_url: str,
    base_domain: str,
    options: CrawlOptions | None = None,
    cancel_event: asyncio.Event | None = None,
    on_page_crawled: PageCallback | None = None,
) -> CrawlSummary:
    """Execute bounded breadth-first crawl of a verified target domain using Playwright."""
    opts = options or CrawlOptions()
    start_time = time.perf_counter()

    # 1. Pre-validate starting URL against target policy
    validated_start_url = await validate_target_url(
        start_url,
        base_domain,
        allow_loopback=opts.allow_loopback,
        allow_subdomains=opts.allow_subdomains,
        allowed_ports=opts.allowed_ports,
    )

    queue: deque[tuple[str, int]] = deque([(validated_start_url, 0)])
    seen_urls: set[str] = {validated_start_url}
    crawled_pages: list[CrawledPage] = []
    crawl_errors: list[str] = []
    is_complete = True

    logger.info(
        "Starting crawl execution",
        start_url=validated_start_url,
        base_domain=base_domain,
        max_pages=opts.max_pages,
        max_depth=opts.max_depth,
    )

    async with create_isolated_browser_context(
        allow_loopback=opts.allow_loopback,
        navigation_timeout_ms=opts.navigation_timeout_ms,
    ) as context:
        page = await context.new_page()

        while queue:
            # Check external cancellation signal
            if cancel_event and cancel_event.is_set():
                logger.info(
                    "Crawl operation cancelled by user signal", pages_so_far=len(crawled_pages)
                )
                is_complete = False
                break

            # Check scan deadline
            elapsed_seconds = time.perf_counter() - start_time
            if elapsed_seconds >= opts.max_duration_seconds:
                logger.info(
                    "Crawl reached maximum allotted duration deadline", elapsed_s=elapsed_seconds
                )
                is_complete = False
                break

            # Check maximum page limit
            if len(crawled_pages) >= opts.max_pages:
                logger.info("Crawl reached maximum page threshold", limit=opts.max_pages)
                break

            current_url, current_depth = queue.popleft()
            page_start = time.perf_counter()

            try:
                # Pre-validate navigation target
                await validate_target_url(
                    current_url,
                    base_domain,
                    allow_loopback=opts.allow_loopback,
                    allow_subdomains=opts.allow_subdomains,
                    allowed_ports=opts.allowed_ports,
                )

                response = await page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=opts.navigation_timeout_ms,
                )

                status_code = response.status if response else 200
                final_url = page.url

                # Verify final URL after potential HTTP/client redirect
                final_url = await validate_target_url(
                    final_url,
                    base_domain,
                    allow_loopback=opts.allow_loopback,
                    allow_subdomains=opts.allow_subdomains,
                    allowed_ports=opts.allowed_ports,
                )

                title = await page.title()
                html_content = await page.content()

                # Enforce response HTML size bounds
                if len(html_content.encode("utf-8", errors="replace")) > opts.max_html_bytes:
                    html_content = html_content[: opts.max_html_bytes]

                # Extract links from rendered DOM
                raw_hrefs = await page.evaluate(
                    """() => {
                        const anchors = Array.from(document.querySelectorAll('a[href]'));
                        return anchors.map(a => a.getAttribute('href')).filter(Boolean);
                    }"""
                )

                discovered_links: list[str] = []
                for href in raw_hrefs:
                    try:
                        normalized_link = normalize_url(href, base_url=final_url)
                        if is_eligible_crawl_target(
                            normalized_link,
                            base_domain,
                            allow_subdomains=opts.allow_subdomains,
                        ):
                            discovered_links.append(normalized_link)
                            if (
                                normalized_link not in seen_urls
                                and current_depth + 1 <= opts.max_depth
                            ):
                                seen_urls.add(normalized_link)
                                queue.append((normalized_link, current_depth + 1))
                    except Exception:
                        continue

                load_ms = round((time.perf_counter() - page_start) * 1000, 2)
                page_record = CrawledPage(
                    url=final_url,
                    status_code=status_code,
                    title=title,
                    html_content=html_content,
                    depth=current_depth,
                    links_discovered=discovered_links,
                    load_duration_ms=load_ms,
                )
                crawled_pages.append(page_record)

                if on_page_crawled:
                    await on_page_crawled(page_record)

                logger.info(
                    "Crawled page",
                    url=final_url,
                    depth=current_depth,
                    status=status_code,
                    links_found=len(discovered_links),
                    duration_ms=load_ms,
                )

            except Exception as e:
                load_ms = round((time.perf_counter() - page_start) * 1000, 2)
                err_msg = str(e)
                crawl_errors.append(f"Failed to crawl '{current_url}': {err_msg}")
                logger.warning(
                    "Error crawling page",
                    url=current_url,
                    depth=current_depth,
                    error=err_msg,
                )
                page_record = CrawledPage(
                    url=current_url,
                    status_code=None,
                    depth=current_depth,
                    load_duration_ms=load_ms,
                    error=err_msg,
                )
                crawled_pages.append(page_record)

    total_duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return CrawlSummary(
        start_url=validated_start_url,
        base_domain=base_domain,
        total_pages_crawled=len(crawled_pages),
        total_duration_ms=total_duration_ms,
        is_complete=is_complete,
        pages=crawled_pages,
        errors=crawl_errors,
    )
