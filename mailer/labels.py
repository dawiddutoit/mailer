"""Label operations for Gmail."""

from googleapiclient.discovery import Resource

from mailer.types import GmailLabel, LabelID


def create_label(service: Resource, name: str) -> GmailLabel:
    """Create a new label.

    Args:
        service: Authenticated Gmail API service
        name: Name of the label to create

    Returns:
        Created label object
    """
    # TODO: Implement label creation
    raise NotImplementedError("Label creation not yet implemented")


def list_labels(service: Resource) -> list[GmailLabel]:
    """List all labels in the user's mailbox.

    Args:
        service: Authenticated Gmail API service

    Returns:
        List of label objects
    """
    # TODO: Implement label listing
    raise NotImplementedError("Label listing not yet implemented")


def apply_label(service: Resource, message_id: str, label_id: str) -> None:
    """Apply a label to a message.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message
        label_id: ID of the label to apply
    """
    # TODO: Implement apply label
    raise NotImplementedError("Apply label not yet implemented")


def remove_label(service: Resource, message_id: str, label_id: str) -> None:
    """Remove a label from a message.

    Args:
        service: Authenticated Gmail API service
        message_id: ID of the message
        label_id: ID of the label to remove
    """
    # TODO: Implement remove label
    raise NotImplementedError("Remove label not yet implemented")
