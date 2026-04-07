"""Tests for authentication."""

import pytest
from fastapi import HTTPException

from kimidokku.auth import mask_secrets, verify_api_key, generate_api_key


class TestMaskSecrets:
    """Test secret masking functionality."""

    def test_masks_secret_keys(self):
        """Test that secret keys are masked."""
        config = {
            "DATABASE_URL": "postgres://user:pass@localhost/db",
            "API_KEY": "secret123",
            "SECRET_TOKEN": "token456",
            "PASSWORD": "mypass",
            "PUBLIC_VAR": "visible",
        }

        masked = mask_secrets(config)

        # URLs should not be masked even if they contain "pass"
        assert masked["DATABASE_URL"] == "postgres://user:pass@localhost/db"
        # Secrets should be masked
        assert masked["API_KEY"] == "***"
        assert masked["SECRET_TOKEN"] == "***"
        assert masked["PASSWORD"] == "***"
        # Public vars should not be masked
        assert masked["PUBLIC_VAR"] == "visible"

    def test_case_insensitive_matching(self):
        """Test that secret detection is case insensitive."""
        config = {
            "my_api_KEY": "secret",
            "MY_SECRET": "hidden",
        }

        masked = mask_secrets(config)

        assert masked["my_api_KEY"] == "***"
        assert masked["MY_SECRET"] == "***"


class TestGenerateApiKey:
    """Test API key generation."""

    def test_generates_valid_uuid(self):
        """Test that generated key is valid UUID4."""
        import uuid

        key = generate_api_key()

        # Should be able to parse as UUID
        parsed = uuid.UUID(key)
        assert parsed.version == 4

    def test_generates_unique_keys(self):
        """Test that generated keys are unique."""
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100
