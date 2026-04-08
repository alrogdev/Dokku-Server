# KimiDokku MCP - Production Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical security vulnerabilities and high-priority issues to make KimiDokku MCP production-ready.

**Architecture:** Security-first approach with proper validation layers, rate limiting middleware, CSRF protection for UI, connection pooling for database, and standardized error handling across all modules.

**Tech Stack:** Python 3.11+, FastAPI, FastMCP, aiosqlite, slowapi (rate limiting), python-multipart, itsdangerous (CSRF), shlex (command parsing)

---

## File Structure Changes

```
/Users/anrogdev/OpenWork/KimiDokku MCP/
├── src/kimidokku/
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── security_headers.py    # Security headers middleware
│   │   └── rate_limiter.py        # Rate limiting setup
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_manager.py        # Background task tracking
│   │   └── validators.py          # Input validation helpers
│   ├── tools/
│   │   └── apps.py                # MODIFIED: create_app, delete_app
│   ├── routers/
│   │   └── api_keys.py            # NEW: API Key management REST API
│   └── csrf.py                    # NEW: CSRF protection
├── tests/
│   ├── test_security.py           # Security tests
│   ├── test_integration.py        # Integration tests
│   └── test_rate_limit.py         # Rate limiting tests
```

---

## Week 1: Security Fixes (CRITICAL - Block Production)

### Task 1: Fix Command Injection Vulnerability

**Files:**
- Modify: `src/kimidokku/tools/logs.py`
- Test: `tests/test_security.py`

- [ ] **Step 1: Write security test for command injection**

Create `tests/test_security.py`:

```python
"""Security tests for KimiDokku MCP."""

import pytest

from kimidokku.tools.logs import _validate_command


class TestCommandInjection:
    """Test command injection prevention."""

    def test_valid_command_passes(self):
        """Valid commands should pass validation."""
        assert _validate_command("python manage.py migrate") is True
        assert _validate_command("rails db:migrate") is True
        assert _validate_command("bundle exec rake db:setup") is True
        assert _validate_command("echo hello") is True
        assert _validate_command("node server.js") is True

    def test_command_chaining_blocked(self):
        """Command chaining operators should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("python; rm -rf /")
        with pytest.raises(ValueError):
            _validate_command("python && rm -rf /")
        with pytest.raises(ValueError):
            _validate_command("python || rm -rf /")
        with pytest.raises(ValueError):
            _validate_command("python | cat /etc/passwd")

    def test_command_substitution_blocked(self):
        """Command substitution should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("python $(rm -rf /)")
        with pytest.raises(ValueError):
            _validate_command("python `rm -rf /`")

    def test_ifs_substitution_blocked(self):
        """IFS substitution should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("python${IFS}script.py")

    def test_newline_injection_blocked(self):
        """Newline injection should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("python\nrm -rf /")

    def test_shell_redirection_blocked(self):
        """Shell redirection should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("python > /etc/passwd")
        with pytest.raises(ValueError):
            _validate_command("python >> /etc/passwd")

    def test_disallowed_base_command(self):
        """Commands not in whitelist should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("bash -c 'rm -rf /'")
        with pytest.raises(ValueError):
            _validate_command("sh -c 'rm -rf /'")
        with pytest.raises(ValueError):
            _validate_command("curl http://evil.com")

    def test_empty_command(self):
        """Empty command should be blocked."""
        with pytest.raises(ValueError):
            _validate_command("")
        with pytest.raises(ValueError):
            _validate_command("   ")

    def test_shlex_parsing(self):
        """Test that shlex parsing handles quoted arguments correctly."""
        # This should pass - quoted string is a single argument
        assert _validate_command('python -c "print(1)"') is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "/Users/anrogdev/OpenWork/KimiDokku MCP"
source .venv/bin/activate
pytest tests/test_security.py::TestCommandInjection -v
```

Expected: Tests FAIL (old implementation doesn't have proper validation)

- [ ] **Step 3: Fix command validation in logs.py**

Replace the `_validate_command` function in `src/kimidokku/tools/logs.py`:

```python
import shlex

# Whitelist for run_command - only safe commands
ALLOWED_COMMANDS = {"rake", "python", "node", "echo", "rails", "bundle", "npm", "yarn"}
FORBIDDEN_PATTERNS = [
    r";",           # Command separator
    r"\|",          # Pipe
    r"\$\(",        # Command substitution $()
    r"`",           # Backtick substitution
    r">>",          # Append redirection
    r">",           # Overwrite redirection
    r"&&",          # AND operator
    r"\|\|",        # OR operator
    r"\$\{IFS\}",   # IFS substitution
    r"\n",          # Newline
    r"\r",          # Carriage return
]


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
```

Also update the `run_command` tool to use `shlex.split`:

```python
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
    
    # Parse command safely with shlex
    cmd_args = shlex.split(command)
    
    try:
        # Run dokku run with parsed arguments
        proc = await asyncio.create_subprocess_exec(
            "dokku", "run", app_name, *cmd_args,
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
```

- [ ] **Step 4: Run tests to verify fix**

```bash
pytest tests/test_security.py::TestCommandInjection -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_security.py src/kimidokku/tools/logs.py
git commit -m "security: fix command injection vulnerability in run_command tool"
```

---

### Task 2: Add UUID Validation for API Keys

**Files:**
- Modify: `src/kimidokku/auth.py`
- Test: `tests/test_security.py`

- [ ] **Step 1: Write test for API key validation**

Add to `tests/test_security.py`:

```python
import uuid

from fastapi import HTTPException

from kimidokku.auth import verify_api_key


class TestAPIKeyValidation:
    """Test API key format validation."""

    @pytest.mark.asyncio
    async def test_valid_uuid4_accepted(self, monkeypatch):
        """Valid UUIDv4 should be accepted."""
        valid_key = str(uuid.uuid4())
        
        # Mock database to return valid key
        async def mock_fetch_one(query, params):
            if params[0] == valid_key:
                return {"id": valid_key, "is_active": True}
            return None
        
        monkeypatch.setattr("kimidokku.auth.db.fetch_one", mock_fetch_one)
        
        result = await verify_api_key(valid_key)
        assert result == valid_key

    @pytest.mark.asyncio
    async def test_invalid_uuid_rejected(self):
        """Invalid UUID format should be rejected."""
        invalid_keys = [
            "not-a-uuid",
            "12345",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-invalid",  # Too long
            "550e8400-e29b-11d4-a716-446655440000",  # UUIDv1, not v4
            "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character
        ]
        
        for key in invalid_keys:
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(key)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_key_rejected(self):
        """Empty API key should be rejected."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_revoked_key_rejected(self, monkeypatch):
        """Revoked API key should be rejected."""
        valid_key = str(uuid.uuid4())
        
        async def mock_fetch_one(query, params):
            if params[0] == valid_key:
                return {"id": valid_key, "is_active": False}
            return None
        
        monkeypatch.setattr("kimidokku.auth.db.fetch_one", mock_fetch_one)
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(valid_key)
        assert exc_info.value.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_security.py::TestAPIKeyValidation -v
```

Expected: Tests FAIL (current implementation only checks length)

- [ ] **Step 3: Update auth.py with UUID validation**

Replace the `verify_api_key` function in `src/kimidokku/auth.py`:

```python
import uuid


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key and return associated key ID."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate UUIDv4 format
    try:
        parsed = uuid.UUID(api_key)
        if parsed.version != 4:
            raise ValueError("Not a UUIDv4")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    # Check if key exists and is active
    result = await db.fetch_one(
        "SELECT id, is_active FROM api_keys WHERE id = ?",
        (api_key,),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not result["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is revoked",
        )

    return result["id"]
```

- [ ] **Step 4: Run tests to verify fix**

```bash
pytest tests/test_security.py::TestAPIKeyValidation -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_security.py src/kimidokku/auth.py
git commit -m "security: add proper UUIDv4 validation for API keys"
```

---

### Task 3: Add Rate Limiting

**Files:**
- Create: `src/kimidokku/middleware/__init__.py`
- Create: `src/kimidokku/middleware/rate_limiter.py`
- Modify: `src/kimidokku/main.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add slowapi dependency**

Add to `pyproject.toml` dependencies:

```toml
dependencies = [
    # ... existing dependencies ...
    "slowapi>=0.1.9",
    "redis>=5.0.0",  # Optional, for distributed rate limiting
]
```

- [ ] **Step 2: Create rate limiter middleware**

Create `src/kimidokku/middleware/__init__.py`:

```python
"""Middleware package."""
```

Create `src/kimidokku/middleware/rate_limiter.py`:

```python
"""Rate limiting configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address


# Create limiter instance
# Using remote address as key, but could also use API key for authenticated routes
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default: 100 requests per minute
)


def get_limiter() -> Limiter:
    """Get rate limiter instance."""
    return limiter
```

- [ ] **Step 3: Integrate rate limiter into main.py**

Modify `src/kimidokku/main.py`:

```python
from slowapi.errors import RateLimitExceeded

from kimidokku.middleware.rate_limiter import limiter


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="KimiDokku MCP",
        description="MCP-First PaaS Platform for Dokku",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # ... rest of the code ...


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "retry_after": exc.headers.get("Retry-After")},
    )
```

- [ ] **Step 4: Add rate limits to critical endpoints**

In `src/kimidokku/routers/webhooks.py`:

```python
from kimidokku.middleware.rate_limiter import limiter

@router.post("/github/{app_name}")
@limiter.limit("10/minute")  # Limit webhook endpoints
async def github_webhook(...):
    ...

@router.post("/gitlab/{app_name}")
@limiter.limit("10/minute")
async def gitlab_webhook(...):
    ...
```

In `src/kimidokku/routers/ui.py`:

```python
from kimidokku.middleware.rate_limiter import limiter

@router.get("/")
@limiter.limit("30/minute")
async def dashboard(...):
    ...
```

- [ ] **Step 5: Test rate limiting**

Create `tests/test_rate_limit.py`:

```python
"""Tests for rate limiting."""

import pytest
from fastapi.testclient import TestClient

from kimidokku.main import app

client = TestClient(app)


def test_rate_limit_applies_to_webhooks():
    """Test that rate limiting is applied to webhook endpoints."""
    # Make multiple requests to trigger rate limit
    for i in range(15):
        response = client.post(
            "/webhook/github/test-app",
            headers={"X-Hub-Signature-256": "sha256=test"},
            json={"ref": "refs/heads/main"},
        )
    
    # After 10 requests (limit), should get 429
    assert response.status_code == 429
```

- [ ] **Step 6: Install dependencies and test**

```bash
pip install slowapi redis
pytest tests/test_rate_limit.py -v
```

Expected: Tests verify rate limiting works

- [ ] **Step 7: Commit**

```bash
git add src/kimidokku/middleware/ src/kimidokku/main.py src/kimidokku/routers/webhooks.py src/kimidokku/routers/ui.py pyproject.toml tests/test_rate_limit.py
git commit -m "security: add rate limiting to prevent brute force attacks"
```

---

### Task 4: Add CSRF Protection

**Files:**
- Create: `src/kimidokku/csrf.py`
- Modify: `src/kimidokku/main.py`
- Modify: `src/kimidokku/routers/ui.py`
- Modify: `templates/base.html`

- [ ] **Step 1: Create CSRF protection module**

Create `src/kimidokku/csrf.py`:

```python
"""CSRF protection for Web UI."""

import secrets
from typing import Optional

from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from kimidokku.config import get_settings


class CSRFProtection:
    """CSRF token generation and validation."""
    
    def __init__(self, secret_key: str):
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.token_name = "csrf_token"
        self.max_age = 3600  # 1 hour
    
    def generate_token(self) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        return self.serializer.dumps(token)
    
    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token."""
        try:
            self.serializer.loads(token, max_age=self.max_age)
            return True
        except (BadSignature, Exception):
            return False
    
    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Get CSRF token from request (header or form)."""
        # Check header first (for HTMX requests)
        token = request.headers.get("X-CSRF-Token")
        if token:
            return token
        
        # Check form data
        form_data = request.form()
        if form_data and self.token_name in form_data:
            return form_data[self.token_name]
        
        return None


def get_csrf() -> CSRFProtection:
    """Get CSRF protection instance."""
    settings = get_settings()
    # Use auth_pass as secret if no specific CSRF secret configured
    secret = getattr(settings, 'csrf_secret', None) or settings.auth_pass
    return CSRFProtection(secret)


async def verify_csrf_token(request: Request):
    """Dependency to verify CSRF token on POST/PUT/DELETE requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True
    
    csrf = get_csrf()
    token = csrf.get_token_from_request(request)
    
    if not token or not csrf.validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        )
    
    return True
```

- [ ] **Step 2: Update base template with CSRF token**

Modify `templates/base.html`:

```html
<head>
    <!-- ... existing head content ... -->
    
    <!-- CSRF Token for HTMX -->
    <meta name="csrf-token" content="{{ csrf_token }}">
    <script>
        // Add CSRF token to all HTMX requests
        document.body.addEventListener('htmx:configRequest', function(event) {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            if (csrfToken) {
                event.detail.headers['X-CSRF-Token'] = csrfToken;
            }
        });
    </script>
    
    {% block head %}{% endblock %}
</head>
```

- [ ] **Step 3: Add CSRF to main.py**

Modify `src/kimidokku/main.py`:

```python
from kimidokku.csrf import get_csrf


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_database()
    
    # Initialize CSRF
    csrf = get_csrf()
    app.state.csrf = csrf
    
    yield
    
    # Shutdown
    pass
```

- [ ] **Step 4: Update UI routes with CSRF**

Modify `src/kimidokku/routers/ui.py`:

```python
from kimidokku.csrf import verify_csrf_token


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    templates=Depends(get_templates),
    username: str = Depends(verify_basic_auth),
):
    """Dashboard page."""
    csrf = request.app.state.csrf
    
    # ... existing stats query code ...
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "recent_deploys": recent_deploys,
            "version": "0.1.0",
            "csrf_token": csrf.generate_token(),  # Add CSRF token
        },
    )


# Add CSRF verification to POST endpoints
@router.post("/keys/{key_id}/revoke")
async def revoke_key(
    key_id: str,
    request: Request,
    _: bool = Depends(verify_csrf_token),  # CSRF check
    username: str = Depends(verify_basic_auth),
):
    """Revoke an API key."""
    # ... implementation ...
    pass
```

- [ ] **Step 5: Test CSRF protection**

Add to `tests/test_security.py`:

```python
class TestCSRFProtection:
    """Test CSRF protection."""

    def test_csrf_token_in_meta_tag(self, client):
        """CSRF token should be in meta tag on GET requests."""
        response = client.get("/", auth=("admin", "changeme"))
        assert response.status_code == 200
        assert b'csrf-token' in response.content

    def test_post_without_csrf_fails(self, client):
        """POST without CSRF token should fail."""
        response = client.post(
            "/keys/test-key/revoke",
            auth=("admin", "changeme"),
        )
        assert response.status_code == 403
```

- [ ] **Step 6: Commit**

```bash
git add src/kimidokku/csrf.py src/kimidokku/middleware/ src/kimidokku/main.py src/kimidokku/routers/ui.py templates/base.html tests/test_security.py pyproject.toml
git commit -m "security: add CSRF protection for Web UI"
```

---

### Task 5: Add Security Headers Middleware

**Files:**
- Create: `src/kimidokku/middleware/security_headers.py`
- Modify: `src/kimidokku/main.py`

- [ ] **Step 1: Create security headers middleware**

Create `src/kimidokku/middleware/security_headers.py`:

```python
"""Security headers middleware."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Strict Transport Security (HTTPS only)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
```

- [ ] **Step 2: Add middleware to main.py**

Modify `src/kimidokku/main.py`:

```python
from kimidokku.middleware.security_headers import SecurityHeadersMiddleware


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="KimiDokku MCP",
        description="MCP-First PaaS Platform for Dokku",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add rate limiting (from Task 3)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # ... rest of the code ...
```

- [ ] **Step 3: Test security headers**

Add to `tests/test_security.py`:

```python
def test_security_headers_present(client):
    """Security headers should be present in responses."""
    response = client.get("/health")
    
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
```

- [ ] **Step 4: Commit**

```bash
git add src/kimidokku/middleware/security_headers.py src/kimidokku/main.py tests/test_security.py
git commit -m "security: add security headers middleware (CSP, HSTS, X-Frame-Options, etc.)"
```

---

## Week 1 Summary

By the end of Week 1, all critical security vulnerabilities should be fixed:

- ✅ Command injection vulnerability patched
- ✅ UUID validation for API keys implemented
- ✅ Rate limiting added
- ✅ CSRF protection for Web UI
- ✅ Security headers middleware

**Testing:** Run full security test suite:
```bash
pytest tests/test_security.py tests/test_rate_limit.py -v
```

---

## Week 2: Stability & Features

### Task 6: Fix Health Check and Timestamp

**Files:**
- Modify: `src/kimidokku/main.py`

- [ ] **Step 1: Fix hardcoded timestamp and add Dokku connectivity check**

Replace the health check endpoint in `src/kimidokku/main.py`:

```python
from datetime import datetime, timezone


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Dokku connectivity
    try:
        proc = await asyncio.create_subprocess_exec(
            "dokku", "version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=5.0)
        dokku_connected = proc.returncode == 0
    except Exception:
        dokku_connected = False
    
    return {
        "status": "ok",
        "dokku_connected": dokku_connected,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 2: Commit**

```bash
git add src/kimidokku/main.py
git commit -m "fix: dynamic timestamp and real Dokku connectivity check in health endpoint"
```

---

### Task 7: Standardize Error Handling

**Files:**
- Create: `src/kimidokku/exceptions.py`
- Modify: All tool files

- [ ] **Step 1: Create custom exceptions**

Create `src/kimidokku/exceptions.py`:

```python
"""Custom exceptions for KimiDokku MCP."""


class KimiDokkuError(Exception):
    """Base exception."""
    pass


class AppNotFoundError(KimiDokkuError):
    """App not found."""
    pass


class PermissionDeniedError(KimiDokkuError):
    """Permission denied."""
    pass


class CommandError(KimiDokkuError):
    """Command execution error."""
    pass


class ValidationError(KimiDokkuError):
    """Input validation error."""
    pass
```

- [ ] **Step 2: Add exception handlers to main.py**

```python
from kimidokku.exceptions import (
    AppNotFoundError,
    CommandError,
    KimiDokkuError,
    PermissionDeniedError,
    ValidationError,
)


@app.exception_handler(KimiDokkuError)
async def kimidokku_exception_handler(request: Request, exc: KimiDokkuError):
    """Handle KimiDokku exceptions."""
    status_code = 500
    if isinstance(exc, AppNotFoundError):
        status_code = 404
    elif isinstance(exc, PermissionDeniedError):
        status_code = 403
    elif isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, CommandError):
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "message": str(exc)},
    )
```

- [ ] **Step 3: Update tools to use exceptions**

Example for `src/kimidokku/tools/logs.py`:

```python
from kimidokku.exceptions import AppNotFoundError, CommandError, ValidationError


@mcp.tool()
async def run_command(...) -> dict:
    """Run one-off command."""
    # Verify app ownership
    app = await db.fetch_one(...)
    
    if not app:
        raise AppNotFoundError(f"App '{app_name}' not found or access denied")
    
    # Validate command
    try:
        _validate_command(command)
    except ValueError as e:
        raise ValidationError(str(e))
    
    # Run command
    try:
        proc = await asyncio.create_subprocess_exec(...)
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise CommandError(f"Command failed: {stderr.decode()}")
        
        return {
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
            "exit_code": proc.returncode,
        }
    except Exception as e:
        raise CommandError(f"Failed to run command: {e}")
```

- [ ] **Step 4: Commit**

```bash
git add src/kimidokku/exceptions.py src/kimidokku/main.py src/kimidokku/tools/logs.py
git commit -m "refactor: standardize error handling with custom exceptions"
```

---

### Task 8: Add create_app and delete_app MCP Tools

**Files:**
- Modify: `src/kimidokku/tools/apps.py`

- [ ] **Step 1: Add create_app tool**

```python
@mcp.tool()
async def create_app(
    api_key_id: str,
    name: str,
    git_url: Optional[str] = None,
    branch: str = "main",
) -> dict:
    """
    Create a new Dokku app.
    
    Args:
        api_key_id: API key ID
        name: App name (lowercase alphanumeric and hyphens only)
        git_url: Optional git repository URL
        branch: Git branch (default: main)
    
    Returns:
        App details including auto-generated domain
    """
    # Validate app name
    if not re.match(r'^[a-z0-9-]+$', name):
        raise ValidationError("App name must be lowercase alphanumeric and hyphens only")
    
    if len(name) > 63:
        raise ValidationError("App name must be 63 characters or less")
    
    # Check if app already exists
    existing = await db.fetch_one("SELECT name FROM apps WHERE name = ?", (name,))
    if existing:
        raise ValidationError(f"App '{name}' already exists")
    
    # Check API key app limit
    key_info = await db.fetch_one(
        "SELECT max_apps FROM api_keys WHERE id = ?",
        (api_key_id,)
    )
    if not key_info:
        raise PermissionDeniedError("Invalid API key")
    
    app_count = await db.fetch_one(
        "SELECT COUNT(*) as count FROM apps WHERE api_key_id = ?",
        (api_key_id,)
    )
    if app_count["count"] >= key_info["max_apps"]:
        raise PermissionDeniedError(f"API key has reached max apps limit ({key_info['max_apps']})")
    
    # Create app in Dokku
    try:
        proc = await asyncio.create_subprocess_exec(
            "dokku", "apps:create", name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise CommandError(f"Failed to create app: {stderr.decode()}")
        
        # Generate auto domain
        settings = get_settings()
        auto_domain = f"{name}.{settings.kimidokku_domain}"
        
        # Add domain to app
        await asyncio.create_subprocess_exec(
            "dokku", "domains:add", name, auto_domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Store in database
        await db.execute(
            """
            INSERT INTO apps (name, api_key_id, auto_domain, git_url, branch, status)
            VALUES (?, ?, ?, ?, ?, 'stopped')
            """,
            (name, api_key_id, auto_domain, git_url, branch),
        )
        
        return {
            "name": name,
            "auto_domain": auto_domain,
            "status": "stopped",
            "message": f"App '{name}' created successfully",
        }
        
    except Exception as e:
        # Cleanup on failure
        await asyncio.create_subprocess_exec(
            "dokku", "apps:destroy", name, "--force",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        raise CommandError(f"Failed to create app: {e}")
```

- [ ] **Step 2: Add delete_app tool**

```python
@mcp.tool()
async def delete_app(
    app_name: str,
    api_key_id: str,
    force: bool = False,
) -> dict:
    """
    Delete a Dokku app and all associated data.
    
    Args:
        app_name: Name of the app to delete
        api_key_id: API key ID
        force: If True, delete without confirmation (required)
    
    Returns:
        Deletion status
    """
    if not force:
        raise ValidationError("force=True is required to delete an app")
    
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )
    
    if not app:
        raise AppNotFoundError(f"App '{app_name}' not found or access denied")
    
    try:
        # Delete from Dokku
        proc = await asyncio.create_subprocess_exec(
            "dokku", "apps:destroy", app_name, "--force",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise CommandError(f"Failed to delete app: {stderr.decode()}")
        
        # Delete from database (cascade will handle related records)
        await db.execute("DELETE FROM apps WHERE name = ?", (app_name,))
        
        return {
            "success": True,
            "message": f"App '{app_name}' deleted successfully",
        }
        
    except Exception as e:
        raise CommandError(f"Failed to delete app: {e}")
```

- [ ] **Step 3: Commit**

```bash
git add src/kimidokku/tools/apps.py
git commit -m "feat: add create_app and delete_app MCP tools"
```

---

## Week 3: Testing & API Key Management

### Task 9: Add API Key Management REST API

**Files:**
- Create: `src/kimidokku/routers/api_keys.py`

- [ ] **Step 1: Create API keys REST router**

```python
"""API Key management REST API."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from kimidokku.auth import verify_basic_auth, generate_api_key
from kimidokku.database import db

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    name: str
    max_apps: int = 10


class APIKeyResponse(BaseModel):
    id: str
    name: str
    max_apps: int
    created_at: str
    is_active: bool


@router.post("/", response_model=dict)
async def create_api_key(
    data: APIKeyCreate,
    username: str = Depends(verify_basic_auth),
):
    """Create a new API key."""
    # Generate UUID
    key_id = await generate_api_key()
    
    # Store in database
    await db.execute(
        """
        INSERT INTO api_keys (id, name, max_apps, is_active)
        VALUES (?, ?, ?, 1)
        """,
        (key_id, data.name, data.max_apps),
    )
    
    return {
        "id": key_id,
        "name": data.name,
        "key": key_id,  # Return full key (shown only once)
        "max_apps": data.max_apps,
        "message": "Store this key securely - it will not be shown again",
    }


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    username: str = Depends(verify_basic_auth),
):
    """List all API keys."""
    keys = await db.fetch_all(
        """
        SELECT id, name, max_apps, created_at, is_active
        FROM api_keys
        ORDER BY created_at DESC
        """
    )
    return keys


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    username: str = Depends(verify_basic_auth),
):
    """Revoke an API key."""
    await db.execute(
        "UPDATE api_keys SET is_active = 0 WHERE id = ?",
        (key_id,),
    )
    return {"message": "API key revoked successfully"}


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    username: str = Depends(verify_basic_auth),
):
    """Delete an API key and all associated apps."""
    # Check if key exists
    key = await db.fetch_one("SELECT id FROM api_keys WHERE id = ?", (key_id,))
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Delete key (cascade will handle apps)
    await db.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    
    return {"message": "API key and associated apps deleted"}
```

- [ ] **Step 2: Add router to main.py**

```python
from kimidokku.routers import api_keys

app.include_router(api_keys.router)
```

- [ ] **Step 3: Commit**

```bash
git add src/kimidokku/routers/api_keys.py src/kimidokku/main.py
git commit -m "feat: add API key management REST API endpoints"
```

---

## Final Testing & Integration

### Task 10: Run Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
cd "/Users/anrogdev/OpenWork/KimiDokku MCP"
source .venv/bin/activate
pytest tests/ -v --tb=short
```

- [ ] **Step 2: Security audit**

```bash
# Run security-focused tests
pytest tests/test_security.py -v

# Check for common vulnerabilities
bandit -r src/kimidokku/
```

- [ ] **Step 3: Update CODE-REVIEW-1.md**

Mark resolved issues as fixed:

```markdown
## ✅ Исправленные проблемы

### Критические
- [x] Command Injection Vulnerability (Week 1, Task 1)
- [x] Слабая валидация API Key (Week 1, Task 2)
- [x] Нет Rate Limiting (Week 1, Task 3)
- [x] Нет CSRF защиты (Week 1, Task 4)
- [x] Нет Security Headers (Week 1, Task 5)

### Высокий приоритет
- [x] Несогласованная обработка ошибок (Week 2, Task 7)
- [x] Missing create_app/delete_app (Week 2, Task 8)
```

- [ ] **Step 4: Final commit**

```bash
git add CODE-REVIEW-1.md
git commit -m "docs: update code review with resolved issues"
```

---

## Summary

This implementation plan addresses all 5 critical security issues and most high-priority issues identified in the code review:

### Week 1: Security (CRITICAL)
1. ✅ Command injection fix with shlex
2. ✅ UUIDv4 validation for API keys
3. ✅ Rate limiting with slowapi
4. ✅ CSRF protection for Web UI
5. ✅ Security headers middleware

### Week 2: Stability & Features
6. ✅ Fixed health check with real Dokku verification
7. ✅ Standardized error handling with custom exceptions
8. ✅ Added create_app and delete_app MCP tools

### Week 3: Testing & API
9. ✅ API Key management REST API
10. ✅ Comprehensive security tests

**Estimated time**: 2-3 weeks of focused development

**Result**: Production-ready KimiDokku MCP platform with enterprise-grade security.
