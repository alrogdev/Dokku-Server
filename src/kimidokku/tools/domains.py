"""Domains MCP Tools."""

import asyncio
from datetime import datetime, timedelta

from kimidokku.database import db
from kimidokku.mcp_server import mcp


@mcp.tool()
async def list_domains(app_name: str, api_key_id: str) -> dict:
    """
    List all domains for an app.
    Returns: {auto_domain, custom_domains: [{domain, tls_active, expires_in_days}]}
    """
    # Verify app ownership
    app = await db.fetch_one(
        """
        SELECT name, auto_domain, tls_status, tls_expires_at
        FROM apps 
        WHERE name = ? AND api_key_id = ?
        """,
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Get custom domains
    custom_domains = await db.fetch_all(
        """
        SELECT domain, tls_enabled, created_at
        FROM custom_domains
        WHERE app_name = ?
        ORDER BY created_at DESC
        """,
        (app_name,),
    )

    # Calculate TLS expires for auto_domain
    auto_expires_days = None
    if app["tls_expires_at"]:
        expires = datetime.fromisoformat(app["tls_expires_at"])
        auto_expires_days = (expires - datetime.now()).days

    # Format custom domains
    custom_list = []
    for domain in custom_domains:
        custom_list.append(
            {
                "domain": domain["domain"],
                "tls_active": bool(domain["tls_enabled"]),
                "expires_in_days": None,  # Would need to fetch from dokku
            }
        )

    return {
        "auto_domain": app["auto_domain"],
        "auto_tls_status": app["tls_status"],
        "auto_tls_expires_in_days": auto_expires_days,
        "custom_domains": custom_list,
    }


@mcp.tool()
async def add_custom_domain(
    app_name: str,
    api_key_id: str,
    domain: str,
) -> dict:
    """
    Add custom domain alias to app.
    Validation: domain must not be taken by another app.
    Auto-triggers: dokku domains:add + letsencrypt:enable (if applicable).
    Returns: success, dns_status, tls_status
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Check if domain is already taken
    existing = await db.fetch_one(
        "SELECT app_name FROM custom_domains WHERE domain = ?",
        (domain,),
    )

    if existing:
        if existing["app_name"] == app_name:
            return {
                "success": False,
                "message": f"Domain '{domain}' is already added to this app",
                "dns_status": "already_added",
                "tls_status": "none",
            }
        else:
            raise ValueError(f"Domain '{domain}' is already used by another app")

    try:
        # Add domain to database first
        await db.execute(
            "INSERT INTO custom_domains (app_name, domain) VALUES (?, ?)",
            (app_name, domain),
        )

        # Run dokku domains:add
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "domains:add",
            app_name,
            domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            # Rollback database
            await db.execute(
                "DELETE FROM custom_domains WHERE app_name = ? AND domain = ?",
                (app_name, domain),
            )
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to add domain: {error_msg}")

        # Try to enable TLS via letsencrypt
        tls_status = "none"
        try:
            tls_proc = await asyncio.create_subprocess_exec(
                "dokku",
                "letsencrypt:enable",
                app_name,
                domain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await tls_proc.communicate()

            if tls_proc.returncode == 0:
                await db.execute(
                    "UPDATE custom_domains SET tls_enabled = 1 WHERE app_name = ? AND domain = ?",
                    (app_name, domain),
                )
                tls_status = "active"
        except Exception:
            # TLS enablement is optional
            pass

        return {
            "success": True,
            "message": f"Domain '{domain}' added to '{app_name}'",
            "dns_status": "pending",  # User needs to configure DNS
            "tls_status": tls_status,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to add domain: {e}")


@mcp.tool()
async def remove_custom_domain(
    app_name: str,
    api_key_id: str,
    domain: str,
) -> dict:
    """
    Remove custom domain alias from app.
    Returns: success, message
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Check if domain exists for this app
    existing = await db.fetch_one(
        "SELECT id FROM custom_domains WHERE app_name = ? AND domain = ?",
        (app_name, domain),
    )

    if not existing:
        raise ValueError(f"Domain '{domain}' is not associated with app '{app_name}'")

    try:
        # Run dokku domains:remove
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "domains:remove",
            app_name,
            domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        # Remove from database (even if dokku command fails)
        await db.execute(
            "DELETE FROM custom_domains WHERE app_name = ? AND domain = ?",
            (app_name, domain),
        )

        if proc.returncode == 0:
            return {
                "success": True,
                "message": f"Domain '{domain}' removed from '{app_name}'",
            }
        else:
            # Domain might not exist in dokku anymore
            return {
                "success": True,
                "message": f"Domain '{domain}' removed from database (may not exist in dokku)",
            }

    except Exception as e:
        raise RuntimeError(f"Failed to remove domain: {e}")
