"""Tests for mailer.export module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock

from mailer.export import (
    ExportConfig,
    ExportStats,
    create_project_queries,
    create_sender_queries,
    export_messages,
)


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_values(self, tmp_path: Path) -> None:
        """Verify default configuration values."""
        config = ExportConfig(output_dir=tmp_path)

        assert config.by_sender is True
        assert config.by_topic is True
        assert config.save_attachments is True
        assert config.create_index is True
        assert config.max_results_per_query == 100

    def test_custom_values(self, tmp_path: Path) -> None:
        """Verify custom configuration values."""
        config = ExportConfig(
            output_dir=tmp_path,
            by_sender=False,
            by_topic=False,
            save_attachments=False,
            create_index=False,
            max_results_per_query=50,
        )

        assert config.by_sender is False
        assert config.max_results_per_query == 50


class TestExportStats:
    """Tests for ExportStats dataclass."""

    def test_creates_stats(self) -> None:
        """Verify stats dataclass creation."""
        stats = ExportStats(
            emails_processed=10,
            emails_saved=8,
            attachments_saved=3,
            errors=["error1", "error2"],
        )

        assert stats.emails_processed == 10
        assert stats.emails_saved == 8
        assert stats.attachments_saved == 3
        assert len(stats.errors) == 2


class TestExportMessages:
    """Tests for export_messages function."""

    def test_export_creates_output_dir(
        self, mock_gmail_service: Mock, tmp_path: Path
    ) -> None:
        """Verify output directory is created."""
        output_dir = tmp_path / "export_output"
        config = ExportConfig(output_dir=output_dir)
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        export_messages(mock_gmail_service, {"test": "query"}, config)

        assert output_dir.exists()

    def test_export_returns_stats(
        self, mock_gmail_service: Mock, tmp_path: Path
    ) -> None:
        """Verify export returns ExportStats."""
        config = ExportConfig(output_dir=tmp_path)
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        result = export_messages(mock_gmail_service, {"test": "query"}, config)

        assert isinstance(result, ExportStats)

    def test_export_handles_no_messages(
        self, mock_gmail_service: Mock, tmp_path: Path
    ) -> None:
        """Verify export handles empty results."""
        config = ExportConfig(output_dir=tmp_path)
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        result = export_messages(mock_gmail_service, {"test": "query"}, config)

        assert result.emails_processed == 0
        assert result.emails_saved == 0

    def test_export_creates_index(
        self, mock_gmail_service: Mock, tmp_path: Path
    ) -> None:
        """Verify index is created when configured."""
        config = ExportConfig(output_dir=tmp_path, create_index=True)
        mock_gmail_service.users().messages().list().execute.return_value = {"messages": []}

        export_messages(mock_gmail_service, {"test": "query"}, config)

        assert (tmp_path / "Email_Index.md").exists()


class TestCreateProjectQueries:
    """Tests for create_project_queries function."""

    def test_creates_queries_for_terms(self) -> None:
        """Verify queries are created for project terms."""
        queries = create_project_queries(["project alpha", "phase 1"])

        assert "general" in queries
        assert "important" in queries
        assert "with_attachments" in queries
        assert '"project alpha"' in queries["general"]
        assert '"phase 1"' in queries["general"]

    def test_creates_or_queries(self) -> None:
        """Verify terms are combined with OR."""
        queries = create_project_queries(["term1", "term2"])

        assert " OR " in queries["general"]


class TestCreateSenderQueries:
    """Tests for create_sender_queries function."""

    def test_creates_queries_for_senders(self) -> None:
        """Verify queries are created for each sender."""
        queries = create_sender_queries(
            ["sender@example.com", "other@domain.com"],
            ["project"]
        )

        assert "from_example.com" in queries
        assert "from_domain.com" in queries
        assert "from:sender@example.com" in queries["from_example.com"]

    def test_includes_project_terms(self) -> None:
        """Verify project terms are included in queries."""
        queries = create_sender_queries(
            ["sender@example.com"],
            ["term1", "term2"]
        )

        assert '"term1"' in queries["from_example.com"]
        assert '"term2"' in queries["from_example.com"]
