"""Tests for error handling."""

import pytest
from mailer.errors import (
    MailerError,
    AuthenticationError,
    GmailAPIError,
    MessageNotFoundError,
    QuotaExceededError,
    parse_gmail_error,
)


class TestErrorTypes:
    """Tests for error type hierarchy."""

    def test_all_errors_inherit_from_mailer_error(self) -> None:
        """Test that all custom errors inherit from MailerError."""
        assert issubclass(AuthenticationError, MailerError)
        assert issubclass(GmailAPIError, MailerError)
        assert issubclass(MessageNotFoundError, MailerError)
        assert issubclass(QuotaExceededError, MailerError)

    def test_gmail_api_error_stores_status_code(self) -> None:
        """Test GmailAPIError stores HTTP status code."""
        error = GmailAPIError("API failed", status_code=400)
        assert error.status_code == 400
        assert str(error) == "API failed"


class TestParseGmailError:
    """Tests for parse_gmail_error function."""

    def test_parses_not_found_error(self) -> None:
        """Test parsing 'not found' errors."""
        error = Exception("Message not found")
        parsed = parse_gmail_error(error)
        assert isinstance(parsed, MessageNotFoundError)

    def test_parses_quota_error(self) -> None:
        """Test parsing quota exceeded errors."""
        error = Exception("Quota exceeded")
        parsed = parse_gmail_error(error)
        assert isinstance(parsed, QuotaExceededError)

    def test_parses_rate_limit_error(self) -> None:
        """Test parsing rate limit errors."""
        error = Exception("Rate limit exceeded")
        parsed = parse_gmail_error(error)
        assert isinstance(parsed, QuotaExceededError)

    def test_parses_auth_error(self) -> None:
        """Test parsing authentication errors."""
        error = Exception("Invalid credentials")
        parsed = parse_gmail_error(error)
        assert isinstance(parsed, AuthenticationError)

    def test_parses_generic_error(self) -> None:
        """Test parsing unknown errors as GmailAPIError."""
        error = Exception("Unknown error")
        parsed = parse_gmail_error(error)
        assert isinstance(parsed, GmailAPIError)
