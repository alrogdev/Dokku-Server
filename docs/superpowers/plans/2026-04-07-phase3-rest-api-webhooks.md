# KimiDokku MCP - Phase 3: REST API Webhooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement REST API endpoints for GitHub and GitLab webhooks to enable auto-deployment on git push events.

**Architecture:** FastAPI router-based webhooks with HMAC-SHA256 verification (GitHub) and token verification (GitLab). Webhooks trigger async deployment via existing MCP tools logic. Separate router module mounted in main FastAPI app.

**Tech Stack:** FastAPI, hmac (stdlib), hashlib (stdlib), asyncio

---

## File Structure

```
/Users/anrogdev/OpenWork/KimiDokku MCP/
├── src/kimidokku/
│   ├── __init__.py
│   ├── main.py                  # Modified: Add webhook router
│   ├── routers/
│   │   ├── __init__.py
│   │   └── webhooks.py          # GitHub/GitLab webhook endpoints
│   └── utils/
│       ├── __init__.py
│       └── webhook_verify.py    # HMAC verification utilities
└── tests/
    └── test_webhooks.py         # Webhook endpoint tests
```

---

### Task 1: Webhook Verification Utilities

**Files:**
- Create: `src/kimidokku/utils/__init__.py`
- Create: `src/kimidokku/utils/webhook_verify.py`
- Create: `tests/test_webhook_verify.py`

- [ ] **Step 1: Create utils package init**

```python
"""Utility functions package."""
```

- [ ] **Step 2: Create webhook_verify.py**

```python
"""Webhook signature verification utilities."""

import hashlib
import hmac
from typing import Optional


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook HMAC-SHA256 signature.
    
    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (e.g., "sha256=abc123...")
        secret: Webhook secret
    
    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False
    
    # Extract hash from signature
    expected_hash = signature[7:]  # Remove "sha256=" prefix
    
    # Calculate HMAC
    mac = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    )
    computed_hash = mac.hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_hash, computed_hash)


def verify_gitlab_token(provided_token: str, expected_token: str) -> bool:
    """
    Verify GitLab webhook X-Gitlab-Token.
    
    Args:
        provided_token: X-Gitlab-Token header value
        expected_token: Expected token
    
    Returns:
        True if token matches
    """
    if not provided_token or not expected_token:
        return False
    
    # Constant-time comparison
    return hmac.compare_digest(provided_token, expected_token)


def extract_git_ref(payload: dict) -> Optional[str]:
    """Extract git ref (branch/tag) from webhook payload."""
    ref = payload.get("ref", "")
    if ref.startswith("refs/heads/"):
        return ref[11:]  # Remove "refs/heads/" prefix
    elif ref.startswith("refs/tags/"):
        return ref[10:]  # Remove "refs/tags/" prefix
    return ref


def extract_commit_hash(payload: dict) -> Optional[str]:
    """Extract commit hash from webhook payload."""
    # GitHub: after, GitLab: checkout_sha or after
    return payload.get("after") or payload.get("checkout_sha")


def is_valid_push_event(payload: dict, provider: str) -> bool:
    """Check if payload is a valid push event."""
    if provider == "github":
        # GitHub push event has 'ref' and 'commits'
        return "ref" in payload and "commits" in payload
    elif provider == "gitlab":
        # GitLab push event has 'ref' and 'commits' or 'checkout_sha'
        return "ref" in payload
    return False
```

- [ ] **Step 3: Write tests**

```python
"""Tests for webhook verification utilities."""

import pytest

from kimidokku.utils.webhook_verify import (
    extract_commit_hash,
    extract_git_ref,
    is_valid_push_event,
    verify_github_signature,
    verify_gitlab_token,
)


class TestVerifyGitHubSignature:
    """Test GitHub webhook signature verification."""

    def test_valid_signature(self):
        """Test that valid signature passes."""
        secret = "mysecret"
        payload = b'{"ref": "refs/heads/main"}'
        # Calculate expected signature
        import hashlib
        import hmac
        
        mac = hmac.new(secret.encode(), payload, hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"
        
        assert verify_github_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        """Test that invalid signature fails."""
        secret = "mysecret"
        payload = b'{"ref": "refs/heads/main"}'
        signature = "sha256=invalidhash123"
        
        assert verify_github_signature(payload, signature, secret) is False

    def test_missing_signature(self):
        """Test that missing signature fails."""
        secret = "mysecret"
        payload = b'{"ref": "refs/heads/main"}'
        
        assert verify_github_signature(payload, "", secret) is False
        assert verify_github_signature(payload, None, secret) is False

    def test_wrong_secret(self):
        """Test that wrong secret produces invalid signature."""
        secret = "mysecret"
        wrong_secret = "wrongsecret"
        payload = b'{"ref": "refs/heads/main"}'
        
        import hashlib
        import hmac
        
        mac = hmac.new(secret.encode(), payload, hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"
        
        assert verify_github_signature(payload, signature, wrong_secret) is False


class TestVerifyGitLabToken:
    """Test GitLab webhook token verification."""

    def test_valid_token(self):
        """Test that valid token passes."""
        assert verify_gitlab_token("secrettoken", "secrettoken") is True

    def test_invalid_token(self):
        """Test that invalid token fails."""
        assert verify_gitlab_token("wrongtoken", "secrettoken") is False

    def test_missing_token(self):
        """Test that missing token fails."""
        assert verify_gitlab_token("", "secrettoken") is False
        assert verify_gitlab_token(None, "secrettoken") is False


class TestExtractGitRef:
    """Test git ref extraction."""

    def test_extract_branch(self):
        """Test extracting branch name."""
        payload = {"ref": "refs/heads/main"}
        assert extract_git_ref(payload) == "main"

    def test_extract_tag(self):
        """Test extracting tag name."""
        payload = {"ref": "refs/tags/v1.0.0"}
        assert extract_git_ref(payload) == "v1.0.0"

    def test_extract_plain_ref(self):
        """Test extracting plain ref."""
        payload = {"ref": "main"}
        assert extract_git_ref(payload) == "main"

    def test_missing_ref(self):
        """Test handling missing ref."""
        assert extract_git_ref({}) is None


class TestExtractCommitHash:
    """Test commit hash extraction."""

    def test_github_after(self):
        """Test GitHub 'after' field."""
        payload = {"after": "abc123"}
        assert extract_commit_hash(payload) == "abc123"

    def test_gitlab_checkout_sha(self):
        """Test GitLab 'checkout_sha' field."""
        payload = {"checkout_sha": "def456"}
        assert extract_commit_hash(payload) == "def456"

    def test_missing_hash(self):
        """Test handling missing hash."""
        assert extract_commit_hash({}) is None


class TestIsValidPushEvent:
    """Test push event validation."""

    def test_github_push(self):
        """Test GitHub push event."""
        payload = {"ref": "refs/heads/main", "commits": []}
        assert is_valid_push_event(payload, "github") is True

    def test_gitlab_push(self):
        """Test GitLab push event."""
        payload = {"ref": "refs/heads/main", "checkout_sha": "abc"}
        assert is_valid_push_event(payload, "gitlab") is True

    def test_invalid_provider(self):
        """Test invalid provider."""
        assert is_valid_push_event({"ref": "main"}, "unknown") is False
```

- [ ] **Step 4: Run tests**

```bash
cd "/Users/anrogdev/OpenWork/KimiDokku MCP"
source .venv/bin/activate
pytest tests/test_webhook_verify.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/kimidokku/utils/ tests/test_webhook_verify.py
git commit -m "feat: add webhook verification utilities (HMAC, token validation)"
```

---

### Task 2: GitHub Webhook Endpoint

**Files:**
- Create: `src/kimidokku/routers/__init__.py`
- Create: `src/kimidokku/routers/webhooks.py`

- [ ] **Step 1: Create routers package init**

```python
"""FastAPI routers package."""
```

- [ ] **Step 2: Create webhooks.py with GitHub endpoint**

```python
"""Webhook endpoints for GitHub and GitLab."""

from fastapi import APIRouter, Header, HTTPException, Request, status

from kimidokku.database import db
from kimidokku.tools.apps import _run_git_deploy
from kimidokku.utils.webhook_verify import (
    extract_commit_hash,
    extract_git_ref,
    is_valid_push_event,
    verify_github_signature,
)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/github/{app_name}")
async def github_webhook(
    app_name: str,
    request: Request,
    x_hub_signature_256: str = Header(None),
):
    """
    GitHub webhook endpoint for auto-deploy.
    
    Verifies HMAC-SHA256 signature and triggers deployment if branch matches.
    """
    # Get app details including webhook secret
    app = await db.fetch_one(
        """
        SELECT a.name, a.branch, a.git_url, k.id as api_key_id, 
               c.value as webhook_secret
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        LEFT JOIN platform_config c ON c.key = 'webhook_secret_' || a.name
        WHERE a.name = ? AND k.is_active = 1
        """,
        (app_name,),
    )
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App '{app_name}' not found",
        )
    
    # Get webhook secret (from app-specific config or fallback)
    webhook_secret = app.get("webhook_secret")
    if not webhook_secret:
        # Try to get default webhook secret
        config = await db.fetch_one(
            "SELECT value FROM platform_config WHERE key = 'webhook_secret_default'"
        )
        webhook_secret = config["value"] if config else None
    
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook secret not configured",
        )
    
    # Read raw body for signature verification
    body = await request.body()
    
    # Verify signature
    if not verify_github_signature(body, x_hub_signature_256, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )
    
    # Parse payload
    try:
        import json
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    
    # Validate it's a push event
    if not is_valid_push_event(payload, "github"):
        return {
            "status": "ignored",
            "message": "Not a push event or no commits",
        }
    
    # Extract branch from ref
    pushed_branch = extract_git_ref(payload)
    if pushed_branch != app["branch"]:
        return {
            "status": "ignored",
            "message": f"Branch mismatch: got '{pushed_branch}', expected '{app['branch']}'",
        }
    
    # Check if app has git_url configured
    if not app["git_url"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App has no git_url configured",
        )
    
    # Create deploy log entry
    commit_hash = extract_commit_hash(payload)
    cursor = await db.execute(
        """
        INSERT INTO deploy_logs (app_name, triggered_by, git_ref, status, started_at)
        VALUES (?, 'webhook', ?, 'in_progress', datetime('now'))
        """,
        (app_name, commit_hash or pushed_branch),
    )
    deploy_id = cursor.lastrowid
    
    # Update app status
    await db.execute(
        "UPDATE apps SET status = 'deploying', last_deploy_at = datetime('now') WHERE name = ?",
        (app_name,),
    )
    
    # Trigger async deployment
    import asyncio
    asyncio.create_task(
        _run_git_deploy(app_name, app["git_url"], pushed_branch, deploy_id)
    )
    
    return {
        "status": "queued",
        "deploy_id": deploy_id,
        "message": f"Deployment queued for {app_name} from branch {pushed_branch}",
    }
```

- [ ] **Step 3: Update mcp_server.py or main.py**

Actually, update main.py to include the router:

Add to main.py imports:
```python
from kimidokku.routers import webhooks
```

Add to create_app() before return:
```python
    # Include webhook router
    app.include_router(webhooks.router)
```

- [ ] **Step 4: Commit**

```bash
git add src/kimidokku/routers/ src/kimidokku/main.py
git commit -m "feat: add GitHub webhook endpoint with HMAC verification"
```

---

### Task 3: GitLab Webhook Endpoint

**Files:**
- Modify: `src/kimidokku/routers/webhooks.py`

- [ ] **Step 1: Add GitLab endpoint to webhooks.py**

Add after the GitHub endpoint:

```python
@router.post("/gitlab/{app_name}")
async def gitlab_webhook(
    app_name: str,
    request: Request,
    x_gitlab_token: str = Header(None),
):
    """
    GitLab webhook endpoint for auto-deploy.
    
    Verifies X-Gitlab-Token and triggers deployment if branch matches.
    """
    # Get app details including webhook secret
    app = await db.fetch_one(
        """
        SELECT a.name, a.branch, a.git_url, k.id as api_key_id,
               c.value as webhook_secret
        FROM apps a
        JOIN api_keys k ON a.api_key_id = k.id
        LEFT JOIN platform_config c ON c.key = 'webhook_secret_' || a.name
        WHERE a.name = ? AND k.is_active = 1
        """,
        (app_name,),
    )
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App '{app_name}' not found",
        )
    
    # Get webhook secret (from app-specific config or fallback)
    webhook_secret = app.get("webhook_secret")
    if not webhook_secret:
        # Try to get default webhook secret
        config = await db.fetch_one(
            "SELECT value FROM platform_config WHERE key = 'webhook_secret_default'"
        )
        webhook_secret = config["value"] if config else None
    
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook secret not configured",
        )
    
    # Verify token
    from kimidokku.utils.webhook_verify import verify_gitlab_token
    
    if not verify_gitlab_token(x_gitlab_token, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # Parse payload
    try:
        import json
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    
    # Validate it's a push event
    if not is_valid_push_event(payload, "gitlab"):
        return {
            "status": "ignored",
            "message": "Not a push event",
        }
    
    # Extract branch from ref
    pushed_branch = extract_git_ref(payload)
    if pushed_branch != app["branch"]:
        return {
            "status": "ignored",
            "message": f"Branch mismatch: got '{pushed_branch}', expected '{app['branch']}'",
        }
    
    # Check if app has git_url configured
    if not app["git_url"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App has no git_url configured",
        )
    
    # Create deploy log entry
    commit_hash = extract_commit_hash(payload)
    cursor = await db.execute(
        """
        INSERT INTO deploy_logs (app_name, triggered_by, git_ref, status, started_at)
        VALUES (?, 'webhook', ?, 'in_progress', datetime('now'))
        """,
        (app_name, commit_hash or pushed_branch),
    )
    deploy_id = cursor.lastrowid
    
    # Update app status
    await db.execute(
        "UPDATE apps SET status = 'deploying', last_deploy_at = datetime('now') WHERE name = ?",
        (app_name,),
    )
    
    # Trigger async deployment
    import asyncio
    asyncio.create_task(
        _run_git_deploy(app_name, app["git_url"], pushed_branch, deploy_id)
    )
    
    return {
        "status": "queued",
        "deploy_id": deploy_id,
        "message": f"Deployment queued for {app_name} from branch {pushed_branch}",
    }
```

- [ ] **Step 2: Commit**

```bash
git add src/kimidokku/routers/webhooks.py
git commit -m "feat: add GitLab webhook endpoint with token verification"
```

---

### Task 4: Webhook Integration Tests

**Files:**
- Create: `tests/test_webhooks.py`

- [ ] **Step 1: Create webhook endpoint tests**

```python
"""Tests for webhook endpoints."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from kimidokku.main import app

client = TestClient(app)


class TestGitHubWebhook:
    """Test GitHub webhook endpoint."""

    def _generate_signature(self, payload: bytes, secret: str) -> str:
        """Generate GitHub webhook signature."""
        mac = hmac.new(secret.encode(), payload, hashlib.sha256)
        return f"sha256={mac.hexdigest()}"

    @patch("kimidokku.routers.webhooks.db")
    async def test_missing_app(self, mock_db):
        """Test webhook for non-existent app."""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        response = client.post(
            "/webhook/github/test-app",
            headers={"X-Hub-Signature-256": "sha256=test"},
            json={"ref": "refs/heads/main"},
        )
        
        assert response.status_code == 404

    @patch("kimidokku.routers.webhooks.db")
    async def test_invalid_signature(self, mock_db):
        """Test webhook with invalid signature."""
        mock_db.fetch_one = AsyncMock(return_value={
            "name": "test-app",
            "branch": "main",
            "git_url": "https://github.com/user/repo.git",
            "api_key_id": "key-123",
            "webhook_secret": "mysecret",
        })
        
        response = client.post(
            "/webhook/github/test-app",
            headers={"X-Hub-Signature-256": "sha256=invalid"},
            json={"ref": "refs/heads/main", "commits": []},
        )
        
        assert response.status_code == 401


class TestGitLabWebhook:
    """Test GitLab webhook endpoint."""

    @patch("kimidokku.routers.webhooks.db")
    async def test_missing_app(self, mock_db):
        """Test webhook for non-existent app."""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        response = client.post(
            "/webhook/gitlab/test-app",
            headers={"X-Gitlab-Token": "test-token"},
            json={"ref": "refs/heads/main"},
        )
        
        assert response.status_code == 404

    @patch("kimidokku.routers.webhooks.db")
    async def test_invalid_token(self, mock_db):
        """Test webhook with invalid token."""
        mock_db.fetch_one = AsyncMock(return_value={
            "name": "test-app",
            "branch": "main",
            "git_url": "https://gitlab.com/user/repo.git",
            "api_key_id": "key-123",
            "webhook_secret": "correct-token",
        })
        
        response = client.post(
            "/webhook/gitlab/test-app",
            headers={"X-Gitlab-Token": "wrong-token"},
            json={"ref": "refs/heads/main", "commits": []},
        )
        
        assert response.status_code == 401


class TestWebhookUtils:
    """Test webhook utility functions."""

    def test_extract_branch_from_ref(self):
        """Test extracting branch name from ref."""
        from kimidokku.utils.webhook_verify import extract_git_ref
        
        assert extract_git_ref({"ref": "refs/heads/main"}) == "main"
        assert extract_git_ref({"ref": "refs/heads/feature/test"}) == "feature/test"

    def test_extract_tag_from_ref(self):
        """Test extracting tag name from ref."""
        from kimidokku.utils.webhook_verify import extract_git_ref
        
        assert extract_git_ref({"ref": "refs/tags/v1.0.0"}) == "v1.0.0"
```

- [ ] **Step 2: Run all tests**

```bash
cd "/Users/anrogdev/OpenWork/KimiDokku MCP"
source .venv/bin/activate
pytest tests/test_webhooks.py tests/test_webhook_verify.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_webhooks.py
git commit -m "test: add webhook endpoint tests"
```

---

## Self-Review

**Spec coverage:**
- ✅ GitHub webhook endpoint with HMAC-SHA256 verification
- ✅ GitLab webhook endpoint with token verification
- ✅ Branch matching before deployment
- ✅ Deploy log creation with triggered_by='webhook'
- ✅ Async deployment trigger
- ✅ 404 for non-existent apps
- ✅ 401 for invalid signatures/tokens
- ✅ 400 for missing webhook secrets

**Placeholder scan:**
- ✅ No TBD/TODO placeholders
- ✅ All code shown explicitly

**Type consistency:**
- ✅ Consistent error handling patterns
- ✅ Similar database query patterns

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-07-phase3-rest-api-webhooks.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
