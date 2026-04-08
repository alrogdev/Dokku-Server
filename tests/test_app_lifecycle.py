"""Tests for app lifecycle tools."""

import pytest

from kimidokku.exceptions import AppNotFoundError, PermissionDeniedError, ValidationError
from kimidokku.tools.apps import create_app, delete_app


class TestCreateApp:
    """Test create_app tool."""

    @pytest.mark.asyncio
    async def test_create_app_validates_name(self):
        """Should validate app name format."""
        with pytest.raises(ValidationError):
            await create_app("key-123", "Invalid Name")  # Spaces not allowed

        with pytest.raises(ValidationError):
            await create_app("key-123", "UPPERCASE")  # Uppercase not allowed

    @pytest.mark.asyncio
    async def test_create_app_enforces_limits(self, monkeypatch):
        """Should enforce API key app limits."""

        async def mock_fetch_one(query, params):
            if "max_apps" in query:
                return {"max_apps": 2}
            if "count" in query.lower():
                return {"count": 2}  # Already at limit
            return None

        monkeypatch.setattr("kimidokku.tools.apps.db.fetch_one", mock_fetch_one)

        with pytest.raises(PermissionDeniedError):
            await create_app("key-123", "my-app")


class TestDeleteApp:
    """Test delete_app tool."""

    @pytest.mark.asyncio
    async def test_delete_app_requires_force(self):
        """Should require force=True."""
        with pytest.raises(ValidationError):
            await delete_app("my-app", "key-123", force=False)

    @pytest.mark.asyncio
    async def test_delete_app_checks_ownership(self, monkeypatch):
        """Should verify app ownership."""

        async def mock_fetch_one(query, params):
            return None  # App not found or not owned

        monkeypatch.setattr("kimidokku.tools.apps.db.fetch_one", mock_fetch_one)

        with pytest.raises(AppNotFoundError):
            await delete_app("my-app", "key-123", force=True)
