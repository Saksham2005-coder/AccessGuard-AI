"""Scan management and Server-Sent Events (SSE) streaming API endpoints."""

import asyncio
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Header, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import CurrentUserDep, DbDep
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.models.scan import Scan
from app.schemas.auth import MessageResponse
from app.schemas.scan import ScanCreateRequest, ScanListResponse, ScanResponse
from app.services.project_service import get_project, get_project_verification_status
from app.services.scan_event_service import format_sse_event, get_scan_events_after
from app.services.scan_persistence_service import create_scan_record, get_scan
from app.workers.tasks import (
    execute_scan_pipeline,
    request_scan_cancellation,
    run_scan_task,
)

logger = get_logger("scan_api")

router = APIRouter(tags=["scans"])


@router.post(
    "/projects/{project_id}/scans",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scan(
    project_id: uuid.UUID,
    request: ScanCreateRequest,
    current_user: CurrentUserDep,
    db: DbDep,
    background_tasks: BackgroundTasks,
) -> ScanResponse:
    """Create a new scan job and enqueue background execution."""
    project, _ = await get_project(db, project_id, current_user.id)

    # Verify project domain has been verified
    is_verified, _ = await get_project_verification_status(db, project.id)
    if not is_verified:
        raise NotFoundError(
            f"Domain '{project.base_domain}' is not verified. "
            "Please complete DNS TXT verification before running a scan."
        )

    scan_config = {
        "max_pages": request.max_pages,
        "max_depth": request.max_depth,
    }

    scan = await create_scan_record(
        db,
        project=project,
        user=current_user,
        target_url=request.target_url,
        scan_config=scan_config,
    )
    await db.commit()

    # Enqueue background execution via Celery, falling back to asyncio background task if broker is offline
    try:
        run_scan_task.delay(str(scan.id))
        logger.info("Enqueued scan in Celery queue", scan_id=str(scan.id))
    except Exception as e:
        logger.warning(
            "Celery broker unreachable, dispatching in-process background task",
            scan_id=str(scan.id),
            error=str(e),
        )
        background_tasks.add_task(execute_scan_pipeline, scan.id)

    return ScanResponse.model_validate(scan)


@router.get(
    "/projects/{project_id}/scans",
    response_model=ScanListResponse,
)
async def list_project_scans(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ScanListResponse:
    """List all scans belonging to a project owned by the authenticated tenant."""
    await get_project(db, project_id, current_user.id)

    result = await db.execute(
        select(Scan).where(Scan.project_id == project_id).order_by(Scan.created_at.desc())
    )
    scans = result.scalars().all()
    items = [ScanResponse.model_validate(s) for s in scans]
    return ScanListResponse(items=items, total=len(items))


@router.get(
    "/scans/{scan_id}",
    response_model=ScanResponse,
)
async def get_scan_by_id(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> ScanResponse:
    """Retrieve details of a specific scan job."""
    scan = await get_scan(db, scan_id, current_user.id)
    return ScanResponse.model_validate(scan)


@router.post(
    "/scans/{scan_id}/cancel",
    response_model=MessageResponse,
)
async def cancel_scan(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> MessageResponse:
    """Request early cancellation of an active scan."""
    scan = await get_scan(db, scan_id, current_user.id)

    if scan.status in ("completed", "completed_with_errors", "failed", "cancelled"):
        return MessageResponse(message=f"Scan is already in terminal state '{scan.status}'.")

    request_scan_cancellation(scan_id)
    logger.info(
        "Cancellation requested for scan", scan_id=str(scan_id), user_id=str(current_user.id)
    )
    return MessageResponse(message="Scan cancellation request received.")


@router.get(
    "/scans/{scan_id}/events",
)
async def stream_scan_events(
    scan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
    last_event_id: int | None = Query(default=None),
    header_last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    """Stream real-time progress events using W3C Server-Sent Events (SSE).

    Supports:
    - Tenant authorization (User cannot stream another user's scan events).
    - Event replay starting after sequence cursor provided in Query or Last-Event-ID header.
    - Polling termination when scan reaches a terminal status.
    """
    # Verify tenant ownership
    await get_scan(db, scan_id, current_user.id)

    # Determine starting cursor
    cursor = 0
    if header_last_event_id and header_last_event_id.isdigit():
        cursor = int(header_last_event_id)
    elif last_event_id is not None:
        cursor = last_event_id

    async def event_generator() -> AsyncGenerator[str, None]:
        current_cursor = cursor
        terminal_states = {"completed", "completed_with_errors", "failed", "cancelled"}

        while True:
            # Fetch persisted events after cursor
            events = await get_scan_events_after(db, scan_id, after_sequence=current_cursor)
            for event in events:
                yield format_sse_event(event)
                current_cursor = event.sequence_number

            # Check scan status
            result = await db.execute(select(Scan.status).where(Scan.id == scan_id))
            status_val = result.scalar_one_or_none()

            if status_val in terminal_states:
                # Deliver any final events that arrived concurrently before ending stream
                final_events = await get_scan_events_after(
                    db, scan_id, after_sequence=current_cursor
                )
                for event in final_events:
                    yield format_sse_event(event)
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
