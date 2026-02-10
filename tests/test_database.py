"""Tests for mailer.database module."""

from pathlib import Path

import pytest

from mailer.database import (
    create_database,
    extract_email_parts,
    get_all_emails,
    get_default_db_path,
    get_emails_by_domain,
    get_emails_by_sender,
    get_stats,
    insert_email,
    insert_emails,
    search_emails,
)
from mailer.types import GmailMessage


class TestCreateDatabase:
    """Tests for create_database function."""

    def test_creates_database_file(self, tmp_db_path: Path) -> None:
        """Verify database file is created."""
        conn = create_database(tmp_db_path)
        conn.close()

        assert tmp_db_path.exists()

    def test_creates_tables(self, tmp_db_path: Path) -> None:
        """Verify tables are created."""
        conn = create_database(tmp_db_path)

        # Check tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "emails" in tables
        assert "attachments" in tables
        assert "emails_fts" in tables

    def test_idempotent_creation(self, tmp_db_path: Path) -> None:
        """Verify database can be created multiple times."""
        conn1 = create_database(tmp_db_path)
        conn1.close()

        # Should not raise
        conn2 = create_database(tmp_db_path)
        conn2.close()


class TestExtractEmailParts:
    """Tests for extract_email_parts function."""

    def test_extracts_from_name_email_format(self) -> None:
        """Verify extraction from 'Name <email>' format."""
        email, name, domain = extract_email_parts("John Doe <john@example.com>")

        assert email == "john@example.com"
        assert name == "John Doe"
        assert domain == "example.com"

    def test_extracts_from_email_only(self) -> None:
        """Verify extraction from plain email."""
        email, name, domain = extract_email_parts("john@example.com")

        assert email == "john@example.com"
        assert name == ""
        assert domain == "example.com"

    def test_extracts_from_quoted_name(self) -> None:
        """Verify extraction from quoted name format."""
        email, name, domain = extract_email_parts('"John Doe" <john@example.com>')

        assert email == "john@example.com"
        assert name == "John Doe"
        assert domain == "example.com"

    def test_handles_empty_string(self) -> None:
        """Verify empty string is handled."""
        email, name, domain = extract_email_parts("")

        assert email == ""
        assert name == ""
        assert domain == ""


class TestInsertEmail:
    """Tests for insert_email function."""

    def test_insert_new_email(
        self, tmp_db_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify new email is inserted."""
        conn = create_database(tmp_db_path)

        is_new = insert_email(conn, sample_message)
        conn.commit()

        assert is_new is True

        # Verify it's in database
        cursor = conn.execute("SELECT id FROM emails WHERE id = ?", (sample_message.id,))
        assert cursor.fetchone() is not None
        conn.close()

    def test_update_existing_email(
        self, tmp_db_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify existing email is updated."""
        conn = create_database(tmp_db_path)

        # Insert first time
        insert_email(conn, sample_message)
        conn.commit()

        # Insert again
        is_new = insert_email(conn, sample_message)
        conn.commit()

        assert is_new is False
        conn.close()


class TestInsertEmails:
    """Tests for insert_emails function."""

    def test_insert_multiple_emails(
        self, tmp_db_path: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify multiple emails are inserted."""
        conn = create_database(tmp_db_path)

        new_count = insert_emails(conn, sample_messages)

        assert new_count == len(sample_messages)
        conn.close()

    def test_returns_new_count_only(
        self, tmp_db_path: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify only new emails are counted."""
        conn = create_database(tmp_db_path)

        # Insert once
        insert_emails(conn, sample_messages)
        # Insert again
        new_count = insert_emails(conn, sample_messages)

        assert new_count == 0
        conn.close()


class TestSearchEmails:
    """Tests for search_emails function."""

    def test_search_finds_matching_emails(
        self, tmp_db_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify search finds matching emails."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, [sample_message])

        results = search_emails(conn, sample_message.subject, limit=10)

        assert len(results) == 1
        assert results[0]["id"] == sample_message.id
        conn.close()

    def test_search_no_results(self, tmp_db_path: Path) -> None:
        """Verify search returns empty for no matches."""
        conn = create_database(tmp_db_path)

        results = search_emails(conn, "nonexistent query", limit=10)

        assert results == []
        conn.close()


class TestGetEmailsByDomain:
    """Tests for get_emails_by_domain function."""

    def test_gets_emails_by_domain(
        self, tmp_db_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify emails are retrieved by domain."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, [sample_message])

        results = get_emails_by_domain(conn, "example.com", limit=10)

        assert len(results) == 1
        conn.close()

    def test_handles_at_prefix(
        self, tmp_db_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify @ prefix is stripped."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, [sample_message])

        results = get_emails_by_domain(conn, "@example.com", limit=10)

        assert len(results) == 1
        conn.close()


class TestGetEmailsBySender:
    """Tests for get_emails_by_sender function."""

    def test_gets_emails_by_sender(
        self, tmp_db_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify emails are retrieved by sender."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, [sample_message])

        results = get_emails_by_sender(conn, "sender@example.com", limit=10)

        assert len(results) == 1
        conn.close()


class TestGetAllEmails:
    """Tests for get_all_emails function."""

    def test_gets_all_emails(
        self, tmp_db_path: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify all emails are retrieved."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, sample_messages)

        results = get_all_emails(conn, limit=100)

        assert len(results) == len(sample_messages)
        conn.close()

    def test_respects_limit(
        self, tmp_db_path: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify limit is respected."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, sample_messages)

        results = get_all_emails(conn, limit=1)

        assert len(results) == 1
        conn.close()


class TestGetStats:
    """Tests for get_stats function."""

    def test_gets_stats(
        self, tmp_db_path: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify stats are returned."""
        conn = create_database(tmp_db_path)
        insert_emails(conn, sample_messages)

        stats = get_stats(conn)

        assert stats["total_emails"] == len(sample_messages)
        assert "total_threads" in stats
        assert "unique_domains" in stats
        assert "top_domains" in stats
        assert "top_senders" in stats
        conn.close()

    def test_empty_database_stats(self, tmp_db_path: Path) -> None:
        """Verify stats for empty database."""
        conn = create_database(tmp_db_path)

        stats = get_stats(conn)

        assert stats["total_emails"] == 0
        conn.close()


class TestGetDefaultDbPath:
    """Tests for get_default_db_path function."""

    def test_returns_path_in_home(self) -> None:
        """Verify default path is in user's home directory."""
        result = get_default_db_path()

        assert isinstance(result, Path)
        assert ".mailer" in str(result)
        assert "emails.db" in str(result)
