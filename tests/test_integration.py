"""Integration tests for KimiDokku MCP."""

import pytest
from fastapi.testclient import TestClient

from kimidokku.csrf import get_csrf
from kimidokku.main import app


@pytest.fixture
def client():
    """Create a test client with database initialization."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def csrf_token():
    """Generate a valid CSRF token for testing."""
    csrf = get_csrf()
    return csrf.generate_token()


def get_csrf_headers(csrf_token):
    """Get headers dict with CSRF token for POST/DELETE requests."""
    return {"X-CSRF-Token": csrf_token}


class TestSecurityHeaders:
    """Test security headers are present."""

    def test_security_headers_on_all_routes(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"


class TestRateLimiting:
    """Test rate limiting enforcement."""

    def test_webhook_rate_limit(self, client):
        """Should return 429 after limit exceeded."""
        # Make 15 rapid requests
        for i in range(15):
            response = client.post(
                "/webhook/github/test-app",
                headers={"X-Hub-Signature-256": "sha256=test"},
                json={"ref": "refs/heads/main"},
            )

        # Should get rate limited
        assert response.status_code == 429


class TestAPIKeyLifecycle:
    """Test full API key lifecycle."""

    def test_create_list_revoke_delete(self, client, csrf_token):
        """Full CRUD cycle for API keys."""
        # Create
        create_resp = client.post(
            "/api/keys",
            json={"name": "lifecycle-test"},
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert create_resp.status_code == 200
        key_id = create_resp.json()["id"]

        # List
        list_resp = client.get("/api/keys", auth=("admin", "changeme"))
        assert list_resp.status_code == 200

        # Revoke
        revoke_resp = client.post(
            f"/api/keys/{key_id}/revoke",
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert revoke_resp.status_code == 200

        # Delete
        delete_resp = client.delete(
            f"/api/keys/{key_id}",
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert delete_resp.status_code == 200
