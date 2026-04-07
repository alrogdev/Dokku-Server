"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from kimidokku.config import Settings, get_settings


class TestSettings:
    """Test settings loading and validation."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()

        assert settings.kimidokku_domain == "app.localhost"
        assert settings.dokku_host == "localhost"
        assert settings.auth_user == "admin"
        assert settings.auth_pass == "changeme"
        assert settings.db_path == Path("./kimidokku.db")
        assert settings.environment == "development"

    def test_environment_property(self):
        """Test environment property detection."""
        dev_settings = Settings(environment="development")
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False

        prod_settings = Settings(environment="production")
        assert prod_settings.is_development is False
        assert prod_settings.is_production is True

    def test_custom_values(self):
        """Test that custom values can be set."""
        settings = Settings(
            kimidokku_domain="app.example.com",
            auth_user="custom_admin",
            db_path=Path("/custom/path/db.sqlite"),
        )

        assert settings.kimidokku_domain == "app.example.com"
        assert settings.auth_user == "custom_admin"
        assert settings.db_path == Path("/custom/path/db.sqlite")

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
