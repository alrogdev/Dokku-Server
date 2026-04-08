"""App Lifecycle MCP Tools."""

import asyncio
from datetime import datetime
from typing import Optional

from kimidokku.database import db
from kimidokku.mcp_server import mcp


@mcp.tool()
async def list_apps(api_key_id: str) -> list[dict]:
    """
    List all apps associated with this API key (max 10).

    Returns: List of apps with name, auto_domain, custom_domains, status, last_deploy_at, tls_status
    """
    # Get apps for this API key
    apps = await db.fetch_all(
        """
        SELECT 
            a.name,
            a.auto_domain,
            a.status,
            a.last_deploy_at,
            a.tls_status,
            GROUP_CONCAT(cd.domain) as custom_domains
        FROM apps a
        LEFT JOIN custom_domains cd ON a.name = cd.app_name
        WHERE a.api_key_id = ?
        GROUP BY a.name
        ORDER BY a.created_at DESC
        """,
        (api_key_id,),
    )

    result = []
    for app in apps:
        custom_domains = app["custom_domains"].split(",") if app["custom_domains"] else []
        result.append(
            {
                "name": app["name"],
                "auto_domain": app["auto_domain"],
                "custom_domains": custom_domains,
                "status": app["status"],
                "last_deploy_at": app["last_deploy_at"],
                "tls_status": app["tls_status"],
            }
        )

    return result


@mcp.tool()
async def get_app_status(app_name: str, api_key_id: str) -> dict:
    """
    Get detailed status of a specific app (must belong to caller's API key).

    Returns: status, containers, git_ref, tls_expires_in_days
    """
    # Verify app ownership
    app = await db.fetch_one(
        """
        SELECT 
            a.*,
            GROUP_CONCAT(cd.domain) as custom_domains
        FROM apps a
        LEFT JOIN custom_domains cd ON a.name = cd.app_name
        WHERE a.name = ? AND a.api_key_id = ?
        GROUP BY a.name
        """,
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Calculate TLS expires in days
    tls_expires_in_days = None
    if app["tls_expires_at"]:
        expires = datetime.fromisoformat(app["tls_expires_at"])
        tls_expires_in_days = (expires - datetime.now()).days

    return {
        "name": app["name"],
        "status": app["status"],
        "auto_domain": app["auto_domain"],
        "custom_domains": app["custom_domains"].split(",") if app["custom_domains"] else [],
        "git_url": app["git_url"],
        "branch": app["branch"],
        "tls_status": app["tls_status"],
        "tls_expires_in_days": tls_expires_in_days,
        "created_at": app["created_at"],
        "last_deploy_at": app["last_deploy_at"],
    }


@mcp.tool()
async def deploy_git(
    app_name: str,
    api_key_id: str,
    branch: str = "main",
) -> dict:
    """
    Trigger deployment from git repository.
    Executes: dokku git:sync --build {app_name} {git_url} {branch}

    Returns: deploy_id, status, estimated_seconds
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT git_url FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    if not app["git_url"]:
        raise ValueError(f"App '{app_name}' has no git_url configured")

    # Create deploy log entry
    cursor = await db.execute(
        """
        INSERT INTO deploy_logs (app_name, triggered_by, git_ref, status, started_at)
        VALUES (?, 'mcp', ?, 'in_progress', datetime('now'))
        """,
        (app_name, f"refs/heads/{branch}"),
    )
    deploy_id = cursor.lastrowid

    # Update app status
    await db.execute(
        "UPDATE apps SET status = 'deploying', last_deploy_at = datetime('now') WHERE name = ?",
        (app_name,),
    )

    # Trigger async deployment (non-blocking)
    asyncio.create_task(_run_git_deploy(app_name, app["git_url"], branch, deploy_id))

    return {
        "deploy_id": deploy_id,
        "status": "queued",
        "estimated_seconds": 120,
        "message": f"Deployment queued for {app_name} from branch {branch}",
    }


async def _run_git_deploy(app_name: str, git_url: str, branch: str, deploy_id: int):
    """Run git deployment in background."""
    try:
        # Run dokku git:sync --build
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "git:sync",
            "--build",
            app_name,
            git_url,
            branch,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            await db.execute(
                """
                UPDATE deploy_logs 
                SET status = 'success', finished_at = datetime('now')
                WHERE id = ?
                """,
                (deploy_id,),
            )
            await db.execute(
                "UPDATE apps SET status = 'running' WHERE name = ?",
                (app_name,),
            )
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            await db.execute(
                """
                UPDATE deploy_logs 
                SET status = 'failed', finished_at = datetime('now'), error_message = ?
                WHERE id = ?
                """,
                (error_msg, deploy_id),
            )
            await db.execute(
                "UPDATE apps SET status = 'error' WHERE name = ?",
                (app_name,),
            )
    except Exception as e:
        await db.execute(
            """
            UPDATE deploy_logs 
            SET status = 'failed', finished_at = datetime('now'), error_message = ?
            WHERE id = ?
            """,
            (str(e), deploy_id),
        )
        await db.execute(
            "UPDATE apps SET status = 'error' WHERE name = ?",
            (app_name,),
        )


@mcp.tool()
async def deploy_image(
    app_name: str,
    api_key_id: str,
    image_url: str,
    registry_user: Optional[str] = None,
    registry_pass: Optional[str] = None,
) -> dict:
    """
    Deploy from Docker image registry.
    Executes: dokku git:from-image {app_name} {image_url}

    Returns: deploy_id, status, estimated_seconds
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Create deploy log entry
    cursor = await db.execute(
        """
        INSERT INTO deploy_logs (app_name, triggered_by, git_ref, status, started_at)
        VALUES (?, 'mcp', ?, 'in_progress', datetime('now'))
        """,
        (app_name, image_url),
    )
    deploy_id = cursor.lastrowid

    # Update app status
    await db.execute(
        "UPDATE apps SET status = 'deploying', last_deploy_at = datetime('now') WHERE name = ?",
        (app_name,),
    )

    # Trigger async deployment
    asyncio.create_task(
        _run_image_deploy(app_name, image_url, registry_user, registry_pass, deploy_id)
    )

    return {
        "deploy_id": deploy_id,
        "status": "queued",
        "estimated_seconds": 120,
        "message": f"Deployment queued for {app_name} from image {image_url}",
    }


async def _run_image_deploy(
    app_name: str,
    image_url: str,
    registry_user: Optional[str],
    registry_pass: Optional[str],
    deploy_id: int,
):
    """Run image deployment in background."""
    try:
        # Set registry auth if provided
        if registry_user and registry_pass:
            await asyncio.create_subprocess_exec(
                "dokku",
                "registry:set",
                app_name,
                "username",
                registry_user,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # Note: In production, use docker login or dokku registry-login

        # Run dokku git:from-image
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "git:from-image",
            app_name,
            image_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            await db.execute(
                """
                UPDATE deploy_logs 
                SET status = 'success', finished_at = datetime('now')
                WHERE id = ?
                """,
                (deploy_id,),
            )
            await db.execute(
                "UPDATE apps SET status = 'running' WHERE name = ?",
                (app_name,),
            )
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            await db.execute(
                """
                UPDATE deploy_logs 
                SET status = 'failed', finished_at = datetime('now'), error_message = ?
                WHERE id = ?
                """,
                (error_msg, deploy_id),
            )
            await db.execute(
                "UPDATE apps SET status = 'error' WHERE name = ?",
                (app_name,),
            )
    except Exception as e:
        await db.execute(
            """
            UPDATE deploy_logs 
            SET status = 'failed', finished_at = datetime('now'), error_message = ?
            WHERE id = ?
            """,
            (str(e), deploy_id),
        )
        await db.execute(
            "UPDATE apps SET status = 'error' WHERE name = ?",
            (app_name,),
        )
