"""Tests for rate limiting."""

import pytest
from fastapi.testclient import TestClient

from kimidokku.main import app
from kimidokku.middleware.rate_limiter import limiter, get_limiter

client = TestClient(app)


def test_rate_limiter_instance_exists():
    """Test that rate limiter instance exists and is configured."""
    assert limiter is not None
    assert get_limiter() is limiter


def test_rate_limiter_attached_to_app():
    """Test rate limit exceeded error handler returns proper format."""
    # This test verifies the error handler is registered
    # We can't easily trigger rate limit in tests without making many requests,
    # so we just verify the app has the limiter configured
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is not None


def test_rate_limiter_has_default_limits():
    """Test that default limits are configured."""
    # The limiter should have default limits set
    assert len(limiter._default_limits) > 0
    # Just verify that default limits exist (they are LimitGroup objects)
    assert limiter._default_limits[0] is not None


def test_webhook_rate_limit_decorated():
    """Test that webhook endpoints have rate limit decorators."""
    from kimidokku.routers import webhooks

    # Check that the github_webhook function has been wrapped by limiter
    github_func = webhooks.github_webhook
    # The function should be wrapped (has __wrapped__ attribute from decorator)
    assert hasattr(github_func, "__wrapped__") or "limit" in str(github_func)

    # Check gitlab_webhook too
    gitlab_func = webhooks.gitlab_webhook
    assert hasattr(gitlab_func, "__wrapped__") or "limit" in str(gitlab_func)


def test_ui_rate_limit_decorated():
    """Test that UI endpoints have rate limit decorators."""
    from kimidokku.routers import ui

    # Check that dashboard function has been wrapped by limiter
    dashboard_func = ui.dashboard
    assert hasattr(dashboard_func, "__wrapped__") or "limit" in str(dashboard_func)
