-- KimiDokku MCP Database Schema

-- Global platform configuration
CREATE TABLE IF NOT EXISTS platform_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- API Keys for agent authentication (max 10 apps per key)
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,  -- UUID4
    name TEXT,            -- human-readable label
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    max_apps INTEGER DEFAULT 10 CHECK (max_apps > 0 AND max_apps <= 100),
    is_active BOOLEAN DEFAULT 1
);

-- Dokku applications
CREATE TABLE IF NOT EXISTS apps (
    name TEXT PRIMARY KEY CHECK (name REGEXP '^[a-z0-9-]+$'),
    api_key_id TEXT REFERENCES api_keys(id) ON DELETE RESTRICT,
    auto_domain TEXT,     -- generated: app-name.app.example.com
    git_url TEXT,
    branch TEXT DEFAULT 'main',
    status TEXT CHECK (status IN ('running', 'stopped', 'crashed', 'deploying', 'error')) DEFAULT 'stopped',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_deploy_at TIMESTAMP,
    tls_status TEXT CHECK (tls_status IN ('active', 'expiring', 'error', 'none')) DEFAULT 'none',
    tls_expires_at TIMESTAMP
);

-- Custom domains (aliases)
CREATE TABLE IF NOT EXISTS custom_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT REFERENCES apps(name) ON DELETE CASCADE,
    domain TEXT UNIQUE NOT NULL,
    tls_enabled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Database services (Dokku plugins)
CREATE TABLE IF NOT EXISTS db_services (
    id TEXT PRIMARY KEY,  -- dokku service name
    app_name TEXT REFERENCES apps(name) ON DELETE CASCADE,
    db_type TEXT CHECK (db_type IN ('postgres', 'redis', 'mysql', 'mongo')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    env_var_name TEXT DEFAULT 'DATABASE_URL'
);

-- Deploy logs (audit)
CREATE TABLE IF NOT EXISTS deploy_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT REFERENCES apps(name) ON DELETE CASCADE,
    triggered_by TEXT CHECK (triggered_by IN ('mcp', 'webhook', 'ui')) NOT NULL,
    git_ref TEXT,
    status TEXT CHECK (status IN ('success', 'failed', 'in_progress')) DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    error_message TEXT
);

-- CrowdSec cache (read-only for UI)
CREATE TABLE IF NOT EXISTS crowdsec_cache (
    ip TEXT PRIMARY KEY,
    country TEXT,
    scenario TEXT,
    banned_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Config history for rollback
CREATE TABLE IF NOT EXISTS config_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT REFERENCES apps(name) ON DELETE CASCADE,
    config_json TEXT NOT NULL,  -- JSON string of ENV vars
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT  -- 'mcp', 'ui', etc.
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_apps_api_key ON apps(api_key_id);
CREATE INDEX IF NOT EXISTS idx_apps_status ON apps(status);
CREATE INDEX IF NOT EXISTS idx_custom_domains_app ON custom_domains(app_name);
CREATE INDEX IF NOT EXISTS idx_db_services_app ON db_services(app_name);
CREATE INDEX IF NOT EXISTS idx_deploy_logs_app ON deploy_logs(app_name);
CREATE INDEX IF NOT EXISTS idx_deploy_logs_started ON deploy_logs(started_at);
CREATE INDEX IF NOT EXISTS idx_config_history_app ON config_history(app_name);
