"""Logs & Debug MCP Tools."""

import asyncio
import re
import shlex
from typing import Optional

from kimidokku.database import db
from kimidokku.mcp_server import mcp


# Whitelist for run_command - only safe commands
ALLOWED_COMMANDS = {"rake", "python", "node", "echo", "rails", "bundle", "npm", "yarn"}
FORBIDDEN_PATTERNS = [
    r";",  # Command separator
    r"\|",  # Pipe
    r"\$\(",  # Command substitution $()
    r"`",  # Backtick substitution
    r">>",  # Append redirection
    r">",  # Overwrite redirection
    r"&&",  # AND operator
    r"\|\|",  # OR operator
    r"\$\{IFS\}",  # IFS substitution
    r"\n",  # Newline
    r"\r",  # Carriage return
]


@mcp.tool()
async def get_logs(
    app_name: str,
    api_key_id: str,
    lines: int = 100,
) -> list[dict]:
    """
    Get recent logs (snapshot, not streaming).
    Returns structured: [{timestamp, process, level, message}]
    Level inference: ERROR (stderr/fatal), WARN (warning), INFO (default)
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    try:
        # Run dokku logs
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "logs",
            app_name,
            "-t",
            "-n",
            str(lines),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Failed to get logs"
            raise RuntimeError(error_msg)

        # Parse log lines
        logs = []
        log_text = stdout.decode() if stdout else ""

        for line in log_text.strip().split("\n"):
            if not line:
                continue

            # Parse dokku log format: "2024-01-15 10:30:45 app[web.1]: message"
            parsed = _parse_log_line(line)
            logs.append(parsed)

        return logs[:lines]

    except Exception as e:
        raise RuntimeError(f"Failed to get logs: {e}")


def _parse_log_line(line: str) -> dict:
    """Parse a log line into structured format."""
    # Default values
    timestamp = None
    process = "unknown"
    level = "INFO"
    message = line

    # Try to parse dokku log format
    # Pattern: "2024-01-15 10:30:45 app[web.1]: message"
    match = re.match(
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\[(\S+)\]:\s*(.*)",
        line,
    )

    if match:
        timestamp = match.group(1)
        app_name = match.group(2)
        process = match.group(3)
        message = match.group(4)

    # Infer log level from content
    msg_upper = message.upper()
    if any(kw in msg_upper for kw in ["ERROR", "FATAL", "CRITICAL", "EXCEPTION"]):
        level = "ERROR"
    elif any(kw in msg_upper for kw in ["WARN", "WARNING"]):
        level = "WARN"
    elif any(kw in msg_upper for kw in ["DEBUG", "TRACE"]):
        level = "DEBUG"

    return {
        "timestamp": timestamp,
        "process": process,
        "level": level,
        "message": message,
    }


@mcp.tool()
async def restart_app(app_name: str, api_key_id: str) -> dict:
    """
    Graceful restart of an app.
    Returns: success, message
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    try:
        # Run dokku ps:restart
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "ps:restart",
            app_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            # Update app status
            await db.execute(
                "UPDATE apps SET status = 'running' WHERE name = ?",
                (app_name,),
            )

            return {
                "success": True,
                "message": f"App '{app_name}' restarted successfully",
            }
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            return {
                "success": False,
                "message": f"Failed to restart app: {error_msg}",
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to restart app: {e}",
        }


@mcp.tool()
async def run_command(
    app_name: str,
    api_key_id: str,
    command: str,
) -> dict:
    """
    Run one-off command in app container (dokku run).
    Security: Command whitelist validation (no shell injection)
    Returns: stdout, stderr, exit_code
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Security: Validate command
    _validate_command(command)

    try:
        # Parse command safely with shlex
        cmd_args = shlex.split(command)

        # Run dokku run with parsed arguments
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "run",
            app_name,
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        return {
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
            "exit_code": proc.returncode,
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
        }


def _validate_command(command: str) -> bool:
    """Validate command for security.

    Args:
        command: The command string to validate

    Returns:
        True if command is valid

    Raises:
        ValueError: If command contains forbidden patterns or disallowed base command
    """
    if not command or not command.strip():
        raise ValueError("Command cannot be empty")

    command = command.strip()

    # Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(f"Command contains forbidden pattern: {pattern}")

    # Parse command with shlex to properly handle quoted arguments
    try:
        args = shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid command format: {e}")

    if not args:
        raise ValueError("Command cannot be empty")

    # Check that command starts with allowed base command
    base_cmd = args[0]
    if base_cmd not in ALLOWED_COMMANDS:
        raise ValueError(
            f"Command '{base_cmd}' not allowed. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"
        )

    return True
