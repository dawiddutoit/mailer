"""Attachment operations for Gmail."""

from pathlib import Path
from googleapiclient.discovery import Resource

from mailer.types import GmailAttachment


def upload_attachment(
    service: Resource, message_id: str, file_path: str
) -> GmailAttachment:
    """Upload a file as an attachment to a message.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message to attach to
        file_path: Path to the file to upload

    Returns:
        Attachment object
    """
    # TODO: Implement attachment upload
    raise NotImplementedError("Attachment upload not yet implemented")


def download_attachment(
    service: Resource, message_id: str, attachment_id: str, output_path: str
) -> Path:
    """Download an attachment from a message.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message
        attachment_id: ID of the attachment
        output_path: Path where to save the downloaded file

    Returns:
        Path to the downloaded file
    """
    # TODO: Implement attachment download
    raise NotImplementedError("Attachment download not yet implemented")


def get_attachment_info(
    service: Resource, message_id: str, attachment_id: str
) -> GmailAttachment:
    """Get information about an attachment.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message
        attachment_id: ID of the attachment

    Returns:
        Attachment metadata
    """
    # TODO: Implement get attachment info
    raise NotImplementedError("Get attachment info not yet implemented")
