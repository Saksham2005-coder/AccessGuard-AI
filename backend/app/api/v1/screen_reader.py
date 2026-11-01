"""API endpoints for screen-reader-oriented page reading preview and semantic analysis."""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.screen_reader import ScreenReaderSimulationResponse
from app.services.screen_reader_service import get_or_create_page_simulation

router = APIRouter(tags=["screen-reader"])


@router.get(
    "/scans/{scan_id}/pages/{page_id}/screen-reader-simulation",
    response_model=ScreenReaderSimulationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_page_screen_reader_simulation(
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    force_refresh: bool = Query(default=False),
) -> ScreenReaderSimulationResponse:
    """Retrieve structured screen-reader-oriented reading preview, landmarks, and headings."""
    return await get_or_create_page_simulation(
        db,
        scan_id=scan_id,
        page_id=page_id,
        user_id=current_user.id,
        force_refresh=force_refresh,
    )
