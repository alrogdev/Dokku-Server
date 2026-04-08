"""Tests for webhook verification utilities."""

import hashlib
import hmac
import pytest

from kimidokku.utils.webhook_verify import (
    verify_github_signature,
    verify_gitlab_token,
    extract_git_ref,
    extract_commit_hash,
    is_valid_push_event,
)


class TestVerifyGitHubSignature:
    """Tests for verify_github_signature function."""

    def test_valid_signature(self):
        """Test verification with valid signature."""
        payload = b'{"ref":"refs/heads/main"}'
        secret = "my-secret"

        # Calculate expected signature
        mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        assert verify_github_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        """Test verification with invalid signature."""
        payload = b'{"ref":"refs/heads/main"}'
        secret = "my-secret"
        signature = "sha256=invalidhash123"

        assert verify_github_signature(payload, signature, secret) is False

    def test_missing_signature(self):
        """Test verification with missing signature."""
        payload = b'{"ref":"refs/heads/main"}'
        secret = "my-secret"

        assert verify_github_signature(payload, "", secret) is False
        assert verify_github_signature(payload, None, secret) is False

    def test_wrong_prefix(self):
        """Test signature without sha256= prefix."""
        payload = b'{"ref":"refs/heads/main"}'
        secret = "my-secret"
        signature = "abc123"  # No prefix

        assert verify_github_signature(payload, signature, secret) is False

    def test_tampered_payload(self):
        """Test that tampered payload fails verification."""
        original_payload = b'{"ref":"refs/heads/main"}'
        secret = "my-secret"

        # Calculate signature for original payload
        mac = hmac.new(secret.encode("utf-8"), original_payload, hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        # Try to verify with tampered payload
        tampered_payload = b'{"ref":"refs/heads/malicious"}'
        assert verify_github_signature(tampered_payload, signature, secret) is False


class TestVerifyGitLabToken:
    """Tests for verify_gitlab_token function."""

    def test_valid_token(self):
        """Test verification with valid token."""
        token = "my-secret-token"
        assert verify_gitlab_token(token, token) is True

    def test_invalid_token(self):
        """Test verification with invalid token."""
        assert verify_gitlab_token("wrong-token", "expected-token") is False

    def test_missing_token(self):
        """Test verification with missing tokens."""
        assert verify_gitlab_token("", "expected") is False
        assert verify_gitlab_token("provided", "") is False
        assert verify_gitlab_token(None, "expected") is False


class TestExtractGitRef:
    """Tests for extract_git_ref function."""

    def test_extract_branch(self):
        """Test extracting branch name from refs/heads/."""
        payload = {"ref": "refs/heads/main"}
        assert extract_git_ref(payload) == "main"

    def test_extract_tag(self):
        """Test extracting tag name from refs/tags/."""
        payload = {"ref": "refs/tags/v1.0.0"}
        assert extract_git_ref(payload) == "v1.0.0"

    def test_extract_feature_branch(self):
        """Test extracting feature branch name."""
        payload = {"ref": "refs/heads/feature/new-thing"}
        assert extract_git_ref(payload) == "feature/new-thing"

    def test_empty_ref(self):
        """Test extracting from empty ref."""
        payload = {"ref": ""}
        assert extract_git_ref(payload) == ""

    def test_missing_ref(self):
        """Test extracting from missing ref."""
        payload = {}
        assert extract_git_ref(payload) == ""

    def test_raw_ref(self):
        """Test extracting raw ref without prefix."""
        payload = {"ref": "some-random-ref"}
        assert extract_git_ref(payload) == "some-random-ref"


class TestExtractCommitHash:
    """Tests for extract_commit_hash function."""

    def test_github_after(self):
        """Test extracting from GitHub 'after' field."""
        payload = {"after": "abc123def456"}
        assert extract_commit_hash(payload) == "abc123def456"

    def test_gitlab_checkout_sha(self):
        """Test extracting from GitLab 'checkout_sha' field."""
        payload = {"checkout_sha": "def789abc012"}
        assert extract_commit_hash(payload) == "def789abc012"

    def test_prefer_after_over_checkout_sha(self):
        """Test that 'after' takes precedence over 'checkout_sha'."""
        payload = {"after": "abc123", "checkout_sha": "def456"}
        assert extract_commit_hash(payload) == "abc123"

    def test_missing_commit(self):
        """Test extracting when no commit hash present."""
        payload = {}
        assert extract_commit_hash(payload) is None


class TestIsValidPushEvent:
    """Tests for is_valid_push_event function."""

    def test_github_valid_push(self):
        """Test valid GitHub push event."""
        payload = {"ref": "refs/heads/main", "commits": [{"id": "abc123"}]}
        assert is_valid_push_event(payload, "github") is True

    def test_github_missing_commits(self):
        """Test GitHub payload without commits."""
        payload = {"ref": "refs/heads/main"}
        assert is_valid_push_event(payload, "github") is False

    def test_github_missing_ref(self):
        """Test GitHub payload without ref."""
        payload = {"commits": [{"id": "abc123"}]}
        assert is_valid_push_event(payload, "github") is False

    def test_gitlab_valid_push(self):
        """Test valid GitLab push event."""
        payload = {"ref": "refs/heads/main", "checkout_sha": "abc123"}
        assert is_valid_push_event(payload, "gitlab") is True

    def test_gitlab_only_ref(self):
        """Test GitLab push with just ref."""
        payload = {"ref": "refs/heads/main"}
        assert is_valid_push_event(payload, "gitlab") is True

    def test_gitlab_missing_ref(self):
        """Test GitLab payload without ref."""
        payload = {"checkout_sha": "abc123"}
        assert is_valid_push_event(payload, "gitlab") is False

    def test_unknown_provider(self):
        """Test with unknown provider."""
        payload = {"ref": "refs/heads/main"}
        assert is_valid_push_event(payload, "bitbucket") is False
