"""Rate limiting configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address


# Create limiter instance
# Using remote address as key, but could also use API key for authenticated routes
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default: 100 requests per minute
)


def get_limiter() -> Limiter:
    """Get rate limiter instance."""
    return limiter
