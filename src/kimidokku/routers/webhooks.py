"""Webhook endpoints for GitHub and GitLab."""

from fastapi import APIRouter, Header, HTTPException, Request, status

from kimidokku.database import db
from kimidokku.tools.apps import _run_git_deploy
from kimidokku.utils.webhook_verify import (
    extract_commit_hash,
    extract_git_ref,
    is_valid_push_event,
    verify_github_signature,
)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/github/{app_name}")
async def github_webhook(
    app_name: str,
    request: Request,
    x_hub_signature_256: str = Header(None),
):
    """
    GitHub webhook endpoint for auto-deploy.

    Verifies HMAC-SHA256 signature and triggers deployment if branch matches.
    """
    # Get app details including webhook secret
    app = await db.fetch_one(
        """
        SELECT a.name, a.branch, a.git_url, k.id as api_key_id,
               c.value as webhook_secret
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        LEFT JOIN platform_config c ON c.key = 'webhook_secret_' || a.name
        WHERE a.name = ? AND k.is_active = 1
        """,
        (app_name,),
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App '{app_name}' not found",
        )

    # Get webhook secret (from app-specific config or fallback)
    webhook_secret = app.get("webhook_secret")
    if not webhook_secret:
        # Try to get default webhook secret
        config = await db.fetch_one(
            "SELECT value FROM platform_config WHERE key = 'webhook_secret_default'"
        )
        webhook_secret = config["value"] if config else None

    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook secret not configured",
        )

    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    if not verify_github_signature(body, x_hub_signature_256, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # Parse payload
    try:
        import json

        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Validate it's a push event
    if not is_valid_push_event(payload, "github"):
        return {
            "status": "ignored",
            "message": "Not a push event or no commits",
        }

    # Extract branch from ref
    pushed_branch = extract_git_ref(payload)
    if pushed_branch != app["branch"]:
        return {
            "status": "ignored",
            "message": f"Branch mismatch: got '{pushed_branch}', expected '{app['branch']}'",
        }

    # Check if app has git_url configured
    if not app["git_url"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App has no git_url configured",
        )

    # Create deploy log entry
    commit_hash = extract_commit_hash(payload)
    cursor = await db.execute(
        """
        INSERT INTO deploy_logs (app_name, triggered_by, git_ref, status, started_at)
        VALUES (?, 'webhook', ?, 'in_progress', datetime('now'))
        """,
        (app_name, commit_hash or pushed_branch),
    )
    deploy_id = cursor.lastrowid

    # Update app status
    await db.execute(
        "UPDATE apps SET status = 'deploying', last_deploy_at = datetime('now') WHERE name = ?",
        (app_name,),
    )

    # Trigger async deployment
    import asyncio

    asyncio.create_task(_run_git_deploy(app_name, app["git_url"], pushed_branch, deploy_id))

    return {
        "status": "queued",
        "deploy_id": deploy_id,
        "message": f"Deployment queued for {app_name} from branch {pushed_branch}",
    }


@router.post("/gitlab/{app_name}")
async def gitlab_webhook(
    app_name: str,
    request: Request,
    x_gitlab_token: str = Header(None),
):
    """
    GitLab webhook endpoint for auto-deploy.

    Verifies X-Gitlab-Token and triggers deployment if branch matches.
    """
    # Get app details including webhook secret
    app = await db.fetch_one(
        """
        SELECT a.name, a.branch, a.git_url, k.id as api_key_id,
               c.value as webhook_secret
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        LEFT JOIN platform_config c ON c.key = 'webhook_secret_' || a.name
        WHERE a.name = ? AND k.is_active = 1
        """,
        (app_name,),
    )

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App '{app_name}' not found",
        )

    # Get webhook secret (from app-specific config or fallback)
    webhook_secret = app.get("webhook_secret")
    if not webhook_secret:
        # Try to get default webhook secret
        config = await db.fetch_one(
            "SELECT value FROM platform_config WHERE key = 'webhook_secret_default'"
        )
        webhook_secret = config["value"] if config else None

    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook secret not configured",
        )

    # Verify token
    from kimidokku.utils.webhook_verify import verify_gitlab_token

    if not verify_gitlab_token(x_gitlab_token, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Parse payload
    try:
        import json

        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Validate it's a push event
    if not is_valid_push_event(payload, "gitlab"):
        return {
            "status": "ignored",
            "message": "Not a push event",
        }

    # Extract branch from ref
    pushed_branch = extract_git_ref(payload)
    if pushed_branch != app["branch"]:
        return {
            "status": "ignored",
            "message": f"Branch mismatch: got '{pushed_branch}', expected '{app['branch']}'",
        }

    # Check if app has git_url configured
    if not app["git_url"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App has no git_url configured",
        )

    # Create deploy log entry
    commit_hash = extract_commit_hash(payload)
    cursor = await db.execute(
        """
        INSERT INTO deploy_logs (app_name, triggered_by, git_ref, status, started_at)
        VALUES (?, 'webhook', ?, 'in_progress', datetime('now'))
        """,
        (app_name, commit_hash or pushed_branch),
    )
    deploy_id = cursor.lastrowid

    # Update app status
    await db.execute(
        "UPDATE apps SET status = 'deploying', last_deploy_at = datetime('now') WHERE name = ?",
        (app_name,),
    )

    # Trigger async deployment
    import asyncio

    asyncio.create_task(_run_git_deploy(app_name, app["git_url"], pushed_branch, deploy_id))

    return {
        "status": "queued",
        "deploy_id": deploy_id,
        "message": f"Deployment queued for {app_name} from branch {pushed_branch}",
    }
