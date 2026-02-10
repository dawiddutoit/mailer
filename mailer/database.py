"""SQLite database storage for emails."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from mailer.types import GmailMessage


def create_database(db_path: Path | str) -> sqlite3.Connection:
    """Create or connect to SQLite database with email schema."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            from_email TEXT,
            from_name TEXT,
            from_domain TEXT,
            to_emails TEXT,  -- JSON array
            cc_emails TEXT,  -- JSON array
            subject TEXT,
            body TEXT,
            body_html TEXT,
            snippet TEXT,
            label_ids TEXT,  -- JSON array
            date_header TEXT,  -- RFC 2822 date string
            timestamp INTEGER,  -- Unix timestamp in milliseconds
            size_estimate INTEGER,
            has_attachments INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            attachment_id TEXT NOT NULL,
            filename TEXT,
            mime_type TEXT,
            size INTEGER,
            FOREIGN KEY (message_id) REFERENCES emails(id),
            UNIQUE(message_id, attachment_id)
        );

        CREATE INDEX IF NOT EXISTS idx_emails_from_domain ON emails(from_domain);
        CREATE INDEX IF NOT EXISTS idx_emails_from_email ON emails(from_email);
        CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
        CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject);
        CREATE INDEX IF NOT EXISTS idx_emails_timestamp ON emails(timestamp);
        CREATE INDEX IF NOT EXISTS idx_attachments_message_id ON attachments(message_id);

        -- Full-text search
        CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
            subject,
            body,
            from_email,
            content='emails',
            content_rowid='rowid'
        );

        -- Triggers to keep FTS in sync
        CREATE TRIGGER IF NOT EXISTS emails_ai AFTER INSERT ON emails BEGIN
            INSERT INTO emails_fts(rowid, subject, body, from_email)
            VALUES (NEW.rowid, NEW.subject, NEW.body, NEW.from_email);
        END;

        CREATE TRIGGER IF NOT EXISTS emails_ad AFTER DELETE ON emails BEGIN
            INSERT INTO emails_fts(emails_fts, rowid, subject, body, from_email)
            VALUES ('delete', OLD.rowid, OLD.subject, OLD.body, OLD.from_email);
        END;

        CREATE TRIGGER IF NOT EXISTS emails_au AFTER UPDATE ON emails BEGIN
            INSERT INTO emails_fts(emails_fts, rowid, subject, body, from_email)
            VALUES ('delete', OLD.rowid, OLD.subject, OLD.body, OLD.from_email);
            INSERT INTO emails_fts(rowid, subject, body, from_email)
            VALUES (NEW.rowid, NEW.subject, NEW.body, NEW.from_email);
        END;
    """
    )

    conn.commit()
    return conn


def extract_email_parts(from_header: str) -> tuple[str, str, str]:
    """Extract email, name, and domain from 'Name <email>' format."""
    import re

    match = re.match(r'^"?([^"<]*)"?\s*<([^>]+)>$', from_header.strip())
    if match:
        name = match.group(1).strip()
        email = match.group(2).lower()
    else:
        name = ""
        email = from_header.strip().lower()

    domain = email.split("@")[-1] if "@" in email else ""
    return email, name, domain


def insert_email(conn: sqlite3.Connection, email: GmailMessage) -> bool:
    """Insert or update an email in the database. Returns True if new."""
    email_addr, name, domain = extract_email_parts(email.from_email)

    cursor = conn.execute("SELECT id FROM emails WHERE id = ?", (email.id,))
    exists = cursor.fetchone() is not None

    conn.execute(
        """
        INSERT OR REPLACE INTO emails (
            id, thread_id, from_email, from_name, from_domain,
            to_emails, cc_emails, subject, body, body_html, snippet,
            label_ids, date_header, timestamp, size_estimate, has_attachments, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            email.id,
            email.thread_id,
            email_addr,
            name,
            domain,
            json.dumps(email.to),
            json.dumps(email.cc) if hasattr(email, "cc") else "[]",
            email.subject,
            email.body,
            email.body_html if hasattr(email, "body_html") else "",
            email.snippet,
            json.dumps(email.label_ids),
            email.date if hasattr(email, "date") else "",
            email.timestamp,
            email.size_estimate if hasattr(email, "size_estimate") else 0,
            1 if email.attachments else 0,
            datetime.now().isoformat(),
        ),
    )

    # Insert attachments
    if email.attachments:
        for att in email.attachments:
            conn.execute(
                """
                INSERT OR REPLACE INTO attachments (
                    message_id, attachment_id, filename, mime_type, size
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    email.id,
                    att.attachment_id,
                    att.filename,
                    att.mime_type,
                    att.size,
                ),
            )

    return not exists


def insert_emails(conn: sqlite3.Connection, emails: list[GmailMessage]) -> int:
    """Insert multiple emails. Returns count of new emails."""
    new_count = 0
    for email in emails:
        if insert_email(conn, email):
            new_count += 1
    conn.commit()
    return new_count


def search_emails(conn: sqlite3.Connection, query: str, limit: int = 100) -> list[dict]:
    """Full-text search emails."""
    cursor = conn.execute(
        """
        SELECT e.* FROM emails e
        JOIN emails_fts fts ON e.rowid = fts.rowid
        WHERE emails_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """,
        (query, limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_emails_by_domain(conn: sqlite3.Connection, domain: str, limit: int = 100) -> list[dict]:
    """Get emails from a specific domain."""
    cursor = conn.execute(
        """
        SELECT * FROM emails
        WHERE from_domain = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """,
        (domain.lower().lstrip("@"), limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_emails_by_sender(conn: sqlite3.Connection, email: str, limit: int = 100) -> list[dict]:
    """Get emails from a specific sender."""
    cursor = conn.execute(
        """
        SELECT * FROM emails
        WHERE from_email = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """,
        (email.lower(), limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_all_emails(conn: sqlite3.Connection, limit: int = 1000) -> list[dict]:
    """Get all emails."""
    cursor = conn.execute("SELECT * FROM emails ORDER BY timestamp DESC LIMIT ?", (limit,))
    return [dict(row) for row in cursor.fetchall()]


def get_stats(conn: sqlite3.Connection) -> dict:
    """Get database statistics."""
    stats = {}

    cursor = conn.execute("SELECT COUNT(*) FROM emails")
    stats["total_emails"] = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(DISTINCT thread_id) FROM emails")
    stats["total_threads"] = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(DISTINCT from_domain) FROM emails")
    stats["unique_domains"] = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT from_domain, COUNT(*) as count
        FROM emails
        GROUP BY from_domain
        ORDER BY count DESC
        LIMIT 10
    """
    )
    stats["top_domains"] = [dict(row) for row in cursor.fetchall()]

    cursor = conn.execute(
        """
        SELECT from_email, from_name, COUNT(*) as count
        FROM emails
        GROUP BY from_email
        ORDER BY count DESC
        LIMIT 10
    """
    )
    stats["top_senders"] = [dict(row) for row in cursor.fetchall()]

    return stats


def get_default_db_path() -> Path:
    """Get the default database path."""
    return Path.home() / ".mailer" / "emails.db"
