"""Request context management and request ID tracking."""

import uuid
from contextvars import ContextVar

_request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Retrieve current request ID from context, or empty string if unset."""
    return _request_id_ctx_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set the current request ID in context. Generates a new ID if none provided."""
    req_id = request_id or f"req_{uuid.uuid4().hex[:16]}"
    _request_id_ctx_var.set(req_id)
    return req_id
