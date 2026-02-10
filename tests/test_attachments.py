"""Tests for mailer.attachments module."""

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mailer.attachments import (
    download_all_attachments,
    download_attachment_to_file,
    get_attachment_content,
    get_attachment_size,
)
from mailer.types import GmailAttachment


@pytest.fixture
def sample_attachment_response() -> dict:
    """Sample Gmail API attachment response."""
    content = b"Sample file content for testing"
    encoded = base64.urlsafe_b64encode(content).decode()
    return {
        "data": encoded,
        "size": len(content),
    }


@pytest.fixture
def sample_attachments() -> list[GmailAttachment]:
    """Sample list of GmailAttachment objects."""
    return [
        GmailAttachment(
            attachment_id="att_1",
            message_id="msg_123",
            filename="document.pdf",
            mime_type="application/pdf",
            size=1000,
        ),
        GmailAttachment(
            attachment_id="att_2",
            message_id="msg_123",
            filename="image.png",
            mime_type="image/png",
            size=2000,
        ),
    ]


class TestDownloadAttachmentToFile:
    """Tests for download_attachment_to_file function."""

    def test_download_to_file(
        self,
        mock_gmail_service: MagicMock,
        sample_attachment_response: dict,
        tmp_path: Path,
    ) -> None:
        """Verify download_attachment_to_file saves content to file."""
        mock_gmail_service.users().messages().attachments().get().execute.return_value = (
            sample_attachment_response
        )

        output_path = tmp_path / "downloaded.pdf"
        result = download_attachment_to_file(
            mock_gmail_service, "msg_123", "att_456", output_path
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == b"Sample file content for testing"

    def test_download_creates_parent_dirs(
        self,
        mock_gmail_service: MagicMock,
        sample_attachment_response: dict,
        tmp_path: Path,
    ) -> None:
        """Verify download_attachment_to_file creates parent directories."""
        mock_gmail_service.users().messages().attachments().get().execute.return_value = (
            sample_attachment_response
        )

        output_path = tmp_path / "nested" / "dir" / "file.pdf"
        result = download_attachment_to_file(
            mock_gmail_service, "msg_123", "att_456", output_path
        )

        assert result.exists()
        assert result.parent.exists()


class TestDownloadAllAttachments:
    """Tests for download_all_attachments function."""

    def test_download_all(
        self,
        mock_gmail_service: MagicMock,
        sample_attachments: list[GmailAttachment],
        tmp_path: Path,
    ) -> None:
        """Verify download_all_attachments saves all attachments."""
        content = b"File content"
        encoded = base64.urlsafe_b64encode(content).decode()
        mock_gmail_service.users().messages().attachments().get().execute.return_value = {
            "data": encoded,
            "size": len(content),
        }

        output_dir = tmp_path / "attachments"
        result = download_all_attachments(
            mock_gmail_service, "msg_123", sample_attachments, output_dir
        )

        assert len(result) == 2
        assert (output_dir / "document.pdf").exists()
        assert (output_dir / "image.png").exists()

    def test_handles_duplicate_filenames(
        self,
        mock_gmail_service: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Verify download_all_attachments handles duplicate filenames."""
        content = b"Content"
        encoded = base64.urlsafe_b64encode(content).decode()
        mock_gmail_service.users().messages().attachments().get().execute.return_value = {
            "data": encoded,
            "size": len(content),
        }

        # Create attachments with same filename
        attachments = [
            GmailAttachment(
                attachment_id="att_1",
                message_id="msg_123",
                filename="report.pdf",
                mime_type="application/pdf",
                size=100,
            ),
            GmailAttachment(
                attachment_id="att_2",
                message_id="msg_123",
                filename="report.pdf",  # Same filename
                mime_type="application/pdf",
                size=100,
            ),
        ]

        output_dir = tmp_path / "attachments"
        result = download_all_attachments(
            mock_gmail_service, "msg_123", attachments, output_dir
        )

        assert len(result) == 2
        # Second file should have _1 suffix
        filenames = [p.name for p in result]
        assert "report.pdf" in filenames
        assert "report_1.pdf" in filenames

    def test_empty_attachments(
        self,
        mock_gmail_service: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Verify download_all_attachments handles empty list."""
        output_dir = tmp_path / "attachments"
        result = download_all_attachments(mock_gmail_service, "msg_123", [], output_dir)

        assert result == []


class TestGetAttachmentContent:
    """Tests for get_attachment_content function."""

    def test_get_content_as_bytes(
        self,
        mock_gmail_service: MagicMock,
        sample_attachment_response: dict,
    ) -> None:
        """Verify get_attachment_content returns bytes."""
        mock_gmail_service.users().messages().attachments().get().execute.return_value = (
            sample_attachment_response
        )

        result = get_attachment_content(mock_gmail_service, "msg_123", "att_456")

        assert isinstance(result, bytes)
        assert result == b"Sample file content for testing"

    def test_api_call_parameters(
        self,
        mock_gmail_service: MagicMock,
        sample_attachment_response: dict,
    ) -> None:
        """Verify get_attachment_content uses correct API parameters."""
        mock_gmail_service.users().messages().attachments().get().execute.return_value = (
            sample_attachment_response
        )

        get_attachment_content(mock_gmail_service, "msg_123", "att_456")

        mock_gmail_service.users().messages().attachments().get.assert_called_with(
            userId="me", messageId="msg_123", id="att_456"
        )


class TestGetAttachmentSize:
    """Tests for get_attachment_size function."""

    def test_get_size(
        self,
        mock_gmail_service: MagicMock,
    ) -> None:
        """Verify get_attachment_size returns size in bytes."""
        mock_gmail_service.users().messages().attachments().get().execute.return_value = {
            "data": "",
            "size": 12345,
        }

        result = get_attachment_size(mock_gmail_service, "msg_123", "att_456")

        assert result == 12345

    def test_size_missing_defaults_to_zero(
        self,
        mock_gmail_service: MagicMock,
    ) -> None:
        """Verify get_attachment_size returns 0 if size is missing."""
        mock_gmail_service.users().messages().attachments().get().execute.return_value = {
            "data": ""
        }

        result = get_attachment_size(mock_gmail_service, "msg_123", "att_456")

        assert result == 0
