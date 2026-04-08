**PRD: KimiDokku MCP-First PaaS Platform**

## 1. Overview

**Vision**: Превращение Dokku в AI-native PaaS платформу, где AI-агенты разработчиков управляют жизненным циклом приложений через Model Context Protocol (MCP), а веб-админка служит вспомогательным инструментом для операторов (human-in-the-loop).

**Core Principle**: MCP First — все функции управления приложением доступны через MCP Tools; REST API ограничен вебхуками и служебными эндпоинтами.

---

## 2. Architecture

```yaml
Stack:
  Runtime: Python 3.11+
  Web Framework: FastAPI (async)
  MCP Framework: FastMCP (HTTP SSE transport)
  Database: SQLite (aiosqlite)
  Process Management: asyncio.create_subprocess_exec (local dokku CLI)

Network:
  Transport: HTTPS/TLS (обязательно для MCP SSE)
  Pattern: AI Agent (laptop) ← HTTPS → KimiDokku (VPS) → Local Dokku Daemon

Components:
  - MCP Server (/mcp/sse, /mcp/messages)
  - REST API (/webhook/github, /webhook/gitlab, /health, /api/* minimal)
  - Web Admin UI (HTMX, server-side rendering)
  - Background Tasks: TLS renewal checks (cron), deploy cleanup
```

---

## 3. Domain Model (SQLite Schema)

```sql
-- Глобальная конфигурация платформы
CREATE TABLE platform_config (
    key TEXT PRIMARY KEY,
    value TEXT
);
-- KIMIDOKKU_DOMAIN = app.example.com

-- API Keys (Per-key limit: 10 apps)
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY, -- UUID4
    name TEXT, -- human-readable label (e.g., "Agent Team A")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    max_apps INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT 1
);

-- Приложения Dokku (создаются только через UI)
CREATE TABLE apps (
    name TEXT PRIMARY KEY, -- dokku app name (e.g., "app-a1b2c3")
    api_key_id TEXT REFERENCES api_keys(id),
    auto_domain TEXT, -- generated: app-a1b2c3.app.example.com
    git_url TEXT,
    branch TEXT DEFAULT 'main',
    status TEXT CHECK(status IN ('running', 'stopped', 'crashed', 'deploying')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_deploy_at TIMESTAMP,
    tls_status TEXT CHECK(tls_status IN ('active', 'expiring', 'error', 'none')) DEFAULT 'none',
    tls_expires_at TIMESTAMP
);

-- Кастомные домены (алиасы)
CREATE TABLE custom_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT REFERENCES apps(name) ON DELETE CASCADE,
    domain TEXT UNIQUE NOT NULL, -- NAME.DOMAIN.RU
    tls_enabled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Database Services (Dokku plugins)
CREATE TABLE db_services (
    id TEXT PRIMARY KEY, -- dokku service name (e.g., "postgres-app-a1b2c3")
    app_name TEXT REFERENCES apps(name) ON DELETE CASCADE,
    db_type TEXT CHECK(db_type IN ('postgres', 'redis', 'mysql', 'mongo')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    env_var_name TEXT DEFAULT 'DATABASE_URL' -- or REDIS_URL, etc.
);

-- Deploy Logs (аудит)
CREATE TABLE deploy_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT REFERENCES apps(name),
    triggered_by TEXT CHECK(triggered_by IN ('mcp', 'webhook', 'ui')),
    git_ref TEXT,
    status TEXT CHECK(status IN ('success', 'failed', 'in_progress')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    error_message TEXT
);

-- CrowdSec (read-only cache для UI)
CREATE TABLE crowdsec_cache (
    ip TEXT PRIMARY KEY,
    country TEXT,
    scenario TEXT,
    banned_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

---

## 4. MCP Specification (Primary Interface)

**Transport**: HTTP SSE (`/mcp/sse`)  
**Auth**: `X-API-Key` header (per-key authentication)  
**Protocol**: JSON-RPC 2.0 via MCP

### 4.1 Tools (Agent Capabilities)

#### App Lifecycle
```python
@mcp.tool()
async def list_apps() -> list[dict]:
    """
    List all apps associated with this API key (max 10).
    Returns: [{name, auto_domain, custom_domains[], status, last_deploy_at, tls_status}]
    """
    # Query: SELECT * FROM apps WHERE api_key_id = ?

@mcp.tool()
async def get_app_status(app_name: str) -> dict:
    """
    Detailed status of specific app (must belong to caller's API key).
    Returns: {status, containers: [{type, count}], git_ref, tls_expires_in_days}
    """

@mcp.tool()
async def deploy_git(app_name: str, branch: str = "main") -> dict:
    """
    Trigger deployment from git repository (linked in app.git_url).
    Executes: dokku git:sync --build {app_name} {git_url} {branch}
    Returns: {deploy_id, status: 'queued', estimated_seconds: 120}
    """

@mcp.tool()
async def deploy_image(app_name: str, image_url: str, registry_user: str = None, registry_pass: str = None) -> dict:
    """
    Deploy from Docker image registry.
    Executes: dokku git:from-image {app_name} {image_url}
    """
```

#### Logs & Debug
```python
@mcp.tool()
async def get_logs(app_name: str, lines: int = 100) -> list[dict]:
    """
    Get recent logs (snapshot, not streaming).
    Returns structured: [{timestamp, process, level, message}]
    Level inference: ERROR (stderr/fatal), WARN (warning), INFO (default)
    """

@mcp.tool()
async def restart_app(app_name: str) -> dict:
    """Graceful restart. Returns {success, message}"""

@mcp.tool()
async def run_command(app_name: str, command: str) -> dict:
    """
    One-off command execution (dokku run).
    Security: Command whitelist validation (no shell injection)
    Returns: {stdout, stderr, exit_code}
    """
```

#### Configuration
```python
@mcp.tool()
async def get_config(app_name: str) -> dict:
    """
    Get ENV vars. Secrets auto-masked (values containing KEY, PASS, SECRET, TOKEN shown as ***)
    """

@mcp.tool()
async def set_config(app_name: str, variables: dict, restart: bool = True) -> dict:
    """
    Set multiple ENV vars atomically.
    Backup old config to config_history table before applying.
    If restart=true: triggers dokku ps:restart after config:set
    """
```

#### Domains
```python
@mcp.tool()
async def add_custom_domain(app_name: str, domain: str) -> dict:
    """
    Add NAME.DOMAIN.RU alias to app.
    Validation: domain must not be taken by another app.
    Auto-triggers: dokku domains:add + letsencrypt:enable (if applicable)
    Returns: {success, dns_status, tls_status}
    """

@mcp.tool()
async def remove_custom_domain(app_name: str, domain: str) -> dict:
    """Remove alias domain."""

@mcp.tool()
async def list_domains(app_name: str) -> dict:
    """
    Returns: {
      auto_domain: 'app-XXXX.app.example.com',
      custom_domains: [{domain, tls_active, expires_in_days}]
    }
    """
```

#### Database Services (DaaS)
```python
@mcp.tool()
async def create_database(app_name: str, db_type: str, version: str = "latest") -> dict:
    """
    Create and link database service to app.
    Steps:
      1. dokku {db_type}:create {service_name} {version}
      2. dokku {db_type}:link {service_name} {app_name}
      3. Store connection info, update apps.db_services
    Returns: {service_name, env_var, connection_string_masked}
    """

@mcp.tool()
async def list_databases(app_name: str) -> list[dict]:
    """List linked databases with types and status."""

@mcp.tool()
async def unlink_database(app_name: str, service_name: str, preserve_data: bool = True) -> dict:
    """
    Unlink service from app. If preserve_data=false, also deletes service.
    """
```

### 4.2 Resources (Read-Only Context)

```python
@mcp.resource("dokku://config/{app_name}")
async def app_config_resource(app_name: str) -> str:
    """Plain text KEY=VALUE (masked) for AI context window."""

@mcp.resource("dokku://logs/{app_name}/recent")
async def recent_logs_resource(app_name: str) -> str:
    """Last 50 lines of logs as plain text."""

@mcp.resource("dokku://domains/{app_name}")
async def domains_resource(app_name: str) -> str:
    """List of all domains serving this app."""
```

### 4.3 Prompts (Templates for AI)

```python
@mcp.prompt()
def deployment_workflow(app_name: str) -> str:
    return f"""
    You are deploying to Dokku app '{app_name}'. Follow this checklist:
    1. Check current status with get_app_status()
    2. If crashed, investigate logs before deploying
    3. Verify critical ENV vars are set (DATABASE_URL, etc.)
    4. Execute deploy_git() or deploy_image()
    5. Poll status every 10s for up to 2 minutes
    6. Verify health by checking logs for 'Server started' or similar
    """

@mcp.prompt()
def debug_crashed_app(app_name: str) -> str:
    return f"""
    App '{app_name}' is not running. Diagnostic steps:
    1. Get logs (last 100 lines, filter ERROR)
    2. Check recent config changes (compare with history)
    3. Verify database connectivity (ping via run_command if needed)
    4. If OOM (Out of Memory) detected in logs: suggest restart or scaling
    5. If missing module: suggest rebuild or dependency fix
    """
```

---

## 5. REST API Specification (Secondary)

**Auth**: Same `X-API-Key` header (except webhooks use HMAC)

### 5.1 Webhooks (Auto-Deploy)
```http
POST /webhook/github/{app_name}
X-Hub-Signature-256: sha256={hmac}

Body: GitHub push event
Logic:
  1. Verify HMAC against app.api_key.webhook_secret (stored in DB)
  2. Parse ref (refs/heads/main), compare to app.branch
  3. If match: trigger dokku git:sync --build (async)
  4. Log to deploy_logs with triggered_by='webhook'
  5. Return 200 OK immediately (don't wait for build)
```

```http
POST /webhook/gitlab/{app_name}
X-Gitlab-Token: {token}
Logic: Similar to GitHub
```

### 5.2 Health & Emergency
```http
GET /health
Returns: {status: "ok", dokku_connected: true, timestamp}

GET /api/apps/{app_name}/logs?lines=50
Auth: X-API-Key
Emergency use: Quick curl from phone when MCP unavailable
Response: text/plain (raw dokku logs)
```

---

## 6. Web Admin UI Specification (20/80 Principle)

**Scope**: Только просмотр и базовое управление, которое неудобно делать через AI (визуализация, генерация ключей, CrowdSec).

### 6.1 Dashboard (`/`)
```yaml
Cards:
  - Total Apps: X (running: Y, stopped: Z, crashed: W)
  - TLS Alerts: Apps with expiring certificates (< 10 days)
  - CrowdSec Status: Active bans count, last updated
  
Table: Recent Deploys (last 10 across all apps)
  - App name | Triggered By | Status | Time Ago
```

### 6.2 Apps List (`/apps`)
```yaml
Table:
  - Name | Auto Domain | Custom Domains | Status Badge | Last Deploy | Actions
  
Actions per row:
  - [View] → /apps/{name}
  - [Logs] → Modal with last N lines (refresh button, not auto)
  - [Restart] → With confirmation
```

### 6.3 App Detail (`/apps/{name}`)
**Tabs**:

**Overview**:
- Auto Domain (copy button)
- Status indicator + container counts
- Git URL + Branch
- TLS Status (expires in X days, or error)
- [Add Custom Domain] Button (input: NAME, validates uniqueness)

**Domains**:
- List: auto_domain (primary) + custom_domains[]
- Per domain: TLS status, [Remove] button
- Validation: DNS check (A-record points to server IP)

**Logs**:
- Textarea with last N lines (N = 100/500/1000 selector)
- [Refresh] button (no auto-update)
- Filter by process type (all/web/worker)

**Database**:
- List linked services (type, name, env_var)
- [Create Database] Dropdown: Type (postgres/redis/mysql/mongo)
- [Unlink] with warning about data loss

**API Key**:
- Display current key (masked: `xxxx-xxxx-xxxx-1234`)
- [Regenerate Key] (invalidates old, creates new UUID)
- [Copy to Clipboard]
- Warning: "This key grants access to this app via MCP"

**Deploy History**:
- Table of deploy_logs for this app
- Status (success/failed), git ref, timestamp, error message if failed

### 6.4 API Key Management (`/keys`)
```yaml
List of API Keys:
  - Key Name | Apps Count (X/10) | Created | [View Apps] | [Revoke]
  
Create Key:
  - Input: Name (label)
  - Generates UUID4, shows once (copy to clipboard)
  - Initial state: 0 apps (apps created later via UI with this key)
```

### 6.5 CrowdSec (`/security`)
```yaml
Status Card:
  - CrowdSec Active/Inactive
  - Total Bans (last 24h)
  - Top Attacker Countries

Bans Table:
  - IP | Country | Scenario | Banned At | Expires | [Unban]
  
Actions:
  - [Refresh] (pull fresh cscli data)
  - [Unban IP] (requires confirmation)
```

---

## 7. Security Specification

**S-1. API Key Isolation**
- Keys are UUID4, cryptographically random
- Each MCP/REST request validates key against `apps.api_key_id`
- Attempt to access app not owned by key → 403 Forbidden
- Max 10 apps per key (enforced at `apps` table INSERT)

**S-2. Command Injection Prevention**
- All dokku commands use `asyncio.create_subprocess_exec` (list args, no shell)
- App names validated: `^[a-z0-9-]+$` (lowercase alphanumeric + hyphen only)
- `run_command` tool: whitelist of allowed base commands (rake, python, node, echo), block `;`, `|`, `$()`, backticks

**S-3. Secret Masking**
- Config values containing case-insensitive substrings `KEY`, `PASS`, `SECRET`, `TOKEN`, `URL` (кроме HTTP/S URLs) отображаются как `***` в UI и MCP responses
- Full values доступны только через `dokku config:show` в CLI (вне scope UI/API)

**S-4. TLS/Transport**
- MCP SSE работает только over HTTPS (HSTS enforced)
- Webhook secrets: HMAC-SHA256 verification обязательна (reject if missing/invalid)

**S-5. CrowdSec (Human Only)**
- MCP tools не предоставляют управление банами (только UI)
- Unban требует повторного Basic Auth confirmation (или re-auth)

---

## 8. Deployment & Configuration

**Environment Variables**:
```bash
KIMIDOKKU_DOMAIN=app.example.com        # Базовый домен для auto-domains
DOKKU_HOST=localhost                      # Для dokku CLI (обычно localhost)
AUTH_USER=admin                           # UI Basic Auth
AUTH_PASS=changeme                        # UI Basic Auth
LETSENCRYPT_EMAIL=admin@example.com       # Для TLS
DB_PATH=/app/data/kimidokku.db            # SQLite path (mount volume)
WEBHOOK_SECRET_DEFAULT=optional-fallback  # Для webhook verify если app secret не задан
```

**Dokku Deployment**:
```bash
dokku apps:create kimidokku-ui
dokku config:set kimidokku-ui KIMIDOKKU_DOMAIN=app.example.com ...
dokku storage:mount kimidokku-ui /var/lib/dokku/data/storage/kimidokku:/app/data
dokku domains:add kimidokku-ui ui.example.com
dokku letsencrypt:enable kimidokku-ui
```

**Post-Setup (One-time)**:
```bash
# Настройка глобального домена для auto-domains (выполняется внутри UI или вручную)
dokku domains:set-global app.example.com
```

---

## 9. Acceptance Criteria

**MCP Layer**:
- [ ] AI агент с ключом может выполнить полный цикл: `list_apps` → `deploy_git` → `get_logs` → проверка статуса
- [ ] Агент может создать БД через `create_database` и получить подтверждение линковки
- [ ] Агент может добавить кастомный домен и получить TLS статус
- [ ] Per-key isolation работает (ключ A не видит app ключа B)
- [ ] Limit 10 apps per key enforced

**UI Layer**:
- [ ] Dashboard показывает точное количество apps по статусам (running/stopped/crashed)
- [ ] Генерация API ключа показывает UUID только один раз (copy to clipboard)
- [ ] CrowdSec виджет отображает актуальные баны (±1 минута)
- [ ] Unban IP работает из UI и сразу отображается в списке

**Integration**:
- [ ] GitHub webhook push → auto-deploy работает без участия MCP
- [ ] Auto-domain генерируется при создании app через UI (app-XXXXXX.app.DOMAIN.RU)
- [ ] TLS сертификат выпускается автоматически для auto-domain и custom domains
- [ ] При fail renew появляется красный индикатор в UI и запись в MCP доступных логах

**Security**:
- [ ] Command injection попытки блокируются (тест: app_name="test; rm -rf /" → 400 Bad Request)
- [ ] Secrets masked in UI и MCP responses
- [ ] Invalid API key → 401 Unauthorized на всех endpoints

