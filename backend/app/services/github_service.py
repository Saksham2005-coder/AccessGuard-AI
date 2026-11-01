"""GitHub Pull Request integration service.

Phase 19 Feature 7: Secure repository connection, constant-time HMAC-SHA256 signature
validation, delivery idempotency, evidence-grounded PR review generation, and non-destructive
GitHub API comment posting.
"""

import hashlib
import hmac
import json
import secrets
import uuid

import httpx
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, PolicyViolationError
from app.core.logging import get_logger
from app.db.models.finding import Finding
from app.db.models.github import GitHubIntegration, GitHubReviewRecord
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.github import (
    GitHubIntegrationCreate,
    GitHubIntegrationResponse,
    GitHubIntegrationUpdate,
    GitHubReviewRecordResponse,
    GitHubWebhookResponse,
    TestReviewRequest,
)
from app.services.project_service import get_project_verification_status

logger = get_logger("github_service")

GITHUB_API_BASE = "https://api.github.com"
WEBHOOK_PATH = "/api/v1/github/webhook"


def verify_webhook_signature(payload_bytes: bytes, signature_header: str | None, secret: str) -> bool:
    """Verify GitHub webhook payload signature using constant-time HMAC-SHA256 comparison."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_digest = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    expected_header = f"sha256={expected_digest}"
    return hmac.compare_digest(signature_header, expected_header)


def mask_secret(secret: str) -> str:
    """Return a masked preview of a secret string."""
    if len(secret) >= 12:
        return f"{secret[:6]}...{secret[-4:]}"
    return "***"


def build_integration_response(
    integration: GitHubIntegration, full_secret: str | None = None
) -> GitHubIntegrationResponse:
    """Helper to convert GitHubIntegration model into API response schema."""
    return GitHubIntegrationResponse(
        id=integration.id,
        project_id=integration.project_id,
        repo_owner=integration.repo_owner,
        repo_name=integration.repo_name,
        installation_id=integration.installation_id,
        webhook_secret_preview=mask_secret(integration.webhook_secret),
        webhook_secret=full_secret,
        webhook_url=WEBHOOK_PATH,
        has_token=bool(integration.access_token and len(integration.access_token) > 0),
        target_branch=integration.target_branch,
        enabled=integration.enabled,
        auto_review_prs=integration.auto_review_prs,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


def build_review_response(record: GitHubReviewRecord) -> GitHubReviewRecordResponse:
    """Helper to convert GitHubReviewRecord model into API response schema."""
    return GitHubReviewRecordResponse(
        id=record.id,
        integration_id=record.integration_id,
        project_id=record.project_id,
        delivery_id=record.delivery_id,
        pr_number=record.pr_number,
        pr_title=record.pr_title,
        pr_author=record.pr_author,
        head_sha=record.head_sha,
        base_sha=record.base_sha,
        scan_id=record.scan_id,
        status=record.status,
        comment_id=record.comment_id,
        summary_markdown=record.summary_markdown,
        error_message=record.error_message,
        created_at=record.created_at,
    )


def format_pr_review_markdown(
    project_name: str,
    target_url: str,
    scan: Scan | None,
    findings: list[Finding],
    pr_number: int,
    head_sha: str,
) -> str:
    """Generate concise, evidence-based accessibility review comment for a pull request."""
    critical_count = sum(1 for f in findings if f.impact == "critical")
    serious_count = sum(1 for f in findings if f.impact == "serious")
    moderate_count = sum(1 for f in findings if f.impact == "moderate")
    minor_count = sum(1 for f in findings if f.impact == "minor")
    total_violations = len(findings)

    # Pick top 5 high-impact findings
    sorted_findings = sorted(
        findings,
        key=lambda f: {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}.get(f.impact or "minor", 4),
    )
    top_findings = sorted_findings[:5]

    findings_table = ""
    if top_findings:
        findings_table += "\n### 🔍 High-Impact Violations\n\n"
        findings_table += "| Rule | Impact | Selector | Description |\n"
        findings_table += "| :--- | :--- | :--- | :--- |\n"
        for f in top_findings:
            rule = f.axe_rule_id
            impact_badge = {
                "critical": "🔴 Critical",
                "serious": "🟠 Serious",
                "moderate": "🟡 Moderate",
                "minor": "⚪ Minor",
            }.get(f.impact or "minor", f.impact or "Unknown")
            selector = f"`{(f.selector or '')[:35]}`" if f.selector else "`N/A`"
            desc = (f.description or "")[:80] + ("..." if len(f.description or "") > 80 else "")
            findings_table += f"| `{rule}` | {impact_badge} | {selector} | {desc} |\n"
    else:
        findings_table = "\n*No automated accessibility violations detected in the most recent scan evaluation.*\n"

    scan_info = f"Scan `{scan.id}`" if scan else "Baseline Evaluation"

    return f"""## 🛡️ AccessGuard AI — Accessibility Review

**Project:** {project_name}<br/>
**Target URL:** `{target_url}`<br/>
**PR:** #{pr_number} | **Commit:** `{head_sha[:8]}` | **Basis:** {scan_info}

### 📊 Violations Summary
| Impact | Count |
| :--- | :--- |
| 🔴 **Critical** | {critical_count} |
| 🟠 **Serious** | {serious_count} |
| 🟡 **Moderate** | {moderate_count} |
| ⚪ **Minor** | {minor_count} |
| **Total** | **{total_violations}** |
{findings_table}
---
> ⚠️ **Disclaimer:** This automated accessibility assessment was generated by AccessGuard AI. Automated testing detects a subset of accessibility barriers and does not constitute a legal WCAG compliance certification. Assistive technology testing (screen readers, keyboard traversal) is recommended for complete coverage.
"""


async def post_github_pr_comment(
    token: str,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    body: str,
    existing_comment_id: str | None = None,
) -> str | None:
    """Post or update an accessibility review comment on GitHub PR using REST API."""
    if not token:
        logger.info("No GitHub access token configured; skipping remote comment posting.")
        return None

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AccessGuard-AI-PR-Reviewer",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if existing_comment_id:
                # Update existing comment to prevent spam
                url = f"{GITHUB_API_BASE}/repos/{repo_owner}/{repo_name}/issues/comments/{existing_comment_id}"
                resp = await client.patch(url, headers=headers, json={"body": body})
                if resp.status_code == 200:
                    return existing_comment_id

            # Post new comment
            url = f"{GITHUB_API_BASE}/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
            resp = await client.post(url, headers=headers, json={"body": body})
            if resp.status_code in (200, 201):
                data = resp.json()
                return str(data.get("id"))
            else:
                logger.warning(
                    "GitHub API comment posting returned non-success",
                    status_code=resp.status_code,
                    body=resp.text,
                )
                return None
        except Exception as e:
            logger.error("Failed to post comment to GitHub", error=str(e))
            return None


async def get_project_integration(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID | None = None
) -> GitHubIntegration | None:
    """Retrieve the GitHub integration configured for a project with optional owner verification."""
    if user_id is not None:
        proj_res = await db.execute(
            select(Project).where(Project.id == project_id, Project.owner_id == user_id)
        )
        if not proj_res.scalar_one_or_none():
            return None

    result = await db.execute(
        select(GitHubIntegration).where(GitHubIntegration.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_project_integration(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: GitHubIntegrationCreate,
) -> tuple[GitHubIntegration, str]:
    """Create or update a GitHub repository connection for a project."""
    # Verify project exists and user has access
    project_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = project_res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found or unauthorized")

    secret = data.webhook_secret or f"whsec_{secrets.token_hex(20)}"

    existing = await get_project_integration(db, project_id)
    if existing:
        existing.repo_owner = data.repo_owner
        existing.repo_name = data.repo_name
        existing.installation_id = data.installation_id
        if data.webhook_secret:
            existing.webhook_secret = data.webhook_secret
        if data.access_token is not None:
            existing.access_token = data.access_token
        existing.target_branch = data.target_branch
        existing.enabled = data.enabled
        existing.auto_review_prs = data.auto_review_prs
        await db.flush()
        return existing, existing.webhook_secret
    else:
        new_integration = GitHubIntegration(
            project_id=project_id,
            repo_owner=data.repo_owner,
            repo_name=data.repo_name,
            installation_id=data.installation_id,
            webhook_secret=secret,
            access_token=data.access_token,
            target_branch=data.target_branch,
            enabled=data.enabled,
            auto_review_prs=data.auto_review_prs,
            created_by=user_id,
        )
        db.add(new_integration)
        await db.flush()
        return new_integration, secret


async def update_project_integration(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: GitHubIntegrationUpdate,
) -> GitHubIntegration:
    """Partially update integration settings."""
    project_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    if not project_res.scalar_one_or_none():
        raise NotFoundError("Project not found or unauthorized")

    integration = await get_project_integration(db, project_id)
    if not integration:
        raise NotFoundError("GitHub integration not configured for this project")

    if data.target_branch is not None:
        integration.target_branch = data.target_branch
    if data.enabled is not None:
        integration.enabled = data.enabled
    if data.auto_review_prs is not None:
        integration.auto_review_prs = data.auto_review_prs
    if data.access_token is not None:
        integration.access_token = data.access_token

    await db.flush()
    return integration


async def delete_project_integration(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Disconnect and delete GitHub integration."""
    project_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    if not project_res.scalar_one_or_none():
        raise NotFoundError("Project not found or unauthorized")

    integration = await get_project_integration(db, project_id)
    if not integration:
        raise NotFoundError("GitHub integration not found")

    await db.delete(integration)
    await db.flush()


async def list_project_reviews(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, limit: int = 50
) -> list[GitHubReviewRecord]:
    """List historical review records for a project."""
    project_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    if not project_res.scalar_one_or_none():
        raise NotFoundError("Project not found or unauthorized")

    result = await db.execute(
        select(GitHubReviewRecord)
        .where(GitHubReviewRecord.project_id == project_id)
        .order_by(desc(GitHubReviewRecord.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def process_webhook_payload(
    db: AsyncSession,
    delivery_id: str,
    event_type: str,
    signature_header: str | None,
    raw_body: bytes,
) -> tuple[int, GitHubWebhookResponse]:
    """Process an incoming GitHub webhook event with signature and idempotency checks."""
    # 1. Idempotency check: prevent duplicate deliveries
    dup_res = await db.execute(
        select(GitHubReviewRecord).where(GitHubReviewRecord.delivery_id == delivery_id)
    )
    if dup_res.scalar_one_or_none():
        return 200, GitHubWebhookResponse(
            status="duplicate",
            message="Webhook delivery already processed",
            delivery_id=delivery_id,
        )

    # 2. Ping event handling
    if event_type == "ping":
        return 200, GitHubWebhookResponse(
            status="pong",
            message="AccessGuard webhook listener active",
            delivery_id=delivery_id,
        )

    # 3. Parse JSON body
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        return 400, GitHubWebhookResponse(
            status="error",
            message=f"Invalid JSON payload: {str(e)}",
            delivery_id=delivery_id,
        )

    repo_data = payload.get("repository", {})
    repo_owner = repo_data.get("owner", {}).get("login", "")
    repo_name = repo_data.get("name", "")

    if not repo_owner or not repo_name:
        return 400, GitHubWebhookResponse(
            status="error",
            message="Repository owner or name missing from payload",
            delivery_id=delivery_id,
        )

    # 4. Lookup active integration
    res = await db.execute(
        select(GitHubIntegration).where(
            GitHubIntegration.repo_owner == repo_owner,
            GitHubIntegration.repo_name == repo_name,
            GitHubIntegration.enabled == True,  # noqa: E712
        )
    )
    integration = res.scalar_one_or_none()
    if not integration:
        return 200, GitHubWebhookResponse(
            status="unlinked",
            message=f"Repository {repo_owner}/{repo_name} not linked or integration disabled",
            delivery_id=delivery_id,
        )

    # 5. Verify HMAC-SHA256 signature
    if not verify_webhook_signature(raw_body, signature_header, integration.webhook_secret):
        logger.warning(
            "Webhook signature mismatch",
            repo=f"{repo_owner}/{repo_name}",
            delivery_id=delivery_id,
        )
        return 401, GitHubWebhookResponse(
            status="unauthorized",
            message="Invalid HMAC-SHA256 webhook signature",
            delivery_id=delivery_id,
        )

    # 6. Only process pull_request events
    if event_type != "pull_request":
        return 200, GitHubWebhookResponse(
            status="ignored",
            message=f"Event {event_type} ignored; only pull_request is evaluated",
            delivery_id=delivery_id,
        )

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return 200, GitHubWebhookResponse(
            status="ignored",
            message=f"Pull request action '{action}' ignored",
            delivery_id=delivery_id,
        )

    if not integration.auto_review_prs:
        return 200, GitHubWebhookResponse(
            status="skipped",
            message="Automatic PR reviews are disabled for this integration",
            delivery_id=delivery_id,
        )

    pr = payload.get("pull_request", {})
    pr_number = pr.get("number", 0)
    pr_title = pr.get("title", "Untitled PR")
    pr_author = pr.get("user", {}).get("login")
    head_sha = pr.get("head", {}).get("sha", "unknown_sha")
    base_sha = pr.get("base", {}).get("sha", "unknown_sha")

    # 7. Check domain verification for the project
    is_verified, _ = await get_project_verification_status(db, integration.project_id)
    if not is_verified:
        # Create record noting domain verification requirement
        rec = GitHubReviewRecord(
            integration_id=integration.id,
            project_id=integration.project_id,
            delivery_id=delivery_id,
            pr_number=pr_number,
            pr_title=pr_title,
            pr_author=pr_author,
            head_sha=head_sha,
            base_sha=base_sha,
            status="skipped",
            error_message="Domain verification required before PR accessibility audit can be executed.",
        )
        db.add(rec)
        await db.flush()
        return 200, GitHubWebhookResponse(
            status="skipped",
            message="Domain unverified; audit skipped per security policy",
            delivery_id=delivery_id,
            review_id=rec.id,
        )

    # 8. Fetch project info and latest completed scan
    project_res = await db.execute(select(Project).where(Project.id == integration.project_id))
    project = project_res.scalar_one()

    scan_res = await db.execute(
        select(Scan)
        .where(Scan.project_id == integration.project_id, Scan.status == "completed")
        .order_by(desc(Scan.created_at))
        .limit(1)
    )
    latest_scan = scan_res.scalar_one_or_none()

    findings: list[Finding] = []
    if latest_scan:
        f_res = await db.execute(
            select(Finding)
            .join(ScanPage, Finding.scan_page_id == ScanPage.id)
            .where(ScanPage.scan_id == latest_scan.id)
        )
        findings = list(f_res.scalars().all())

    # 9. Format review comment
    target_url = latest_scan.target_url if latest_scan else f"https://{project.base_domain}"
    review_markdown = format_pr_review_markdown(
        project_name=project.name,
        target_url=target_url,
        scan=latest_scan,
        findings=findings,
        pr_number=pr_number,
        head_sha=head_sha,
    )

    # 10. Post comment to GitHub if token configured
    comment_id = None
    if integration.access_token:
        comment_id = await post_github_pr_comment(
            token=integration.access_token,
            repo_owner=integration.repo_owner,
            repo_name=integration.repo_name,
            pr_number=pr_number,
            body=review_markdown,
        )

    # 11. Persist review record
    review_record = GitHubReviewRecord(
        integration_id=integration.id,
        project_id=integration.project_id,
        delivery_id=delivery_id,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_author=pr_author,
        head_sha=head_sha,
        base_sha=base_sha,
        scan_id=latest_scan.id if latest_scan else None,
        status="reviewed",
        comment_id=comment_id,
        summary_markdown=review_markdown,
    )
    db.add(review_record)
    await db.flush()

    return 200, GitHubWebhookResponse(
        status="reviewed",
        message="Pull request accessibility review generated and recorded",
        delivery_id=delivery_id,
        review_id=review_record.id,
    )


async def execute_test_pr_review(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    req: TestReviewRequest,
) -> GitHubReviewRecord:
    """Trigger an on-demand test PR review using latest scan findings."""
    project_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = project_res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found or unauthorized")

    integration = await get_project_integration(db, project_id)
    if not integration:
        raise NotFoundError("GitHub integration not configured for this project")

    is_verified, _ = await get_project_verification_status(db, project_id)
    if not is_verified:
        raise PolicyViolationError(
            "Project domain is not verified. Domain verification is required for accessibility reviews."
        )

    # Fetch latest completed scan
    scan_res = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id, Scan.status == "completed")
        .order_by(desc(Scan.created_at))
        .limit(1)
    )
    latest_scan = scan_res.scalar_one_or_none()

    findings: list[Finding] = []
    if latest_scan:
        f_res = await db.execute(
            select(Finding)
            .join(ScanPage, Finding.scan_page_id == ScanPage.id)
            .where(ScanPage.scan_id == latest_scan.id)
        )
        findings = list(f_res.scalars().all())

    target_url = latest_scan.target_url if latest_scan else f"https://{project.base_domain}"
    review_markdown = format_pr_review_markdown(
        project_name=project.name,
        target_url=target_url,
        scan=latest_scan,
        findings=findings,
        pr_number=req.pr_number,
        head_sha=req.head_sha,
    )

    delivery_id = f"test_{uuid.uuid4().hex[:16]}"
    comment_id = None
    if integration.access_token:
        comment_id = await post_github_pr_comment(
            token=integration.access_token,
            repo_owner=integration.repo_owner,
            repo_name=integration.repo_name,
            pr_number=req.pr_number,
            body=review_markdown,
        )

    record = GitHubReviewRecord(
        integration_id=integration.id,
        project_id=project_id,
        delivery_id=delivery_id,
        pr_number=req.pr_number,
        pr_title=req.pr_title,
        pr_author=req.pr_author,
        head_sha=req.head_sha,
        base_sha=req.base_sha,
        scan_id=latest_scan.id if latest_scan else None,
        status="reviewed",
        comment_id=comment_id,
        summary_markdown=review_markdown,
    )
    db.add(record)
    await db.flush()
    return record
