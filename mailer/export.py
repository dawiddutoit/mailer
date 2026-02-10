"""Email export and archiving operations.

This module provides functions for bulk exporting and organizing Gmail messages
into local storage, including:
- Searching and downloading messages in bulk
- Organizing by sender, topic, date
- Saving attachments
- Creating searchable indexes
"""

import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import Resource


@dataclass(frozen=True)
class ExportConfig:
    """Configuration for email export operations."""

    output_dir: Path
    by_sender: bool = True
    by_topic: bool = True
    save_attachments: bool = True
    create_index: bool = True
    max_results_per_query: int = 100


@dataclass(frozen=True)
class ExportStats:
    """Statistics for an export operation."""

    emails_processed: int
    emails_saved: int
    attachments_saved: int
    errors: list[str]


def export_messages(
    service: Resource,
    queries: dict[str, str],
    config: ExportConfig,
) -> ExportStats:
    """Export messages matching queries to local storage.

    Args:
        service: Authenticated Gmail API service
        queries: Dict of {category: gmail_query_string}
        config: Export configuration

    Returns:
        Statistics about the export operation
    """
    emails_processed = 0
    emails_saved = 0
    attachments_saved = 0
    errors: list[str] = []

    config.output_dir.mkdir(parents=True, exist_ok=True)

    for category, query in queries.items():
        try:
            # Search for messages
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=config.max_results_per_query)
                .execute()
            )

            messages = results.get("messages", [])

            for msg_ref in messages:
                try:
                    msg_id = msg_ref["id"]
                    message = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="full")
                        .execute()
                    )

                    emails_processed += 1

                    # Save email
                    _save_message_text(message, config, category)
                    emails_saved += 1

                    # Save attachments if configured
                    if config.save_attachments:
                        att_count = _save_message_attachments(service, message, msg_id, config)
                        attachments_saved += att_count

                except Exception as e:
                    errors.append(f"Error processing message {msg_ref.get('id', 'unknown')}: {e}")

        except Exception as e:
            errors.append(f"Error processing category '{category}': {e}")

    # Create index if configured
    if config.create_index:
        _create_export_index(config.output_dir, emails_saved, attachments_saved)

    return ExportStats(
        emails_processed=emails_processed,
        emails_saved=emails_saved,
        attachments_saved=attachments_saved,
        errors=errors,
    )


def _save_message_text(message: dict, config: ExportConfig, category: str) -> None:
    """Save message as text file."""
    headers = _extract_headers(message)
    body = _extract_body(message)

    # Determine save locations
    save_dirs: list[Path] = []

    if config.by_sender:
        sender = headers.get("from", "unknown")
        sender_dir = _sanitize_sender_name(sender)
        save_dirs.append(config.output_dir / "By_Sender" / sender_dir)

    if config.by_topic:
        topic_dir = category.replace(" ", "_")
        save_dirs.append(config.output_dir / "By_Topic" / topic_dir)

    # Create filename
    date_str = _parse_date_for_filename(headers.get("date", ""))
    subject = headers.get("subject", "No Subject")
    clean_subject = _sanitize_filename(subject)
    msg_id = message["id"]
    filename = f"{date_str}_{clean_subject[:50]}_{msg_id[:8]}.txt"

    # Email content
    content = _format_email_content(message, headers, body)

    # Save to all configured locations
    for save_dir in save_dirs:
        save_dir.mkdir(parents=True, exist_ok=True)
        filepath = save_dir / filename
        filepath.write_text(content, encoding="utf-8")


def _save_message_attachments(
    service: Resource, message: dict, msg_id: str, config: ExportConfig
) -> int:
    """Save message attachments. Returns count of saved attachments."""
    count = 0
    headers = _extract_headers(message)
    subject = headers.get("subject", "No Subject")
    clean_subject = _sanitize_filename(subject)

    if "parts" not in message["payload"]:
        return 0

    att_dir = config.output_dir / "By_Sender" / "Attachments" / clean_subject[:30]
    att_dir.mkdir(parents=True, exist_ok=True)

    for part in message["payload"]["parts"]:
        if part.get("filename"):
            attachment_id = part["body"].get("attachmentId")
            if attachment_id:
                try:
                    attachment = (
                        service.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=msg_id, id=attachment_id)
                        .execute()
                    )

                    data = base64.urlsafe_b64decode(attachment["data"])
                    filepath = att_dir / part["filename"]
                    filepath.write_bytes(data)
                    count += 1
                except Exception:
                    # Skip attachment on error
                    pass

    return count


def _extract_headers(message: dict) -> dict[str, str]:
    """Extract key headers from message."""
    headers = {}
    for header in message["payload"].get("headers", []):
        name = header["name"].lower()
        if name in ["from", "to", "subject", "date"]:
            headers[name] = header["value"]
    return headers


def _extract_body(message: dict) -> str:
    """Extract message body text."""
    body = ""

    if "parts" in message["payload"]:
        # Multipart message
        for part in message["payload"]["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part["body"]:
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="ignore"
                )
                break
    else:
        # Simple message
        if "data" in message["payload"]["body"]:
            body = base64.urlsafe_b64decode(message["payload"]["body"]["data"]).decode(
                "utf-8", errors="ignore"
            )

    return body


def _format_email_content(message: dict, headers: dict[str, str], body: str) -> str:
    """Format email as text with metadata."""
    msg_id = message["id"]
    return f"""
{"=" * 80}
MESSAGE ID: {msg_id}
FROM: {headers.get("from", "Unknown")}
TO: {headers.get("to", "Unknown")}
DATE: {headers.get("date", "Unknown")}
SUBJECT: {headers.get("subject", "No Subject")}
{"=" * 80}

{body}

{"=" * 80}
GMAIL URL: https://mail.google.com/mail/u/0/#all/{msg_id}
{"=" * 80}
"""


def _sanitize_sender_name(sender: str) -> str:
    """Extract and sanitize sender name for directory."""
    # Extract domain from email or use name
    if "@" in sender:
        # Get domain part
        email_part = sender.split("<")[-1].replace(">", "").strip()
        domain = email_part.split("@")[1] if "@" in email_part else email_part
        return _sanitize_filename(domain)
    return _sanitize_filename(sender)


def _sanitize_filename(name: str) -> str:
    """Sanitize string for use as filename."""
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()


def _parse_date_for_filename(date_str: str) -> str:
    """Parse email date header to YYYY-MM-DD format."""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")

    try:
        # Email dates are like: "Mon, 15 Aug 2023 10:30:00 +0200"
        date_part = date_str.split(",")[1].strip().split("+")[0].strip()
        date_obj = datetime.strptime(date_part, "%d %b %Y %H:%M:%S")
        return date_obj.strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _create_export_index(output_dir: Path, emails_saved: int, attachments_saved: int) -> None:
    """Create markdown index of exported emails."""
    index_file = output_dir / "Email_Index.md"

    with index_file.open("w", encoding="utf-8") as f:
        f.write("# Email Export Index\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Total Emails:** {emails_saved}\n")
        f.write(f"**Total Attachments:** {attachments_saved}\n\n")
        f.write("---\n\n")

        # Index by sender
        f.write("## By Sender\n\n")
        sender_dir = output_dir / "By_Sender"
        if sender_dir.exists():
            for sender_folder in sorted(sender_dir.iterdir()):
                if sender_folder.is_dir() and sender_folder.name != "Attachments":
                    emails = list(sender_folder.glob("*.txt"))
                    f.write(f"### {sender_folder.name.replace('_', ' ')}\n")
                    f.write(f"**Count:** {len(emails)} emails\n\n")
                    for email_file in sorted(emails)[:10]:
                        f.write(f"- `{email_file.name}`\n")
                    if len(emails) > 10:
                        f.write(f"- ... and {len(emails) - 10} more\n")
                    f.write("\n")

        # Index by topic
        f.write("## By Topic\n\n")
        topic_dir = output_dir / "By_Topic"
        if topic_dir.exists():
            for topic_folder in sorted(topic_dir.iterdir()):
                if topic_folder.is_dir():
                    emails = list(topic_folder.glob("*.txt"))
                    f.write(f"### {topic_folder.name.replace('_', ' ')}\n")
                    f.write(f"**Count:** {len(emails)} emails\n\n")


def create_project_queries(project_terms: list[str]) -> dict[str, str]:
    """Create common search queries for a project.

    Args:
        project_terms: List of terms to search for (e.g., ["house du toit", "16 morgan"])

    Returns:
        Dict of {category: gmail_query_string}
    """
    # Build OR clause for project terms
    terms_query = " OR ".join(f'"{term}"' for term in project_terms)

    return {
        "general": f"subject:({terms_query})",
        "important": f"is:important ({terms_query})",
        "with_attachments": f"has:attachment ({terms_query})",
    }


def create_sender_queries(senders: list[str], project_terms: list[str]) -> dict[str, str]:
    """Create queries filtered by specific senders.

    Args:
        senders: List of email addresses or domains
        project_terms: List of project terms to filter by

    Returns:
        Dict of {category: gmail_query_string}
    """
    terms_query = " OR ".join(f'"{term}"' for term in project_terms)
    queries = {}

    for sender in senders:
        # Extract domain or email
        sender_key = sender.split("@")[1] if "@" in sender else sender
        queries[f"from_{sender_key}"] = f"from:{sender} ({terms_query})"

    return queries
