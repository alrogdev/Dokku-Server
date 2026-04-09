"""Tests for custom exceptions."""

import pytest
from fastapi.testclient import TestClient

from kimidokku.exceptions import (
    AppNotFoundError,
    CommandError,
    KimiDokkuError,
    PermissionDeniedError,
    ValidationError,
)
from kimidokku.main import app

client = TestClient(app)


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_base_exception_inheritance(self):
        """All exceptions should inherit from KimiDokkuError."""
        assert issubclass(AppNotFoundError, KimiDokkuError)
        assert issubclass(PermissionDeniedError, KimiDokkuError)
        assert issubclass(CommandError, KimiDokkuError)
        assert issubclass(ValidationError, KimiDokkuError)

    def test_base_exception_is_exception(self):
        """KimiDokkuError should inherit from Exception."""
        assert issubclass(KimiDokkuError, Exception)

    def test_app_not_found_error_message(self):
        """AppNotFoundError should accept and store message."""
        exc = AppNotFoundError("App 'test' not found")
        assert str(exc) == "App 'test' not found"

    def test_validation_error_message(self):
        """ValidationError should accept and store message."""
        exc = ValidationError("Invalid input")
        assert str(exc) == "Invalid input"

    def test_command_error_message(self):
        """CommandError should accept and store message."""
        exc = CommandError("Command failed")
        assert str(exc) == "Command failed"

    def test_permission_denied_error_message(self):
        """PermissionDeniedError should accept and store message."""
        exc = PermissionDeniedError("Access denied")
        assert str(exc) == "Access denied"


class TestExceptionHandlers:
    """Test exception handlers in FastAPI app."""

    @pytest.mark.asyncio
    async def test_app_not_found_error_handler(self):
        """AppNotFoundError should return 404 JSON response."""
        from kimidokku.main import kimidokku_exception_handler

        class MockRequest:
            pass

        exc = AppNotFoundError("App not found")
        response = await kimidokku_exception_handler(MockRequest(), exc)

        assert response.status_code == 404
        assert response.body == b'{"error":"AppNotFoundError","message":"App not found"}'

    @pytest.mark.asyncio
    async def test_permission_denied_error_handler(self):
        """PermissionDeniedError should return 403 JSON response."""
        from kimidokku.main import kimidokku_exception_handler

        class MockRequest:
            pass

        exc = PermissionDeniedError("Permission denied")
        response = await kimidokku_exception_handler(MockRequest(), exc)

        assert response.status_code == 403
        assert response.body == b'{"error":"PermissionDeniedError","message":"Permission denied"}'

    @pytest.mark.asyncio
    async def test_validation_error_handler(self):
        """ValidationError should return 400 JSON response."""
        from kimidokku.main import kimidokku_exception_handler

        class MockRequest:
            pass

        exc = ValidationError("Invalid command format")
        response = await kimidokku_exception_handler(MockRequest(), exc)

        assert response.status_code == 400
        assert response.body == b'{"error":"ValidationError","message":"Invalid command format"}'

    @pytest.mark.asyncio
    async def test_command_error_handler(self):
        """CommandError should return 500 JSON response."""
        from kimidokku.main import kimidokku_exception_handler

        class MockRequest:
            pass

        exc = CommandError("Command failed")
        response = await kimidokku_exception_handler(MockRequest(), exc)

        assert response.status_code == 500
        assert response.body == b'{"error":"CommandError","message":"Command failed"}'

    @pytest.mark.asyncio
    async def test_base_error_handler(self):
        """Base KimiDokkuError should return 500 JSON response."""
        from kimidokku.main import kimidokku_exception_handler

        class MockRequest:
            pass

        exc = KimiDokkuError("Generic error")
        response = await kimidokku_exception_handler(MockRequest(), exc)

        assert response.status_code == 500
        assert response.body == b'{"error":"KimiDokkuError","message":"Generic error"}'


class TestLogsModuleExceptions:
    """Test that logs.py uses custom exceptions correctly."""

    def test_logs_imports_exceptions(self):
        """logs.py should import custom exceptions."""
        from kimidokku.tools import logs

        assert hasattr(logs, "AppNotFoundError")
        assert hasattr(logs, "CommandError")
        assert hasattr(logs, "ValidationError")
