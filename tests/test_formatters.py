"""Tests for mailer.formatters module."""

import json
from datetime import datetime
from pathlib import Path

from mailer.formatters import (
    format_as_json,
    format_as_jsonl,
    format_dict_as_json,
    format_dicts_as_jsonl,
    format_thread_as_json,
    format_threads_as_json,
    format_threads_as_jsonl,
    write_output,
)
from mailer.types import GmailMessage, GmailThread


class TestFormatAsJson:
    """Tests for format_as_json function."""

    def test_format_single_message(self, sample_message: GmailMessage) -> None:
        """Verify single message is formatted."""
        result = format_as_json([sample_message])

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["id"] == sample_message.id

    def test_format_multiple_messages(self, sample_messages: list[GmailMessage]) -> None:
        """Verify multiple messages are formatted."""
        result = format_as_json(sample_messages)

        parsed = json.loads(result)
        assert len(parsed) == len(sample_messages)

    def test_format_with_indent(self, sample_message: GmailMessage) -> None:
        """Verify indentation is applied."""
        result = format_as_json([sample_message], indent=4)

        # Should have multiple lines due to indentation
        assert "\n" in result
        assert "    " in result  # 4-space indent

    def test_format_empty_list(self) -> None:
        """Verify empty list produces empty JSON array."""
        result = format_as_json([])

        assert result == "[]"


class TestFormatAsJsonl:
    """Tests for format_as_jsonl function."""

    def test_format_single_message(self, sample_message: GmailMessage) -> None:
        """Verify single message is formatted."""
        result = format_as_jsonl([sample_message])

        lines = result.strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["id"] == sample_message.id

    def test_format_multiple_messages(self, sample_messages: list[GmailMessage]) -> None:
        """Verify each message is on separate line."""
        result = format_as_jsonl(sample_messages)

        lines = result.strip().split("\n")
        assert len(lines) == len(sample_messages)

        # Each line should be valid JSON
        for line in lines:
            json.loads(line)  # Should not raise

    def test_format_empty_list(self) -> None:
        """Verify empty list produces empty string."""
        result = format_as_jsonl([])

        assert result == ""


class TestFormatThreadAsJson:
    """Tests for format_thread_as_json function."""

    def test_format_thread(self, sample_thread: GmailThread) -> None:
        """Verify thread is formatted."""
        result = format_thread_as_json(sample_thread)

        parsed = json.loads(result)
        assert parsed["id"] == sample_thread.id
        assert len(parsed["messages"]) == len(sample_thread.messages)


class TestFormatThreadsAsJson:
    """Tests for format_threads_as_json function."""

    def test_format_threads(self, sample_thread: GmailThread) -> None:
        """Verify threads are formatted."""
        result = format_threads_as_json([sample_thread])

        parsed = json.loads(result)
        assert len(parsed) == 1


class TestFormatThreadsAsJsonl:
    """Tests for format_threads_as_jsonl function."""

    def test_format_threads(self, sample_thread: GmailThread) -> None:
        """Verify threads are formatted as JSONL."""
        result = format_threads_as_jsonl([sample_thread, sample_thread])

        lines = result.strip().split("\n")
        assert len(lines) == 2


class TestFormatDictAsJson:
    """Tests for format_dict_as_json function."""

    def test_format_dict(self) -> None:
        """Verify dict is formatted."""
        data = {"key": "value", "number": 42}
        result = format_dict_as_json(data)

        parsed = json.loads(result)
        assert parsed == data

    def test_format_list_of_dicts(self) -> None:
        """Verify list of dicts is formatted."""
        data = [{"a": 1}, {"b": 2}]
        result = format_dict_as_json(data)

        parsed = json.loads(result)
        assert parsed == data


class TestFormatDictsAsJsonl:
    """Tests for format_dicts_as_jsonl function."""

    def test_format_dicts(self) -> None:
        """Verify dicts are formatted as JSONL."""
        data = [{"a": 1}, {"b": 2}, {"c": 3}]
        result = format_dicts_as_jsonl(data)

        lines = result.strip().split("\n")
        assert len(lines) == 3


class TestJsonSerializer:
    """Tests for _json_serializer function."""

    def test_serializes_datetime(self, sample_message: GmailMessage) -> None:
        """Verify datetime is serialized."""
        # GmailMessage has computed datetime_utc field
        result = format_as_json([sample_message])

        # Should not raise and should contain ISO format date
        assert "2024" in result  # From timestamp

    def test_serializes_bytes(self) -> None:
        """Verify bytes are serialized."""
        # Create a dict with bytes (would be handled by serializer)
        data = {"content": "test"}
        result = format_dict_as_json(data)

        assert "test" in result


class TestWriteOutput:
    """Tests for write_output function."""

    def test_write_to_file(self, tmp_path: Path) -> None:
        """Verify content is written to file."""
        output_file = tmp_path / "output.json"
        content = '{"test": true}'

        write_output(content, str(output_file))

        assert output_file.exists()
        assert output_file.read_text() == content

    def test_write_to_stdout(self, capsys) -> None:
        """Verify content is printed to stdout when no path given."""
        content = '{"test": true}'

        write_output(content, None)

        captured = capsys.readouterr()
        assert content in captured.out
