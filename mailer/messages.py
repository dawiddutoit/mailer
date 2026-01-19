"""Message operations for Gmail."""

from googleapiclient.discovery import Resource

from mailer.types import GmailMessage, MessageID


def send_message(
    service: Resource,
    to: str,
    subject: str,
    body: str,
    from_email: str | None = None,
) -> MessageID:
    """Send an email message.

    Args:
        service: Authenticated Gmail API service
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        from_email: Sender email (defaults to authenticated user)

    Returns:
        ID of the sent message
    """
    # TODO: Implement message sending
    raise NotImplementedError("Message sending not yet implemented")


def list_messages(
    service: Resource, max_results: int = 10, query: str | None = None
) -> list[GmailMessage]:
    """List messages from the user's mailbox.

    Args:
        service: Authenticated Gmail API service
        max_results: Maximum number of messages to return
        query: Gmail query string for filtering

    Returns:
        List of message objects
    """
    # TODO: Implement message listing
    raise NotImplementedError("Message listing not yet implemented")


def get_message(service: Resource, message_id: str) -> GmailMessage:
    """Get a specific message by ID.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message to retrieve

    Returns:
        Message object with details
    """
    # TODO: Implement get message
    raise NotImplementedError("Get message not yet implemented")


def delete_message(service: Resource, message_id: str) -> None:
    """Delete a message.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message to delete
    """
    # TODO: Implement message deletion
    raise NotImplementedError("Message deletion not yet implemented")


def search_messages(
    service: Resource, query: str, max_results: int = 100
) -> list[GmailMessage]:
    """Search messages using Gmail query syntax.

    Args:
        service: Authenticated Gmail API service
        query: Gmail search query
        max_results: Maximum number of results

    Returns:
        List of matching messages
    """
    # TODO: Implement message search
    raise NotImplementedError("Message search not yet implemented")
