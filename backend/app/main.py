"""FastAPI application factory, lifespan, middleware and route registration."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_v1_router
from app.api.v1.health import router as health_router
from app.config import Settings, get_settings
from app.core.errors import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import get_logger, setup_logging
from app.core.request_context import set_request_id

logger = get_logger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management handling startup and shutdown hooks."""
    settings = get_settings()
    setup_logging(settings.APP_ENV)
    logger.info(
        "AccessGuard AI starting up",
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
        llm_provider=settings.LLM_PROVIDER,
    )

    # Validate security constraints in production
    settings.validate_runtime_security()

    yield

    logger.info("AccessGuard AI shutting down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.APP_NAME,
        version=app_settings.APP_VERSION,
        description="Automated accessibility scanning, WCAG RAG, and human-approved remediation.",
        lifespan=lifespan,
        docs_url="/docs" if app_settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if app_settings.APP_ENV != "production" else None,
    )

    # 1. Request ID and Access Logging Middleware
    @app.middleware("http")
    async def request_id_and_logging_middleware(request: Request, call_next) -> Response:
        inbound_req_id = request.headers.get("X-Request-ID")
        req_id = set_request_id(inbound_req_id)
        start_time = time.perf_counter()

        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            request_id=req_id,
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=req_id,
        )
        return response

    # 2. CORS Middleware with Explicit Origin Allowlist
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # 3. Centralized Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 4. Root Health Probes (Direct access for container health checks)
    app.include_router(health_router)

    # 5. Versioned API Router
    app.include_router(api_v1_router, prefix=app_settings.API_V1_PREFIX)

    return app


app = create_app()
