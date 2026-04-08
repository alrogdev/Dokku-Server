"""MCP Resources for read-only app context."""

import asyncio
import json

from kimidokku.auth import mask_secrets
from kimidokku.database import db
from kimidokku.mcp_server import mcp


@mcp.resource("dokku://config/{app_name}{?api_key}")
async def app_config_resource(app_name: str, api_key: str = None) -> str:
    """Plain text KEY=VALUE (masked) for AI context window."""
    # Verify API key has access to this app
    app = await db.fetch_one(
        """
        SELECT a.name 
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        WHERE a.name = ? AND k.id = ? AND k.is_active = 1
        """,
        (app_name, api_key),
    )

    if not app:
        return f"# Error: App '{app_name}' not found or access denied"

    try:
        # Get config from dokku
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "config:show",
            app_name,
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0 or not stdout:
            return f"# No configuration for {app_name}"

        config = json.loads(stdout.decode())
        masked_config = mask_secrets(config)

        # Format as KEY=VALUE
        lines = [f"# Configuration for {app_name}", ""]
        for key, value in masked_config.items():
            lines.append(f"{key}={value}")

        return "\n".join(lines)

    except Exception as e:
        return f"# Error reading config: {e}"


@mcp.resource("dokku://logs/{app_name}/recent{?api_key}")
async def recent_logs_resource(app_name: str, api_key: str = None) -> str:
    """Last 50 lines of logs as plain text."""
    # Verify API key has access to this app
    app = await db.fetch_one(
        """
        SELECT a.name 
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        WHERE a.name = ? AND k.id = ? AND k.is_active = 1
        """,
        (app_name, api_key),
    )

    if not app:
        return f"# Error: App '{app_name}' not found or access denied"

    try:
        # Get logs from dokku
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "logs",
            app_name,
            "-t",
            "-n",
            "50",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return f"# No logs available for {app_name}"

        logs = stdout.decode() if stdout else ""

        if not logs.strip():
            return f"# No logs for {app_name}"

        header = f"# Recent logs for {app_name}\n# (last 50 lines)\n\n"
        return header + logs

    except Exception as e:
        return f"# Error reading logs: {e}"


@mcp.resource("dokku://domains/{app_name}{?api_key}")
async def domains_resource(app_name: str, api_key: str = None) -> str:
    """List of all domains serving this app."""
    # Verify API key has access to this app
    app = await db.fetch_one(
        """
        SELECT a.name, a.auto_domain 
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        WHERE a.name = ? AND k.id = ? AND k.is_active = 1
        """,
        (app_name, api_key),
    )

    if not app:
        return f"# Error: App '{app_name}' not found or access denied"

    try:
        # Get custom domains
        custom_domains = await db.fetch_all(
            "SELECT domain FROM custom_domains WHERE app_name = ? ORDER BY created_at DESC",
            (app_name,),
        )

        lines = [f"# Domains for {app_name}", ""]
        lines.append(f"# Auto-generated domain:")
        lines.append(app["auto_domain"])
        lines.append("")

        if custom_domains:
            lines.append(f"# Custom domains ({len(custom_domains)}):")
            for d in custom_domains:
                lines.append(d["domain"])
        else:
            lines.append("# No custom domains")

        return "\n".join(lines)

    except Exception as e:
        return f"# Error reading domains: {e}"
