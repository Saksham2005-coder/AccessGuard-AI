"""Integration tests for scan event recording, sequencing, and Server-Sent Events (SSE) streaming."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.user import User
from app.services.scan_event_service import (
    format_sse_event,
    get_scan_events_after,
    record_scan_event,
)


async def create_user_and_token(
    client: AsyncClient, email: str, password: str = "SecurePass123!"
) -> tuple[dict, str]:
    """Helper to register and login a test user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": email.split("@")[0]},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = login_resp.json()
    return data["user"], data["access_token"]


@pytest.mark.asyncio
async def test_scan_event_sequencing_and_retrieval(db_session: AsyncSession) -> None:
    """Verify scan events increment monotonically per scan and support replay cursors."""
    user = User(email="events.user@example.com", password_hash="hash", display_name="User")
    db_session.add(user)
    await db_session.flush()

    project = Project(owner_id=user.id, name="Project", base_domain="example.org")
    db_session.add(project)
    await db_session.flush()

    scan = Scan(
        project_id=project.id,
        requested_by=user.id,
        target_url="https://example.org/",
        status="running",
    )
    db_session.add(scan)
    await db_session.flush()

    # Record 3 events
    ev1 = await record_scan_event(db_session, scan.id, "stage_changed", {"stage": "validating"})
    ev2 = await record_scan_event(db_session, scan.id, "stage_changed", {"stage": "crawling"})
    ev3 = await record_scan_event(
        db_session, scan.id, "page_discovered", {"url": "https://example.org/about"}
    )

    assert ev1.sequence_number == 1
    assert ev2.sequence_number == 2
    assert ev3.sequence_number == 3

    # Replay after cursor 1
    events_after_1 = await get_scan_events_after(db_session, scan.id, after_sequence=1)
    assert len(events_after_1) == 2
    assert [e.sequence_number for e in events_after_1] == [2, 3]

    # Replay after cursor 3 (empty)
    events_after_3 = await get_scan_events_after(db_session, scan.id, after_sequence=3)
    assert len(events_after_3) == 0

    # Format SSE
    formatted = format_sse_event(ev1)
    assert "id: 1" in formatted
    assert "event: stage_changed" in formatted
    assert '"stage":"validating"' in formatted


@pytest.mark.asyncio
async def test_stream_scan_events_sse_endpoint(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verify SSE endpoint streams historical events and completes when scan is in terminal state."""
    _, token = await create_user_and_token(async_client, "sse.subscriber@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create project
    create_proj = await async_client.post(
        "/api/v1/projects",
        json={"name": "SSE Project", "base_domain": "sse.example.org"},
        headers=headers,
    )
    project_id = create_proj.json()["id"]

    # 2. Add terminal scan directly into DB
    user_result = await async_client.get("/api/v1/auth/me", headers=headers)
    user_id = user_result.json()["id"]

    import uuid

    scan = Scan(
        project_id=uuid.UUID(project_id),
        requested_by=uuid.UUID(user_id),
        target_url="https://sse.example.org/",
        status="completed",
    )
    db_session.add(scan)
    await db_session.flush()

    # Add 2 events
    await record_scan_event(db_session, scan.id, "stage_changed", {"stage": "crawling"})
    await record_scan_event(db_session, scan.id, "scan_completed", {"status": "completed"})
    await db_session.commit()

    # 3. Stream events from SSE endpoint
    response = await async_client.get(
        f"/api/v1/scans/{scan.id}/events",
        headers=headers,
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]
    content = response.text

    assert "event: stage_changed" in content
    assert "event: scan_completed" in content
    assert "id: 1" in content
    assert "id: 2" in content


@pytest.mark.asyncio
async def test_stream_scan_events_tenant_isolation(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verify User B cannot access User A's scan events (returns 404)."""
    _, token_alice = await create_user_and_token(async_client, "alice.sse@example.com")
    _, token_mallory = await create_user_and_token(async_client, "mallory.sse@example.com")

    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    headers_mallory = {"Authorization": f"Bearer {token_mallory}"}

    create_proj = await async_client.post(
        "/api/v1/projects",
        json={"name": "Alice Private SSE", "base_domain": "alice-sse.org"},
        headers=headers_alice,
    )
    project_id = create_proj.json()["id"]
    alice_id = (await async_client.get("/api/v1/auth/me", headers=headers_alice)).json()["id"]

    import uuid

    scan = Scan(
        project_id=uuid.UUID(project_id),
        requested_by=uuid.UUID(alice_id),
        target_url="https://alice-sse.org/",
        status="completed",
    )
    db_session.add(scan)
    await db_session.commit()

    # Mallory attempts to connect to Alice's scan events
    response = await async_client.get(
        f"/api/v1/scans/{scan.id}/events",
        headers=headers_mallory,
    )
    assert response.status_code == 404
