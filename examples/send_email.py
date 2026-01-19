"""Example: Send a simple email using the mailer library.

This example demonstrates:
1. Creating an authenticated Gmail service
2. Sending a basic email message
3. Handling authentication flow

Before running:
1. Download credentials.json from Google Cloud Console
2. Enable Gmail API for your project
3. Place credentials.json in the project directory
"""

from mailer import create_service, send_message


def main() -> None:
    """Send a test email."""
    # Create authenticated service
    # First run will open browser for OAuth consent
    service = create_service(
        credentials_file="credentials.json",
        token_file="token.json",
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )

    # Send email
    try:
        message_id = send_message(
            service,
            to="recipient@example.com",
            subject="Hello from Mailer",
            body="This is a test email sent using the mailer library.\n\nBest regards,\nYour AI Agent",
        )
        print(f"✓ Email sent successfully!")
        print(f"  Message ID: {message_id}")
    except Exception as e:
        print(f"✗ Failed to send email: {e}")


if __name__ == "__main__":
    main()
