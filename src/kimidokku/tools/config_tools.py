"""Configuration MCP Tools."""

import asyncio
import json

from kimidokku.database import db
from kimidokku.mcp_server import mcp
from kimidokku.auth import mask_secrets


@mcp.tool()
async def get_config(app_name: str, api_key_id: str) -> dict:
    """
    Get ENV vars for an app. Secrets auto-masked (values containing KEY, PASS, SECRET, TOKEN shown as ***).
    Returns: {variables: dict, secrets_masked: list}
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    try:
        # Run dokku config:show
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "config:show",
            app_name,
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            # App might not have any config yet
            return {
                "variables": {},
                "secrets_masked": [],
            }

        # Parse JSON output
        config = json.loads(stdout.decode()) if stdout else {}

        # Mask secrets
        masked_config = mask_secrets(config)

        # Track which keys were masked
        secrets_masked = [
            key for key, value in config.items() if masked_config[key] == "***" and value != "***"
        ]

        return {
            "variables": masked_config,
            "secrets_masked": secrets_masked,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to get config: {e}")


@mcp.tool()
async def set_config(
    app_name: str,
    api_key_id: str,
    variables: dict,
    restart: bool = True,
) -> dict:
    """
    Set multiple ENV vars atomically.
    Backup old config to config_history table before applying.
    If restart=true: triggers dokku ps:restart after config:set.
    Returns: success, message, variables_set
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    if not variables:
        return {
            "success": True,
            "message": "No variables to set",
            "variables_set": [],
        }

    try:
        # Backup current config
        current_config = await _get_raw_config(app_name)
        await db.execute(
            """
            INSERT INTO config_history (app_name, config_json, created_by)
            VALUES (?, ?, 'mcp')
            """,
            (app_name, json.dumps(current_config)),
        )

        # Build config:set command
        config_args = []
        for key, value in variables.items():
            config_args.append(f"{key}={value}")

        # Run dokku config:set
        cmd = ["dokku", "config:set"]
        if not restart:
            cmd.append("--no-restart")
        cmd.append(app_name)
        cmd.extend(config_args)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            return {
                "success": True,
                "message": f"Set {len(variables)} variable(s) for '{app_name}'",
                "variables_set": list(variables.keys()),
                "restarted": restart,
            }
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            return {
                "success": False,
                "message": f"Failed to set config: {error_msg}",
                "variables_set": [],
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to set config: {e}",
            "variables_set": [],
        }


async def _get_raw_config(app_name: str) -> dict:
    """Get raw config without masking."""
    try:
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

        if proc.returncode == 0 and stdout:
            return json.loads(stdout.decode())
        return {}
    except Exception:
        return {}
