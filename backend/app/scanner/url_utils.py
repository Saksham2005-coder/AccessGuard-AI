"""URL parsing, normalization, and origin validation utilities for web crawling."""

import posixpath
import re
import urllib.parse

from app.core.errors import ValidationError
from app.domain.domain_utils import normalize_domain

# File extensions that represent non-HTML documents or static binary assets to ignore during HTML crawl
IGNORED_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",
        ".exe",
        ".dmg",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".bmp",
        ".tiff",
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
        ".mp4",
        ".webm",
        ".avi",
        ".mov",
        ".mkv",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".css",
        ".js",
        ".json",
        ".xml",
        ".rss",
        ".atom",
    }
)

# Reject control characters and unusual whitespace in URLs
CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def normalize_url(url: str, base_url: str | None = None) -> str:
    """Normalize and validate a URL for safe crawler navigation.

    Rules:
    - Resolves relative URLs if base_url is provided.
    - Requires http or https scheme.
    - Rejects credentials (userinfo) in netloc.
    - Normalizes hostname to lowercase punycode via IDNA.
    - Normalizes empty path to '/' and collapses dot-segments.
    - Removes default ports (80 for http, 443 for https).
    - Canonicalizes query parameters in deterministic alphabetical order.
    - Strips fragment identifiers entirely.
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string.")

    cleaned = url.strip()

    if CONTROL_CHAR_REGEX.search(cleaned):
        raise ValidationError("URL contains forbidden control characters.")

    if base_url:
        cleaned = urllib.parse.urljoin(base_url, cleaned)

    parsed = urllib.parse.urlsplit(cleaned)

    # 1. Scheme validation
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValidationError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only 'http' and 'https' are allowed."
        )

    # 2. Netloc validation
    netloc = parsed.netloc
    if not netloc:
        raise ValidationError("URL is missing a valid hostname.")

    if "@" in netloc:
        raise ValidationError("User credentials in URL authority are forbidden.")

    # Extract host and optional port
    port: int | None = None
    if ":" in netloc:
        host_part, port_str = netloc.rsplit(":", 1)
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError as e:
            raise ValidationError(f"Invalid network port in URL: {port_str}") from e
    else:
        host_part = netloc

    # Normalize host: if host_part is an IP literal, validate formatting; otherwise normalize via normalize_domain
    try:
        import ipaddress

        ipaddress.ip_address(host_part)
        normalized_host = host_part.lower()
    except ValueError:
        normalized_host = normalize_domain(host_part)

    # Reconstruct normalized netloc, stripping default ports
    if port is not None:
        if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
            final_netloc = normalized_host
        else:
            final_netloc = f"{normalized_host}:{port}"
    else:
        final_netloc = normalized_host

    # 3. Path normalization
    path = parsed.path or "/"
    # Collapse redundant slashes and relative traversals
    # posixpath.normpath removes trailing slash for non-root paths, so preserve it if original had it
    has_trailing_slash = path.endswith("/") and path != "/"
    normalized_path = posixpath.normpath(path)
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path
    if has_trailing_slash and not normalized_path.endswith("/"):
        normalized_path += "/"

    # 4. Query normalization
    normalized_query = ""
    if parsed.query:
        # Parse query params, sort deterministically, and re-encode
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        pairs.sort(key=lambda item: (item[0], item[1]))
        normalized_query = urllib.parse.urlencode(pairs)

    # 5. Fragment is explicitly discarded (empty string)
    return urllib.parse.urlunsplit((scheme, final_netloc, normalized_path, normalized_query, ""))


def get_url_origin(url: str) -> str:
    """Return the origin (scheme://host[:port]) of a normalized URL."""
    parsed = urllib.parse.urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_origin(url_a: str, url_b: str) -> bool:
    """Return True if both URLs share the exact same scheme, host, and port."""
    parsed_a = urllib.parse.urlsplit(url_a)
    parsed_b = urllib.parse.urlsplit(url_b)
    return (
        parsed_a.scheme.lower() == parsed_b.scheme.lower()
        and parsed_a.netloc.lower() == parsed_b.netloc.lower()
    )


def is_eligible_crawl_target(
    url: str,
    base_domain: str,
    allow_subdomains: bool = False,
) -> bool:
    """Determine whether a URL is an eligible target under project domain constraints.

    Rules:
    - Must have http or https scheme.
    - Host must match base_domain (or be a subdomain if allow_subdomains is True).
    - File extension must not be in the static binary asset blocklist.
    """
    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception:
        return False

    if parsed.scheme.lower() not in ("http", "https"):
        return False

    host = parsed.hostname
    if not host:
        return False
    host = host.lower()

    base = base_domain.lower()
    if allow_subdomains:
        if host != base and not host.endswith("." + base):
            return False
    elif host != base:
        return False

    # Check file extension
    path_lower = parsed.path.lower()
    _, ext = posixpath.splitext(path_lower)
    return ext not in IGNORED_EXTENSIONS
