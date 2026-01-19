"""Shared pytest fixtures for mailer tests."""

import pytest
from unittest.mock import Mock, MagicMock
from googleapiclient.discovery import Resource


@pytest.fixture
def mock_gmail_service() -> Mock:
    """Create a mock Gmail API service object."""
    service = MagicMock(spec=Resource)
    return service


@pytest.fixture
def mock_credentials() -> Mock:
    """Create mock Gmail credentials."""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    creds.refresh_token = "mock_refresh_token"
    return creds


@pytest.fixture
def sample_message_data() -> dict:
    """Sample Gmail message data for testing."""
    return {
        "id": "msg_123",
        "threadId": "thread_456",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "This is a test message...",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
            ],
            "body": {"data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ=="},
        },
        "internalDate": "1234567890000",
    }


@pytest.fixture
def sample_label_data() -> dict:
    """Sample Gmail label data for testing."""
    return {
        "id": "label_123",
        "name": "TestLabel",
        "type": "user",
        "messageListVisibility": "show",
        "labelListVisibility": "labelShow",
    }


@pytest.fixture
def sample_thread_data() -> dict:
    """Sample Gmail thread data for testing."""
    return {
        "id": "thread_456",
        "snippet": "This is a conversation...",
        "messages": [
            {
                "id": "msg_1",
                "threadId": "thread_456",
                "labelIds": ["INBOX"],
                "snippet": "First message",
            },
            {
                "id": "msg_2",
                "threadId": "thread_456",
                "labelIds": ["INBOX"],
                "snippet": "Second message",
            },
        ],
    }
