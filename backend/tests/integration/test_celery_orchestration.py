"""Integration tests for background scan pipeline orchestration, stage transitions, and cancellation."""

import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import utc_now
from app.db.models.domain_verification import ProjectDomainVerification
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_event import ScanEvent
from app.db.models.user import User
from app.scanner.target_policy import set_target_policy_resolver_override
from app.workers.celery_app import celery_app
from app.workers.tasks import (
    execute_scan_pipeline,
    request_scan_cancellation,
)


class OrchestrationFixtureHandler(BaseHTTPRequestHandler):
    """Simple HTTP fixture for scan orchestration tests."""

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        body = """<!DOCTYPE html>
        <html lang="en">
        <head><title>Orchestration App</title></head>
        <body>
            <h1>Accessible App Header</h1>
            <p>Welcome to the tested app.</p>
        </body>
        </html>"""
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


@pytest.fixture(scope="module")
def orch_fixture_server() -> Generator[tuple[str, int], None, None]:
    """Start local HTTP server on loopback interface with ephemeral OS port."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), OrchestrationFixtureHandler)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", port

    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def clean_resolver() -> Generator[None, None, None]:
    yield
    set_target_policy_resolver_override(None)


@pytest.mark.asyncio
async def test_celery_app_configuration() -> None:
    """Verify Celery application adheres to blueprint conventions."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.worker_prefetch_multiplier == 1


@pytest.mark.asyncio
async def test_execute_scan_pipeline_success(
    db_session: AsyncSession,
    orch_fixture_server: tuple[str, int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify end-to-end scan execution transitions through all stages and records progress events."""
    base_url, port = orch_fixture_server
    settings = get_settings()
    monkeypatch.setattr(settings, "TEST_ALLOW_LOOPBACK", True)

    # 1. Create user, project, and mark domain verified
    user = User(email="orch.user@example.com", password_hash="hash", display_name="Orchestrator")
    db_session.add(user)
    await db_session.flush()

    project = Project(owner_id=user.id, name="Orch Test App", base_domain="127.0.0.1")
    db_session.add(project)
    await db_session.flush()

    verification = ProjectDomainVerification(
        project_id=project.id,
        domain="127.0.0.1",
        verification_token="token_123",
        status="verified",
        verified_at=utc_now(),
        expires_at=utc_now(),
    )
    db_session.add(verification)
    await db_session.flush()

    # 2. Create Scan
    scan = Scan(
        project_id=project.id,
        requested_by=user.id,
        target_url=base_url + "/",
        status="pending",
        config={"max_pages": 3, "max_depth": 1},
    )
    db_session.add(scan)
    await db_session.commit()

    # 3. Execute pipeline
    await execute_scan_pipeline(scan.id, db=db_session)

    # 4. Verify scan terminal status
    await db_session.refresh(scan)
    assert scan.status == "completed"
    assert scan.started_at is not None
    assert scan.completed_at is not None
    assert scan.total_pages >= 1
    assert scan.pages_succeeded >= 1

    # 5. Verify events recorded
    events_res = await db_session.execute(
        select(ScanEvent)
        .where(ScanEvent.scan_id == scan.id)
        .order_by(ScanEvent.sequence_number.asc())
    )
    events = events_res.scalars().all()
    event_types = [e.event_type for e in events]

    assert "stage_changed" in event_types
    assert "scan_completed" in event_types


@pytest.mark.asyncio
async def test_execute_scan_pipeline_unverified_domain_fails(
    db_session: AsyncSession,
) -> None:
    """Verify scan fails immediately if target project base domain is not verified."""
    user = User(email="unverified.user@example.com", password_hash="hash", display_name="User")
    db_session.add(user)
    await db_session.flush()

    project = Project(owner_id=user.id, name="Unverified App", base_domain="unverified.com")
    db_session.add(project)
    await db_session.flush()

    # No verification record -> unverified
    scan = Scan(
        project_id=project.id,
        requested_by=user.id,
        target_url="https://unverified.com/",
        status="pending",
    )
    db_session.add(scan)
    await db_session.commit()

    await execute_scan_pipeline(scan.id, db=db_session)

    await db_session.refresh(scan)
    assert scan.status == "failed"
    assert scan.error_code == "DOMAIN_NOT_VERIFIED"
    assert "not verified" in scan.error_summary.lower()


@pytest.mark.asyncio
async def test_execute_scan_pipeline_cancellation(
    db_session: AsyncSession,
) -> None:
    """Verify pipeline halts and marks status 'cancelled' when cancellation is requested."""
    user = User(email="cancel.user@example.com", password_hash="hash", display_name="User")
    db_session.add(user)
    await db_session.flush()

    project = Project(owner_id=user.id, name="Cancel App", base_domain="example.org")
    db_session.add(project)
    await db_session.flush()

    scan = Scan(
        project_id=project.id,
        requested_by=user.id,
        target_url="https://example.org/",
        status="pending",
    )
    db_session.add(scan)
    await db_session.commit()

    # Request cancellation before execution
    request_scan_cancellation(scan.id)

    await execute_scan_pipeline(scan.id, db=db_session)

    await db_session.refresh(scan)
    assert scan.status == "cancelled"
