"""Example: Basic mailer library usage.

Demonstrates core functionality:
- Authentication
- Sending messages
- Listing and reading messages
- Searching messages

Requirements:
    1. Google Cloud project with Gmail API enabled
    2. OAuth credentials downloaded as credentials.json

Usage:
    python examples/basic_usage.py
"""

from mailer import (
    create_service,
    get_message,
    list_messages,
    search_messages,
    send_message,
)


def main() -> None:
    """Demonstrate basic mailer library usage."""
    # Authenticate with Gmail API
    print("Authenticating with Gmail...")
    service = create_service(
        credentials_file="credentials.json",
        token_file="token.json",
        scopes=[
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
        ],
    )
    print("✓ Authenticated successfully\n")

    # Example 1: Send a message
    print("Example 1: Sending an email")
    print("-" * 40)
    message_id = send_message(
        service,
        to="recipient@example.com",
        subject="Test from Mailer Library",
        body="This is a test email sent using the functional mailer library.",
    )
    print(f"✓ Message sent with ID: {message_id}\n")

    # Example 2: List recent messages
    print("Example 2: Listing recent messages")
    print("-" * 40)
    messages = list_messages(service, max_results=5)
    print(f"Found {len(messages)} recent messages:")
    for msg in messages:
        print(f"  • {msg.subject} (from: {msg.sender})")
    print()

    # Example 3: Get a specific message
    if messages:
        print("Example 3: Reading a specific message")
        print("-" * 40)
        first_message = messages[0]
        detailed_msg = get_message(service, first_message.id)
        print(f"Subject: {detailed_msg.subject}")
        print(f"From: {detailed_msg.sender}")
        print(f"Date: {detailed_msg.date}")
        print(f"Body preview: {detailed_msg.body[:100]}...")
        print()

    # Example 4: Search messages
    print("Example 4: Searching messages")
    print("-" * 40)
    search_results = search_messages(service, query="is:unread", max_results=10)
    print(f"Found {len(search_results)} unread messages")
    print()

    print("✓ All examples completed successfully!")


if __name__ == "__main__":
    main()
