"""Security tests for KimiDokku MCP."""

import pytest

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
