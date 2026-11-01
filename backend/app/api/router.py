"""Central API v1 router mounting all domain route collections."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    findings,
    github,
    health,
    investigations,
    keyboard,
    knowledge,
    projects,
    regression,
    remediations,
    scans,
    screen_reader,
)

api_v1_router = APIRouter()

# Mount health checks, auth, projects, scans, findings, knowledge, remediations, investigations, screen reader, keyboard, regression, and github routes
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(scans.router)
api_v1_router.include_router(findings.router)
api_v1_router.include_router(knowledge.router)
api_v1_router.include_router(remediations.router)
api_v1_router.include_router(investigations.router)
api_v1_router.include_router(screen_reader.router)
api_v1_router.include_router(keyboard.router)
api_v1_router.include_router(regression.router)
api_v1_router.include_router(github.router)


