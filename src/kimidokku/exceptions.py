"""Custom exceptions for KimiDokku MCP."""


class KimiDokkuError(Exception):
    """Base exception."""

    pass


class AppNotFoundError(KimiDokkuError):
    """App not found."""

    pass


class PermissionDeniedError(KimiDokkuError):
    """Permission denied."""

    pass


class CommandError(KimiDokkuError):
    """Command execution error."""

    pass


class ValidationError(KimiDokkuError):
    """Input validation error."""

    pass
