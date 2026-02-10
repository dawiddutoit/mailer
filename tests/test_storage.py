"""Tests for mailer.storage module."""

from pathlib import Path

import pytest

from mailer.storage import EmailStorage, get_default_storage_dir
from mailer.types import GmailMessage


class TestEmailStorage:
    """Tests for EmailStorage class."""

    def test_init_creates_directories(self, tmp_storage_dir: Path) -> None:
        """Verify storage directories are created."""
        storage = EmailStorage(tmp_storage_dir)

        assert storage.storage_dir.exists()
        assert storage.messages_dir.exists()

    def test_has_message_false_initially(self, tmp_storage_dir: Path) -> None:
        """Verify has_message returns False for unknown message."""
        storage = EmailStorage(tmp_storage_dir)

        assert storage.has_message("nonexistent") is False

    def test_store_message_and_has_message(
        self, tmp_storage_dir: Path, sample_message: GmailMessage
    ) -> None:
        """Verify message can be stored and checked."""
        storage = EmailStorage(tmp_storage_dir)

        storage.store_message(sample_message)

        assert storage.has_message(sample_message.id) is True

    def test_store_messages_returns_count(
        self, tmp_storage_dir: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify store_messages returns count of new messages."""
        storage = EmailStorage(tmp_storage_dir)

        count = storage.store_messages(sample_messages)

        assert count == len(sample_messages)

    def test_store_messages_skips_duplicates(
        self, tmp_storage_dir: Path, sample_message: GmailMessage
    ) -> None:
        """Verify duplicate messages are not stored again."""
        storage = EmailStorage(tmp_storage_dir)

        # Store once
        storage.store_messages([sample_message])
        # Try to store again
        count = storage.store_messages([sample_message])

        assert count == 0  # No new messages

    def test_load_message_returns_message(
        self, tmp_storage_dir: Path, sample_message: GmailMessage
    ) -> None:
        """Verify message can be loaded after storing."""
        storage = EmailStorage(tmp_storage_dir)
        storage.store_message(sample_message)

        loaded = storage.load_message(sample_message.id)

        assert loaded is not None
        assert loaded.id == sample_message.id
        assert loaded.subject == sample_message.subject

    def test_load_message_returns_none_for_missing(self, tmp_storage_dir: Path) -> None:
        """Verify load_message returns None for missing message."""
        storage = EmailStorage(tmp_storage_dir)

        loaded = storage.load_message("nonexistent")

        assert loaded is None

    def test_load_all_messages(
        self, tmp_storage_dir: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify all messages can be loaded."""
        storage = EmailStorage(tmp_storage_dir)
        storage.store_messages(sample_messages)

        loaded = storage.load_all_messages()

        assert len(loaded) == len(sample_messages)

    def test_get_new_message_ids(
        self, tmp_storage_dir: Path, sample_message: GmailMessage
    ) -> None:
        """Verify new message IDs are identified."""
        storage = EmailStorage(tmp_storage_dir)
        storage.store_message(sample_message)

        new_ids = storage.get_new_message_ids(
            [sample_message.id, "new_msg_1", "new_msg_2"]
        )

        assert sample_message.id not in new_ids
        assert "new_msg_1" in new_ids
        assert "new_msg_2" in new_ids

    def test_get_stats(
        self, tmp_storage_dir: Path, sample_messages: list[GmailMessage]
    ) -> None:
        """Verify stats are returned."""
        storage = EmailStorage(tmp_storage_dir)
        storage.store_messages(sample_messages)

        stats = storage.get_stats()

        assert stats["total_messages"] == len(sample_messages)
        assert stats["last_sync"] != ""

    def test_index_persisted(
        self, tmp_storage_dir: Path, sample_message: GmailMessage
    ) -> None:
        """Verify index is persisted across instances."""
        # Store message with first instance
        storage1 = EmailStorage(tmp_storage_dir)
        storage1.store_messages([sample_message])

        # Create new instance and check
        storage2 = EmailStorage(tmp_storage_dir)

        assert storage2.has_message(sample_message.id) is True


class TestGetDefaultStorageDir:
    """Tests for get_default_storage_dir function."""

    def test_returns_path_in_home(self) -> None:
        """Verify default path is in user's home directory."""
        result = get_default_storage_dir()

        assert isinstance(result, Path)
        assert ".mailer" in str(result)
        assert "emails" in str(result)
