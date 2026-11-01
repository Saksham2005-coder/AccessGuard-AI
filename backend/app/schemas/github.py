"""Pydantic schemas for GitHub pull request integration.

Phase 19 Feature 7: Validation contracts for GitHub repository connections,
PR review tracking, webhook delivery, and review summaries.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GitHubIntegrationCreate(BaseModel):
    """Payload to link a GitHub repository to an AccessGuard project."""

    repo_owner: str = Field(..., min_length=1, max_length=255, description="GitHub user or org")
    repo_name: str = Field(..., min_length=1, max_length=255, description="GitHub repository name")
    installation_id: str | None = Field(None, max_length=100)
    webhook_secret: str | None = Field(None, description="Optional custom secret, auto-generated if omitted")
    access_token: str | None = Field(None, description="Optional GitHub token for posting PR comments")
    target_branch: str = Field("main", max_length=100)
    enabled: bool = True
    auto_review_prs: bool = True


class GitHubIntegrationUpdate(BaseModel):
    """Payload to update repository settings."""

    target_branch: str | None = Field(None, max_length=100)
    enabled: bool | None = None
    auto_review_prs: bool | None = None
    access_token: str | None = None


class GitHubIntegrationResponse(BaseModel):
    """External view of a connected GitHub repository with masked secrets."""

    id: uuid.UUID
    project_id: uuid.UUID
    repo_owner: str
    repo_name: str
    installation_id: str | None
    webhook_secret_preview: str
    webhook_secret: str | None = Field(None, description="Full secret returned only upon creation/request")
    webhook_url: str
    has_token: bool
    target_branch: str
    enabled: bool
    auto_review_prs: bool
    created_at: datetime
    updated_at: datetime


class GitHubReviewRecordResponse(BaseModel):
    """Historical pull request review event record."""

    id: uuid.UUID
    integration_id: uuid.UUID
    project_id: uuid.UUID
    delivery_id: str
    pr_number: int
    pr_title: str
    pr_author: str | None
    head_sha: str
    base_sha: str
    scan_id: uuid.UUID | None
    status: str
    comment_id: str | None
    summary_markdown: str | None
    error_message: str | None
    created_at: datetime


class GitHubWebhookResponse(BaseModel):
    """Response returned to GitHub webhook deliveries."""

    status: str
    message: str
    delivery_id: str | None = None
    review_id: uuid.UUID | None = None


class TestReviewRequest(BaseModel):
    """Request payload to trigger an on-demand review simulation/test."""

    __test__ = False

    pr_number: int = Field(1, ge=1)
    pr_title: str = Field("Test Accessibility PR Review", max_length=500)
    pr_author: str = Field("developer", max_length=255)
    head_sha: str = Field("sha7bd5b35a1", max_length=100)
    base_sha: str = Field("shafe3aab3b2", max_length=100)
