# KimiDokku MCP Usage Guide

## For Human Users: Connecting to MCP

### What is MCP?

MCP (Model Context Protocol) - это протокол для подключения AI-ассистентов к внешним инструментам. KimiDokku MCP позволяет AI-агентам управлять приложениями на вашем Dokku сервере.

### Connection Methods

#### Method 1: Direct HTTP (SSE)

Подключение через HTTP с Server-Sent Events:

```bash
# MCP endpoint URL
https://kimidokku.clawtech.ru/mcp

# Authentication: API Key in header
X-API-Key: <your-api-key>
```

**Configuration for Claude Desktop:**

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "kimidokku": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sse",
        "--url",
        "https://kimidokku.clawtech.ru/mcp"
      ],
      "env": {
        "X_API_KEY": "<your-api-key>"
      }
    }
  }
}
```

#### Method 2: WebSocket

Для real-time взаимодействия:

```
wss://kimidokku.clawtech.ru/mcp/ws
```

#### Method 3: Stdio (Local Bridge)

Локальный bridge для CLI инструментов:

```bash
# Install MCP bridge
npm install -g @kimidokku/mcp-bridge

# Connect
kimidokku-mcp --server https://kimidokku.clawtech.ru --key <api-key>
```

### Getting API Key

1. **Via Web UI:**
   ```
   https://kimidokku.clawtech.ru/keys
   ```
   Login: `admin` / `<password>`
   Click "Create New Key"

2. **Via REST API:**
   ```bash
   curl -u admin:<password> \
     -H "X-CSRF-Token: <csrf-token>" \
     -X POST \
     -d '{"name": "my-mcp-key", "max_apps": 5}' \
     https://kimidokku.clawtech.ru/api/keys/
   ```

3. **Via Dokku CLI:**
   ```bash
   ssh -p 2233 root@clawtech.ru "sqlite3 /var/lib/dokku/data/storage/kimidokku/kimidokku.db 'INSERT INTO api_keys (id, name, max_apps) VALUES (\"'$(uuidgen)'\", \"mcp-key\", 10);'"
   ```

### Available MCP Tools

После подключения AI-агент получает доступ к инструментам:

| Tool | Description |
|------|-------------|
| `list_apps` | List all your apps |
| `get_app_status` | Check app status and health |
| `create_app` | Create new Dokku app |
| `delete_app` | Delete app (with force=true) |
| `deploy_git` | Deploy from git repository |
| `deploy_image` | Deploy from Docker image |
| `get_logs` | Get application logs |
| `restart_app` | Restart application |
| `run_command` | Run command in app container |
| `get_config` | Get environment variables |
| `set_config` | Set environment variable |
| `add_custom_domain` | Add custom domain |
| `remove_custom_domain` | Remove custom domain |
| `list_domains` | List all domains |
| `create_database` | Create database service |
| `list_databases` | List linked databases |
| `unlink_database` | Unlink database from app |

### MCP Resources

Доступные ресурсы для получения информации:

```
dokku://config/{app_name}          # App configuration
dokku://logs/{app_name}/recent     # Recent logs
dokku://domains/{app_name}         # App domains
dokku://databases/{app_name}       # Linked databases
dokku://deploys/{app_name}         # Deploy history
```

### MCP Prompts

Встроенные prompts для AI:

- `deployment_workflow` - Guide for deploying applications
- `debug_crashed_app` - Troubleshooting crashed applications

---

## For AI Agents: Deployment Guide

### Quick Deploy Workflow

```yaml
# AI Agent Deployment Steps
step_1:  # Check current state
  tool: list_apps
  api_key_id: "<api-key-id>"

step_2:  # Create new app
  tool: create_app
  api_key_id: "<api-key-id>"
  name: "my-new-app"
  git_url: "https://github.com/user/repo.git"
  branch: "main"

step_3:  # Deploy from git
  tool: deploy_git
  app_name: "my-new-app"
  api_key_id: "<api-key-id>"
  branch: "main"

step_4:  # Check status
  tool: get_app_status
  app_name: "my-new-app"
  api_key_id: "<api-key-id>"

step_5:  # Get logs if needed
  tool: get_logs
  app_name: "my-new-app"
  api_key_id: "<api-key-id>"
  lines: 50
```

### Deployment Patterns

#### Pattern 1: Git-Based Deployment

```python
# AI Agent code example
async def deploy_from_git(repo_url: str, app_name: str):
    """Deploy application from git repository."""
    
    # 1. Create app
    create_result = await mcp_client.call_tool(
        "create_app",
        {
            "api_key_id": API_KEY_ID,
            "name": app_name,
            "git_url": repo_url,
            "branch": "main"
        }
    )
    
    # 2. Deploy
    deploy_result = await mcp_client.call_tool(
        "deploy_git",
        {
            "app_name": app_name,
            "api_key_id": API_KEY_ID,
            "branch": "main"
        }
    )
    
    # 3. Check status
    status = await mcp_client.call_tool(
        "get_app_status",
        {
            "app_name": app_name,
            "api_key_id": API_KEY_ID
        }
    )
    
    return {
        "app": create_result,
        "deploy": deploy_result,
        "status": status
    }
```

#### Pattern 2: Docker Image Deployment

```python
async def deploy_from_image(image_url: str, app_name: str):
    """Deploy from Docker registry."""
    
    # 1. Create app (without git)
    await mcp_client.call_tool(
        "create_app",
        {
            "api_key_id": API_KEY_ID,
            "name": app_name
        }
    )
    
    # 2. Deploy from image
    deploy_result = await mcp_client.call_tool(
        "deploy_image",
        {
            "app_name": app_name,
            "api_key_id": API_KEY_ID,
            "image_url": image_url,
            "registry_user": None,  # or username if private
            "registry_pass": None   # or password if private
        }
    )
    
    return deploy_result
```

#### Pattern 3: Environment Configuration

```python
async def configure_app(app_name: str, config: dict):
    """Set environment variables for app."""
    
    results = []
    for key, value in config.items():
        result = await mcp_client.call_tool(
            "set_config",
            {
                "app_name": app_name,
                "api_key_id": API_KEY_ID,
                "key": key,
                "value": value
            }
        )
        results.append(result)
    
    return results
```

#### Pattern 4: Database Setup

```python
async def setup_database(app_name: str, db_type: str = "postgres"):
    """Create and link database to app."""
    
    # 1. Create database
    db_result = await mcp_client.call_tool(
        "create_database",
        {
            "app_name": app_name,
            "api_key_id": API_KEY_ID,
            "db_type": db_type
        }
    )
    
    # 2. Database is auto-linked, get connection info
    dbs = await mcp_client.call_tool(
        "list_databases",
        {
            "app_name": app_name,
            "api_key_id": API_KEY_ID
        }
    )
    
    return {
        "database": db_result,
        "linked": dbs
    }
```

### Error Handling

```python
from kimidokku.exceptions import (
    AppNotFoundError,
    ValidationError,
    PermissionDeniedError,
    CommandError
)

async def safe_deploy(app_name: str):
    """Deploy with error handling."""
    try:
        result = await mcp_client.call_tool("deploy_git", {...})
        return {"success": True, "result": result}
    
    except AppNotFoundError:
        return {"error": "App not found", "action": "create_app first"}
    
    except ValidationError as e:
        return {"error": f"Validation failed: {e}"}
    
    except PermissionDeniedError:
        return {"error": "Invalid API key or key revoked"}
    
    except CommandError as e:
        return {"error": f"Dokku command failed: {e}"}
```

### Webhook Integration

Для автоматического деплоя при git push:

```bash
# GitHub Webhook URL
https://kimidokku.clawtech.ru/webhook/github/{app_name}

# GitLab Webhook URL
https://kimidokku.clawtech.ru/webhook/gitlab/{app_name}

# Headers required:
X-Hub-Signature-256: sha256=<hmac_signature>  # GitHub
X-Gitlab-Token: <webhook_secret>              # GitLab
```

**Setup via MCP:**

```python
# 1. Get current app info
app_info = await mcp_client.call_tool(
    "get_app_status",
    {"app_name": "myapp", "api_key_id": API_KEY_ID}
)

# 2. Webhook secret is auto-generated on app creation
# 3. Configure in GitHub/GitLab repository settings
```

### Best Practices for AI Agents

#### 1. Always Check Before Create

```python
# Check if app exists before creating
apps = await mcp_client.call_tool("list_apps", {"api_key_id": API_KEY_ID})
if any(a["name"] == app_name for a in apps):
    # App exists, use it
    pass
else:
    # Create new
    await mcp_client.call_tool("create_app", {...})
```

#### 2. Verify Deploy Status

```python
import asyncio

async def wait_for_deploy(app_name: str, timeout: int = 120):
    """Wait for deployment to complete."""
    start = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start < timeout:
        status = await mcp_client.call_tool(
            "get_app_status",
            {"app_name": app_name, "api_key_id": API_KEY_ID}
        )
        
        if status["status"] == "running":
            return {"success": True, "status": status}
        elif status["status"] == "error":
            logs = await mcp_client.call_tool(
                "get_logs",
                {"app_name": app_name, "api_key_id": API_KEY_ID, "lines": 50}
            )
            return {"success": False, "error": "Deployment failed", "logs": logs}
        
        await asyncio.sleep(5)
    
    return {"success": False, "error": "Timeout waiting for deployment"}
```

#### 3. Resource Limits

```python
# Check API key limits before creating
key_info = await mcp_client.read_resource(f"dokku://config/{app_name}")
# max_apps is enforced, but good to check beforehand
```

#### 4. Logging

```python
# Always get logs on failure
async def deploy_with_logs(app_name: str, branch: str):
    try:
        deploy_result = await mcp_client.call_tool("deploy_git", {...})
        
        # Wait for completion
        await asyncio.sleep(30)
        
        # Check status
        status = await mcp_client.call_tool("get_app_status", {...})
        
        if status["status"] != "running":
            logs = await mcp_client.call_tool("get_logs", {...})
            return {"success": False, "logs": logs}
        
        return {"success": True}
    
    except Exception as e:
        logs = await mcp_client.call_tool("get_logs", {...})
        return {"success": False, "error": str(e), "logs": logs}
```

### Domain Configuration

```python
async def setup_domain(app_name: str, domain: str):
    """Add custom domain to app."""
    
    # Add domain
    result = await mcp_client.call_tool(
        "add_custom_domain",
        {
            "app_name": app_name,
            "api_key_id": API_KEY_ID,
            "domain": domain
        }
    )
    
    # Note: SSL must be configured manually via Dokku CLI
    # dokku letsencrypt:enable {app_name}
    
    return result
```

### Complete Deployment Example

```python
async def full_deployment_workflow(
    app_name: str,
    git_url: str,
    env_vars: dict,
    db_type: str = None
):
    """Complete deployment workflow."""
    
    results = {
        "steps": [],
        "success": False
    }
    
    try:
        # 1. Create app
        step1 = await mcp_client.call_tool(
            "create_app",
            {
                "api_key_id": API_KEY_ID,
                "name": app_name,
                "git_url": git_url,
                "branch": "main"
            }
        )
        results["steps"].append({"create_app": step1})
        
        # 2. Setup database if needed
        if db_type:
            step2 = await mcp_client.call_tool(
                "create_database",
                {
                    "app_name": app_name,
                    "api_key_id": API_KEY_ID,
                    "db_type": db_type
                }
            )
            results["steps"].append({"create_database": step2})
        
        # 3. Set environment variables
        for key, value in env_vars.items():
            step3 = await mcp_client.call_tool(
                "set_config",
                {
                    "app_name": app_name,
                    "api_key_id": API_KEY_ID,
                    "key": key,
                    "value": value
                }
            )
            results["steps"].append({f"set_config_{key}": step3})
        
        # 4. Deploy
        step4 = await mcp_client.call_tool(
            "deploy_git",
            {
                "app_name": app_name,
                "api_key_id": API_KEY_ID,
                "branch": "main"
            }
        )
        results["steps"].append({"deploy_git": step4})
        
        # 5. Wait and verify
        await asyncio.sleep(60)
        step5 = await mcp_client.call_tool(
            "get_app_status",
            {"app_name": app_name, "api_key_id": API_KEY_ID}
        )
        results["steps"].append({"get_app_status": step5})
        
        results["success"] = step5["status"] == "running"
        results["app_url"] = f"https://{app_name}.clawtech.ru"
        
    except Exception as e:
        results["error"] = str(e)
        # Get logs on failure
        try:
            logs = await mcp_client.call_tool(
                "get_logs",
                {"app_name": app_name, "api_key_id": API_KEY_ID, "lines": 100}
            )
            results["logs"] = logs
        except:
            pass
    
    return results
```

---

## REST API Reference

### Authentication

All REST API requests require Basic Auth:
```
Username: admin
Password: <configured_password>
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/keys` | List API keys |
| POST | `/api/keys` | Create new API key |
| GET | `/api/keys/{id}` | Get key details |
| POST | `/api/keys/{id}/revoke` | Revoke key |
| DELETE | `/api/keys/{id}` | Delete key |
| GET | `/health` | Health check |

### Example: Create API Key via REST

```bash
curl -u admin:<password> \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <csrf_token>" \
  -X POST \
  -d '{"name": "ai-agent-key", "max_apps": 10}' \
  https://kimidokku.clawtech.ru/api/keys
```

---

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to MCP

**Solutions:**
1. Check API key is valid (not revoked)
2. Verify URL: `https://kimidokku.clawtech.ru/mcp`
3. Check firewall allows HTTPS (443)
4. Verify SSL certificate: `curl -v https://kimidokku.clawtech.ru/health`

### Deployment Failures

**Problem:** Deploy fails with "CommandError"

**Actions:**
1. Check app logs: `get_logs` tool
2. Verify git URL is accessible
3. Check buildpack detection (package.json, requirements.txt, etc.)
4. Review Dokku build logs

### Rate Limiting

**Problem:** 429 Too Many Requests

**Limits:**
- Webhooks: 10/minute
- UI routes: 30/minute
- API routes: 100/minute

**Solution:** Add delays between requests

### Permission Denied

**Problem:** Cannot create more apps

**Cause:** API key reached max_apps limit (default: 10)

**Solution:** 
- Create new key with higher limit
- Delete unused apps
- Revoke old keys

---

## Support

- **Documentation:** This file
- **Server Admin:** @Rogdev (Telegram: @Rogdev_Sec_alert_bot)
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Dokku Docs:** https://dokku.com/docs/

---

## Summary

**For Humans:**
1. Get API key from Web UI or REST API
2. Configure MCP client with URL and key
3. AI agent can now manage apps

**For AI Agents:**
1. Use `create_app` + `deploy_git` for new apps
2. Use `deploy_image` for Docker-based apps
3. Use `create_database` for database setup
4. Always check status and logs after deploy
5. Handle errors gracefully

**Security:**
- Never expose API keys
- Use environment variables for secrets
- Enable webhooks only with signature verification
- Monitor CrowdSec for attacks
