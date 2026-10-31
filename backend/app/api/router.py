"""Central API v1 router mounting all domain route collections."""

from fastapi import APIRouter

from app.api.v1 import health

api_v1_router = APIRouter()

# Mount health checks within /api/v1
api_v1_router.include_router(health.router)
