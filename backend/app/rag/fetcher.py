"""Bounded HTTP fetcher for official W3C accessibility documentation."""

import hashlib
import urllib.parse
from pathlib import Path

import httpx

from app.core.errors import PolicyViolationError
from app.core.logging import get_logger

logger = get_logger("rag_fetcher")

# Allowlisted official standards publisher domains
ALLOWED_SOURCE_DOMAINS = frozenset(
    {
        "w3.org",
        "www.w3.org",
    }
)

DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB per document


class FetchedDocument:
    """Container for downloaded document content and provenance metadata."""

    def __init__(
        self,
        url: str,
        content: str,
        checksum: str,
        content_type: str,
        from_cache: bool = False,
    ) -> None:
        self.url = url
        self.content = content
        self.checksum = checksum
        self.content_type = content_type
        self.from_cache = from_cache


class SourceFetcher:
    """Bounded, allowlisted fetcher for official WCAG specifications."""

    def __init__(
        self,
        raw_storage_dir: Path | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_bytes: int = MAX_RESPONSE_BYTES,
    ) -> None:
        self.raw_storage_dir = raw_storage_dir
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

        if self.raw_storage_dir:
            self.raw_storage_dir.mkdir(parents=True, exist_ok=True)

    def validate_source_url(self, url: str) -> None:
        """Enforce domain allowlist and HTTPS protocol."""
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https":
            raise PolicyViolationError(
                f"Knowledge source must use HTTPS protocol: '{url}'",
                code="INVALID_PROTOCOL",
            )
        hostname = (parsed.hostname or "").lower()
        if hostname not in ALLOWED_SOURCE_DOMAINS:
            raise PolicyViolationError(
                f"Knowledge source domain '{hostname}' is not in the official W3C allowlist.",
                code="DOMAIN_NOT_ALLOWED",
            )

    async def fetch(
        self, url: str, source_key: str | None = None, use_cache: bool = True
    ) -> FetchedDocument:
        """Fetch official documentation with bounds and local raw storage caching."""
        self.validate_source_url(url)

        # Check raw cache if storage directory configured
        cache_path: Path | None = None
        if self.raw_storage_dir and source_key:
            cache_path = self.raw_storage_dir / f"{source_key}.html"
            if use_cache and cache_path.exists():
                text = cache_path.read_text(encoding="utf-8")
                checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
                logger.info(
                    "Loaded knowledge source from raw cache",
                    source_key=source_key,
                    path=str(cache_path),
                )
                return FetchedDocument(
                    url=url,
                    content=text,
                    checksum=checksum,
                    content_type="text/html",
                    from_cache=True,
                )

        logger.info("Fetching knowledge source from official URL", url=url)
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_bytes = response.content
            if len(content_bytes) > self.max_bytes:
                raise PolicyViolationError(
                    f"Knowledge source content exceeds size limit ({len(content_bytes)} > {self.max_bytes} bytes).",
                    code="DOCUMENT_TOO_LARGE",
                )

            text = response.text
            checksum = hashlib.sha256(content_bytes).hexdigest()

            if cache_path:
                cache_path.write_text(text, encoding="utf-8")
                logger.info("Saved raw knowledge source to cache", path=str(cache_path))

            return FetchedDocument(
                url=str(response.url),
                content=text,
                checksum=checksum,
                content_type=response.headers.get("content-type", "text/html"),
                from_cache=False,
            )
