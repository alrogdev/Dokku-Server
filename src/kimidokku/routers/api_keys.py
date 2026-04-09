"""API Key management REST API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from kimidokku.auth import verify_basic_auth
from kimidokku.csrf import verify_csrf_token
from kimidokku.database import db

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    max_apps: int = Field(default=10, ge=1, le=100)


class APIKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str
    max_apps: int
    message: str


@router.post("/", response_model=APIKeyCreateResponse)
async def create_api_key(
    data: APIKeyCreate,
    request: Request,
    username: str = Depends(verify_basic_auth),
    _: bool = Depends(verify_csrf_token),
):
    key_id = str(uuid.uuid4())

    await db.execute(
        "INSERT INTO api_keys (id, name, max_apps, is_active) VALUES (?, ?, ?, 1)",
        (key_id, data.name, data.max_apps),
    )

    return APIKeyCreateResponse(
        id=key_id,
        name=data.name,
        key=key_id,
        max_apps=data.max_apps,
        message="Store this key securely - it will not be shown again",
    )


@router.get("/")
async def list_api_keys(username: str = Depends(verify_basic_auth)):
    keys = await db.fetch_all(
        """
        SELECT k.id, k.name, k.max_apps, k.created_at, k.is_active, COUNT(a.name) as app_count
        FROM api_keys k
        LEFT JOIN apps a ON k.id = a.api_key_id
        GROUP BY k.id
        ORDER BY k.created_at DESC
        """
    )
    return keys


@router.get("/{key_id}")
async def get_api_key(key_id: str, username: str = Depends(verify_basic_auth)):
    key = await db.fetch_one(
        """
        SELECT k.id, k.name, k.max_apps, k.created_at, k.is_active, COUNT(a.name) as app_count
        FROM api_keys k
        LEFT JOIN apps a ON k.id = a.api_key_id
        WHERE k.id = ?
        GROUP BY k.id
        """,
        (key_id,),
    )

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    return key


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    request: Request,
    username: str = Depends(verify_basic_auth),
    _: bool = Depends(verify_csrf_token),
):
    key = await db.fetch_one("SELECT id FROM api_keys WHERE id = ?", (key_id,))
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
    return {"message": "API key revoked successfully"}


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    request: Request,
    username: str = Depends(verify_basic_auth),
    _: bool = Depends(verify_csrf_token),
):
    key = await db.fetch_one("SELECT id FROM api_keys WHERE id = ?", (key_id,))
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    return {"message": "API key and associated apps deleted"}
