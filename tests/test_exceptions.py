"""Tests for Liebherr exceptions."""

import pytest

from pyliebherrhomeapi import (
    LiebherrAuthenticationError,
    LiebherrBadRequestError,
    LiebherrConnectionError,
    LiebherrError,
    LiebherrNotFoundError,
    LiebherrPreconditionFailedError,
    LiebherrServerError,
    LiebherrTimeoutError,
    LiebherrUnsupportedError,
)


class TestExceptions:
    """Tests for exception classes."""

    def test_liebherr_error_base(self) -> None:
        """Test base LiebherrError exception."""
        error = LiebherrError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_authentication_error(self) -> None:
        """Test LiebherrAuthenticationError."""
        error = LiebherrAuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, LiebherrError)

    def test_bad_request_error(self) -> None:
        """Test LiebherrBadRequestError."""
        error = LiebherrBadRequestError("Invalid data")
        assert str(error) == "Invalid data"
        assert isinstance(error, LiebherrError)

    def test_connection_error(self) -> None:
        """Test LiebherrConnectionError."""
        error = LiebherrConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, LiebherrError)

    def test_not_found_error(self) -> None:
        """Test LiebherrNotFoundError."""
        error = LiebherrNotFoundError("Device not found")
        assert str(error) == "Device not found"
        assert isinstance(error, LiebherrError)

    def test_precondition_failed_error(self) -> None:
        """Test LiebherrPreconditionFailedError."""
        error = LiebherrPreconditionFailedError("Device not onboarded")
        assert str(error) == "Device not onboarded"
        assert isinstance(error, LiebherrError)

    def test_server_error(self) -> None:
        """Test LiebherrServerError."""
        error = LiebherrServerError("Internal server error")
        assert str(error) == "Internal server error"
        assert isinstance(error, LiebherrError)

    def test_timeout_error(self) -> None:
        """Test LiebherrTimeoutError."""
        error = LiebherrTimeoutError("Request timed out")
        assert str(error) == "Request timed out"
        assert isinstance(error, LiebherrError)

    def test_unsupported_error(self) -> None:
        """Test LiebherrUnsupportedError."""
        error = LiebherrUnsupportedError("Operation not supported")
        assert str(error) == "Operation not supported"
        assert isinstance(error, LiebherrError)

    def test_exception_inheritance(self) -> None:
        """Test that all exceptions inherit from LiebherrError."""
        exceptions = [
            LiebherrAuthenticationError,
            LiebherrBadRequestError,
            LiebherrConnectionError,
            LiebherrNotFoundError,
            LiebherrPreconditionFailedError,
            LiebherrServerError,
            LiebherrTimeoutError,
            LiebherrUnsupportedError,
        ]

        for exc_class in exceptions:
            error = exc_class("Test")
            assert isinstance(error, LiebherrError)
            assert isinstance(error, Exception)

    def test_exception_raising(self) -> None:
        """Test that exceptions can be raised and caught."""
        with pytest.raises(LiebherrError):
            raise LiebherrError("Test")

        with pytest.raises(LiebherrAuthenticationError):
            raise LiebherrAuthenticationError("Auth failed")

        with pytest.raises(LiebherrConnectionError):
            raise LiebherrConnectionError("Connection failed")
