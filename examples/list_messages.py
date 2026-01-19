"""Example: List recent messages from Gmail.

This example demonstrates:
1. Authenticating with Gmail API
2. Listing recent messages
3. Displaying message metadata

Before running:
1. Download credentials.json from Google Cloud Console
2. Enable Gmail API for your project
3. Place credentials.json in the project directory
"""

from mailer import create_service, list_messages


def main() -> None:
    """List recent messages from mailbox."""
    # Create authenticated service
    service = create_service(
        credentials_file="credentials.json",
        token_file="token.json",
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )

    # List recent messages
    try:
        messages = list_messages(service, max_results=10)

        print(f"Found {len(messages)} recent messages:\n")

        for i, msg in enumerate(messages, 1):
            print(f"{i}. [{msg.id}]")
            print(f"   From: {msg.from_email}")
            print(f"   Subject: {msg.subject}")
            print(f"   Snippet: {msg.snippet[:50]}...")
            print()

    except Exception as e:
        print(f"✗ Failed to list messages: {e}")


if __name__ == "__main__":
    main()
