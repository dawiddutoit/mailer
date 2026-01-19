"""Authentication functions for Gmail API."""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from mailer.errors import AuthenticationError


DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def create_credentials(
    credentials_file: str | None = None,
    token_file: str | None = None,
    scopes: list[str] | None = None,
) -> Credentials:
    """Create Gmail API credentials using OAuth 2.0 flow.

    Args:
        credentials_file: Path to credentials.json from Google Cloud Console
        token_file: Path to store/load the authorization token
        scopes: List of Gmail API scopes to request

    Returns:
        Authenticated credentials object

    Raises:
        AuthenticationError: If authentication fails
    """
    resolved_creds_file = credentials_file or os.getenv(
        "GMAIL_CREDENTIALS_FILE", "credentials.json"
    )
    resolved_token_file = token_file or os.getenv("GMAIL_TOKEN_FILE", "token.json")
    resolved_scopes = scopes or DEFAULT_SCOPES

    creds = None

    # Load existing token if available
    token_path = Path(resolved_token_file)
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_path), resolved_scopes
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to load token file: {e}") from e

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise AuthenticationError(f"Failed to refresh token: {e}") from e
        else:
            # Run OAuth flow
            creds_path = Path(resolved_creds_file)
            if not creds_path.exists():
                raise AuthenticationError(
                    f"Credentials file not found: {resolved_creds_file}"
                )

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), resolved_scopes
                )
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise AuthenticationError(f"OAuth flow failed: {e}") from e

        # Save credentials for future use
        try:
            token_path.write_text(creds.to_json())
        except Exception as e:
            raise AuthenticationError(f"Failed to save token: {e}") from e

    return creds


def create_service(
    credentials_file: str | None = None,
    token_file: str | None = None,
    scopes: list[str] | None = None,
) -> Resource:
    """Create authenticated Gmail API service.

    Args:
        credentials_file: Path to credentials.json from Google Cloud Console
        token_file: Path to store/load the authorization token
        scopes: List of Gmail API scopes to request

    Returns:
        Authenticated Gmail API service object

    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        creds = create_credentials(credentials_file, token_file, scopes)
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        if isinstance(e, AuthenticationError):
            raise
        raise AuthenticationError(f"Failed to create Gmail service: {e}") from e


def create_service_from_env() -> Resource:
    """Create Gmail API service using environment variables for configuration."""
    return create_service()


def validate_service(service: Resource) -> bool:
    """Validate that Gmail service is authenticated and functional."""
    try:
        # Try to get user profile as a simple validation
        service.users().getProfile(userId="me").execute()
        return True
    except Exception:
        return False
