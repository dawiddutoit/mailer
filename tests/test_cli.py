"""Tests for mailer.cli module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from mailer.cli import main
from mailer.types import GmailMessage


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create Click CLI test runner."""
    return CliRunner()


class TestMainGroup:
    """Tests for main CLI group."""

    def test_help_displays(self, cli_runner: CliRunner) -> None:
        """Verify help is displayed."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Mailer CLI" in result.output

    def test_version_displays(self, cli_runner: CliRunner) -> None:
        """Verify version is displayed."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestSearchCommand:
    """Tests for search command."""

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.messages.list_messages")
    def test_search_with_query(
        self,
        mock_list_messages: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
    ) -> None:
        """Verify search executes query."""
        mock_create_service.return_value = MagicMock()
        mock_list_messages.return_value = [sample_message]

        result = cli_runner.invoke(main, ["search", "is:unread"])

        assert result.exit_code == 0
        mock_list_messages.assert_called_once()

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.messages.list_messages")
    def test_search_json_format(
        self,
        mock_list_messages: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
    ) -> None:
        """Verify search outputs JSON."""
        mock_create_service.return_value = MagicMock()
        mock_list_messages.return_value = [sample_message]

        result = cli_runner.invoke(main, ["search", "is:unread", "--format", "json"])

        assert result.exit_code == 0
        assert '"id"' in result.output
        assert sample_message.id in result.output

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.messages.list_messages")
    def test_search_jsonl_format(
        self,
        mock_list_messages: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
    ) -> None:
        """Verify search outputs JSONL."""
        mock_create_service.return_value = MagicMock()
        mock_list_messages.return_value = [sample_message]

        result = cli_runner.invoke(main, ["search", "is:unread", "--format", "jsonl"])

        assert result.exit_code == 0
        assert sample_message.id in result.output

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.messages.list_messages")
    def test_search_no_results(
        self,
        mock_list_messages: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Verify search handles no results."""
        mock_create_service.return_value = MagicMock()
        mock_list_messages.return_value = []

        result = cli_runner.invoke(main, ["search", "nonexistent"])

        assert result.exit_code == 0
        assert "No emails found" in result.output


class TestSendCommand:
    """Tests for send command."""

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.messages.send_message")
    def test_send_email_success(
        self,
        mock_send: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Verify email is sent."""
        mock_create_service.return_value = MagicMock()
        mock_send.return_value = "msg_sent_123"

        result = cli_runner.invoke(
            main, ["send", "recipient@example.com", "Test Subject", "Test body"]
        )

        assert result.exit_code == 0
        assert "Email sent" in result.output
        assert "msg_sent_123" in result.output


class TestShowCommand:
    """Tests for show command."""

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.cli.get_message")
    def test_show_email_text_format(
        self,
        mock_get_message: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
    ) -> None:
        """Verify show displays email details."""
        mock_create_service.return_value = MagicMock()
        mock_get_message.return_value = sample_message

        result = cli_runner.invoke(main, ["show", "msg_123"])

        assert result.exit_code == 0
        assert sample_message.subject in result.output
        assert sample_message.from_email in result.output

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.cli.get_message")
    def test_show_email_json_format(
        self,
        mock_get_message: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
    ) -> None:
        """Verify show outputs JSON."""
        mock_create_service.return_value = MagicMock()
        mock_get_message.return_value = sample_message

        result = cli_runner.invoke(main, ["show", "msg_123", "--format", "json"])

        assert result.exit_code == 0
        assert '"id"' in result.output


class TestStatusCommand:
    """Tests for status command."""

    def test_status_no_storage(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Verify status handles missing storage."""
        result = cli_runner.invoke(main, ["status", "--storage", str(tmp_path / "nonexistent")])

        assert result.exit_code == 0
        assert "No storage found" in result.output


class TestDbCommands:
    """Tests for db command group."""

    def test_db_stats_no_database(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Verify stats handles missing database."""
        result = cli_runner.invoke(main, ["db", "stats", "--database", str(tmp_path / "nodb.db")])

        assert result.exit_code == 0
        assert "No database found" in result.output

    def test_db_import_json(
        self, cli_runner: CliRunner, tmp_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify import from JSON file."""
        # Create source JSON file
        import json

        source_file = tmp_path / "emails.json"
        source_file.write_text(json.dumps([sample_message.model_dump()], default=str))

        db_path = tmp_path / "test.db"

        result = cli_runner.invoke(
            main, ["db", "import", str(source_file), "--database", str(db_path)]
        )

        assert result.exit_code == 0
        assert "Imported" in result.output
        assert db_path.exists()

    def test_db_search_no_database(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Verify search handles missing database."""
        result = cli_runner.invoke(
            main, ["db", "search", "test", "--database", str(tmp_path / "nodb.db")]
        )

        assert result.exit_code == 0
        assert "No database found" in result.output

    def test_db_search_with_database(
        self, cli_runner: CliRunner, tmp_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify search works with populated database."""
        from mailer.database import create_database, insert_emails

        db_path = tmp_path / "test.db"
        conn = create_database(db_path)
        insert_emails(conn, [sample_message])
        conn.close()

        result = cli_runner.invoke(
            main, ["db", "search", "Test Subject", "--database", str(db_path)]
        )

        assert result.exit_code == 0

    def test_db_query_command(
        self, cli_runner: CliRunner, tmp_path: Path, sample_message: GmailMessage
    ) -> None:
        """Verify raw SQL query works."""
        from mailer.database import create_database, insert_emails

        db_path = tmp_path / "test.db"
        conn = create_database(db_path)
        insert_emails(conn, [sample_message])
        conn.close()

        result = cli_runner.invoke(
            main,
            ["db", "query", "SELECT COUNT(*) as cnt FROM emails", "--database", str(db_path)],
        )

        assert result.exit_code == 0
        assert "1" in result.output  # Count should be 1


class TestGetEmailsCommand:
    """Tests for get emails command."""

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.cli.list_message_ids")
    @patch("mailer.cli.get_message")
    def test_get_emails_basic(
        self,
        mock_get_message: Mock,
        mock_list_ids: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
        tmp_path: Path,
    ) -> None:
        """Verify get emails fetches and displays messages."""
        mock_create_service.return_value = MagicMock()
        mock_list_ids.return_value = ["msg_123"]
        mock_get_message.return_value = sample_message

        result = cli_runner.invoke(
            main,
            [
                "get",
                "emails",
                "@example.com",
                "--no-cache",
                "--storage",
                str(tmp_path / "storage"),
            ],
        )

        # Should complete (may show table or no results depending on filtering)
        assert result.exit_code == 0


class TestDownloadCommand:
    """Tests for download command."""

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.cli.get_message")
    def test_download_no_attachments(
        self,
        mock_get_message: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message: GmailMessage,
    ) -> None:
        """Verify download handles no attachments."""
        mock_create_service.return_value = MagicMock()
        mock_get_message.return_value = sample_message  # No attachments

        result = cli_runner.invoke(main, ["download", "msg_123"])

        assert result.exit_code == 0
        assert "No attachments found" in result.output

    @patch("mailer.cli.check_credentials_exist", return_value=True)
    @patch("mailer.cli.create_service")
    @patch("mailer.cli.get_message")
    @patch("mailer.cli.download_attachment")
    def test_download_with_attachments(
        self,
        mock_download: Mock,
        mock_get_message: Mock,
        mock_create_service: Mock,
        mock_check_creds: Mock,
        cli_runner: CliRunner,
        sample_message_with_attachment: GmailMessage,
        tmp_path: Path,
    ) -> None:
        """Verify download saves attachments."""
        mock_create_service.return_value = MagicMock()
        mock_get_message.return_value = sample_message_with_attachment
        mock_download.return_value = b"PDF content here"

        result = cli_runner.invoke(
            main, ["download", "msg_789", "--output", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Downloaded" in result.output
