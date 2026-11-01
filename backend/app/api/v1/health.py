"""Health probe endpoints distinguishing liveness from readiness."""

import asyncio

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbDep, SettingsDep
from app.core.logging import get_logger

logger = get_logger("health")

router = APIRouter(tags=["health"])


class LivenessResponse(BaseModel):
    """Payload for liveness probe."""

    status: str = Field(default="alive", description="Process liveness state")


class DependencyCheck(BaseModel):
    """Status for an individual dependency."""

    status: str
    message: str | None = None


class ReadinessResponse(BaseModel):
    """Payload for readiness probe."""

    status: str = Field(..., description="Overall readiness state: ready or unready")
    environment: str
    version: str
    checks: dict[str, DependencyCheck]


async def probe_postgres(db: AsyncSession, timeout: float = 2.0) -> DependencyCheck:
    """Check database connectivity with bounded timeout and safe error reporting."""
    try:
        async with asyncio.timeout(timeout):
            await db.execute(text("SELECT 1"))
        return DependencyCheck(status="ok")
    except TimeoutError:
        logger.warning("Database readiness probe timed out")
        return DependencyCheck(status="unhealthy", message="Database connection timed out")
    except Exception as e:
        logger.warning("Database readiness probe failed", error=str(e))
        return DependencyCheck(status="unhealthy", message="Database connectivity check failed")


async def probe_redis(redis_url: str, timeout: float = 2.0) -> DependencyCheck:
    """Check Redis connectivity with bounded timeout and safe error reporting."""
    if not redis_url or redis_url in (":memory:", "mock", "disabled"):
        return DependencyCheck(status="ok")

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            redis_url,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
        )
        try:
            async with asyncio.timeout(timeout):
                pong = await client.ping()
                if pong:
                    return DependencyCheck(status="ok")
                return DependencyCheck(status="unhealthy", message="Redis ping failed")
        finally:
            await client.close()
    except TimeoutError:
        logger.warning("Redis readiness probe timed out")
        return DependencyCheck(status="unhealthy", message="Redis connection timed out")
    except Exception as e:
        logger.warning("Redis readiness probe failed", error=str(e))
        return DependencyCheck(status="unhealthy", message="Redis connectivity check failed")


async def probe_qdrant(qdrant_url: str, timeout: float = 2.0) -> DependencyCheck:
    """Check Qdrant vector database accessibility with bounded timeout and safe error reporting."""
    if not qdrant_url or qdrant_url in (":memory:", "memory"):
        return DependencyCheck(status="ok")

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=qdrant_url, timeout=int(timeout))
        client.collection_exists("wcag_knowledge")
        return DependencyCheck(status="ok")
    except TimeoutError:
        logger.warning("Qdrant readiness probe timed out")
        return DependencyCheck(status="unhealthy", message="Vector store connection timed out")
    except Exception as e:
        logger.warning("Qdrant readiness probe failed", error=str(e))
        return DependencyCheck(status="unhealthy", message="Vector store connectivity check failed")


@router.get("/health/live", response_model=LivenessResponse, summary="Liveness Probe")
async def health_live() -> LivenessResponse:
    """Return 200 OK indicating the application process is running."""
    return LivenessResponse(status="alive")


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def health_ready(
    settings: SettingsDep,
    response: Response,
    db: DbDep,
) -> ReadinessResponse:
    """Evaluate core dependency connectivity before accepting traffic."""
    checks: dict[str, DependencyCheck] = {}

    # Run probes concurrently with bounded timeouts
    db_check, redis_check, qdrant_check = await asyncio.gather(
        probe_postgres(db),
        probe_redis(settings.REDIS_URL),
        probe_qdrant(settings.QDRANT_URL),
        return_exceptions=False,
    )

    checks["database"] = db_check
    checks["redis"] = redis_check
    checks["qdrant"] = qdrant_check

    is_all_ok = all(check.status == "ok" for check in checks.values())

    if not is_all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        status_label = "unready"
    else:
        status_label = "ready"

    return ReadinessResponse(
        status=status_label,
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
        checks=checks,
    )
