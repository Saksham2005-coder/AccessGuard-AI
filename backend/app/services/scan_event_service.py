"""Scan event persistence, sequencing, and Server-Sent Events formatting."""

import json
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.scan_event import ScanEvent

logger = get_logger("scan_events")


async def record_scan_event(
    db: AsyncSession,
    scan_id: uuid.UUID,
    event_type: str,
    payload: dict[str, Any],
) -> ScanEvent:
    """Record an ordered progress event for a scan job."""
    # Determine the next sequence number for this scan
    seq_query = select(func.coalesce(func.max(ScanEvent.sequence_number), 0)).where(
        ScanEvent.scan_id == scan_id
    )
    result = await db.execute(seq_query)
    current_max = result.scalar_one()
    next_sequence = current_max + 1

    event = ScanEvent(
        scan_id=scan_id,
        sequence_number=next_sequence,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)

    logger.debug(
        "Recorded scan progress event",
        scan_id=str(scan_id),
        sequence=next_sequence,
        event_type=event_type,
    )
    return event


async def get_scan_events_after(
    db: AsyncSession,
    scan_id: uuid.UUID,
    after_sequence: int = 0,
) -> list[ScanEvent]:
    """Retrieve ordered scan events after a given sequence cursor for replay."""
    query = (
        select(ScanEvent)
        .where(
            ScanEvent.scan_id == scan_id,
            ScanEvent.sequence_number > after_sequence,
        )
        .order_by(ScanEvent.sequence_number.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


def format_sse_event(event: ScanEvent) -> str:
    """Format a ScanEvent into standard W3C Server-Sent Events protocol payload."""
    payload_str = json.dumps(event.payload, separators=(",", ":"))
    return f"id: {event.sequence_number}\nevent: {event.event_type}\ndata: {payload_str}\n\n"
