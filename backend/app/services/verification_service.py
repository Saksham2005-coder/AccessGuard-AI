"""DNS TXT record verification service for establishing domain control."""

import secrets
from collections.abc import Callable, Coroutine
from datetime import timedelta
from typing import Any

import dns.asyncresolver
import dns.exception
import dns.resolver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.base import ensure_utc, utc_now
from app.db.models.domain_verification import ProjectDomainVerification
from app.db.models.project import Project

logger = get_logger("verification_service")

# Type alias for injected test DNS resolver: domain -> list[str]
DNSResolverFunc = Callable[[str], Coroutine[Any, Any, list[str]]]

_injected_resolver: DNSResolverFunc | None = None


def set_dns_resolver_override(resolver: DNSResolverFunc | None) -> None:
    """Inject a mock resolver function for test isolation."""
    global _injected_resolver
    _injected_resolver = resolver


async def default_resolve_txt(record_name: str, timeout: float = 3.0) -> list[str]:
    """Resolve DNS TXT records using dnspython with bounded network timeout."""
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    try:
        answers = await resolver.resolve(record_name, "TXT")
        results: list[str] = []
        for rdata in answers:
            # Each rdata string is a sequence of bytes
            txt_strings = [b.decode("utf-8", errors="replace") for b in rdata.strings]
            results.append("".join(txt_strings))
        return results
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
    except dns.exception.Timeout as e:
        raise ValidationError("DNS lookup timed out. Please try verification again.") from e
    except dns.exception.DNSException as e:
        logger.info("DNS resolution error", record=record_name, error=str(e))
        return []


def generate_verification_token() -> str:
    """Generate cryptographically secure verification token (256-bit entropy)."""
    return secrets.token_urlsafe(32)


def get_verification_record_name(domain: str) -> str:
    """Return the canonical DNS TXT record name to be configured by the domain owner."""
    return f"_accessguard-verification.{domain}"


def get_expected_txt_value(token: str) -> str:
    """Return the expected TXT record value for token match."""
    return f"accessguard-verification={token}"


async def create_domain_verification(
    db: AsyncSession, project: Project, expiry_hours: int = 72
) -> ProjectDomainVerification:
    """Create a new domain verification challenge token."""
    token = generate_verification_token()
    now = utc_now()
    expires_at = now + timedelta(hours=expiry_hours)

    verification = ProjectDomainVerification(
        project_id=project.id,
        domain=project.base_domain,
        verification_token=token,
        status="pending",
        expires_at=expires_at,
    )
    db.add(verification)
    await db.flush()
    await db.refresh(verification)

    logger.info(
        "Created domain verification token",
        project_id=str(project.id),
        domain=project.base_domain,
        verification_id=str(verification.id),
    )
    return verification


async def verify_domain_txt_record(
    db: AsyncSession, project: Project
) -> tuple[bool, ProjectDomainVerification, str]:
    """Resolve DNS TXT records and check for valid verification token match.

    Returns: (is_verified, verification_record, message)
    """
    # 1. Fetch latest pending or verified verification record
    result = await db.execute(
        select(ProjectDomainVerification)
        .where(ProjectDomainVerification.project_id == project.id)
        .order_by(ProjectDomainVerification.created_at.desc())
        .limit(1)
    )
    verification = result.scalar_one_or_none()

    if verification is None:
        raise NotFoundError(
            "No verification challenge found for this project. Please generate one."
        )

    # Check if already verified
    if verification.status == "verified":
        return True, verification, "Domain is already verified."

    now = utc_now()
    if ensure_utc(verification.expires_at) <= now:
        verification.status = "expired"
        await db.flush()
        return False, verification, "Verification token has expired. Please generate a new token."

    record_name = get_verification_record_name(verification.domain)
    expected_value = get_expected_txt_value(verification.verification_token)

    # 2. Resolve TXT records using injected resolver or default
    resolve_fn = _injected_resolver or default_resolve_txt
    txt_records = await resolve_fn(record_name)

    logger.info(
        "DNS TXT lookup completed",
        record_name=record_name,
        records_found=len(txt_records),
    )

    # Check for exact token match
    matched = any(expected_value == record.strip() for record in txt_records)

    if matched:
        verification.status = "verified"
        verification.verified_at = utc_now()
        await db.flush()
        logger.info(
            "Domain verified successfully", project_id=str(project.id), domain=verification.domain
        )
        return True, verification, "Domain control verified successfully."

    return (
        False,
        verification,
        (
            f"Verification TXT record not found at '{record_name}'. "
            f"Expected TXT value '{expected_value}'."
        ),
    )
