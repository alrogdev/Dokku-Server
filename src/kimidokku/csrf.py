"""CSRF protection for Web UI."""

import secrets
from typing import Optional

from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from kimidokku.config import get_settings


class CSRFProtection:
    """CSRF token generation and validation."""

    def __init__(self, secret_key: str):
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.token_name = "csrf_token"
        self.max_age = 3600  # 1 hour

    def generate_token(self) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        return self.serializer.dumps(token)

    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token."""
        try:
            self.serializer.loads(token, max_age=self.max_age)
            return True
        except (BadSignature, Exception):
            return False

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Get CSRF token from request (header or form)."""
        # Check header first (for HTMX requests)
        token = request.headers.get("X-CSRF-Token")
        if token:
            return token

        # Check form data
        # Note: This would need to be async in real usage
        return None


def get_csrf() -> CSRFProtection:
    """Get CSRF protection instance."""
    settings = get_settings()
    secret = getattr(settings, "csrf_secret", None) or settings.auth_pass
    return CSRFProtection(secret)


async def verify_csrf_token(request: Request):
    """Dependency to verify CSRF token on POST/PUT/DELETE requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True

    csrf = get_csrf()
    token = request.headers.get("X-CSRF-Token")

    if not token or not csrf.validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        )

    return True
