"""Tests for type definitions and Pydantic models."""

import pytest
from mailer.types import GmailMessage, GmailLabel, GmailThread, GmailDraft


class TestGmailMessage:
    """Tests for GmailMessage model."""

    def test_creates_message_with_required_fields(self) -> None:
        """Test creating message with minimal fields."""
        message = GmailMessage(id="msg_123", thread_id="thread_456")

        assert message.id == "msg_123"
        assert message.thread_id == "thread_456"
        assert message.label_ids == []
        assert message.snippet == ""

    def test_creates_message_with_all_fields(self) -> None:
        """Test creating message with all fields."""
        message = GmailMessage(
            id="msg_123",
            thread_id="thread_456",
            label_ids=["INBOX", "UNREAD"],
            snippet="Test snippet",
            from_email="sender@example.com",
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test body",
            timestamp=1234567890,
        )

        assert message.label_ids == ["INBOX", "UNREAD"]
        assert message.from_email == "sender@example.com"
        assert message.to == ["recipient@example.com"]


class TestGmailLabel:
    """Tests for GmailLabel model."""

    def test_creates_label_with_defaults(self) -> None:
        """Test creating label with default values."""
        label = GmailLabel(id="label_123", name="Test Label")

        assert label.id == "label_123"
        assert label.name == "Test Label"
        assert label.type == "user"

    def test_creates_label_with_custom_values(self) -> None:
        """Test creating label with custom visibility."""
        label = GmailLabel(
            id="label_123",
            name="Test Label",
            type="system",
            message_list_visibility="hide",
        )

        assert label.type == "system"
        assert label.message_list_visibility == "hide"


class TestGmailThread:
    """Tests for GmailThread model."""

    def test_creates_thread_with_messages(self) -> None:
        """Test creating thread with messages."""
        msg1 = GmailMessage(id="msg_1", thread_id="thread_123")
        msg2 = GmailMessage(id="msg_2", thread_id="thread_123")

        thread = GmailThread(
            id="thread_123", snippet="Conversation snippet", messages=[msg1, msg2]
        )

        assert thread.id == "thread_123"
        assert len(thread.messages) == 2
        assert thread.messages[0].id == "msg_1"
