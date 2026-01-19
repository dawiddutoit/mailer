"""Draft operations for Gmail."""

from googleapiclient.discovery import Resource

from mailer.types import GmailDraft, DraftID


def create_draft(
    service: Resource, to: str, subject: str, body: str
) -> GmailDraft:
    """Create a new draft message.

    Args:
        service: Authenticated Gmail API service
        to: Recipient email address
        subject: Email subject
        body: Email body

    Returns:
        Created draft object
    """
    # TODO: Implement draft creation
    raise NotImplementedError("Draft creation not yet implemented")


def update_draft(
    service: Resource, draft_id: str, to: str, subject: str, body: str
) -> GmailDraft:
    """Update an existing draft.

    Args:
        service: Authenticated Gmail API service
        draft_id: ID of the draft to update
        to: Recipient email address
        subject: Email subject
        body: Email body

    Returns:
        Updated draft object
    """
    # TODO: Implement draft update
    raise NotImplementedError("Draft update not yet implemented")


def send_draft(service: Resource, draft_id: str) -> str:
    """Send a draft message.

    Args:
        service: Authenticated Gmail API service
        draft_id: ID of the draft to send

    Returns:
        ID of the sent message
    """
    # TODO: Implement draft sending
    raise NotImplementedError("Draft sending not yet implemented")


def delete_draft(service: Resource, draft_id: str) -> None:
    """Delete a draft.

    Args:
        service: Authenticated Gmail API service
        draft_id: ID of the draft to delete
    """
    # TODO: Implement draft deletion
    raise NotImplementedError("Draft deletion not yet implemented")
