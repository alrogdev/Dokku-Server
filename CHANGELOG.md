# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.1] - 2026-04-08

### Security 🔒
- Enabled HSTS (Strict-Transport-Security) header with `max-age=31536000; includeSubDomains; preload`
- Registry password now passed via stdin instead of CLI arguments (prevents exposure in process list)
- Added CSRF protection enforcement to API Keys management endpoints (`/api/keys/*`)

### Added ✨
- Background task tracking module (`tasks.py`) with persistent storage
- New `background_tasks` database table for monitoring async operations
- Task manager with status tracking: pending, running, success, failed, cancelled

### Fixed 🐛
- Fixed version number in `main.py`: 0.1.0 → 1.0.0
- Fixed `_run_image_deploy` to clear registry password from memory after use

## [1.0.0] - 2026-04-08

### Security 🔒
- **CRITICAL**: Fixed command injection vulnerability in `run_command` tool — now uses `shlex.split()` with comprehensive pattern validation
- **CRITICAL**: Added strict UUIDv4 validation for API keys — prevents authentication bypass
- **CRITICAL**: Implemented rate limiting with `slowapi` — 10-100 requests/minute per endpoint
- **CRITICAL**: Added CSRF protection for Web UI — token-based protection with `itsdangerous`
- **CRITICAL**: Added security headers middleware — CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy

### Added ✨
- `create_app` and `delete_app` MCP tools for full app lifecycle management
- API Key Management REST API (`/api/keys/*` endpoints)
- Comprehensive test suite — 94 tests with 56% coverage
- Test coverage reporting with `pytest-cov`
- Integration tests for security boundaries and error handling

### Fixed 🐛
- Health check now uses dynamic timestamp and actually verifies Dokku connectivity
- Standardized error handling with custom exceptions (`AppNotFoundError`, `CommandError`, etc.)
- Fixed `database.py` to use `@asynccontextmanager` decorator
- Removed incompatible `REGEXP` constraint from SQLite schema
- Fixed rate limit error handler to handle `None` headers

### Changed 🔧
- Updated `verify_api_key()` to validate UUIDv4 format strictly
- Replaced `command.split()` with `shlex.split()` in `run_command`
- Added `npm` and `yarn` to allowed commands whitelist
- Extended `FORBIDDEN_PATTERNS` to include `&&`, `||`, `${IFS}`, `\n`, `\r`

### Documentation 📚
- Created comprehensive README.md with quick start guide
- Added COVERAGE.md with detailed coverage analysis
- Updated CODE-REVIEW-1.md marking all issues as resolved
- Added architecture diagram and deployment instructions

## [0.9.0] - 2026-04-07

### Added
- Initial MCP server implementation with FastMCP
- 15 MCP Tools: list_apps, get_app_status, deploy_git, deploy_image, get_logs, restart_app, run_command, get_config, set_config, add_custom_domain, remove_custom_domain, list_domains, create_database, list_databases, unlink_database
- 3 MCP Resources: config, logs, domains
- 2 MCP Prompts: deployment_workflow, debug_crashed_app
- GitHub and GitLab webhook endpoints with HMAC verification
- Web Admin UI with HTMX and Tailwind CSS
- Dashboard, Apps List, App Detail, API Keys, Security pages
- Basic authentication (API keys and HTTP Basic Auth)
- SQLite database with aiosqlite
- Security tests (24 tests)

### Security
- Initial security implementation with basic input validation
- Webhook signature verification (HMAC-SHA256 for GitHub, token for GitLab)
- Parameterized SQL queries (SQL injection protection)

## Future Roadmap 🗺️

### [1.1.0] - Planned
- Real-time log streaming via WebSockets
- Config rollback functionality
- CrowdSec integration (actual ban management)
- App scaling (`dokku ps:scale`)
- Process visibility tools

### [1.2.0] - Planned
- Multi-tenancy support
- Advanced monitoring and alerting
- Backup and restore functionality
- GitLab CI/CD integration

---

For detailed security review, see [CODE-REVIEW-1.md](CODE-REVIEW-1.md).
For test coverage, see [COVERAGE.md](COVERAGE.md).
