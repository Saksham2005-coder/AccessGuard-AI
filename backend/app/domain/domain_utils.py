"""Domain normalization, validation, and IDNA handling."""

import re

from app.core.errors import ValidationError

# RFC 1035 / RFC 1123 label regex
LABEL_REGEX = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)


def normalize_domain(domain_input: str) -> str:
    """Normalize and validate domain name with IDNA/punycode support.

    Rules:
    - Strips whitespace and leading/trailing dots.
    - Converts to lowercase.
    - Encodes and decodes via IDNA for internationalized domain names.
    - Rejects IP addresses, schemes (http://), paths, ports, and userinfo.
    - Validates label lengths and character sets.
    """
    if not domain_input or not isinstance(domain_input, str):
        raise ValidationError("Domain name must be a non-empty string.")

    cleaned = domain_input.strip().lower()

    # Reject URLs passed where domain is expected
    if "://" in cleaned or "/" in cleaned or ":" in cleaned or "@" in cleaned:
        raise ValidationError(
            "Expected bare domain name (e.g. 'example.com'), not a URL or host:port combination."
        )

    # Strip trailing dot if present (FQDN notation)
    cleaned = cleaned.rstrip(".")

    if len(cleaned) > 253:
        raise ValidationError("Domain name exceeds maximum RFC length of 253 characters.")

    # Apply IDNA encoding / decoding for internationalized domains
    try:
        ascii_domain = cleaned.encode("idna").decode("ascii")
    except UnicodeError as e:
        raise ValidationError(f"Invalid domain encoding: {e}") from e

    labels = ascii_domain.split(".")
    if len(labels) < 2:
        raise ValidationError("Domain must contain at least a name and public top-level domain.")

    for label in labels:
        if not label:
            raise ValidationError("Domain contains empty labels.")
        if len(label) > 63:
            raise ValidationError(f"Domain label '{label}' exceeds maximum 63 characters.")
        if not LABEL_REGEX.match(label):
            raise ValidationError(f"Domain label '{label}' contains invalid characters.")

    # Reject pure numeric TLDs
    if labels[-1].isdigit():
        raise ValidationError("Top-level domain cannot be completely numeric.")

    return ascii_domain
