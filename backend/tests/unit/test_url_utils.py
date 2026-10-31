"""Unit tests for URL normalization, origin comparison, and crawler target filtering."""

import pytest

from app.core.errors import ValidationError
from app.scanner.url_utils import (
    get_url_origin,
    is_eligible_crawl_target,
    is_same_origin,
    normalize_url,
)


def test_normalize_standard_urls() -> None:
    """Verify standard HTTP/HTTPS URLs are normalized cleanly."""
    assert normalize_url("https://example.com") == "https://example.com/"
    assert normalize_url("https://EXAMPLE.COM/about") == "https://example.com/about"
    assert normalize_url("http://example.com:80/path") == "http://example.com/path"
    assert normalize_url("https://example.com:443/path") == "https://example.com/path"
    assert normalize_url("https://example.com:8080/path") == "https://example.com:8080/path"


def test_normalize_strips_fragments_and_sorts_queries() -> None:
    """Verify fragment identifiers are discarded and queries are sorted deterministically."""
    url = "https://example.com/search?z=last&a=first#heading-1"
    assert normalize_url(url) == "https://example.com/search?a=first&z=last"


def test_normalize_path_traversal() -> None:
    """Verify dot-segment traversals are canonicalized safely."""
    assert normalize_url("https://example.com/a/b/../c") == "https://example.com/a/c"
    assert normalize_url("https://example.com/a/./b/") == "https://example.com/a/b/"


def test_normalize_relative_url_with_base() -> None:
    """Verify relative URLs are resolved against a base URL."""
    base = "https://example.com/catalog/items"
    assert normalize_url("/pricing", base_url=base) == "https://example.com/pricing"
    assert normalize_url("detail?id=5", base_url=base) == "https://example.com/catalog/detail?id=5"


def test_normalize_idna_hostname() -> None:
    """Verify internationalized hostnames are converted to punycode."""
    assert normalize_url("https://münchen.de/news") == "https://xn--mnchen-3ya.de/news"


@pytest.mark.parametrize(
    "invalid_url",
    [
        "",
        "   ",
        "file:///etc/passwd",
        "ftp://example.com/file.txt",
        "javascript:alert(1)",
        "data:text/html,<h1>Hello</h1>",
        "https://user:password@example.com/dashboard",
        "https://:8080/path",
        "https://example.com:999999/path",  # out of range port
    ],
)
def test_normalize_invalid_urls_raise_validation_error(invalid_url: str) -> None:
    """Verify invalid or forbidden schemes and formats raise ValidationError."""
    with pytest.raises(ValidationError):
        normalize_url(invalid_url)


def test_same_origin_comparison() -> None:
    """Verify origin comparisons correctly evaluate scheme, host, and port."""
    assert is_same_origin("https://example.com/a", "https://example.com/b?query=1")
    assert not is_same_origin("http://example.com/", "https://example.com/")
    assert not is_same_origin("https://example.com:8080/", "https://example.com:8081/")
    assert not is_same_origin("https://sub.example.com/", "https://example.com/")


def test_get_url_origin() -> None:
    """Verify origin extraction string format."""
    assert get_url_origin("https://example.com:8080/path?q=1") == "https://example.com:8080"
    assert get_url_origin("http://example.com/about") == "http://example.com"


def test_is_eligible_crawl_target_base_domain() -> None:
    """Verify eligibility filtering enforces domain boundary and ignores binary files."""
    base = "example.com"

    # Valid same-origin page
    assert is_eligible_crawl_target("https://example.com/blog", base)
    assert is_eligible_crawl_target("http://example.com/about", base)

    # Subdomain not allowed by default
    assert not is_eligible_crawl_target(
        "https://api.example.com/docs", base, allow_subdomains=False
    )
    assert is_eligible_crawl_target("https://api.example.com/docs", base, allow_subdomains=True)

    # Cross domain
    assert not is_eligible_crawl_target("https://evil.com/phish", base, allow_subdomains=True)

    # Ignored binary and media extensions
    assert not is_eligible_crawl_target("https://example.com/report.pdf", base)
    assert not is_eligible_crawl_target("https://example.com/image.png", base)
    assert not is_eligible_crawl_target("https://example.com/archive.zip", base)
    assert not is_eligible_crawl_target("https://example.com/style.css", base)
