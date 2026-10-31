"""FastAPI application entrypoint for AccessGuard AI."""

from fastapi import FastAPI

app = FastAPI(
    title="AccessGuard AI",
    version="0.1.0",
    description="Automated accessibility scanning, WCAG RAG, and human-approved remediation.",
)


@app.get("/health/live", tags=["health"])
async def health_live() -> dict[str, str]:
    """Liveness probe indicating process is running."""
    return {"status": "alive"}
