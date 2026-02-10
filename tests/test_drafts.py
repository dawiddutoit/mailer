"""Tests for mailer.drafts module."""

import base64
from unittest.mock import MagicMock

import pytest

from mailer.drafts import (
    create_draft,
    delete_draft,
    get_draft,
    list_draft_ids,
    list_drafts,
    send_draft,
    update_draft,
    _create_mime_message,
    _encode_message,
    _parse_draft,
)
from mailer.types import GmailDraft, GmailMessage


@pytest.fixture
def sample_draft_data() -> dict:
    """Sample Gmail API draft data."""
    return {
        "id": "draft_123",
        "message": {
            "id": "msg_456",
            "threadId": "thread_789",
            "labelIds": ["DRAFT"],
            "snippet": "Draft message content...",
            "sizeEstimate": 500,
            "internalDate": "1704106800000",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": "me@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Draft Subject"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 10:00:00 +0000"},
                ],
                "body": {"data": "RHJhZnQgYm9keSBjb250ZW50", "size": 18},
            },
        },
    }


@pytest.fixture
def sample_draft_list_response() -> dict:
    """Sample Gmail API drafts list response."""
    return {
        "drafts": [
            {"id": "draft_1", "message": {"id": "msg_1"}},
            {"id": "draft_2", "message": {"id": "msg_2"}},
        ],
        "resultSizeEstimate": 2,
    }


class TestListDraftIds:
    """Tests for list_draft_ids function."""

    def test_list_draft_ids_basic(self, mock_gmail_service: MagicMock) -> None:
        """Verify list_draft_ids returns draft IDs."""
        mock_gmail_service.users().drafts().list().execute.return_value = {
            "drafts": [
                {"id": "draft_1", "message": {"id": "msg_1"}},
                {"id": "draft_2", "message": {"id": "msg_2"}},
            ]
        }

        result = list_draft_ids(mock_gmail_service, max_results=10)

        assert len(result) == 2
        assert result == ["draft_1", "draft_2"]

    def test_list_draft_ids_empty(self, mock_gmail_service: MagicMock) -> None:
        """Verify list_draft_ids handles empty response."""
        mock_gmail_service.users().drafts().list().execute.return_value = {"drafts": []}

        result = list_draft_ids(mock_gmail_service)

        assert result == []

    def test_list_draft_ids_with_pagination(self, mock_gmail_service: MagicMock) -> None:
        """Verify list_draft_ids handles pagination."""
        mock_gmail_service.users().drafts().list().execute.side_effect = [
            {
                "drafts": [{"id": "draft_1"}],
                "nextPageToken": "token_2",
            },
            {
                "drafts": [{"id": "draft_2"}],
            },
        ]

        result = list_draft_ids(mock_gmail_service, max_results=0)  # 0 = all

        assert len(result) == 2


class TestGetDraft:
    """Tests for get_draft function."""

    def test_get_draft_by_id(
        self, mock_gmail_service: MagicMock, sample_draft_data: dict
    ) -> None:
        """Verify get_draft returns draft details."""
        mock_gmail_service.users().drafts().get().execute.return_value = sample_draft_data

        result = get_draft(mock_gmail_service, "draft_123")

        assert isinstance(result, GmailDraft)
        assert result.id == "draft_123"
        assert result.message.id == "msg_456"
        assert result.message.subject == "Draft Subject"


class TestCreateDraft:
    """Tests for create_draft function."""

    def test_create_draft_basic(
        self, mock_gmail_service: MagicMock, sample_draft_data: dict
    ) -> None:
        """Verify create_draft creates a new draft."""
        mock_gmail_service.users().drafts().create().execute.return_value = {
            "id": "draft_new"
        }
        mock_gmail_service.users().drafts().get().execute.return_value = sample_draft_data

        result = create_draft(
            mock_gmail_service,
            to="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
        )

        assert isinstance(result, GmailDraft)
        mock_gmail_service.users().drafts().create.assert_called()

    def test_create_draft_with_cc_bcc(
        self, mock_gmail_service: MagicMock, sample_draft_data: dict
    ) -> None:
        """Verify create_draft includes CC and BCC."""
        mock_gmail_service.users().drafts().create().execute.return_value = {
            "id": "draft_new"
        }
        mock_gmail_service.users().drafts().get().execute.return_value = sample_draft_data

        result = create_draft(
            mock_gmail_service,
            to="to@example.com",
            subject="Subject",
            body="Body",
            cc="cc@example.com",
            bcc="bcc@example.com",
        )

        assert isinstance(result, GmailDraft)


class TestUpdateDraft:
    """Tests for update_draft function."""

    def test_update_draft(
        self, mock_gmail_service: MagicMock, sample_draft_data: dict
    ) -> None:
        """Verify update_draft replaces draft content."""
        mock_gmail_service.users().drafts().update().execute.return_value = {
            "id": "draft_123"
        }
        mock_gmail_service.users().drafts().get().execute.return_value = sample_draft_data

        result = update_draft(
            mock_gmail_service,
            draft_id="draft_123",
            to="new_recipient@example.com",
            subject="Updated Subject",
            body="Updated body content",
        )

        assert isinstance(result, GmailDraft)
        mock_gmail_service.users().drafts().update.assert_called()


class TestSendDraft:
    """Tests for send_draft function."""

    def test_send_draft(self, mock_gmail_service: MagicMock) -> None:
        """Verify send_draft sends a draft and returns message ID."""
        mock_gmail_service.users().drafts().send().execute.return_value = {
            "id": "sent_msg_123"
        }

        result = send_draft(mock_gmail_service, "draft_123")

        assert result == "sent_msg_123"
        mock_gmail_service.users().drafts().send.assert_called_with(
            userId="me", body={"id": "draft_123"}
        )


class TestDeleteDraft:
    """Tests for delete_draft function."""

    def test_delete_draft(self, mock_gmail_service: MagicMock) -> None:
        """Verify delete_draft calls the API correctly."""
        delete_draft(mock_gmail_service, "draft_123")

        mock_gmail_service.users().drafts().delete.assert_called_with(
            userId="me", id="draft_123"
        )


class TestCreateMimeMessage:
    """Tests for _create_mime_message function."""

    def test_basic_message(self) -> None:
        """Verify _create_mime_message creates valid MIME."""
        result = _create_mime_message(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test body",
        )

        assert "To: recipient@example.com" in result
        assert "Subject: Test Subject" in result
        assert "Test body" in result

    def test_message_with_cc_bcc(self) -> None:
        """Verify _create_mime_message includes CC and BCC."""
        result = _create_mime_message(
            to="to@example.com",
            subject="Subject",
            body="Body",
            cc="cc@example.com",
            bcc="bcc@example.com",
        )

        assert "Cc: cc@example.com" in result
        assert "Bcc: bcc@example.com" in result


class TestEncodeMessage:
    """Tests for _encode_message function."""

    def test_encode_message(self) -> None:
        """Verify _encode_message produces valid base64url."""
        message = "Test message content"
        result = _encode_message(message)

        # Verify it can be decoded back
        decoded = base64.urlsafe_b64decode(result).decode()
        assert decoded == message


class TestParseDraft:
    """Tests for _parse_draft function."""

    def test_parse_full_draft(self, sample_draft_data: dict) -> None:
        """Verify _parse_draft handles complete draft data."""
        result = _parse_draft(sample_draft_data)

        assert isinstance(result, GmailDraft)
        assert result.id == "draft_123"
        assert isinstance(result.message, GmailMessage)
        assert result.message.id == "msg_456"
        assert result.message.subject == "Draft Subject"

    def test_parse_minimal_draft(self) -> None:
        """Verify _parse_draft handles minimal data."""
        minimal_data = {
            "id": "draft_minimal",
            "message": {
                "id": "msg_min",
                "threadId": "thread_min",
            },
        }

        result = _parse_draft(minimal_data)

        assert result.id == "draft_minimal"
        assert result.message.id == "msg_min"
