"""SSRF prevention, DNS pre-resolution, and target safety policy engine."""

import ipaddress
import urllib.parse
from collections.abc import Callable, Coroutine
from typing import Any

import dns.asyncresolver
import dns.exception
import dns.resolver

from app.config import get_settings
from app.core.errors import PolicyViolationError
from app.core.logging import get_logger
from app.scanner.url_utils import normalize_url

logger = get_logger("target_policy")

# Well-known cloud provider instance metadata IPs
CLOUD_METADATA_IPS = frozenset(
    {
        "169.254.169.254",  # AWS EC2, GCP, Azure, OpenStack IMDS
        "100.100.100.200",  # Alibaba Cloud metadata
        "fd00:ec2::254",  # AWS IMDSv6
    }
)

# Standard default permitted ports
STANDARD_PORTS = frozenset({80, 443})

# Type alias for test DNS resolver injection: host -> list of IP address strings
HostResolverFunc = Callable[[str], Coroutine[Any, Any, list[str]]]
_injected_host_resolver: HostResolverFunc | None = None


def set_target_policy_resolver_override(resolver: HostResolverFunc | None) -> None:
    """Inject a mock resolver function for test isolation."""
    global _injected_host_resolver
    _injected_host_resolver = resolver


def classify_ip_address(ip_str: str, allow_loopback: bool = False) -> tuple[bool, str]:
    """Classify an IP address and determine whether it is safe for outbound navigation.

    Returns: (is_safe, reason_message)
    """
    try:
        ip = ipaddress.ip_address(ip_str.strip())
    except ValueError:
        return False, f"Invalid IP address format: '{ip_str}'"

    # Check for IPv4-mapped IPv6 address (e.g. ::ffff:127.0.0.1 or ::ffff:169.254.169.254)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    str_repr = str(ip)

    # Cloud metadata checks
    if str_repr in CLOUD_METADATA_IPS:
        return (
            False,
            f"Access to cloud instance metadata service ({str_repr}) is strictly forbidden.",
        )

    # Loopback checks
    if ip.is_loopback:
        if allow_loopback:
            return True, "Loopback allowed by test override"
        return False, f"Access to loopback address ({str_repr}) is forbidden."

    # Private RFC 1918 / ULA checks
    if ip.is_private:
        return False, f"Access to private internal network address ({str_repr}) is forbidden."

    # Link-local checks
    if ip.is_link_local:
        return False, f"Access to link-local address ({str_repr}) is forbidden."

    # Multicast checks
    if ip.is_multicast:
        return False, f"Access to multicast address ({str_repr}) is forbidden."

    # Reserved or unspecified checks (e.g. 0.0.0.0)
    if ip.is_reserved or ip.is_unspecified:
        return False, f"Access to reserved or unspecified address ({str_repr}) is forbidden."

    return True, "Public IP address verified"


async def default_resolve_host_ips(hostname: str, timeout: float = 3.0) -> list[str]:
    """Resolve both IPv4 (A) and IPv6 (AAAA) records for a hostname."""
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    resolved_ips: list[str] = []

    for record_type in ("A", "AAAA"):
        try:
            answers = await resolver.resolve(hostname, record_type)
            for rdata in answers:
                resolved_ips.append(rdata.address)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            continue
        except dns.exception.Timeout as e:
            raise PolicyViolationError(f"DNS lookup timed out for target host '{hostname}'.") from e
        except dns.exception.DNSException as e:
            logger.info("DNS resolution lookup note", host=hostname, type=record_type, error=str(e))
            continue

    return resolved_ips


async def resolve_and_validate_hostname(
    hostname: str,
    allow_loopback: bool = False,
) -> list[str]:
    """Resolve hostname and validate ALL returned A/AAAA IP answers against SSRF policy.

    Enforces:
    - Test-only loopback exception can NEVER be enabled in production environment.
    - If any returned IP is non-public, the entire host is rejected.
    """
    settings = get_settings()

    # CRITICAL PRODUCTION SAFETY GATE
    if allow_loopback and settings.APP_ENV.lower() == "production":
        raise PolicyViolationError(
            "Test-only loopback exception cannot be enabled in production environment."
        )

    # If hostname is already a raw IP literal
    try:
        ipaddress.ip_address(hostname)
        is_literal_ip = True
    except ValueError:
        is_literal_ip = False

    if is_literal_ip:
        is_safe, reason = classify_ip_address(hostname, allow_loopback=allow_loopback)
        if not is_safe:
            raise PolicyViolationError(reason, code="SSRF_TARGET_BLOCKED")
        return [hostname]

    # Rejection of explicit localhost strings unless loopback is allowed
    if hostname.lower() in ("localhost", "localhost.") and not allow_loopback:
        raise PolicyViolationError("Access to localhost is forbidden.", code="SSRF_TARGET_BLOCKED")

    # Perform DNS resolution
    resolver_fn = _injected_host_resolver or default_resolve_host_ips
    resolved_ips = await resolver_fn(hostname)

    if not resolved_ips:
        raise PolicyViolationError(
            f"Host '{hostname}' could not be resolved to any reachable IP address.",
            code="HOST_UNRESOLVABLE",
        )

    # Validate ALL answers (protect against mixed public/private DNS answers)
    for ip_str in resolved_ips:
        is_safe, reason = classify_ip_address(ip_str, allow_loopback=allow_loopback)
        if not is_safe:
            logger.warning(
                "SSRF target rejected",
                hostname=hostname,
                blocked_ip=ip_str,
                reason=reason,
            )
            raise PolicyViolationError(
                f"Target hostname '{hostname}' resolved to forbidden address ({ip_str}): {reason}",
                code="SSRF_TARGET_BLOCKED",
            )

    return resolved_ips


async def validate_target_url(
    url: str,
    verified_base_domain: str,
    allow_loopback: bool = False,
    allow_subdomains: bool = False,
    allowed_ports: set[int] | None = None,
) -> str:
    """Perform end-to-end target validation for a prospective scan URL.

    Checks:
    1. Normalizes URL syntax.
    2. Enforces HTTP/HTTPS protocol.
    3. Enforces permitted ports (default 80/443).
    4. Enforces verified domain matching.
    5. Resolves hostname and validates all IP answers against SSRF policy.
    """
    normalized = normalize_url(url)
    parsed = urllib.parse.urlsplit(normalized)

    # Protocol validation
    if parsed.scheme not in ("http", "https"):
        raise PolicyViolationError(
            f"URL scheme '{parsed.scheme}' is forbidden. Only HTTP and HTTPS are permitted.",
            code="INVALID_PROTOCOL",
        )

    # Port validation
    if allowed_ports is not None:
        permitted_ports = allowed_ports
    elif allow_loopback:
        permitted_ports = None  # Loopback test fixtures use ephemeral ports
    else:
        permitted_ports = STANDARD_PORTS

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if permitted_ports is not None and port not in permitted_ports:
        raise PolicyViolationError(
            f"Port {port} is not permitted for scanning. Allowed ports: {sorted(permitted_ports)}",
            code="PORT_NOT_ALLOWED",
        )

    # Domain match validation
    hostname = parsed.hostname
    if not hostname:
        raise PolicyViolationError("URL has no valid hostname.", code="INVALID_TARGET")

    base = verified_base_domain.lower()
    host_lower = hostname.lower()

    if allow_subdomains:
        if host_lower != base and not host_lower.endswith("." + base):
            raise PolicyViolationError(
                f"Target host '{hostname}' is not within verified domain '{verified_base_domain}'.",
                code="DOMAIN_MISMATCH",
            )
    elif host_lower != base:
        raise PolicyViolationError(
            f"Target host '{hostname}' does not match verified domain '{verified_base_domain}'.",
            code="DOMAIN_MISMATCH",
        )

    # SSRF IP pre-resolution validation
    await resolve_and_validate_hostname(hostname, allow_loopback=allow_loopback)

    return normalized
