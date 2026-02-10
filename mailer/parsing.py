"""Email parsing functions using mail-parser and email-reply-parser.

This module provides pure functions for parsing email content:
- parse_raw_email: Parse raw email bytes (RFC 5322 format)
- parse_gmail_payload: Parse Gmail API payload dict
- extract_latest_reply: Extract only the latest reply from email body
"""

import base64
import contextlib
from email.utils import parsedate_to_datetime

import mailparser
from email_reply_parser import EmailReplyParser

from mailer.types import ParsedAttachment, ParsedEmail


def parse_raw_email(raw_bytes: bytes) -> ParsedEmail:
    """Parse raw email bytes into structured data.

    Args:
        raw_bytes: Raw email in RFC 5322 format

    Returns:
        ParsedEmail with all extracted components
    """
    mail = mailparser.parse_from_bytes(raw_bytes)
    return _mailparser_to_parsed_email(mail)


def parse_raw_email_string(raw_string: str) -> ParsedEmail:
    """Parse raw email string into structured data."""
    mail = mailparser.parse_from_string(raw_string)
    return _mailparser_to_parsed_email(mail)


def _mailparser_to_parsed_email(mail: mailparser.MailParser) -> ParsedEmail:
    """Convert mailparser.MailParser to ParsedEmail model."""
    # Format addresses - mail-parser returns list of tuples [(name, email), ...]
    from_email = _format_address(mail.from_)
    to_list = _format_addresses(mail.to)
    cc_list = _format_addresses(mail.cc)
    bcc_list = _format_addresses(mail.bcc)

    # Parse date
    date = None
    if mail.date:
        date = mail.date

    # Extract attachments
    attachments = []
    for att in mail.attachments:
        attachments.append(
            ParsedAttachment(
                filename=att.get("filename", ""),
                content_type=att.get("mail_content_type", "application/octet-stream"),
                size=len(att.get("payload", "")) if att.get("payload") else 0,
                payload=att.get("payload", ""),
                content_id=att.get("content-id"),
                content_disposition=att.get("content_disposition"),
            )
        )

    return ParsedEmail(
        subject=mail.subject or "",
        from_email=from_email,
        to=to_list,
        cc=cc_list,
        bcc=bcc_list,
        date=date,
        message_id=mail.message_id or "",
        text_plain=mail.text_plain if mail.text_plain else [],
        text_html=mail.text_html if mail.text_html else [],
        attachments=attachments,
        defects=list(mail.defects) if mail.defects else [],
    )


def _format_address(addr: list[tuple[str, str]] | None) -> str:
    """Format address tuple to string."""
    if not addr:
        return ""
    if isinstance(addr, list) and len(addr) > 0:
        name, email = addr[0]
        if name:
            return f"{name} <{email}>"
        return email
    return ""


def _format_addresses(addrs: list[tuple[str, str]] | None) -> list[str]:
    """Format list of address tuples to strings."""
    if not addrs:
        return []
    result = []
    for name, email in addrs:
        if name:
            result.append(f"{name} <{email}>")
        else:
            result.append(email)
    return result


def extract_latest_reply(body_text: str) -> str:
    """Extract only the latest reply, stripping quoted text and signatures.

    Args:
        body_text: Full email body text (may contain quoted replies)

    Returns:
        Just the latest reply content, without quoted text
    """
    if not body_text:
        return ""

    import re

    # Normalize line endings (Gmail uses \r\n, email-reply-parser expects \n)
    text = body_text.replace("\r\n", "\n")

    # Normalize Unicode whitespace (Gmail uses \u202f narrow no-break space)
    text = re.sub(r"[\u202f\u00a0]", " ", text)

    # Fix Gmail's line wrapping inside "On ... wrote:" headers
    # Pattern 1: Newline before "wrote:"
    #   On Mon, 19 Jan 2026, 14:00 Name <email@example.com>
    #   wrote:
    text = re.sub(
        r"(On [^\n]+<[^>]+>)\n(wrote:)",
        r"\1 \2",
        text,
    )

    # Pattern 2: Newline inside angle brackets (Gmail wraps long emails)
    #   On Tue, Jan 27, 2026 at 8:10 AM Name <
    #   email@example.com> wrote:
    text = re.sub(
        r"(On [^\n]+)<\n([^>]+)>(\s*wrote:)",
        r"\1<\2>\3",
        text,
    )

    return EmailReplyParser.parse_reply(text)


def parse_gmail_payload(payload: dict, headers: dict[str, str] | None = None) -> ParsedEmail:
    """Parse Gmail API payload dict into structured data.

    The Gmail API returns messages in a nested payload format when using
    format="full". This function extracts body content from that structure.

    Args:
        payload: Gmail API message payload dict
        headers: Optional pre-extracted headers dict

    Returns:
        ParsedEmail with extracted components
    """
    if headers is None:
        headers = _extract_gmail_headers(payload)

    # Extract body parts
    text_plain_parts: list[str] = []
    text_html_parts: list[str] = []
    attachments: list[ParsedAttachment] = []

    _extract_gmail_parts(payload, text_plain_parts, text_html_parts, attachments)

    # Parse date
    date = None
    if headers.get("date"):
        with contextlib.suppress(ValueError, TypeError):
            date = parsedate_to_datetime(headers["date"])

    # Parse addresses
    to_list = _parse_address_header(headers.get("to", ""))
    cc_list = _parse_address_header(headers.get("cc", ""))

    return ParsedEmail(
        subject=headers.get("subject", ""),
        from_email=headers.get("from", ""),
        to=to_list,
        cc=cc_list,
        date=date,
        message_id=headers.get("message-id", ""),
        text_plain=text_plain_parts,
        text_html=text_html_parts,
        attachments=attachments,
    )


def _extract_gmail_headers(payload: dict) -> dict[str, str]:
    """Extract headers from Gmail payload."""
    headers: dict[str, str] = {}
    for header in payload.get("headers", []):
        name = header["name"].lower()
        headers[name] = header["value"]
    return headers


def _extract_gmail_parts(
    payload: dict,
    text_plain: list[str],
    text_html: list[str],
    attachments: list[ParsedAttachment],
) -> None:
    """Recursively extract parts from Gmail payload."""
    mime_type = payload.get("mimeType", "")

    # Check for body data in this part
    body = payload.get("body", {})
    if "data" in body and body.get("size", 0) > 0:
        decoded = base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="ignore")

        # Check if this is an attachment
        filename = payload.get("filename", "")
        if filename:
            attachments.append(
                ParsedAttachment(
                    filename=filename,
                    content_type=mime_type,
                    size=body.get("size", 0),
                    payload=body["data"],  # Keep base64 encoded
                )
            )
        elif mime_type == "text/plain":
            text_plain.append(decoded)
        elif mime_type == "text/html":
            text_html.append(decoded)

    # Recurse into parts
    for part in payload.get("parts", []):
        _extract_gmail_parts(part, text_plain, text_html, attachments)


def _parse_address_header(header: str) -> list[str]:
    """Parse comma-separated address header into list."""
    if not header:
        return []
    # Simple split - could be enhanced with proper RFC 5322 parsing
    addresses = []
    for addr in header.split(","):
        addr = addr.strip()
        if addr:
            addresses.append(addr)
    return addresses


def convert_gmail_raw_to_bytes(raw_data: str) -> bytes:
    """Convert Gmail API raw format to bytes for mail-parser.

    When fetching with format="raw", Gmail returns base64url-encoded RFC 5322.
    """
    return base64.urlsafe_b64decode(raw_data)
