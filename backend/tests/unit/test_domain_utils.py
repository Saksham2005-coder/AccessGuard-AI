"""Unit tests for domain normalization and validation."""

import pytest

from app.core.errors import ValidationError
from app.domain.domain_utils import normalize_domain


def test_normalize_valid_ascii_domain() -> None:
    """Test standard ASCII domain normalization."""
    assert normalize_domain("example.com") == "example.com"
    assert normalize_domain("SUB.EXAMPLE.CO.UK") == "sub.example.co.uk"
    assert normalize_domain("  portal-app.internal.io  ") == "portal-app.internal.io"


def test_normalize_domain_with_trailing_dot() -> None:
    """Test trailing root dot is stripped properly."""
    assert normalize_domain("example.com.") == "example.com"
    assert normalize_domain("app.service.org.") == "app.service.org"


def test_normalize_internationalized_domain_name() -> None:
    """Test IDNA punycode encoding for non-ASCII domain names."""
    # German umlaut domain
    assert normalize_domain("münchen.de") == "xn--mnchen-3ya.de"
    # Already punycode encoded
    assert normalize_domain("xn--mnchen-3ya.de") == "xn--mnchen-3ya.de"


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "   ",
        "https://example.com",
        "http://example.com/path",
        "example.com/path",
        "example.com:8080",
        "user:pass@example.com",
        "localhost",  # single label without TLD
        "192.168.1.1",  # pure numeric TLD
        "example..com",  # empty label
        "-example.com",  # leading hyphen
        "example-.com",  # trailing hyphen
        "exam$ple.com",  # special character
        "a" * 64 + ".com",  # label > 63 chars
        ("sub." * 50) + "com" * 40,  # exceeds 253 chars
    ],
)
def test_normalize_invalid_domains_raise_validation_error(invalid_input: str) -> None:
    """Test various invalid inputs trigger ValidationError."""
    with pytest.raises(ValidationError):
        normalize_domain(invalid_input)
