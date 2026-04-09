"""Tests for API Key Management REST API."""

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


class TestAPICreateKey:
    def test_create_key_requires_auth(self, client):
        response = client.post("/api/keys", json={"name": "test-key"})
        assert response.status_code == 401

    def test_create_key_success(self, client, csrf_token):
        response = client.post(
            "/api/keys",
            json={"name": "test-key", "max_apps": 5},
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "key" in data
        assert data["name"] == "test-key"

    def test_create_key_default_max_apps(self, client, csrf_token):
        response = client.post(
            "/api/keys",
            json={"name": "test-key-default"},
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert response.json()["max_apps"] == 10


class TestAPIListKeys:
    def test_list_keys_requires_auth(self, client):
        response = client.get("/api/keys")
        assert response.status_code == 401

    def test_list_keys_success(self, client):
        response = client.get("/api/keys", auth=("admin", "changeme"))
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAPIRevokeKey:
    def test_revoke_key_success(self, client, csrf_token):
        create_resp = client.post(
            "/api/keys",
            json={"name": "key-to-revoke"},
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        key_id = create_resp.json()["id"]

        response = client.post(
            f"/api/keys/{key_id}/revoke",
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert response.status_code == 200

    def test_revoke_nonexistent_key(self, client, csrf_token):
        response = client.post(
            "/api/keys/nonexistent/revoke",
            auth=("admin", "changeme"),
            headers=get_csrf_headers(csrf_token),
        )
        assert response.status_code == 404
