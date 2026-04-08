# KimiDokku MCP Platform Design

**Date**: 2026-04-07  
**Based on**: PRD KimiDokku MCP.md

---

## 1. Overview

**Vision**: Превращение Dokku в AI-native PaaS платформу, где AI-агенты разработчиков управляют жизненным циклом приложений через Model Context Protocol (MCP), а веб-админка служит вспомогательным инструментом для операторов.

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

## 3. Database Schema

### 3.1 Tables

| Table | Purpose |
|-------|---------|
| `platform_config` | Глобальная конфигурация платформы (KIMIDOKKU_DOMAIN) |
| `api_keys` | API ключи для аутентификации (UUID4, max 10 apps per key) |
| `apps` | Приложения Dokku (создаются через UI) |
| `custom_domains` | Кастомные домены-алиасы для приложений |
| `db_services` | Связанные сервисы БД (postgres, redis, mysql, mongo) |
| `deploy_logs` | Аудит деплоев |
| `crowdsec_cache` | Read-only cache банов CrowdSec для UI |

### 3.2 Key Constraints

- API Key: max 10 apps per key (enforced at INSERT)
- App name validation: `^[a-z0-9-]+$` (lowercase alphanumeric + hyphen only)
- TLS status enum: 'active', 'expiring', 'error', 'none'
- Deploy status enum: 'success', 'failed', 'in_progress'

---

## 4. MCP Specification

**Transport**: HTTP SSE (`/mcp/sse`)  
**Auth**: `X-API-Key` header (per-key authentication)  
**Protocol**: JSON-RPC 2.0 via MCP

### 4.1 Tools (15 инструментов)

#### App Lifecycle
| Tool | Purpose |
|------|---------|
| `list_apps` | Список приложений для данного API ключа |
| `get_app_status` | Детальный статус приложения |
| `deploy_git` | Деплой из git репозитория |
| `deploy_image` | Деплой из Docker образа |

#### Logs & Debug
| Tool | Purpose |
|------|---------|
| `get_logs` | Получение логов (snapshot) |
| `restart_app` | Перезапуск приложения |
| `run_command` | Выполнение one-off команд (dokku run) |

#### Configuration
| Tool | Purpose |
|------|---------|
| `get_config` | Получение ENV vars (с маскировкой секретов) |
| `set_config` | Установка ENV vars атомарно |

#### Domains
| Tool | Purpose |
|------|---------|
| `add_custom_domain` | Добавление кастомного домена |
| `remove_custom_domain` | Удаление кастомного домена |
| `list_domains` | Список всех доменов приложения |

#### Database Services
| Tool | Purpose |
|------|---------|
| `create_database` | Создание и линковка БД |
| `list_databases` | Список связанных БД |
| `unlink_database` | Отвязка/удаление сервиса БД |

### 4.2 Resources

- `dokku://config/{app_name}` — конфиг приложения (masked)
- `dokku://logs/{app_name}/recent` — последние 50 строк логов
- `dokku://domains/{app_name}` — список доменов

### 4.3 Prompts

- `deployment_workflow` — чеклист деплоя для AI
- `debug_crashed_app` — диагностика упавшего приложения

---

## 5. REST API Specification

**Auth**: `X-API-Key` header (кроме webhooks — там HMAC)

### 5.1 Webhooks (Auto-Deploy)

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /webhook/github/{app_name}` | HMAC-SHA256 | GitHub push webhook |
| `POST /webhook/gitlab/{app_name}` | Token | GitLab webhook |

### 5.2 Health & Emergency

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /health` | None | Health check |
| `GET /api/apps/{app_name}/logs` | X-API-Key | Emergency logs endpoint |

---

## 6. Web Admin UI

**Scope**: Только просмотр и базовое управление, которое неудобно делать через AI.

### 6.1 Pages

| Route | Purpose |
|-------|---------|
| `/` | Dashboard (stats, TLS alerts, CrowdSec, recent deploys) |
| `/apps` | Список приложений с actions |
| `/apps/{name}` | Детали приложения (tabs: Overview, Domains, Logs, Database, API Key, Deploy History) |
| `/keys` | Управление API ключами |
| `/security` | CrowdSec статус и управление банами |

### 6.2 Key UI Features

- **Dashboard**: Cards (Total Apps, TLS Alerts, CrowdSec Status) + Recent Deploys table
- **Apps List**: Table с actions (View, Logs, Restart)
- **App Detail**: Tabs с полной информацией о приложении
- **API Keys**: Генерация UUID4 (показывается только один раз), copy to clipboard
- **CrowdSec**: Список банов с [Unban] action

---

## 7. Security Specification

### S-1. API Key Isolation
- Keys are UUID4, cryptographically random
- Per-key app access validation
- 403 Forbidden при попытке доступа к чужому app
- Max 10 apps per key enforced

### S-2. Command Injection Prevention
- `asyncio.create_subprocess_exec` (list args, no shell)
- App names validated: `^[a-z0-9-]+$`
- `run_command` whitelist: rake, python, node, echo
- Block: `;`, `|`, `$()`, backticks

### S-3. Secret Masking
- Config values containing `KEY`, `PASS`, `SECRET`, `TOKEN` → `***`
- Применяется в UI и MCP responses

### S-4. TLS/Transport
- MCP SSE только over HTTPS (HSTS enforced)
- Webhook HMAC-SHA256 verification обязательна

### S-5. CrowdSec
- MCP tools не предоставляют управление банами
- Unban только через UI с дополнительной аутентификацией

---

## 8. Environment Variables

```bash
KIMIDOKKU_DOMAIN=app.example.com        # Базовый домен для auto-domains
DOKKU_HOST=localhost                      # Для dokku CLI
AUTH_USER=admin                           # UI Basic Auth
AUTH_PASS=changeme                        # UI Basic Auth
LETSENCRYPT_EMAIL=admin@example.com       # Для TLS
DB_PATH=/app/data/kimidokku.db            # SQLite path
WEBHOOK_SECRET_DEFAULT=optional-fallback  # Fallback для webhook verify
```

---

## 9. Acceptance Criteria Summary

**MCP Layer**:
- [ ] AI агент может выполнить полный цикл деплоя
- [ ] Агент может создать БД и получить подтверждение
- [ ] Агент может добавить кастомный домен
- [ ] Per-key isolation работает
- [ ] Limit 10 apps per key enforced

**UI Layer**:
- [ ] Dashboard показывает точное количество apps по статусам
- [ ] Генерация API ключа показывает UUID только один раз
- [ ] CrowdSec виджет отображает актуальные баны
- [ ] Unban IP работает из UI

**Integration**:
- [ ] GitHub webhook → auto-deploy работает
- [ ] Auto-domain генерируется при создании app
- [ ] TLS сертификат выпускается автоматически
- [ ] При fail renew появляется индикатор в UI

**Security**:
- [ ] Command injection блокируется
- [ ] Secrets masked в UI и MCP
- [ ] Invalid API key → 401 Unauthorized
