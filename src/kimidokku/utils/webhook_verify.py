"""Webhook signature verification utilities."""

import hashlib
import hmac
from typing import Optional


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook HMAC-SHA256 signature.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (e.g., "sha256=abc123...")
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False

    # Extract hash from signature
    expected_hash = signature[7:]  # Remove "sha256=" prefix

    # Calculate HMAC
    mac = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    )
    computed_hash = mac.hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_hash, computed_hash)


def verify_gitlab_token(provided_token: str, expected_token: str) -> bool:
    """
    Verify GitLab webhook X-Gitlab-Token.

    Args:
        provided_token: X-Gitlab-Token header value
        expected_token: Expected token

    Returns:
        True if token matches
    """
    if not provided_token or not expected_token:
        return False

    # Constant-time comparison
    return hmac.compare_digest(provided_token, expected_token)


def extract_git_ref(payload: dict) -> Optional[str]:
    """Extract git ref (branch/tag) from webhook payload."""
    ref = payload.get("ref", "")
    if ref.startswith("refs/heads/"):
        return ref[11:]  # Remove "refs/heads/" prefix
    elif ref.startswith("refs/tags/"):
        return ref[10:]  # Remove "refs/tags/" prefix
    return ref


def extract_commit_hash(payload: dict) -> Optional[str]:
    """Extract commit hash from webhook payload."""
    # GitHub: after, GitLab: checkout_sha or after
    return payload.get("after") or payload.get("checkout_sha")


def is_valid_push_event(payload: dict, provider: str) -> bool:
    """Check if payload is a valid push event."""
    if provider == "github":
        # GitHub push event has 'ref' and 'commits'
        return "ref" in payload and "commits" in payload
    elif provider == "gitlab":
        # GitLab push event has 'ref' and 'commits' or 'checkout_sha'
        return "ref" in payload
    return False
