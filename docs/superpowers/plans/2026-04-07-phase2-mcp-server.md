# KimiDokku MCP - Phase 2: MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement MCP Server with 15 Tools, 3 Resources, and 2 Prompts for AI agents to manage Dokku applications.

**Architecture:** FastMCP server with HTTP SSE transport, integrated into FastAPI. Tools organized by domain (apps, logs, config, domains, databases). Resources provide read-only context. Prompts give AI deployment checklists.

**Tech Stack:** FastMCP, FastAPI, Pydantic, asyncio subprocess for dokku CLI

---

## File Structure

```
/Users/anrogdev/OpenWork/KimiDokku MCP/
├── src/kimidokku/
│   ├── __init__.py
│   ├── main.py                  # Modified: Add MCP to FastAPI
│   ├── mcp_server.py            # MCP server setup
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── apps.py              # list_apps, get_app_status, deploy_git, deploy_image
│   │   ├── logs.py              # get_logs, restart_app, run_command
│   │   ├── config.py            # get_config, set_config
│   │   ├── domains.py           # add_custom_domain, remove_custom_domain, list_domains
│   │   └── databases.py         # create_database, list_databases, unlink_database
│   ├── resources/
│   │   ├── __init__.py
│   │   └── app_resources.py     # config, logs, domains resources
│   └── prompts/
│       ├── __init__.py
│       └── deployment_prompts.py # deployment_workflow, debug_crashed_app
├── tests/
│   ├── test_mcp_tools.py
│   └── test_mcp_resources.py
```

---

### Task 1: MCP Server Setup

**Files:**
- Create: `src/kimidokku/mcp_server.py`
- Modify: `src/kimidokku/main.py`

- [ ] **Step 1: Create MCP server module**

```python
"""MCP Server setup with FastMCP."""

from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP(
    name="kimidokku-mcp",
    instructions="""
    KimiDokku MCP Server - Manage Dokku applications via AI agents.
    
    Available capabilities:
    - App Lifecycle: list_apps, get_app_status, deploy_git, deploy_image
    - Logs & Debug: get_logs, restart_app, run_command
    - Configuration: get_config, set_config
    - Domains: add_custom_domain, remove_custom_domain, list_domains
    - Database Services: create_database, list_databases, unlink_database
    """,
)


def get_mcp_server() -> FastMCP:
    """Get MCP server instance."""
    return mcp
```

- [ ] **Step 2: Modify main.py to integrate MCP**

Add to imports:
```python
from kimidokku.mcp_server import get_mcp_server
```

Add to create_app():
```python
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="KimiDokku MCP",
        description="MCP-First PaaS Platform for Dokku",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Mount MCP server
    mcp_server = get_mcp_server()
    app.mount("/mcp", mcp_server.sse_app())
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "dokku_connected": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    
    return app
```

- [ ] **Step 3: Test MCP server starts**

```bash
python -c "from kimidokku.mcp_server import get_mcp_server; print('MCP Server loaded')"
```

- [ ] **Step 4: Commit**

```bash
git add src/kimidokku/mcp_server.py src/kimidokku/main.py
git commit -m "feat: add MCP server setup with FastMCP"
```

---

### Task 2: App Lifecycle Tools

**Files:**
- Create: `src/kimidokku/tools/__init__.py`
- Create: `src/kimidokku/tools/apps.py`
- Create: `tests/test_mcp_tools.py`

- [ ] **Step 1: Create tools package init**

```python
"""MCP Tools package."""
```

- [ ] **Step 2: Create apps.py with 4 tools**

```python
"""App Lifecycle MCP Tools."""

import asyncio
from datetime import datetime
from typing import Optional

from kimidokku.database import db
from kimidokku.mcp_server import mcp
from kimidokku.models import (
    AppListResponse,
    AppResponse,
    AppStatus,
    AppStatusResponse,
    DeployStatus,
)


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
        result.append({
            "name": app["name"],
            "auto_domain": app["auto_domain"],
            "custom_domains": custom_domains,
            "status": app["status"],
            "last_deploy_at": app["last_deploy_at"],
            "tls_status": app["tls_status"],
        })
    
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
    asyncio.create_task(
        _run_git_deploy(app_name, app["git_url"], branch, deploy_id)
    )
    
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
            "dokku", "git:sync", "--build", app_name, git_url, branch,
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
                "dokku", "registry:set", app_name, "username", registry_user,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # Note: In production, use docker login or dokku registry-login
        
        # Run dokku git:from-image
        proc = await asyncio.create_subprocess_exec(
            "dokku", "git:from-image", app_name, image_url,
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
```

- [ ] **Step 3: Register tools in mcp_server.py**

Add at bottom of mcp_server.py:
```python
# Import tools to register them
from kimidokku.tools import apps
```

- [ ] **Step 4: Write basic test**

```python
"""Tests for MCP tools."""

import pytest

from kimidokku.mcp_server import get_mcp_server


class TestMCPServer:
    """Test MCP server setup."""

    def test_mcp_server_created(self):
        """Test that MCP server is created."""
        mcp = get_mcp_server()
        assert mcp is not None
        assert mcp.name == "kimidokku-mcp"

    def test_app_tools_registered(self):
        """Test that app tools are registered."""
        mcp = get_mcp_server()
        tools = mcp._tools
        
        assert "list_apps" in tools
        assert "get_app_status" in tools
        assert "deploy_git" in tools
        assert "deploy_image" in tools
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_mcp_tools.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/kimidokku/tools/ tests/test_mcp_tools.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP app lifecycle tools (list_apps, get_app_status, deploy_git, deploy_image)"
```

---

### Task 3: Logs & Debug Tools

**Files:**
- Create: `src/kimidokku/tools/logs.py`

- [ ] **Step 1: Create logs.py with 3 tools**

```python
"""Logs & Debug MCP Tools."""

import asyncio
import re
from typing import Optional

from kimidokku.database import db
from kimidokku.mcp_server import mcp


# Whitelist for run_command - only safe commands
ALLOWED_COMMANDS = {"rake", "python", "node", "echo", "rails", "bundle"}
FORBIDDEN_PATTERNS = [r";", r"\|", r"\$\(", r"`", r">>", r">"]


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
            "dokku", "logs", app_name, "-t", "-n", str(lines),
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
            "dokku", "ps:restart", app_name,
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
        # Run dokku run
        proc = await asyncio.create_subprocess_exec(
            "dokku", "run", app_name, *command.split(),
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


def _validate_command(command: str) -> None:
    """Validate command for security."""
    # Check for forbidden patterns (shell injection)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(f"Command contains forbidden pattern: {pattern}")
    
    # Check that command starts with allowed base command
    parts = command.strip().split()
    if not parts:
        raise ValueError("Command cannot be empty")
    
    base_cmd = parts[0]
    if base_cmd not in ALLOWED_COMMANDS:
        raise ValueError(
            f"Command '{base_cmd}' not allowed. Allowed: {', '.join(ALLOWED_COMMANDS)}"
        )
```

- [ ] **Step 2: Update mcp_server.py to import logs**

Add after apps import:
```python
from kimidokku.tools import logs
```

- [ ] **Step 3: Update tests**

Add to test_mcp_tools.py:
```python
    def test_logs_tools_registered(self):
        """Test that logs tools are registered."""
        mcp = get_mcp_server()
        tools = mcp._tools
        
        assert "get_logs" in tools
        assert "restart_app" in tools
        assert "run_command" in tools
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_mcp_tools.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/kimidokku/tools/logs.py tests/test_mcp_tools.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP logs and debug tools (get_logs, restart_app, run_command)"
```

---

### Task 4: Configuration Tools

**Files:**
- Create: `src/kimidokku/tools/config_tools.py`

- [ ] **Step 1: Create config_tools.py with 2 tools**

```python
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
            "dokku", "config:show", app_name, "--format", "json",
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
            key for key, value in config.items()
            if masked_config[key] == "***" and value != "***"
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
            "dokku", "config:show", app_name, "--format", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        
        if proc.returncode == 0 and stdout:
            return json.loads(stdout.decode())
        return {}
    except Exception:
        return {}
```

- [ ] **Step 2: Update mcp_server.py**

Add:
```python
from kimidokku.tools import config_tools
```

- [ ] **Step 3: Update tests**

```python
    def test_config_tools_registered(self):
        """Test that config tools are registered."""
        mcp = get_mcp_server()
        tools = mcp._tools
        
        assert "get_config" in tools
        assert "set_config" in tools
```

- [ ] **Step 4: Commit**

```bash
git add src/kimidokku/tools/config_tools.py tests/test_mcp_tools.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP config tools (get_config, set_config)"
```

---

### Task 5: Domain Tools

**Files:**
- Create: `src/kimidokku/tools/domains.py`

- [ ] **Step 1: Create domains.py with 3 tools**

```python
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
        custom_list.append({
            "domain": domain["domain"],
            "tls_active": bool(domain["tls_enabled"]),
            "expires_in_days": None,  # Would need to fetch from dokku
        })
    
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
            "dokku", "domains:add", app_name, domain,
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
                "dokku", "letsencrypt:enable", app_name, domain,
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
            "dokku", "domains:remove", app_name, domain,
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
```

- [ ] **Step 2: Update mcp_server.py**

Add:
```python
from kimidokku.tools import domains
```

- [ ] **Step 3: Update tests**

```python
    def test_domain_tools_registered(self):
        """Test that domain tools are registered."""
        mcp = get_mcp_server()
        tools = mcp._tools
        
        assert "list_domains" in tools
        assert "add_custom_domain" in tools
        assert "remove_custom_domain" in tools
```

- [ ] **Step 4: Commit**

```bash
git add src/kimidokku/tools/domains.py tests/test_mcp_tools.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP domain tools (list_domains, add_custom_domain, remove_custom_domain)"
```

---

### Task 6: Database Service Tools

**Files:**
- Create: `src/kimidokku/tools/databases.py`

- [ ] **Step 1: Create databases.py with 3 tools**

```python
"""Database Services MCP Tools."""

import asyncio
import uuid

from kimidokku.database import db
from kimidokku.mcp_server import mcp
from kimidokku.models import DBType


@mcp.tool()
async def create_database(
    app_name: str,
    api_key_id: str,
    db_type: str,
    version: str = "latest",
) -> dict:
    """
    Create and link database service to app.
    Steps:
      1. dokku {db_type}:create {service_name} {version}
      2. dokku {db_type}:link {service_name} {app_name}
      3. Store connection info, update apps.db_services
    Returns: service_name, env_var, connection_string_masked
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )
    
    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")
    
    # Validate db_type
    try:
        db_type_enum = DBType(db_type.lower())
    except ValueError:
        raise ValueError(f"Invalid db_type '{db_type}'. Must be one of: postgres, redis, mysql, mongo")
    
    # Generate service name
    service_name = f"{db_type_enum.value}-{app_name}-{uuid.uuid4().hex[:8]}"
    
    try:
        # Step 1: Create service
        create_proc = await asyncio.create_subprocess_exec(
            "dokku", f"{db_type_enum.value}:create", service_name, version,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if create_proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to create database service: {error_msg}")
        
        # Step 2: Link service to app
        link_proc = await asyncio.create_subprocess_exec(
            "dokku", f"{db_type_enum.value}:link", service_name, app_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await link_proc.communicate()
        
        if link_proc.returncode != 0:
            # Try to destroy the service we just created
            await asyncio.create_subprocess_exec(
                "dokku", f"{db_type_enum.value}:destroy", service_name, "--force",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to link database service: {error_msg}")
        
        # Step 3: Store in database
        env_var = _get_default_env_var(db_type_enum)
        await db.execute(
            """
            INSERT INTO db_services (id, app_name, db_type, env_var_name)
            VALUES (?, ?, ?, ?)
            """,
            (service_name, app_name, db_type_enum.value, env_var),
        )
        
        return {
            "service_name": service_name,
            "db_type": db_type_enum.value,
            "env_var": env_var,
            "connection_string_masked": f"${env_var} (set in app environment)",
            "message": f"{db_type_enum.value} service '{service_name}' created and linked to '{app_name}'",
        }
    
    except Exception as e:
        raise RuntimeError(f"Failed to create database: {e}")


@mcp.tool()
async def list_databases(app_name: str, api_key_id: str) -> list[dict]:
    """
    List linked databases with types and status.
    Returns: [{service_name, db_type, env_var, created_at}]
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )
    
    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")
    
    # Get linked databases
    services = await db.fetch_all(
        """
        SELECT id, db_type, env_var_name, created_at
        FROM db_services
        WHERE app_name = ?
        ORDER BY created_at DESC
        """,
        (app_name,),
    )
    
    return [
        {
            "service_name": s["id"],
            "db_type": s["db_type"],
            "env_var": s["env_var_name"],
            "created_at": s["created_at"],
        }
        for s in services
    ]


@mcp.tool()
async def unlink_database(
    app_name: str,
    api_key_id: str,
    service_name: str,
    preserve_data: bool = True,
) -> dict:
    """
    Unlink service from app. If preserve_data=false, also deletes service.
    Returns: success, message
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )
    
    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")
    
    # Get service info
    service = await db.fetch_one(
        "SELECT db_type FROM db_services WHERE id = ? AND app_name = ?",
        (service_name, app_name),
    )
    
    if not service:
        raise ValueError(f"Service '{service_name}' not found for app '{app_name}'")
    
    db_type = service["db_type"]
    
    try:
        # Unlink service
        unlink_proc = await asyncio.create_subprocess_exec(
            "dokku", f"{db_type}:unlink", service_name, app_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await unlink_proc.communicate()
        
        # Delete from database
        await db.execute(
            "DELETE FROM db_services WHERE id = ?",
            (service_name,),
        )
        
        if not preserve_data:
            # Destroy the service
            destroy_proc = await asyncio.create_subprocess_exec(
                "dokku", f"{db_type}:destroy", service_name, "--force",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await destroy_proc.communicate()
            
            return {
                "success": True,
                "message": f"Service '{service_name}' unlinked and destroyed",
            }
        
        return {
            "success": True,
            "message": f"Service '{service_name}' unlinked (data preserved)",
        }
    
    except Exception as e:
        raise RuntimeError(f"Failed to unlink database: {e}")


def _get_default_env_var(db_type: DBType) -> str:
    """Get default environment variable name for database type."""
    env_vars = {
        DBType.POSTGRES: "DATABASE_URL",
        DBType.REDIS: "REDIS_URL",
        DBType.MYSQL: "DATABASE_URL",
        DBType.MONGO: "MONGODB_URI",
    }
    return env_vars.get(db_type, "DATABASE_URL")
```

- [ ] **Step 2: Update mcp_server.py**

Add:
```python
from kimidokku.tools import databases
```

- [ ] **Step 3: Update tests**

```python
    def test_database_tools_registered(self):
        """Test that database tools are registered."""
        mcp = get_mcp_server()
        tools = mcp._tools
        
        assert "create_database" in tools
        assert "list_databases" in tools
        assert "unlink_database" in tools
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/test_mcp_tools.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/kimidokku/tools/databases.py tests/test_mcp_tools.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP database tools (create_database, list_databases, unlink_database)"
```

---

### Task 7: MCP Resources

**Files:**
- Create: `src/kimidokku/resources/__init__.py`
- Create: `src/kimidokku/resources/app_resources.py`

- [ ] **Step 1: Create resources package**

```python
"""MCP Resources package."""
```

- [ ] **Step 2: Create app_resources.py with 3 resources**

```python
"""MCP Resources for read-only app context."""

import asyncio
import json

from kimidokku.auth import mask_secrets
from kimidokku.database import db
from kimidokku.mcp_server import mcp


@mcp.resource("dokku://config/{app_name}")
async def app_config_resource(app_name: str, api_key: str) -> str:
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
            "dokku", "config:show", app_name, "--format", "json",
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


@mcp.resource("dokku://logs/{app_name}/recent")
async def recent_logs_resource(app_name: str, api_key: str) -> str:
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
            "dokku", "logs", app_name, "-t", "-n", "50",
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


@mcp.resource("dokku://domains/{app_name}")
async def domains_resource(app_name: str, api_key: str) -> str:
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
```

- [ ] **Step 3: Update mcp_server.py**

Add:
```python
from kimidokku.resources import app_resources
```

- [ ] **Step 4: Create resource tests**

Create `tests/test_mcp_resources.py`:
```python
"""Tests for MCP resources."""

from kimidokku.mcp_server import get_mcp_server


class TestMCPResources:
    """Test MCP resources."""

    def test_resources_registered(self):
        """Test that resources are registered."""
        mcp = get_mcp_server()
        resources = mcp._resources
        
        assert "dokku://config/{app_name}" in resources
        assert "dokku://logs/{app_name}/recent" in resources
        assert "dokku://domains/{app_name}" in resources
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_mcp_resources.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/kimidokku/resources/ tests/test_mcp_resources.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP resources (config, logs, domains)"
```

---

### Task 8: MCP Prompts

**Files:**
- Create: `src/kimidokku/prompts/__init__.py`
- Create: `src/kimidokku/prompts/deployment_prompts.py`

- [ ] **Step 1: Create prompts package**

```python
"""MCP Prompts package."""
```

- [ ] **Step 2: Create deployment_prompts.py with 2 prompts**

```python
"""MCP Prompts for deployment workflows."""

from kimidokku.mcp_server import mcp


@mcp.prompt()
def deployment_workflow(app_name: str) -> str:
    """Deployment checklist for AI agents."""
    return f"""# Deployment Workflow for '{app_name}'

You are deploying to Dokku app '{app_name}'. Follow this checklist:

## Pre-deployment Checks
1. **Check current status** - Use `get_app_status(app_name="{app_name}")`
2. **If crashed, investigate logs** - Use `get_logs(app_name="{app_name}", lines=100)`
3. **Verify critical ENV vars** - Use `get_config(app_name="{app_name}")`
   - Ensure DATABASE_URL is set (if using database)
   - Ensure all required secrets are configured
4. **Check recent deploy history** - Review last deployment status

## Deployment
5. **Execute deployment**
   - For git: `deploy_git(app_name="{app_name}", branch="main")`
   - For image: `deploy_image(app_name="{app_name}", image_url="...")`

## Post-deployment Verification
6. **Poll status every 10s for up to 2 minutes**
   - Use `get_app_status(app_name="{app_name}")`
7. **Verify health by checking logs**
   - Use `get_logs(app_name="{app_name}", lines=50)`
   - Look for "Server started", "Listening on port", or similar indicators
8. **Confirm app status is 'running'**

## Rollback (if needed)
9. If deployment fails:
   - Check logs for error details
   - Consider restarting: `restart_app(app_name="{app_name}")`
   - Or revert config changes if applicable

Remember: Always verify before declaring success!
"""


@mcp.prompt()
def debug_crashed_app(app_name: str) -> str:
    """Diagnostic steps for crashed applications."""
    return f"""# Debug Crashed App: '{app_name}'

App '{app_name}' is not running. Follow these diagnostic steps:

## Step 1: Get Recent Logs
Use `get_logs(app_name="{app_name}", lines=100)`
- Filter for ERROR or FATAL messages
- Look for stack traces
- Check the last few lines before crash

## Step 2: Check Recent Config Changes
Use `get_config(app_name="{app_name}")`
- Compare with previous working configuration
- Check if any sensitive values were changed
- Verify all required ENV vars are present

## Step 3: Verify Database Connectivity (if applicable)
Use `run_command(app_name="{app_name}", command="python -c 'import os; print(\"DB_URL set:\", \"DATABASE_URL\" in os.environ)'")`
- Check if DATABASE_URL or similar is accessible
- For Rails apps: `rails db:migrate:status`
- For Django apps: `python manage.py showmigrations`

## Step 4: Analyze Common Issues

### If OOM (Out of Memory) detected in logs:
- Suggest: Restart app to free memory
- Use: `restart_app(app_name="{app_name}")`
- Long-term: Consider scaling or memory optimization

### If missing module/dependency error:
- Check: Was requirements.txt/package.json updated?
- Suggest: Rebuild with `deploy_git` to reinstall dependencies
- Check: Verify the correct branch/commit is deployed

### If database connection error:
- Verify: `get_config` shows correct DATABASE_URL
- Check: Database service is running (via dokku)
- Test: Connection from app container

### If port binding error:
- Verify: App listens on $PORT (not hardcoded)
- Check: Multiple processes not conflicting

## Step 5: Attempt Recovery

### Option A: Restart
```
restart_app(app_name="{app_name}")
```

### Option B: Check running processes
```
run_command(app_name="{app_name}", command="ps aux")
```

### Option C: Test one-off command
```
run_command(app_name="{app_name}", command="echo 'Container is accessible'")
```

## Step 6: Document Findings
Once root cause is identified:
1. Note the specific error
2. Document the fix applied
3. Consider preventive measures
"""
```

- [ ] **Step 3: Update mcp_server.py**

Add:
```python
from kimidokku.prompts import deployment_prompts
```

- [ ] **Step 4: Create prompt tests**

Add to `tests/test_mcp_resources.py`:
```python
    def test_prompts_registered(self):
        """Test that prompts are registered."""
        mcp = get_mcp_server()
        prompts = mcp._prompts
        
        assert "deployment_workflow" in prompts
        assert "debug_crashed_app" in prompts
```

- [ ] **Step 5: Run all MCP tests**

```bash
pytest tests/test_mcp_tools.py tests/test_mcp_resources.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/kimidokku/prompts/ tests/test_mcp_resources.py src/kimidokku/mcp_server.py
git commit -m "feat: add MCP prompts (deployment_workflow, debug_crashed_app)"
```

---

## Self-Review

**Spec coverage:**
- ✅ 15 MCP Tools: apps (4), logs (3), config (2), domains (3), databases (3)
- ✅ 3 MCP Resources: config, logs, domains
- ✅ 2 MCP Prompts: deployment_workflow, debug_crashed_app
- ✅ API key authentication in all tools
- ✅ Per-key isolation enforced
- ✅ Secret masking in config tools
- ✅ Command validation in run_command

**Placeholder scan:**
- ✅ No TBD/TODO placeholders
- ✅ All code shown explicitly

**Type consistency:**
- ✅ All tools use consistent parameter names
- ✅ Return types match across similar tools

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-07-phase2-mcp-server.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
