"""Security test suite validating SSRF protection, IP classification, and network safety boundaries."""

from collections.abc import Generator

import pytest

from app.config import get_settings
from app.core.errors import PolicyViolationError
from app.scanner.target_policy import (
    classify_ip_address,
    resolve_and_validate_hostname,
    set_target_policy_resolver_override,
    validate_target_url,
)


@pytest.fixture(autouse=True)
def clean_policy_resolver() -> Generator[None, None, None]:
    """Ensure mock resolver is reset after every test."""
    yield
    set_target_policy_resolver_override(None)


@pytest.mark.parametrize(
    ("ip_str", "description"),
    [
        ("127.0.0.1", "Standard IPv4 loopback"),
        ("127.0.0.2", "Non-standard IPv4 loopback block"),
        ("::1", "IPv6 loopback"),
        ("10.0.0.1", "RFC 1918 10/8 private range"),
        ("10.254.254.254", "RFC 1918 10/8 private range"),
        ("172.16.0.1", "RFC 1918 172.16/12 private range"),
        ("172.31.255.255", "RFC 1918 172.16/12 private range"),
        ("192.168.1.1", "RFC 1918 192.168/16 private range"),
        ("169.254.1.1", "IPv4 link-local address"),
        ("fe80::1", "IPv6 link-local address"),
        ("169.254.169.254", "Cloud IMDS instance metadata IP"),
        ("100.100.100.200", "Alibaba cloud metadata IP"),
        ("fd00:ec2::254", "AWS IMDSv6 instance metadata IP"),
        ("0.0.0.0", "IPv4 unspecified address"),
        ("::", "IPv6 unspecified address"),
        ("224.0.0.1", "IPv4 multicast address"),
        ("ff02::1", "IPv6 multicast address"),
        ("::ffff:127.0.0.1", "IPv4-mapped IPv6 loopback"),
        ("::ffff:169.254.169.254", "IPv4-mapped IPv6 cloud metadata"),
        ("::ffff:10.0.0.1", "IPv4-mapped IPv6 private IP"),
    ],
)
def test_blocked_ip_addresses(ip_str: str, description: str) -> None:
    """Verify all internal, private, reserved, and metadata IP representations are blocked."""
    is_safe, reason = classify_ip_address(ip_str, allow_loopback=False)
    assert not is_safe, (
        f"Expected {ip_str} ({description}) to be blocked, but was allowed: {reason}"
    )


@pytest.mark.parametrize(
    "public_ip",
    [
        "93.184.216.34",  # example.com
        "1.1.1.1",  # Cloudflare DNS
        "8.8.8.8",  # Google DNS
        "2606:2800:220:1:248:1893:25c8:1946",  # example.com IPv6
    ],
)
def test_public_ip_addresses_allowed(public_ip: str) -> None:
    """Verify genuinely public IP addresses pass classification."""
    is_safe, reason = classify_ip_address(public_ip)
    assert is_safe, f"Expected public IP {public_ip} to be safe: {reason}"


@pytest.mark.asyncio
async def test_hostname_resolving_to_private_ip_is_blocked() -> None:
    """Verify hostname resolving to private IP raises SSRF PolicyViolationError."""

    async def mock_dns(_host: str) -> list[str]:
        return ["10.0.0.50"]

    set_target_policy_resolver_override(mock_dns)

    with pytest.raises(PolicyViolationError) as exc_info:
        await resolve_and_validate_hostname("internal.corp.com")
    assert exc_info.value.code == "SSRF_TARGET_BLOCKED"


@pytest.mark.asyncio
async def test_mixed_public_private_dns_answers_rejected() -> None:
    """Verify host returning mixed public and private IPs is rejected (SSRF bypass defense)."""

    async def mock_dns(_host: str) -> list[str]:
        return ["93.184.216.34", "192.168.1.5"]

    set_target_policy_resolver_override(mock_dns)

    with pytest.raises(PolicyViolationError) as exc_info:
        await resolve_and_validate_hostname("mixed.example.com")
    assert exc_info.value.code == "SSRF_TARGET_BLOCKED"


@pytest.mark.asyncio
async def test_unresolvable_hostname_raises_error() -> None:
    """Verify hostname with zero DNS records fails validation."""

    async def mock_dns(_host: str) -> list[str]:
        return []

    set_target_policy_resolver_override(mock_dns)

    with pytest.raises(PolicyViolationError) as exc_info:
        await resolve_and_validate_hostname("nonexistent.invalid")
    assert exc_info.value.code == "HOST_UNRESOLVABLE"


@pytest.mark.asyncio
async def test_loopback_exception_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify production environment gate strictly forbids allow_loopback=True."""
    settings = get_settings()
    monkeypatch.setattr(settings, "APP_ENV", "production")

    with pytest.raises(PolicyViolationError) as exc_info:
        await resolve_and_validate_hostname("localhost", allow_loopback=True)

    assert "production environment" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_target_url_non_standard_ports_rejected() -> None:
    """Verify scan target attempting to access database/internal service ports is rejected."""
    # Attempting to scan Redis or PostgreSQL port
    with pytest.raises(PolicyViolationError) as exc_redis:
        await validate_target_url("http://example.com:6379", "example.com")
    assert exc_redis.value.code == "PORT_NOT_ALLOWED"

    with pytest.raises(PolicyViolationError) as exc_pg:
        await validate_target_url("http://example.com:5432", "example.com")
    assert exc_pg.value.code == "PORT_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_target_url_domain_mismatch_rejected() -> None:
    """Verify target URL host that does not match verified base domain is rejected."""
    with pytest.raises(PolicyViolationError) as exc_mismatch:
        await validate_target_url("https://unverified.com/home", "example.com")
    assert exc_mismatch.value.code == "DOMAIN_MISMATCH"
