# Mailer

A functional Python library for AI agents to interact with Gmail. Built with simplicity and composability in mind.

## Features

- **Functional Design** - Pure functions, explicit dependencies, no hidden state
- **Type Safe** - Complete type hints for all public APIs
- **AI-Agent Optimized** - Simple, predictable interfaces designed for programmatic use
- **Gmail API Wrapper** - Clean abstractions over Google's Gmail API v1
- **Message Operations** - Send, read, delete, modify emails and drafts
- **Label Management** - Create, apply, and manage Gmail labels
- **Thread Support** - Work with email threads and conversations
- **Search & Filter** - Query messages with Gmail's powerful search syntax
- **Attachment Handling** - Upload and download file attachments

## Installation

### Prerequisites

- Python 3.11 or higher
- Google Cloud project with Gmail API enabled
- OAuth 2.0 credentials from Google Cloud Console

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Quick Start

### 1. Set Up Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in your project directory

### 2. First Authentication

```python
from mailer import create_service, send_message

# First run will open browser for OAuth consent
service = create_service(
    credentials_file="credentials.json",
    token_file="token.json",
    scopes=["https://www.googleapis.com/auth/gmail.send"]
)

# Send your first email
message_id = send_message(
    service,
    to="recipient@example.com",
    subject="Hello from Mailer",
    body="This is a test email sent using the Mailer library."
)
print(f"Sent message: {message_id}")
```

### 3. Read Messages

```python
from mailer import create_service, list_messages, get_message

service = create_service("credentials.json", "token.json")

# List recent messages
messages = list_messages(service, max_results=10)

# Read a specific message
message = get_message(service, message_id=messages[0]['id'])
print(f"Subject: {message['subject']}")
print(f"From: {message['from']}")
print(f"Body: {message['body']}")
```

## Usage Examples

### Send Email with Attachment

```python
from mailer import send_message_with_attachment

message_id = send_message_with_attachment(
    service,
    to="recipient@example.com",
    subject="Report",
    body="Please find the attached report.",
    attachment_path="/path/to/report.pdf"
)
```

### Search Messages

```python
from mailer import search_messages

# Search using Gmail query syntax
messages = search_messages(
    service,
    query="from:boss@company.com is:unread",
    max_results=20
)
```

### Manage Labels

```python
from mailer import create_label, apply_label, list_labels

# Create a new label
label = create_label(service, name="Important")

# Apply label to a message
apply_label(service, message_id="msg_123", label_id=label['id'])

# List all labels
labels = list_labels(service)
```

### Work with Drafts

```python
from mailer import create_draft, update_draft, send_draft

# Create a draft
draft = create_draft(
    service,
    to="recipient@example.com",
    subject="Draft Email",
    body="This is a draft."
)

# Send the draft
send_draft(service, draft_id=draft['id'])
```

## Environment Variables

Configure the library using environment variables:

```bash
# Path to OAuth credentials file (default: ./credentials.json)
export GMAIL_CREDENTIALS_FILE="/path/to/credentials.json"

# Path to token file (default: ./token.json)
export GMAIL_TOKEN_FILE="/path/to/token.json"

# Gmail API scopes (comma-separated, default: full access)
export GMAIL_SCOPES="gmail.readonly,gmail.send"
```

## Gmail API Scopes

Choose minimal scopes for your use case:

- `gmail.readonly` - Read all messages, labels, and settings
- `gmail.send` - Send messages only
- `gmail.modify` - Read, write, and modify messages (but not delete)
- `gmail.compose` - Create, read, update, and send drafts
- `gmail.labels` - Manage mailbox labels

Full scope documentation: https://developers.google.com/gmail/api/auth/scopes

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=mailer --cov-report=html

# Specific test file
pytest tests/test_messages.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy .
```

## Architecture

This library follows functional programming principles:

- **Pure functions** - No hidden side effects
- **Explicit dependencies** - Service objects passed as parameters
- **Immutable data** - Pydantic models for structured data
- **Single responsibility** - Each function does one thing well
- **Flat structure** - Simple module organization

See [CLAUDE.md](./CLAUDE.md) for detailed architectural guidance.

## API Reference

### Authentication

- `create_service(credentials_file, token_file, scopes)` - Create authenticated Gmail service

### Messages

- `send_message(service, to, subject, body, from_email)` - Send an email
- `send_message_with_attachment(service, to, subject, body, attachment_path)` - Send with attachment
- `list_messages(service, max_results, query)` - List messages
- `get_message(service, message_id)` - Get message details
- `delete_message(service, message_id)` - Delete a message
- `search_messages(service, query, max_results)` - Search with Gmail query syntax

### Labels

- `create_label(service, name)` - Create a label
- `list_labels(service)` - List all labels
- `apply_label(service, message_id, label_id)` - Apply label to message
- `remove_label(service, message_id, label_id)` - Remove label from message

### Threads

- `list_threads(service, max_results, query)` - List email threads
- `get_thread(service, thread_id)` - Get thread details

### Drafts

- `create_draft(service, to, subject, body)` - Create draft
- `update_draft(service, draft_id, to, subject, body)` - Update draft
- `send_draft(service, draft_id)` - Send draft
- `delete_draft(service, draft_id)` - Delete draft

## Security Notes

- **Never commit credentials** - Add `credentials.json` and `token.json` to `.gitignore`
- **Use minimal scopes** - Request only the permissions you need
- **Secure token storage** - Keep `token.json` secure, it provides access to the Gmail account
- **Environment variables** - Use environment variables for credential paths in production

## Contributing

This library follows strict design principles:

1. All functions must have complete type hints
2. Keep functions pure (no side effects)
3. Pass dependencies explicitly (no global state)
4. One function per responsibility
5. Flat module structure

See [CLAUDE.md](./CLAUDE.md) for complete development guidelines.

## License

MIT License - See LICENSE file for details.

## Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth 2.0 Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Message Format Reference](https://developers.google.com/gmail/api/reference/rest/v1/users.messages)
