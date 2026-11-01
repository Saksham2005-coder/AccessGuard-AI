"""API endpoints for GitHub Pull Request Integration.

Phase 19 Feature 7: Repository connection management, HMAC-verified webhook ingestion,
and automated PR accessibility review reports.
"""

import uuid

from fastapi import APIRouter, Header, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUserDep, DbDep
from app.core.errors import NotFoundError
from app.schemas.github import (
    GitHubIntegrationCreate,
    GitHubIntegrationResponse,
    GitHubIntegrationUpdate,
    GitHubReviewRecordResponse,
    GitHubWebhookResponse,
    TestReviewRequest,
)
from app.services import github_service

router = APIRouter(tags=["github"])


@router.post(
    "/github/webhook",
    response_model=GitHubWebhookResponse,
    status_code=status.HTTP_200_OK,
)
async def handle_github_webhook(
    request: Request,
    db: DbDep,
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_github_event: str = Header("pull_request", alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
) -> Response:
    """Public webhook listener receiving and verifying GitHub delivery events."""
    raw_body = await request.body()
    status_code, response_data = await github_service.process_webhook_payload(
        db=db,
        delivery_id=x_github_delivery,
        event_type=x_github_event,
        signature_header=x_hub_signature_256,
        raw_body=raw_body,
    )
    return JSONResponse(status_code=status_code, content=response_data.model_dump())


@router.get(
    "/projects/{project_id}/github/integration",
    response_model=GitHubIntegrationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_project_github_integration(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GitHubIntegrationResponse:
    """Retrieve connected GitHub repository configuration for a project."""
    integration = await github_service.get_project_integration(
        db, project_id, user_id=current_user.id
    )
    if not integration:
        raise NotFoundError("GitHub repository is not connected for this project")
    return github_service.build_integration_response(integration)


@router.post(
    "/projects/{project_id}/github/integration",
    response_model=GitHubIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def connect_project_github_repo(
    project_id: uuid.UUID,
    data: GitHubIntegrationCreate,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GitHubIntegrationResponse:
    """Link a GitHub repository to a project with an HMAC webhook secret."""
    integration, secret = await github_service.create_or_update_project_integration(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        data=data,
    )
    return github_service.build_integration_response(integration, full_secret=secret)


@router.patch(
    "/projects/{project_id}/github/integration",
    response_model=GitHubIntegrationResponse,
    status_code=status.HTTP_200_OK,
)
async def update_project_github_repo(
    project_id: uuid.UUID,
    data: GitHubIntegrationUpdate,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GitHubIntegrationResponse:
    """Update settings for connected GitHub repository."""
    integration = await github_service.update_project_integration(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        data=data,
    )
    return github_service.build_integration_response(integration)


@router.delete(
    "/projects/{project_id}/github/integration",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def disconnect_project_github_repo(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> None:
    """Disconnect and remove GitHub repository integration."""
    await github_service.delete_project_integration(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/github/reviews",
    response_model=list[GitHubReviewRecordResponse],
    status_code=status.HTTP_200_OK,
)
async def list_project_pr_reviews(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> list[GitHubReviewRecordResponse]:
    """List historical pull request accessibility reviews for a project."""
    records = await github_service.list_project_reviews(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )
    return [github_service.build_review_response(r) for r in records]


@router.post(
    "/projects/{project_id}/github/test-review",
    response_model=GitHubReviewRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_test_pr_review(
    project_id: uuid.UUID,
    data: TestReviewRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GitHubReviewRecordResponse:
    """Trigger an on-demand PR accessibility review using latest project scan evidence."""
    record = await github_service.execute_test_pr_review(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        req=data,
    )
    return github_service.build_review_response(record)
