"""Centralized application exception definitions and response schemas."""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.request_context import get_request_id

logger = get_logger("errors")


class ErrorBody(BaseModel):
    """Payload representing standard error envelope."""

    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable explanation of error condition")
    request_id: str = Field(..., description="Unique request tracing identifier")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Structured contextual error details"
    )


class ErrorResponse(BaseModel):
    """Standard API error response wrapper."""

    error: ErrorBody


class AppException(Exception):
    """Base class for domain and application level errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    """Raised when an entity is not found or not accessible to user."""

    def __init__(
        self, message: str = "Resource not found", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class AuthenticationError(AppException):
    """Raised when authentication credentials are missing, invalid, or expired."""

    def __init__(
        self, message: str = "Authentication failed", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(AppException):
    """Raised when an authenticated user does not have permission for the resource."""

    def __init__(
        self, message: str = "Access forbidden", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationError(AppException):
    """Raised when business logic validation fails."""

    def __init__(
        self, message: str = "Validation error", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class PolicyViolationError(AppException):
    """Raised when scan target or patch policy fails security boundaries."""

    def __init__(
        self, message: str, code: str = "POLICY_VIOLATION", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ConflictError(AppException):
    """Raised when attempting to create a duplicate or conflicting resource."""

    def __init__(
        self, message: str = "Resource conflict", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class RateLimitError(AppException):
    """Raised when request rate limits are exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class InfrastructureUnavailableError(AppException):
    """Raised when downstream dependency (DB/Redis/Qdrant) is unreachable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    req_id = get_request_id()
    if exc.status_code >= 500:
        logger.error(
            "Application error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=req_id,
        )
    else:
        logger.info(
            "Client error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=req_id,
        )

    response_data = ErrorResponse(
        error=ErrorBody(
            code=exc.code,
            message=exc.message,
            request_id=req_id,
            details=exc.details,
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data.model_dump(),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI and Pydantic schema validation errors."""
    req_id = get_request_id()
    formatted_errors: dict[str, Any] = {}
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc not in ("body",))
        formatted_errors[field or "request"] = err["msg"]

    logger.info("Request schema validation failed", errors=formatted_errors, request_id=req_id)
    response_data = ErrorResponse(
        error=ErrorBody(
            code="VALIDATION_ERROR",
            message="Request parameters failed schema validation.",
            request_id=req_id,
            details=formatted_errors,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data.model_dump(),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions without leaking stack traces or internal state."""
    req_id = get_request_id()
    logger.exception("Unhandled server exception", exc_info=exc, request_id=req_id)
    response_data = ErrorResponse(
        error=ErrorBody(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please contact support.",
            request_id=req_id,
            details={},
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data.model_dump(),
    )
