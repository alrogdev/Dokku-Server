"""Authentication and authorization utilities."""

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials

from kimidokku.config import get_settings
from kimidokku.database import db

# API Key header for MCP/REST authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# HTTP Basic auth for Web UI
http_basic = HTTPBasic(auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key and return associated key ID."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate UUID format
    try:
        # Basic UUID validation (will be enhanced with proper validation)
        if len(api_key) < 32:
            raise ValueError("Invalid API key format")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    # Check if key exists and is active
    result = await db.fetch_one(
        "SELECT id, is_active FROM api_keys WHERE id = ?",
        (api_key,),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not result["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is revoked",
        )

    return result["id"]


async def verify_app_ownership(
    app_name: str,
    api_key_id: str = Depends(verify_api_key),
) -> tuple[str, str]:
    """Verify that the API key owns the specified app."""
    result = await db.fetch_one(
        "SELECT api_key_id FROM apps WHERE name = ?",
        (app_name,),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"App '{app_name}' not found",
        )

    if result["api_key_id"] != api_key_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this app",
        )

    return app_name, api_key_id


async def verify_basic_auth(
    credentials: HTTPBasicCredentials = Depends(http_basic),
) -> str:
    """Verify Web UI basic authentication."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    settings = get_settings()

    is_correct_username = secrets.compare_digest(credentials.username, settings.auth_user)
    is_correct_password = secrets.compare_digest(credentials.password, settings.auth_pass)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def generate_api_key() -> str:
    """Generate a new cryptographically secure API key (UUID4 format)."""
    import uuid

    return str(uuid.uuid4())


SECRET_PATTERNS = [
    "key",
    "pass",
    "secret",
    "token",
    "private",
    "credential",
]


def mask_secrets(config: dict[str, str]) -> dict[str, str]:
    """Mask secret values in configuration."""
    masked = {}
    for key, value in config.items():
        key_lower = key.lower()
        is_secret = any(pattern in key_lower for pattern in SECRET_PATTERNS)
        # Don't mask URLs that start with http
        if is_secret and not value.startswith(("http://", "https://")):
            masked[key] = "***"
        else:
            masked[key] = value
    return masked
