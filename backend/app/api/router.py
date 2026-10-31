"""Central API v1 router mounting all domain route collections."""

from fastapi import APIRouter

from app.api.v1 import auth, health, projects

api_v1_router = APIRouter()

# Mount health checks, authentication, and project management routes
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(projects.router)
