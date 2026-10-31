"""Structured logging configuration using structlog."""

import logging
import re
import sys
from typing import Any

import structlog

from app.core.request_context import get_request_id

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "gemini_api_key",
    "groq_api_key",
    "jwt_secret_key",
}

API_KEY_PATTERNS = [
    re.compile(r"AIzaSy[A-Za-z0-9_-]{20,}"),
    re.compile(r"AQ\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"gsk_[A-Za-z0-9_-]{20,}"),
]


def scrub_sensitive_text(text: str) -> str:
    """Scrub raw API key patterns from text strings."""
    for pattern in API_KEY_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    return text


def censor_sensitive_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact dictionary keys and string values that match sensitive patterns."""
    clean: dict[str, Any] = {}
    for k, v in d.items():
        if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
            clean[k] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k] = censor_sensitive_dict(v)
        elif isinstance(v, str):
            clean[k] = scrub_sensitive_text(v)
        else:
            clean[k] = v
    return clean


def censor_sensitive_data(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Censor sensitive parameters and raw key patterns in log payloads."""
    for key, value in list(event_dict.items()):
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
        elif isinstance(value, dict):
            event_dict[key] = censor_sensitive_dict(value)
        elif isinstance(value, str):
            event_dict[key] = scrub_sensitive_text(value)
    return event_dict


def inject_request_id(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject current context request ID into all structured logs."""
    req_id = get_request_id()
    if req_id and "request_id" not in event_dict:
        event_dict["request_id"] = req_id
    return event_dict


def setup_logging(app_env: str = "development") -> None:
    """Configure structlog and standard logging based on application environment."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        inject_request_id,
        censor_sensitive_data,
    ]

    if app_env == "production":
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if app_env != "development" else logging.DEBUG,
    )


def get_logger(name: str = "accessguard") -> structlog.stdlib.BoundLogger:
    """Return a configured structlog bound logger."""
    return structlog.get_logger(name)
