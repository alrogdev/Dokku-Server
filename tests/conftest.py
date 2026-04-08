"""Pytest fixtures for KimiDokku MCP tests."""

import asyncio
import uuid

import pytest
import pytest_asyncio

from kimidokku.database import db


@pytest_asyncio.fixture
async def test_db():
    """Initialize test database."""
    await db.initialize(":memory:")
    yield db


@pytest_asyncio.fixture
async def test_api_key(test_db):
    """Create a test API key."""
    key_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO api_keys (id, name, max_apps, is_active) VALUES (?, ?, ?, 1)",
        (key_id, "test-key", 10),
    )
    yield key_id
    await db.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
