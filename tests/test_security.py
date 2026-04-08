"""Security tests for KimiDokku MCP."""

import uuid

import pytest
from fastapi import HTTPException

from kimidokku.auth import verify_api_key
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
