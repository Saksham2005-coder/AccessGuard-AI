"""Scanner engine: URL normalization, SSRF target policy, and Playwright crawler."""

from app.scanner.browser import BrowserManager, browser_manager, create_isolated_browser_context
from app.scanner.crawler import crawl_website
from app.scanner.schemas import CrawledPage, CrawlOptions, CrawlSummary
from app.scanner.target_policy import (
    classify_ip_address,
    resolve_and_validate_hostname,
    set_target_policy_resolver_override,
    validate_target_url,
)
from app.scanner.url_utils import (
    is_eligible_crawl_target,
    is_same_origin,
    normalize_url,
)

__all__ = [
    "BrowserManager",
    "CrawlOptions",
    "CrawlSummary",
    "CrawledPage",
    "browser_manager",
    "classify_ip_address",
    "crawl_website",
    "create_isolated_browser_context",
    "is_eligible_crawl_target",
    "is_same_origin",
    "normalize_url",
    "resolve_and_validate_hostname",
    "set_target_policy_resolver_override",
    "validate_target_url",
]
