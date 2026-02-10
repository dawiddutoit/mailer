# Mailer

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/dawiddutoih)

A functional Python library and CLI for interacting with Gmail. Designed for AI agents and automation with local caching, SQLite storage, and incremental sync.

## Features

- **CLI Tool** - Full-featured command-line interface for email operations
- **Local Caching** - Incremental sync to avoid re-fetching emails
- **SQLite Database** - Full-text search across cached emails
- **Attachment Support** - Extract metadata and download attachments
- **Pattern Matching** - Filter emails by sender domain, glob, or regex
- **Export Formats** - JSON, JSONL, CSV output formats
- **Functional Design** - Pure functions, explicit dependencies, type-safe

## Claude Code Integration

This project ships with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills that help AI agents use the mailer CLI effectively. When you open this project in Claude Code, the skills are loaded automatically.

### Included Skills

| Skill | What It Does |
|-------|-------------|
| **mailer-cli** | Complete CLI reference -- inbox, search, send, labels, drafts, attachments, analysis commands, Gmail search syntax |

### Setup

1. Clone this repository
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
3. Open the project directory in Claude Code

Skills are stored in `.claude/skills/` and loaded automatically. Claude Code will know how to read your inbox, search emails, send messages, manage labels/drafts, and analyze email patterns without needing detailed instructions.

## Installation

```bash
# Using uv (recommended)
cd mailer
uv sync

# Or using pip
pip install -e .
```

## Quick Start

### 1. Set Up Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project → Enable **Gmail API**
3. Go to **APIs & Services > Credentials**
4. Create **OAuth 2.0 Client ID** (Desktop app type)
5. Download as `credentials.json` and place in the mailer directory
6. Go to [OAuth Consent Screen](https://console.cloud.google.com/auth/audience) → Add yourself as a **Test User**

### 2. Create `.env` File

```bash
# .env
GMAIL_CREDENTIALS_FILE=/path/to/mailer/credentials.json
GMAIL_TOKEN_FILE=/path/to/mailer/token.json
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

### 3. First Authentication

```bash
# This will open a browser for OAuth consent
mailer search "is:unread" --limit 5
```

After consent, a `token.json` is saved for future use.

## CLI Commands

### Fetching Emails

```bash
# Get emails from a domain (with caching)
mailer get emails "@example.com"

# Get emails with a limit
mailer get emails "@example.com" --limit 100

# Sync only new emails (incremental)
mailer get emails "@example.com" --sync

# Force re-fetch (bypass cache)
mailer get emails "@example.com" --no-cache

# Using Gmail query syntax
mailer get emails -q "has:attachment from:boss@company.com"

# Pattern matching options
mailer get emails "*@example.com"       # Glob pattern
mailer get emails "@example.com"        # Endswith shorthand
mailer get emails "/pattern/"           # Regex
```

### Exporting Emails

```bash
# Export to ~/.mailer/exports/ with auto-generated filename
mailer export "@example.com"
# → ~/.mailer/exports/example.com_2026-01-29.json

# Export with custom filename
mailer export "@example.com" -o my_emails.json

# Export as CSV
mailer export "@example.com" --format csv

# Export as JSONL (one JSON object per line)
mailer export "@example.com" --format jsonl
```

### Searching Emails

```bash
# Search using Gmail query syntax
mailer search "is:unread"
mailer search "from:boss@company.com subject:urgent"
mailer search "has:attachment larger:5M"

# Output as JSON
mailer search "is:important" --format json
```

### Viewing Email Details

```bash
# Show full email details
mailer show <message_id>

# Output as JSON
mailer show <message_id> --format json
```

### Working with Attachments

```bash
# List all attachments in database
mailer db attachments

# Filter by type
mailer db attachments --type application/pdf

# Download attachments from an email
mailer download <message_id>
mailer download <message_id> -o ./downloads/
mailer download <message_id> -f "specific_file.pdf"
```

### Sending Emails

```bash
mailer send recipient@example.com "Subject" "Body text"
```

### Database Operations

```bash
# Import cached emails into SQLite
mailer db import-all

# Import from specific source
mailer db import ~/.mailer/emails/@example.com
mailer db import exported_emails.json

# View database statistics
mailer db stats

# Full-text search in database
mailer db search "invoice"
mailer db search "painting OR flooring"

# Raw SQL queries
mailer db query "SELECT from_name, COUNT(*) FROM emails GROUP BY from_name"

# Refresh emails with missing data
mailer db refresh --missing-body

# List attachments
mailer db attachments --type application/pdf
```

### Label Management

```bash
# List all labels
mailer labels list
mailer labels list --format json

# Create a new label
mailer labels create "My Label"
mailer labels create "Work/Projects" --visibility hide

# Delete a label
mailer labels delete Label_123
mailer labels delete Label_123 --force

# Apply a label to a message
mailer labels apply <message_id> "Work"
mailer labels apply <message_id> Label_123

# Remove a label from a message
mailer labels remove <message_id> "Work"
```

### Draft Management

```bash
# List all drafts
mailer drafts list
mailer drafts list --limit 10
mailer drafts list --format json

# Show a specific draft
mailer drafts show <draft_id>

# Create a new draft
mailer drafts create "user@example.com" "Subject" "Body text"
mailer drafts create "user@example.com" "Subject" "Body" --cc "cc@example.com"

# Send a draft
mailer drafts send <draft_id>

# Delete a draft
mailer drafts delete <draft_id>
mailer drafts delete <draft_id> --force
```

### Storage Status

```bash
# View cache status
mailer status
```

## File Structure

```
~/.mailer/
├── emails.db              # SQLite database with full-text search
├── emails/                # Cached email JSON files
│   └── @example.com/      # Organized by pattern
│       ├── index.json     # Cache index
│       └── messages/      # Individual message files
│           ├── abc123.json
│           └── def456.json
└── exports/               # Exported files
    ├── example.com_2026-01-29.json
    └── custom_export.csv
```

## Database Schema

```sql
-- Main emails table
emails (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    from_email TEXT,
    from_name TEXT,
    from_domain TEXT,
    to_emails TEXT,        -- JSON array
    cc_emails TEXT,        -- JSON array
    subject TEXT,
    body TEXT,             -- Plain text
    body_html TEXT,        -- HTML version
    snippet TEXT,
    label_ids TEXT,        -- JSON array
    date_header TEXT,      -- RFC 2822 date
    timestamp INTEGER,     -- Unix ms
    size_estimate INTEGER,
    has_attachments INTEGER,
    created_at TEXT,
    updated_at TEXT
)

-- Attachments table
attachments (
    id INTEGER PRIMARY KEY,
    message_id TEXT,       -- FK to emails.id
    attachment_id TEXT,    -- Gmail attachment ID
    filename TEXT,
    mime_type TEXT,
    size INTEGER
)

-- Full-text search (FTS5)
emails_fts (subject, body, from_email)
```

## Python API

### Authentication

```python
from mailer import create_service

# Create authenticated service
service = create_service(
    credentials_file="credentials.json",
    token_file="token.json"
)

# Or use environment variables
service = create_service_from_env()
```

### Reading Emails

```python
from mailer import create_service, list_messages, get_message, list_message_ids

service = create_service("credentials.json", "token.json")

# List recent messages with full content
messages = list_messages(service, max_results=10)

# List only message IDs (faster, with pagination)
ids = list_message_ids(service, max_results=100, query="from:example.com")

# Get a specific message
msg = get_message(service, message_id="abc123")
print(f"Subject: {msg.subject}")
print(f"From: {msg.from_email}")
print(f"Date: {msg.date_formatted}")
print(f"Body: {msg.body}")
print(f"Attachments: {len(msg.attachments)}")
```

### Sending Emails

```python
from mailer import create_service, send_message

service = create_service("credentials.json", "token.json")

message_id = send_message(
    service,
    to="recipient@example.com",
    subject="Hello",
    body="This is the email body."
)
```

### Downloading Attachments

```python
from mailer import create_service, get_message, download_attachment

service = create_service("credentials.json", "token.json")

msg = get_message(service, "message_id")

for att in msg.attachments:
    data = download_attachment(service, msg.id, att.attachment_id)
    with open(att.filename, "wb") as f:
        f.write(data)
```

### Working with Threads

Threads group related messages (original + all replies) into a single conversation:

```python
from mailer import create_service
from mailer.threads import get_thread, list_threads, search_threads

service = create_service("credentials.json", "token.json")

# Get a specific thread with all messages
thread = get_thread(service, "thread_id")
print(f"Thread has {len(thread.messages)} messages")

for msg in thread.messages:
    print(f"From: {msg.from_email}")
    print(f"Subject: {msg.subject}")
    print(f"Reply only: {msg.reply_text}")  # Just the latest reply, no quoted text
    print("---")

# List recent threads
threads = list_threads(service, max_results=10)

# Search threads with Gmail query
threads = search_threads(service, "from:boss@company.com", max_results=20)
```

### Extracting Reply Text

When working with email threads, `reply_text` gives you just the new content without quoted replies:

```python
from mailer.parsing import extract_latest_reply

# Full email body with quoted text
body = """
Thanks for the update!

On Mon, Jan 27, 2026, John <john@example.com> wrote:
> Here's the report you requested.
> Let me know if you have questions.
"""

# Extract only the latest reply
reply = extract_latest_reply(body)
print(reply)  # "Thanks for the update!"
```

### Working with Labels

```python
from mailer import create_service
from mailer.labels import (
    list_labels, create_label, delete_label,
    apply_label, remove_label, get_or_create_label
)

service = create_service("credentials.json", "token.json")

# List all labels
labels = list_labels(service)
for label in labels:
    print(f"{label.name} ({label.id})")

# Create a new label
new_label = create_label(service, "Project/Important")

# Apply a label to a message
apply_label(service, "message_id", new_label.id)

# Remove a label from a message
remove_label(service, "message_id", new_label.id)

# Get or create a label by name
label = get_or_create_label(service, "Work")
```

### Working with Drafts

```python
from mailer import create_service
from mailer.drafts import (
    list_drafts, create_draft, update_draft, send_draft, delete_draft
)

service = create_service("credentials.json", "token.json")

# List all drafts
drafts = list_drafts(service, max_results=10)
for draft in drafts:
    print(f"{draft.id}: {draft.message.subject}")

# Create a draft
draft = create_draft(
    service,
    to="recipient@example.com",
    subject="Draft Subject",
    body="This is the draft body.",
    cc="cc@example.com"
)
print(f"Created draft: {draft.id}")

# Update a draft
updated = update_draft(
    service,
    draft_id=draft.id,
    to="recipient@example.com",
    subject="Updated Subject",
    body="Updated body content."
)

# Send the draft
message_id = send_draft(service, draft.id)
print(f"Sent! Message ID: {message_id}")

# Delete a draft
delete_draft(service, "draft_id")
```

### File-based Attachment Downloads

```python
from pathlib import Path
from mailer import create_service, get_message
from mailer.attachments import download_attachment_to_file, download_all_attachments

service = create_service("credentials.json", "token.json")

# Get a message with attachments
msg = get_message(service, "message_id")

# Download a single attachment to file
if msg.attachments:
    att = msg.attachments[0]
    path = download_attachment_to_file(
        service, msg.id, att.attachment_id, Path("./downloads") / att.filename
    )
    print(f"Downloaded: {path}")

# Download all attachments from a message
paths = download_all_attachments(
    service, msg.id, msg.attachments, Path("./downloads")
)
print(f"Downloaded {len(paths)} files")
```

### Using the Database

```python
from mailer.database import create_database, search_emails, get_stats

conn = create_database("~/.mailer/emails.db")

# Full-text search
results = search_emails(conn, "invoice", limit=20)

# Get statistics
stats = get_stats(conn)
print(f"Total emails: {stats['total_emails']}")
print(f"Top senders: {stats['top_senders']}")
```

### Using the Cache

```python
from mailer.storage import EmailStorage

storage = EmailStorage("~/.mailer/emails/@example.com")

# Check what's cached
print(storage.get_stats())

# Load cached messages
messages = storage.load_all_messages()

# Check if a message is cached
if not storage.has_message("abc123"):
    # Fetch and store
    msg = get_message(service, "abc123")
    storage.store_message(msg)
```

## Data Models

### GmailMessage

```python
class GmailMessage:
    id: str
    thread_id: str
    label_ids: list[str]
    snippet: str
    from_email: str           # "Name <email@example.com>"
    to: list[str]
    cc: list[str]
    subject: str
    body: str                 # Plain text (preferred)
    body_html: str            # HTML version
    reply_text: str           # Just the latest reply (no quoted text) - populated in threads
    date: str                 # RFC 2822 format
    timestamp: int            # Unix milliseconds
    attachments: list[GmailAttachment]
    size_estimate: int

    # Computed properties
    has_attachments: bool
    datetime_utc: datetime
    date_formatted: str       # "YYYY-MM-DD HH:MM"
```

### GmailAttachment

```python
class GmailAttachment:
    attachment_id: str        # For downloading
    message_id: str           # Parent message
    filename: str
    mime_type: str
    size: int                 # Bytes
```

### GmailThread

```python
class GmailThread:
    id: str                   # Thread ID
    snippet: str              # Preview of thread content
    messages: list[GmailMessage]  # All messages in thread (chronological)
```

Note: Each message in a thread includes `reply_text` which contains just the new content without quoted replies.

## Architecture

```
mailer/
├── __init__.py          # Public API exports
├── cli.py               # Click-based CLI
├── auth.py              # OAuth 2.0 authentication
├── messages.py          # Message operations (send, list, get, delete)
├── threads.py           # Thread/conversation operations (full content + reply parsing)
├── parsing.py           # Email parsing (RFC 5322, Gmail payload, reply extraction)
├── labels.py            # Label management (stub)
├── drafts.py            # Draft operations (stub)
├── attachments.py       # Attachment file operations (stub)
├── storage.py           # Local JSON caching
├── database.py          # SQLite storage + FTS
├── types.py             # Pydantic models
├── errors.py            # Exception types
└── formatters.py        # Output formatting utilities
```

### Design Principles

1. **Functional** - Pure functions, no hidden state
2. **Explicit** - All dependencies passed as parameters
3. **Type-safe** - Complete type hints, Pydantic models
4. **Incremental** - Cache locally, sync only what's needed
5. **AI-friendly** - Simple interfaces, structured output

## Gmail Query Syntax

Use Gmail's search syntax with `-q` or `--query`:

```bash
# Unread emails
mailer search "is:unread"

# From specific sender
mailer search "from:boss@company.com"

# With attachments
mailer search "has:attachment"

# Date range
mailer search "after:2024/01/01 before:2024/12/31"

# Subject contains
mailer search "subject:invoice"

# Multiple conditions
mailer search "from:company.com has:attachment is:unread"

# Size filters
mailer search "larger:5M"
mailer search "smaller:100K"
```

## Security

- **Never commit credentials** - `credentials.json` and `token.json` are in `.gitignore`
- **Use test users** - Unverified apps require explicit test user approval
- **Minimal scopes** - Request only needed permissions
- **Local storage** - Emails cached locally in `~/.mailer/`

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run mypy .
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_CREDENTIALS_FILE` | `./credentials.json` | OAuth credentials file |
| `GMAIL_TOKEN_FILE` | `./token.json` | OAuth token storage |
| `GMAIL_CLIENT_ID` | - | OAuth client ID |

## License

MIT License
