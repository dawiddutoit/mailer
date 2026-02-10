"""Tests for mailer.labels module."""

from unittest.mock import MagicMock

import pytest

from mailer.labels import (
    apply_label,
    apply_labels,
    create_label,
    delete_label,
    get_label,
    get_label_by_name,
    get_or_create_label,
    list_labels,
    remove_label,
    remove_labels,
    update_label,
    _parse_label,
)
from mailer.types import GmailLabel


class TestListLabels:
    """Tests for list_labels function."""

    def test_list_labels_returns_list(self, mock_gmail_service: MagicMock) -> None:
        """Verify list_labels returns a list of GmailLabel objects."""
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "Label_1", "name": "Work", "type": "user"},
            ]
        }

        result = list_labels(mock_gmail_service)

        assert len(result) == 2
        assert isinstance(result[0], GmailLabel)
        assert result[0].id == "INBOX"
        assert result[1].name == "Work"

    def test_list_labels_empty(self, mock_gmail_service: MagicMock) -> None:
        """Verify list_labels handles empty response."""
        mock_gmail_service.users().labels().list().execute.return_value = {"labels": []}

        result = list_labels(mock_gmail_service)

        assert result == []


class TestGetLabel:
    """Tests for get_label function."""

    def test_get_label_by_id(self, mock_gmail_service: MagicMock) -> None:
        """Verify get_label returns label details."""
        mock_gmail_service.users().labels().get().execute.return_value = {
            "id": "Label_1",
            "name": "Important",
            "type": "user",
            "messageListVisibility": "show",
            "labelListVisibility": "labelShow",
        }

        result = get_label(mock_gmail_service, "Label_1")

        assert result.id == "Label_1"
        assert result.name == "Important"
        mock_gmail_service.users().labels().get.assert_called_with(userId="me", id="Label_1")


class TestCreateLabel:
    """Tests for create_label function."""

    def test_create_label_basic(self, mock_gmail_service: MagicMock) -> None:
        """Verify create_label creates a new label."""
        mock_gmail_service.users().labels().create().execute.return_value = {
            "id": "Label_123",
            "name": "New Label",
            "type": "user",
            "messageListVisibility": "show",
            "labelListVisibility": "labelShow",
        }

        result = create_label(mock_gmail_service, "New Label")

        assert result.id == "Label_123"
        assert result.name == "New Label"

    def test_create_label_with_visibility(self, mock_gmail_service: MagicMock) -> None:
        """Verify create_label respects visibility settings."""
        mock_gmail_service.users().labels().create().execute.return_value = {
            "id": "Label_456",
            "name": "Hidden Label",
            "type": "user",
            "messageListVisibility": "hide",
            "labelListVisibility": "labelHide",
        }

        result = create_label(
            mock_gmail_service,
            "Hidden Label",
            message_list_visibility="hide",
            label_list_visibility="labelHide",
        )

        assert result.message_list_visibility == "hide"
        assert result.label_list_visibility == "labelHide"


class TestUpdateLabel:
    """Tests for update_label function."""

    def test_update_label_name(self, mock_gmail_service: MagicMock) -> None:
        """Verify update_label can update label name."""
        # Mock get to return current label
        mock_gmail_service.users().labels().get().execute.return_value = {
            "id": "Label_1",
            "name": "Old Name",
            "messageListVisibility": "show",
            "labelListVisibility": "labelShow",
        }
        # Mock update to return updated label
        mock_gmail_service.users().labels().update().execute.return_value = {
            "id": "Label_1",
            "name": "New Name",
            "type": "user",
            "messageListVisibility": "show",
            "labelListVisibility": "labelShow",
        }

        result = update_label(mock_gmail_service, "Label_1", name="New Name")

        assert result.name == "New Name"


class TestDeleteLabel:
    """Tests for delete_label function."""

    def test_delete_label(self, mock_gmail_service: MagicMock) -> None:
        """Verify delete_label calls the API correctly."""
        delete_label(mock_gmail_service, "Label_123")

        mock_gmail_service.users().labels().delete.assert_called_with(userId="me", id="Label_123")


class TestApplyLabel:
    """Tests for apply_label function."""

    def test_apply_label_to_message(self, mock_gmail_service: MagicMock) -> None:
        """Verify apply_label modifies a message."""
        apply_label(mock_gmail_service, "msg_123", "Label_456")

        mock_gmail_service.users().messages().modify.assert_called_with(
            userId="me", id="msg_123", body={"addLabelIds": ["Label_456"]}
        )


class TestApplyLabels:
    """Tests for apply_labels function."""

    def test_apply_multiple_labels(self, mock_gmail_service: MagicMock) -> None:
        """Verify apply_labels applies multiple labels at once."""
        apply_labels(mock_gmail_service, "msg_123", ["Label_1", "Label_2"])

        mock_gmail_service.users().messages().modify.assert_called_with(
            userId="me", id="msg_123", body={"addLabelIds": ["Label_1", "Label_2"]}
        )

    def test_apply_labels_empty_list(self, mock_gmail_service: MagicMock) -> None:
        """Verify apply_labels does nothing with empty list."""
        apply_labels(mock_gmail_service, "msg_123", [])

        mock_gmail_service.users().messages().modify.assert_not_called()


class TestRemoveLabel:
    """Tests for remove_label function."""

    def test_remove_label_from_message(self, mock_gmail_service: MagicMock) -> None:
        """Verify remove_label modifies a message."""
        remove_label(mock_gmail_service, "msg_123", "Label_456")

        mock_gmail_service.users().messages().modify.assert_called_with(
            userId="me", id="msg_123", body={"removeLabelIds": ["Label_456"]}
        )


class TestRemoveLabels:
    """Tests for remove_labels function."""

    def test_remove_multiple_labels(self, mock_gmail_service: MagicMock) -> None:
        """Verify remove_labels removes multiple labels at once."""
        remove_labels(mock_gmail_service, "msg_123", ["Label_1", "Label_2"])

        mock_gmail_service.users().messages().modify.assert_called_with(
            userId="me", id="msg_123", body={"removeLabelIds": ["Label_1", "Label_2"]}
        )

    def test_remove_labels_empty_list(self, mock_gmail_service: MagicMock) -> None:
        """Verify remove_labels does nothing with empty list."""
        remove_labels(mock_gmail_service, "msg_123", [])

        mock_gmail_service.users().messages().modify.assert_not_called()


class TestGetLabelByName:
    """Tests for get_label_by_name function."""

    def test_find_existing_label(self, mock_gmail_service: MagicMock) -> None:
        """Verify get_label_by_name finds a label by name."""
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [
                {"id": "Label_1", "name": "Work", "type": "user"},
                {"id": "Label_2", "name": "Personal", "type": "user"},
            ]
        }

        result = get_label_by_name(mock_gmail_service, "Work")

        assert result is not None
        assert result.name == "Work"
        assert result.id == "Label_1"

    def test_find_label_case_insensitive(self, mock_gmail_service: MagicMock) -> None:
        """Verify get_label_by_name is case-insensitive."""
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [{"id": "Label_1", "name": "Work", "type": "user"}]
        }

        result = get_label_by_name(mock_gmail_service, "work")

        assert result is not None
        assert result.name == "Work"

    def test_label_not_found(self, mock_gmail_service: MagicMock) -> None:
        """Verify get_label_by_name returns None for non-existent label."""
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [{"id": "Label_1", "name": "Work", "type": "user"}]
        }

        result = get_label_by_name(mock_gmail_service, "NonExistent")

        assert result is None


class TestGetOrCreateLabel:
    """Tests for get_or_create_label function."""

    def test_get_existing_label(self, mock_gmail_service: MagicMock) -> None:
        """Verify get_or_create_label returns existing label."""
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [{"id": "Label_1", "name": "Work", "type": "user"}]
        }

        result = get_or_create_label(mock_gmail_service, "Work")

        assert result.id == "Label_1"
        mock_gmail_service.users().labels().create.assert_not_called()

    def test_create_new_label(self, mock_gmail_service: MagicMock) -> None:
        """Verify get_or_create_label creates new label if not found."""
        mock_gmail_service.users().labels().list().execute.return_value = {"labels": []}
        mock_gmail_service.users().labels().create().execute.return_value = {
            "id": "Label_New",
            "name": "New Label",
            "type": "user",
        }

        result = get_or_create_label(mock_gmail_service, "New Label")

        assert result.id == "Label_New"
        mock_gmail_service.users().labels().create.assert_called()


class TestParseLabel:
    """Tests for _parse_label function."""

    def test_parse_full_label_data(self, sample_label_data: dict) -> None:
        """Verify _parse_label handles complete label data."""
        result = _parse_label(sample_label_data)

        assert result.id == "label_123"
        assert result.name == "TestLabel"
        assert result.type == "user"
        assert result.message_list_visibility == "show"
        assert result.label_list_visibility == "labelShow"

    def test_parse_minimal_label_data(self) -> None:
        """Verify _parse_label handles minimal data with defaults."""
        minimal_data = {"id": "INBOX", "name": "INBOX"}

        result = _parse_label(minimal_data)

        assert result.id == "INBOX"
        assert result.name == "INBOX"
        assert result.type == "user"  # default
        assert result.message_list_visibility == "show"  # default
        assert result.label_list_visibility == "labelShow"  # default
