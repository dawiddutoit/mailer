"""Tests for mailer.threads module."""

from unittest.mock import Mock

from mailer.threads import (
    get_thread,
    get_thread_messages,
    list_thread_ids,
    list_threads,
    search_threads,
)
from mailer.types import GmailMessage, GmailThread


class TestListThreadIds:
    """Tests for list_thread_ids function."""

    def test_list_thread_ids_returns_ids(self, mock_gmail_service: Mock) -> None:
        """Verify thread IDs are returned."""
        mock_gmail_service.users().threads().list().execute.return_value = {
            "threads": [{"id": "thread_1"}, {"id": "thread_2"}]
        }

        result = list_thread_ids(mock_gmail_service, max_results=10)

        assert result == ["thread_1", "thread_2"]

    def test_list_thread_ids_with_query(self, mock_gmail_service: Mock) -> None:
        """Verify query is passed to API."""
        mock_gmail_service.users().threads().list().execute.return_value = {"threads": []}

        list_thread_ids(mock_gmail_service, max_results=10, query="from:test@example.com")

        mock_gmail_service.users().threads().list.assert_called()

    def test_list_thread_ids_empty(self, mock_gmail_service: Mock) -> None:
        """Verify empty list when no threads."""
        mock_gmail_service.users().threads().list().execute.return_value = {"threads": []}

        result = list_thread_ids(mock_gmail_service, max_results=10)

        assert result == []

    def test_list_thread_ids_pagination(self, mock_gmail_service: Mock) -> None:
        """Verify pagination is handled."""
        page1 = {"threads": [{"id": "thread_1"}], "nextPageToken": "token"}
        page2 = {"threads": [{"id": "thread_2"}]}
        mock_gmail_service.users().threads().list().execute.side_effect = [page1, page2]

        result = list_thread_ids(mock_gmail_service, max_results=0)  # 0 = all

        assert len(result) == 2


class TestGetThread:
    """Tests for get_thread function."""

    def test_get_thread_returns_thread(
        self, mock_gmail_service: Mock, sample_thread_data: dict
    ) -> None:
        """Verify thread is fetched and parsed."""
        mock_gmail_service.users().threads().get().execute.return_value = sample_thread_data

        result = get_thread(mock_gmail_service, "thread_456")

        assert isinstance(result, GmailThread)
        assert result.id == "thread_456"
        assert len(result.messages) == 2

    def test_get_thread_parses_messages(
        self, mock_gmail_service: Mock, sample_thread_data: dict
    ) -> None:
        """Verify thread messages are parsed."""
        mock_gmail_service.users().threads().get().execute.return_value = sample_thread_data

        result = get_thread(mock_gmail_service, "thread_456")

        assert all(isinstance(msg, GmailMessage) for msg in result.messages)
        assert result.messages[0].subject == "Discussion Topic"
        assert result.messages[1].subject == "Re: Discussion Topic"


class TestGetThreadMessages:
    """Tests for get_thread_messages function."""

    def test_get_thread_messages_returns_list(
        self, mock_gmail_service: Mock, sample_thread_data: dict
    ) -> None:
        """Verify list of messages is returned."""
        mock_gmail_service.users().threads().get().execute.return_value = sample_thread_data

        result = get_thread_messages(mock_gmail_service, "thread_456")

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(msg, GmailMessage) for msg in result)


class TestListThreads:
    """Tests for list_threads function."""

    def test_list_threads_returns_threads(
        self, mock_gmail_service: Mock, sample_thread_data: dict
    ) -> None:
        """Verify threads are listed with full content."""
        mock_gmail_service.users().threads().list().execute.return_value = {
            "threads": [{"id": "thread_456"}]
        }
        mock_gmail_service.users().threads().get().execute.return_value = sample_thread_data

        result = list_threads(mock_gmail_service, max_results=1)

        assert len(result) == 1
        assert isinstance(result[0], GmailThread)


class TestSearchThreads:
    """Tests for search_threads function."""

    def test_search_threads_with_query(
        self, mock_gmail_service: Mock, sample_thread_data: dict
    ) -> None:
        """Verify search passes query."""
        mock_gmail_service.users().threads().list().execute.return_value = {
            "threads": [{"id": "thread_456"}]
        }
        mock_gmail_service.users().threads().get().execute.return_value = sample_thread_data

        result = search_threads(mock_gmail_service, query="subject:Discussion", max_results=10)

        assert len(result) == 1
