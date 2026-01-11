"""Exceptions for pyliebherrhomeapi."""


class LiebherrError(Exception):
    """Base exception for Liebherr API errors."""


class LiebherrConnectionError(LiebherrError):
    """Exception raised when connection to Liebherr API fails."""


class LiebherrTimeoutError(LiebherrError):
    """Exception raised when request to Liebherr API times out."""


class LiebherrAuthenticationError(LiebherrError):
    """Exception raised when authentication fails."""


class LiebherrBadRequestError(LiebherrError):
    """Exception raised when invalid data is provided."""


class LiebherrNotFoundError(LiebherrError):
    """Exception raised when device is not reachable."""


class LiebherrPreconditionFailedError(LiebherrError):
    """Exception raised when precondition fails (device not onboarded)."""


class LiebherrUnsupportedError(LiebherrError):
    """Exception raised when operation is not supported."""


class LiebherrServerError(LiebherrError):
    """Exception raised when server returns 500 error."""
