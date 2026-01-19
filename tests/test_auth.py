"""Tests for authentication functions."""

import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

from mailer.auth import create_credentials, create_service, validate_service
from mailer.errors import AuthenticationError


class TestCreateCredentials:
    """Tests for create_credentials function."""

    def test_creates_credentials_from_existing_token(
        self, tmp_path: Path, mock_credentials: Mock
    ) -> None:
        """Test loading credentials from existing token file."""
        # Setup
        token_file = tmp_path / "token.json"
        token_file.write_text('{"token": "test"}')

        with patch(
            "mailer.auth.Credentials.from_authorized_user_file"
        ) as mock_from_file:
            mock_from_file.return_value = mock_credentials

            # Execute
            creds = create_credentials(
                credentials_file="credentials.json",
                token_file=str(token_file),
                scopes=["gmail.readonly"],
            )

            # Assert
            assert creds == mock_credentials
            mock_from_file.assert_called_once()

    def test_raises_error_when_credentials_file_missing(self, tmp_path: Path) -> None:
        """Test that missing credentials file raises error."""
        with pytest.raises(AuthenticationError, match="Credentials file not found"):
            create_credentials(
                credentials_file="nonexistent.json",
                token_file=str(tmp_path / "token.json"),
            )


class TestCreateService:
    """Tests for create_service function."""

    def test_creates_service_with_valid_credentials(
        self, mock_credentials: Mock
    ) -> None:
        """Test creating Gmail service with valid credentials."""
        with patch("mailer.auth.create_credentials") as mock_create_creds:
            mock_create_creds.return_value = mock_credentials

            with patch("mailer.auth.build") as mock_build:
                mock_service = MagicMock()
                mock_build.return_value = mock_service

                # Execute
                service = create_service(
                    credentials_file="creds.json", token_file="token.json"
                )

                # Assert
                assert service == mock_service
                mock_build.assert_called_once_with(
                    "gmail", "v1", credentials=mock_credentials
                )


class TestValidateService:
    """Tests for validate_service function."""

    def test_returns_true_for_valid_service(self, mock_gmail_service: Mock) -> None:
        """Test validation passes for working service."""
        # Setup
        mock_profile = {"emailAddress": "test@example.com"}
        mock_gmail_service.users().getProfile().execute.return_value = mock_profile

        # Execute & Assert
        assert validate_service(mock_gmail_service) is True

    def test_returns_false_for_invalid_service(self, mock_gmail_service: Mock) -> None:
        """Test validation fails for non-working service."""
        # Setup
        mock_gmail_service.users().getProfile().execute.side_effect = Exception(
            "API Error"
        )

        # Execute & Assert
        assert validate_service(mock_gmail_service) is False
