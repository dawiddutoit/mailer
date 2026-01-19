"""Error types for Gmail operations."""


class MailerError(Exception):
    """Base exception for all Mailer errors."""

    pass


class AuthenticationError(MailerError):
    """Raised when authentication fails."""

    pass


class GmailAPIError(MailerError):
    """Raised when Gmail API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MessageNotFoundError(MailerError):
    """Raised when a message is not found."""

    pass


class LabelNotFoundError(MailerError):
    """Raised when a label is not found."""

    pass


class ThreadNotFoundError(MailerError):
    """Raised when a thread is not found."""

    pass


class DraftNotFoundError(MailerError):
    """Raised when a draft is not found."""

    pass


class QuotaExceededError(MailerError):
    """Raised when Gmail API quota is exceeded."""

    pass


class InvalidMessageFormatError(MailerError):
    """Raised when message format is invalid."""

    pass


def parse_gmail_error(error: Exception) -> MailerError:
    """Parse Gmail API error and return appropriate Mailer exception."""
    error_str = str(error)

    if "not found" in error_str.lower():
        return MessageNotFoundError(error_str)
    elif "quota" in error_str.lower() or "rate limit" in error_str.lower():
        return QuotaExceededError(error_str)
    elif "auth" in error_str.lower() or "credential" in error_str.lower():
        return AuthenticationError(error_str)
    else:
        return GmailAPIError(error_str)
