"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient

from kimidokku.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_returns_ok(self):
        """Health check should return status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_has_timestamp(self):
        """Health check should have dynamic timestamp."""
        response = client.get("/health")
        data = response.json()

        # Should not be the hardcoded placeholder
        assert data["timestamp"] != "2024-01-01T00:00:00Z"

        # Should be a valid ISO format timestamp
        from datetime import datetime

        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert timestamp.year >= 2024

    def test_health_check_checks_dokku(self):
        """Health check should report dokku connectivity."""
        response = client.get("/health")
        data = response.json()

        # Should have dokku_connected field
        assert "dokku_connected" in data
        # Should be boolean, not always True
        assert isinstance(data["dokku_connected"], bool)
