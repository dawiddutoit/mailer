# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python library designed to provide reusable code for AI agents to create, read, and interact with Gmail. The library follows functional programming principles and is modular and easy to integrate into other AI-powered tools.

## Development Commands

### Package Management
- Install dependencies: `uv sync` or `pip install -e .`
- Add a new dependency: `uv add <package>` (recommended) or manually edit `pyproject.toml`

### Testing
- Run all tests: `pytest`
- Run a single test file: `pytest tests/test_<name>.py`
- Run a specific test: `pytest tests/test_<name>.py::test_function_name`
- Run with coverage: `pytest --cov=. --cov-report=html`

### Code Quality
- Format code: `ruff format .`
- Lint code: `ruff check .`
- Fix auto-fixable lint issues: `ruff check --fix .`
- Type checking: `mypy .`

## Architecture

### Core Design Principles

#### Single Responsibility Principle (SRP)
- **One Function, One Job**: Each function must do exactly one thing and do it well
- **One Module, One Domain**: Each module should handle one Gmail domain (e.g., `messages.py` for all message operations)
- **No God Objects**: Avoid classes or modules that do too many things
- **Clear Boundaries**: Functions should have clear inputs and outputs with no hidden dependencies

#### Functional Programming Principles
- **Pure Functions**: Functions should be pure whenever possible (same input → same output, no side effects)
- **Immutability**: Prefer immutable data structures; avoid modifying inputs
- **Composition**: Build complex operations by composing simple functions
- **Explicit Dependencies**: All dependencies (API clients, configs) must be passed as parameters, not global state
- **Avoid Classes**: Prefer functions over classes unless the class provides clear value (e.g., data models)
- **Type Safety**: All functions must have complete type hints (parameters and return values)

#### Structure
- **Flat Architecture**: Use a flat module structure - no nested directories
- **Domain Modules**: One file per Gmail domain (e.g., `auth.py`, `messages.py`, `labels.py`, `threads.py`)
- **Small, Focused Functions**: Functions should be small (ideally < 20 lines) and do one thing
- **AI-Agent First**: All interfaces should be simple and intuitive for AI agents to use programmatically
- **Error Handling**: Return explicit Result types or raise clear exceptions that AI agents can parse

### Expected Flat Structure
```
mailer/
├── __init__.py         # Public API exports
├── auth.py             # Authentication and credential management
├── messages.py         # Message operations (send, read, delete, modify)
├── labels.py           # Label operations (create, list, apply, remove)
├── threads.py          # Thread operations (list, read, modify)
├── drafts.py           # Draft operations (create, update, send, delete)
├── attachments.py      # Attachment operations (upload, download)
├── search.py           # Search and filter operations
├── types.py            # Shared type definitions and Pydantic models
└── errors.py           # Error types and handling utilities
```

### Anti-Patterns to Avoid
- ❌ Nested directory structures (`mailer/messages/send.py`)
- ❌ Classes with multiple methods doing different things
- ❌ Functions with side effects hidden from the signature
- ❌ Mutable global state or singletons
- ❌ Functions that do more than one thing
- ❌ Missing type hints
- ❌ Functions longer than 30 lines (usually indicates multiple responsibilities)

## Gmail API Patterns

### Authentication
Gmail API uses OAuth 2.0 with credential files and tokens:
- `credentials.json` - OAuth client configuration (downloaded from Google Cloud Console)
- `token.json` - User authorization token (generated on first auth, refreshed automatically)

**Environment variables:**
- `GMAIL_CREDENTIALS_FILE` - Path to credentials.json (default: `./credentials.json`)
- `GMAIL_TOKEN_FILE` - Path to token.json (default: `./token.json`)
- `GMAIL_SCOPES` - Comma-separated list of OAuth scopes (default: Gmail read/write)

### Gmail API Service
All Gmail operations require an authenticated service object:
```python
from googleapiclient.discovery import build

def create_service(credentials):
    """Create Gmail API service from credentials."""
    return build('gmail', 'v1', credentials=credentials)
```

### Message Format
Gmail uses a unique message format with base64url-encoded content:
- Messages have IDs and thread IDs
- Message bodies are base64url-encoded
- Attachments are separate parts with their own encoding
- Labels are applied as arrays of label IDs

## Code Examples

### ✅ Good: Single Responsibility + Functional
```python
from googleapiclient.discovery import Resource
from typing import Optional

def send_message(
    service: Resource,
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None
) -> dict:
    """Send an email message. One function, one job."""
    message = create_mime_message(to, subject, body, from_email)
    encoded_message = encode_message(message)
    result = service.users().messages().send(
        userId='me',
        body={'raw': encoded_message}
    ).execute()
    return result

def create_mime_message(to: str, subject: str, body: str, from_email: Optional[str] = None) -> str:
    """Create MIME message. Separate function for separate responsibility."""
    # MIME message creation logic
    ...

def encode_message(message: str) -> str:
    """Encode message to base64url format."""
    return base64.urlsafe_b64encode(message.encode()).decode()
```

### ❌ Bad: Multiple Responsibilities + Stateful
```python
class EmailManager:
    def __init__(self, credentials_file: str):
        self.service = self._create_service(credentials_file)  # Hidden state
        self.last_message = None  # Mutable state

    def send_and_archive(self, to: str, subject: str, body: str):
        # Does two things! Should be two separate functions
        msg = self._send(to, subject, body)
        self.last_message = msg  # Side effect
        self._archive(msg['id'])
        return msg
```

### Function Composition Example
```python
from typing import Callable
from functools import partial

# Small, focused functions
def create_credentials(credentials_file: str, token_file: str, scopes: list[str]):
    """Create Gmail credentials. One job."""
    # OAuth flow logic
    ...

def create_service(credentials) -> Resource:
    """Create Gmail API service."""
    return build('gmail', 'v1', credentials=credentials)

def send_message(service: Resource, to: str, subject: str, body: str) -> str:
    """Send message, return message ID."""
    message = create_mime_message(to, subject, body)
    result = service.users().messages().send(userId='me', body=message).execute()
    return result['id']

# Compose them together
def send_email_authenticated(
    credentials_file: str,
    token_file: str,
    to: str,
    subject: str,
    body: str
) -> str:
    """Compose smaller functions to build complete workflow."""
    credentials = create_credentials(credentials_file, token_file, ['gmail.send'])
    service = create_service(credentials)
    message_id = send_message(service, to, subject, body)
    return message_id
```

## Important Notes

- Never commit Gmail credentials (`credentials.json`) or tokens (`token.json`) to the repository
- All Gmail API calls should handle rate limits and quota errors gracefully
- Functions should return structured data (Pydantic models preferred) rather than raw API responses
- Include retry logic for transient failures in separate, composable retry functions
- All public functions must have complete type hints (parameters and return types)
- Dependencies (like `Resource` service objects) must always be passed as parameters, never as globals
- Keep functions pure when possible - no hidden side effects or mutable state
- Message IDs and Thread IDs are strings, not integers
- Always use `userId='me'` for the authenticated user's mailbox

## Gmail API Scopes

Choose minimal scopes needed for your operations:
- `gmail.readonly` - Read all messages, labels, and settings
- `gmail.send` - Send messages only
- `gmail.modify` - Read, write, and modify (but not delete) messages
- `gmail.compose` - Create, read, update, and send drafts
- `gmail.labels` - Manage mailbox labels
- Full scope list: https://developers.google.com/gmail/api/auth/scopes

## Testing Strategy

- Mock all Gmail API service calls (never call real Gmail API in tests)
- Use `unittest.mock.Mock` to create mock service objects
- Test edge cases: empty responses, rate limits, network errors
- Verify base64url encoding/decoding correctness
- Test MIME message construction with various content types
