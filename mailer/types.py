"""Type definitions and Pydantic models for Gmail operations."""

from typing import NewType
from pydantic import BaseModel, Field


# Type aliases for Gmail IDs
MessageID = NewType("MessageID", str)
ThreadID = NewType("ThreadID", str)
LabelID = NewType("LabelID", str)
DraftID = NewType("DraftID", str)


class GmailMessage(BaseModel):
    """Gmail message model."""

    id: str
    thread_id: str
    label_ids: list[str] = Field(default_factory=list)
    snippet: str = ""
    from_email: str = ""
    to: list[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    timestamp: int = 0


class GmailThread(BaseModel):
    """Gmail thread model."""

    id: str
    snippet: str = ""
    messages: list[GmailMessage] = Field(default_factory=list)


class GmailLabel(BaseModel):
    """Gmail label model."""

    id: str
    name: str
    type: str = "user"
    message_list_visibility: str = "show"
    label_list_visibility: str = "labelShow"


class GmailDraft(BaseModel):
    """Gmail draft model."""

    id: str
    message: GmailMessage


class GmailAttachment(BaseModel):
    """Gmail attachment model."""

    filename: str
    mime_type: str
    size: int
    attachment_id: str | None = None
    data: bytes | None = None
