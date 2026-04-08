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
        mock_db.fetch_one = AsyncMock(
            return_value={
                "name": "test-app",
                "branch": "main",
                "git_url": "https://github.com/user/repo.git",
                "api_key_id": "key-123",
                "webhook_secret": "mysecret",
            }
        )

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
        mock_db.fetch_one = AsyncMock(
            return_value={
                "name": "test-app",
                "branch": "main",
                "git_url": "https://gitlab.com/user/repo.git",
                "api_key_id": "key-123",
                "webhook_secret": "correct-token",
            }
        )

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
