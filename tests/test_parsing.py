"""Tests for email parsing module."""

import pytest

from mailer.parsing import extract_latest_reply, parse_gmail_payload
from mailer.types import ParsedEmail


class TestExtractLatestReply:
    """Tests for extract_latest_reply function."""

    def test_extracts_reply_from_simple_email(self) -> None:
        """Test extracting reply when there's no quoted text."""
        body = "This is a simple email with no quoted content."
        result = extract_latest_reply(body)
        assert result == body

    def test_extracts_reply_stripping_quoted_text(self) -> None:
        """Test that quoted text is stripped from the reply."""
        body = """Yes that is fine, I will email you in the morning.

On Fri, Nov 16, 2012 at 1:48 PM, Test User <test@example.com> wrote:

> Our support team just commented on your open Ticket:
> "Hi, can we chat in the morning about your question?"
"""
        result = extract_latest_reply(body)
        # Should only contain the new reply, not the quoted text
        assert "Yes that is fine" in result
        assert "Our support team" not in result

    def test_extracts_reply_with_outlook_format(self) -> None:
        """Test extraction with Outlook-style quoting."""
        body = """Thanks for the update.

From: Test User <test@example.com>
Sent: Monday, January 15, 2024 10:00 AM
To: Me <me@example.com>
Subject: RE: Project Update

This is the original message that should be stripped.
"""
        result = extract_latest_reply(body)
        assert "Thanks for the update" in result
        # The quoted content should be removed
        assert "This is the original message" not in result

    def test_handles_empty_body(self) -> None:
        """Test that empty body returns empty string."""
        result = extract_latest_reply("")
        assert result == ""

    def test_handles_none_gracefully(self) -> None:
        """Test that None-ish input returns empty string."""
        result = extract_latest_reply("")
        assert result == ""

    def test_handles_crlf_line_endings(self) -> None:
        """Test that Windows-style line endings are handled."""
        body = "Thanks for the update.\r\n\r\nOn Mon, Jan 15, 2024 Test <test@example.com> wrote:\r\n\r\n> Original message"
        result = extract_latest_reply(body)
        assert "Thanks for the update" in result
        assert "Original message" not in result

    def test_handles_multiline_wrote_header(self) -> None:
        """Test Gmail's multi-line 'On X wrote:' pattern."""
        body = """Hi, sounds good.

On Mon, 19 Jan 2026, 14:00 Test User, <test@example.com>
wrote:

> Previous message content
"""
        result = extract_latest_reply(body)
        assert result.strip() == "Hi, sounds good."

    def test_handles_wrapped_email_in_angle_brackets(self) -> None:
        """Test Gmail's line wrapping inside angle brackets."""
        body = """Thanks!

On Tue, Jan 27, 2026 at 8:10\u202fAM Test User <
test@example.com> wrote:

> Previous content
"""
        result = extract_latest_reply(body)
        assert result.strip() == "Thanks!"

    def test_handles_unicode_whitespace(self) -> None:
        """Test handling of narrow non-breaking space."""
        body = "Reply here.\n\nOn Mon at 8:10\u202fAM Test <t@e.com> wrote:\n\n> Quoted"
        result = extract_latest_reply(body)
        assert "Reply here" in result
        assert "Quoted" not in result


class TestParseGmailPayload:
    """Tests for parse_gmail_payload function."""

    def test_parses_simple_payload(self) -> None:
        """Test parsing a simple Gmail payload."""
        payload = {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"},
            ],
            "body": {
                "size": 12,
                "data": "SGVsbG8gV29ybGQ=",  # "Hello World" base64 encoded
            },
        }

        result = parse_gmail_payload(payload)

        assert isinstance(result, ParsedEmail)
        assert result.subject == "Test Subject"
        assert result.from_email == "sender@example.com"
        assert "recipient@example.com" in result.to
        assert "Hello World" in result.text_plain

    def test_parses_multipart_payload(self) -> None:
        """Test parsing a multipart Gmail payload."""
        payload = {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Multipart Test"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "size": 10,
                        "data": "UGxhaW4gdGV4dA==",  # "Plain text"
                    },
                },
                {
                    "mimeType": "text/html",
                    "body": {
                        "size": 20,
                        "data": "PGh0bWw+Qm9keTwvaHRtbD4=",  # "<html>Body</html>"
                    },
                },
            ],
        }

        result = parse_gmail_payload(payload)

        assert result.subject == "Multipart Test"
        assert "Plain text" in result.text_plain
        assert "<html>Body</html>" in result.text_html

    def test_extracts_attachments(self) -> None:
        """Test that attachments are extracted from payload."""
        payload = {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "Subject", "value": "With Attachment"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"size": 5, "data": "SGVsbG8="},  # "Hello"
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "document.pdf",
                    "body": {"size": 1000, "data": "UERGZGF0YWhlcmU="},  # "PDFdatahere"
                },
            ],
        }

        result = parse_gmail_payload(payload)

        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "document.pdf"
        assert result.attachments[0].content_type == "application/pdf"

    def test_handles_empty_payload(self) -> None:
        """Test handling of minimal payload."""
        payload = {"mimeType": "text/plain", "headers": [], "body": {}}

        result = parse_gmail_payload(payload)

        assert result.subject == ""
        assert result.from_email == ""
        assert result.text_plain == []
