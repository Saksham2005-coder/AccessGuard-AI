"""Central API v1 router mounting all domain route collections."""

from fastapi import APIRouter

from app.api.v1 import auth, health, knowledge, projects, scans

api_v1_router = APIRouter()

# Mount health checks, authentication, project management, scan, and knowledge routes
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(scans.router)
api_v1_router.include_router(knowledge.router)
