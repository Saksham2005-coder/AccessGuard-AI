"""Data schemas and transfer models for crawler pages and results."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class CrawledPage(BaseModel):
    """Structured capture of a crawled and rendered web page."""

    model_config = ConfigDict(from_attributes=True)

    url: str = Field(..., description="Canonical normalized URL")
    status_code: int | None = Field(default=None, description="HTTP response status code")
    title: str = Field(default="", description="Rendered document title")
    html_content: str = Field(default="", description="Rendered DOM inner HTML")
    depth: int = Field(default=0, description="BFS discovery depth from seed URL")
    links_discovered: list[str] = Field(
        default_factory=list, description="Outbound links extracted"
    )
    load_duration_ms: float = Field(
        default=0.0, description="Page render elapsed time in milliseconds"
    )
    error: str | None = Field(default=None, description="Navigation or render error if failed")


class CrawlSummary(BaseModel):
    """Aggregate outcome of a bounded web crawl execution."""

    model_config = ConfigDict(from_attributes=True)

    start_url: str
    base_domain: str
    total_pages_crawled: int
    total_duration_ms: float
    is_complete: bool
    pages: list[CrawledPage] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


@dataclass
class CrawlOptions:
    """Execution constraints and bounds for crawler runs."""

    max_pages: int = 20
    max_depth: int = 3
    max_duration_seconds: float = 180.0
    navigation_timeout_ms: int = 15_000
    allow_subdomains: bool = False
    allow_loopback: bool = False
    allowed_ports: set[int] | None = None
    max_html_bytes: int = 10 * 1024 * 1024  # 10MB limit per page
