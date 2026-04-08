# KimiDokku MCP

AI-native PaaS platform for Dokku with MCP (Model Context Protocol) interface.

## Features

- 🤖 **MCP Server** — 17 Tools, 3 Resources, 2 Prompts for AI agents
- 🌐 **REST API** — GitHub/GitLab webhooks, API Key management
- 🖥️ **Web Admin UI** — HTMX-based interface with real-time updates
- 🔒 **Enterprise Security** — CSRF, rate limiting, security headers, input validation
- 🚀 **App Lifecycle** — Create, deploy, configure, scale, and delete apps
- 🗄️ **Database Services** — PostgreSQL, Redis, MySQL, MongoDB integration

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the server
python -m kimidokku.main
```

The server will be available at:
- Web UI: http://localhost:8000/
- MCP Server: http://localhost:8000/mcp
- REST API: http://localhost:8000/api/

## Configuration

See `.env.example` for all available options:

```bash
KIMIDOKKU_DOMAIN=app.example.com
AUTH_USER=admin
AUTH_PASS=changeme
DB_PATH=./kimidokku.db
```

## MCP Tools

### App Lifecycle
- `list_apps` — List all apps for an API key
- `get_app_status` — Get detailed app status
- `create_app` — Create a new app
- `delete_app` — Delete an app
- `deploy_git` — Deploy from git repository
- `deploy_image` — Deploy from Docker image

### Configuration
- `get_config` — Get environment variables
- `set_config` — Set environment variables

### Domains
- `list_domains` — List all domains for an app
- `add_custom_domain` — Add a custom domain
- `remove_custom_domain` — Remove a custom domain

### Database
- `create_database` — Create and link a database service
- `list_databases` — List linked databases
- `unlink_database` — Unlink a database service

### Logs & Debug
- `get_logs` — Get recent logs
- `restart_app` — Restart an app
- `run_command` — Run one-off commands (secure)

## API Documentation

### Authentication
- **MCP/REST API**: `X-API-Key` header with UUIDv4 key
- **Web UI**: HTTP Basic Auth

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/webhook/github/{app}` | GitHub webhook |
| POST | `/webhook/gitlab/{app}` | GitLab webhook |
| GET | `/api/keys` | List API keys |
| POST | `/api/keys` | Create API key |
| POST | `/api/keys/{id}/revoke` | Revoke API key |
| DELETE | `/api/keys/{id}` | Delete API key |

## Security

All 5 critical vulnerabilities from initial audit have been patched:

1. ✅ **Command Injection** — Fixed with `shlex.split()` and comprehensive pattern validation
2. ✅ **UUID Validation** — Strict UUIDv4 format checking
3. ✅ **Rate Limiting** — 10-100 requests/minute per endpoint
4. ✅ **CSRF Protection** — Token-based protection for Web UI
5. ✅ **Security Headers** — CSP, X-Frame-Options, X-Content-Type-Options

See [CODE-REVIEW-1.md](CODE-REVIEW-1.md) for detailed security review.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/kimidokku --cov-report=term

# Run security tests only
pytest tests/test_security.py -v
```

**Test Coverage**: 56% overall, 100% security-critical components

## Architecture

```
src/kimidokku/
├── main.py              # FastAPI app with MCP
├── mcp_server.py        # MCP server setup
├── config.py            # Configuration
├── database.py          # SQLite with aiosqlite
├── auth.py              # Authentication
├── csrf.py              # CSRF protection
├── exceptions.py        # Custom exceptions
├── tools/               # MCP Tools
├── resources/           # MCP Resources
├── prompts/             # MCP Prompts
├── routers/             # REST API routes
├── middleware/          # Rate limiting, security headers
└── utils/               # Helper functions
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[dev]"
EXPOSE 8000
CMD ["python", "-m", "kimidokku.main"]
```

### Dokku

```bash
# Create app
dokku apps:create kimidokku-mcp

# Set environment variables
dokku config:set kimidokku-mcp KIMIDOKKU_DOMAIN=apps.example.com

# Mount database volume
dokku storage:mount kimidokku-mcp /var/lib/dokku/data/storage/kimidokku:/app/data

# Deploy
git push dokku main
```

## License

MIT License — see LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/kimidokku-mcp/issues)
- **Documentation**: See `docs/` directory
- **Code Review**: See [CODE-REVIEW-1.md](CODE-REVIEW-1.md)

---

**Made with ❤️ for the AI-native infrastructure community**
