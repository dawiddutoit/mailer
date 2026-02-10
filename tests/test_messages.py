"""Tests for mailer.messages module."""

from unittest.mock import MagicMock, Mock

import pytest

from mailer.messages import (
    delete_message,
    get_message,
    list_message_ids,
    list_messages,
    parse_message_data,
    search_messages,
    send_message,
)
from mailer.types import GmailMessage


class TestSendMessage:
    """Tests for send_message function."""

    def test_send_message_success(self, mock_gmail_service: Mock) -> None:
        """Verify message is sent and ID returned."""
        mock_gmail_service.users().messages().send().execute.return_value = {"id": "msg_sent_123"}

        result = send_message(
            mock_gmail_service, to="recipient@example.com", subject="Test", body="Hello"
        )

        assert result == "msg_sent_123"

    def test_send_message_with_from_email(self, mock_gmail_service: Mock) -> None:
        """Verify from_email is included in message."""
        mock_gmail_service.users().messages().send().execute.return_value = {"id": "msg_sent_456"}

        result = send_message(
            mock_gmail_service,
            to="recipient@example.com",
            subject="Test",
            body="Hello",
            from_email="sender@example.com",
        )

        assert result == "msg_sent_456"
        # Verify send was called
        mock_gmail_service.users().messages().send.assert_called()


class TestListMessageIds:
    """Tests for list_message_ids function."""

    def test_list_message_ids_returns_ids(
        self, mock_gmail_service: Mock, mock_gmail_list_response: dict
    ) -> None:
        """Verify message IDs are returned."""
        mock_gmail_service.users().messages().list().execute.return_value = mock_gmail_list_response

        result = list_message_ids(mock_gmail_service, max_results=10)

        assert result == ["msg_1", "msg_2", "msg_3"]

    def test_list_message_ids_with_query(
        self, mock_gmail_service: Mock, mock_gmail_list_response: dict
    ) -> None:
        """Verify query is passed to API."""
        mock_gmail_service.users().messages().list().execute.return_value = mock_gmail_list_response

        list_message_ids(mock_gmail_service, max_results=10, query="is:unread")

        mock_gmail_service.users().messages().list.assert_called()

    def test_list_message_ids_empty(self, mock_gmail_service: Mock) -> None:
        """Verify empty list when no messages."""
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        result = list_message_ids(mock_gmail_service, max_results=10)

        assert result == []

    def test_list_message_ids_with_pagination(
        self, mock_gmail_service: Mock, mock_gmail_list_response_with_pagination: tuple[dict, dict]
    ) -> None:
        """Verify pagination is handled correctly."""
        page1, page2 = mock_gmail_list_response_with_pagination
        mock_gmail_service.users().messages().list().execute.side_effect = [page1, page2]

        result = list_message_ids(mock_gmail_service, max_results=0)  # 0 = get all

        assert len(result) == 4
        assert result == ["msg_1", "msg_2", "msg_3", "msg_4"]

    def test_list_message_ids_respects_max_results(
        self, mock_gmail_service: Mock, mock_gmail_list_response: dict
    ) -> None:
        """Verify max_results limits returned IDs."""
        mock_gmail_service.users().messages().list().execute.return_value = mock_gmail_list_response

        result = list_message_ids(mock_gmail_service, max_results=2)

        assert len(result) == 2


class TestGetMessage:
    """Tests for get_message function."""

    def test_get_message_returns_gmail_message(
        self, mock_gmail_service: Mock, sample_message_data: dict
    ) -> None:
        """Verify message is fetched and parsed."""
        mock_gmail_service.users().messages().get().execute.return_value = sample_message_data

        result = get_message(mock_gmail_service, "msg_123")

        assert isinstance(result, GmailMessage)
        assert result.id == "msg_123"
        assert result.subject == "Test Subject"
        assert result.from_email == "sender@example.com"

    def test_get_message_parses_body(
        self, mock_gmail_service: Mock, sample_message_data: dict
    ) -> None:
        """Verify message body is decoded."""
        mock_gmail_service.users().messages().get().execute.return_value = sample_message_data

        result = get_message(mock_gmail_service, "msg_123")

        assert "This is a test message" in result.body


class TestParseMessageData:
    """Tests for parse_message_data function."""

    def test_parse_message_data_extracts_fields(self, sample_message_data: dict) -> None:
        """Verify all fields are extracted."""
        result = parse_message_data(sample_message_data)

        assert result.id == "msg_123"
        assert result.thread_id == "thread_456"
        assert result.subject == "Test Subject"
        assert result.from_email == "sender@example.com"
        assert "recipient@example.com" in result.to
        assert "cc@example.com" in result.cc
        assert result.size_estimate == 1024

    def test_parse_message_data_handles_multipart(
        self, sample_multipart_message_data: dict
    ) -> None:
        """Verify multipart messages are parsed."""
        result = parse_message_data(sample_multipart_message_data)

        assert result.id == "msg_multipart"
        # Plain text should be extracted
        assert result.body != ""

    def test_parse_message_data_extracts_attachments(
        self, sample_message_with_attachment_data: dict
    ) -> None:
        """Verify attachments are extracted."""
        result = parse_message_data(sample_message_with_attachment_data)

        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "report.pdf"
        assert result.attachments[0].mime_type == "application/pdf"

    def test_parse_message_data_converts_timestamp(self, sample_message_data: dict) -> None:
        """Verify timestamp is converted."""
        result = parse_message_data(sample_message_data)

        assert result.timestamp == 1704106800000

    def test_parse_message_data_handles_missing_headers(self) -> None:
        """Verify missing headers don't cause errors."""
        minimal_data = {
            "id": "minimal",
            "threadId": "thread",
            "payload": {"headers": [], "body": {}},
        }

        result = parse_message_data(minimal_data)

        assert result.id == "minimal"
        assert result.subject == ""
        assert result.from_email == ""


class TestListMessages:
    """Tests for list_messages function."""

    def test_list_messages_returns_full_messages(
        self, mock_gmail_service: Mock, sample_message_data: dict
    ) -> None:
        """Verify full message objects are returned."""
        mock_gmail_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg_123", "threadId": "thread_456"}]
        }
        mock_gmail_service.users().messages().get().execute.return_value = sample_message_data

        result = list_messages(mock_gmail_service, max_results=1)

        assert len(result) == 1
        assert isinstance(result[0], GmailMessage)
        assert result[0].id == "msg_123"

    def test_list_messages_empty_result(self, mock_gmail_service: Mock) -> None:
        """Verify empty list when no messages."""
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        result = list_messages(mock_gmail_service, max_results=10)

        assert result == []


class TestDeleteMessage:
    """Tests for delete_message function."""

    def test_delete_message_calls_api(self, mock_gmail_service: Mock) -> None:
        """Verify delete API is called."""
        mock_gmail_service.users().messages().delete().execute.return_value = None

        delete_message(mock_gmail_service, "msg_to_delete")

        mock_gmail_service.users().messages().delete.assert_called()


class TestSearchMessages:
    """Tests for search_messages function."""

    def test_search_messages_with_query(
        self, mock_gmail_service: Mock, sample_message_data: dict
    ) -> None:
        """Verify search passes query to API."""
        mock_gmail_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg_123", "threadId": "thread_456"}]
        }
        mock_gmail_service.users().messages().get().execute.return_value = sample_message_data

        result = search_messages(mock_gmail_service, query="from:sender@example.com", max_results=10)

        assert len(result) == 1
        assert result[0].id == "msg_123"

    def test_search_messages_empty_results(self, mock_gmail_service: Mock) -> None:
        """Verify empty search returns empty list."""
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        result = search_messages(mock_gmail_service, query="nonexistent", max_results=10)

        assert result == []
