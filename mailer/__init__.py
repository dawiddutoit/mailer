"""Mailer - A functional Python library for AI agents to interact with Gmail.

This library follows functional programming principles with:
- Pure functions wherever possible
- Immutable data structures (Pydantic models)
- Explicit dependencies (no global state)
- Single responsibility per function
- Flat module structure

Example usage:
    from mailer import create_service, send_message

    service = create_service("credentials.json", "token.json")
    message_id = send_message(service, "user@example.com", "Subject", "Body")
"""

# Auth functions
from mailer.auth import (
    create_credentials,
    create_service,
    create_service_from_env,
    validate_service,
)

# Message functions
from mailer.messages import (
    delete_message,
    get_message,
    list_messages,
    search_messages,
    send_message,
)

# Label functions
from mailer.labels import (
    apply_label,
    create_label,
    list_labels,
    remove_label,
)

# Thread functions
from mailer.threads import (
    get_thread,
    list_threads,
)

# Draft functions
from mailer.drafts import (
    create_draft,
    delete_draft,
    send_draft,
    update_draft,
)

# Attachment functions
from mailer.attachments import (
    download_attachment,
    get_attachment_info,
    upload_attachment,
)

# Type definitions
from mailer.types import (
    DraftID,
    GmailAttachment,
    GmailDraft,
    GmailLabel,
    GmailMessage,
    GmailThread,
    LabelID,
    MessageID,
    ThreadID,
)

# Error types
from mailer.errors import (
    AuthenticationError,
    DraftNotFoundError,
    GmailAPIError,
    InvalidMessageFormatError,
    LabelNotFoundError,
    MailerError,
    MessageNotFoundError,
    QuotaExceededError,
    ThreadNotFoundError,
    parse_gmail_error,
)

__version__ = "0.1.0"

# Public API
__all__ = [
    # Version
    "__version__",
    # Auth
    "create_credentials",
    "create_service",
    "create_service_from_env",
    "validate_service",
    # Messages
    "send_message",
    "list_messages",
    "get_message",
    "delete_message",
    "search_messages",
    # Labels
    "create_label",
    "list_labels",
    "apply_label",
    "remove_label",
    # Threads
    "list_threads",
    "get_thread",
    # Drafts
    "create_draft",
    "update_draft",
    "send_draft",
    "delete_draft",
    # Attachments
    "upload_attachment",
    "download_attachment",
    "get_attachment_info",
    # Types
    "MessageID",
    "ThreadID",
    "LabelID",
    "DraftID",
    "GmailMessage",
    "GmailThread",
    "GmailLabel",
    "GmailDraft",
    "GmailAttachment",
    # Errors
    "MailerError",
    "AuthenticationError",
    "GmailAPIError",
    "MessageNotFoundError",
    "LabelNotFoundError",
    "ThreadNotFoundError",
    "DraftNotFoundError",
    "QuotaExceededError",
    "InvalidMessageFormatError",
    "parse_gmail_error",
]
