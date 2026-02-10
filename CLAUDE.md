# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## CRITICAL: Direct Action - No Exploration Required

**When asked to use the mailer tool, ACT IMMEDIATELY. Do not:**
- ❌ Say "let me check the mailer tool's capabilities"
- ❌ Say "let me first understand the structure"
- ❌ Read source files before running commands
- ❌ Read SKILL.md or CLAUDE.md before acting

**Instead, JUST USE the CLI directly:**
```bash
# Most common commands (in order of usefulness)
mailer inbox                              # See recent inbox (20 emails)
mailer inbox --unread                     # Only unread emails
mailer search "from:fnb subject:payment"  # Gmail query search
mailer show <message_id>                  # View full email
mailer send to@email.com "Subject" "Body" # Send email
mailer list --from @company.com           # List emails from domain
mailer download <message_id>              # Download attachments

# Database operations (for local search after syncing)
mailer db search "keyword"                # Full-text search in SQLite
mailer db stats                           # View database statistics
```

**Gmail search syntax** (used with `search` and `list` commands):
- `from:sender@domain.com` - From sender
- `subject:keyword` - Subject contains
- `is:unread` - Unread only
- `has:attachment` - Has attachments
- `after:2024/01/01` - Date filter
- Combine: `from:fnb subject:payment has:attachment`

**Authentication:** Automatic via `~/.mailer/token.json`. First run triggers OAuth flow.

---

## Project Overview

A Python library and CLI for AI agents to interact with Gmail. Features local caching, SQLite storage with full-text search, and incremental sync.

## Claude Code Skills

This project ships with Claude Code skills in `.claude/skills/` that help AI agents use the mailer CLI effectively with minimal back-and-forth. Skills are automatically available when Claude Code runs in this project directory.

### Available Skills

| Skill | Purpose | When It Activates |
|-------|---------|-------------------|
| **mailer-cli** | Complete CLI reference with commands, Gmail search syntax, workflows | "check email", "search inbox", "send email", "download attachments" |

### Skill Structure

```
.claude/skills/
└── mailer-cli/
    ├── SKILL.md                   # Main skill with quick reference
    └── references/
        └── cli-reference.md       # Complete command reference
```

### How Users Get Skills

Skills are part of the repository. When a user clones the project and opens it with Claude Code, the skills are automatically loaded from `.claude/skills/`. No manual installation needed.

## Skill

Use `mailer-codebase-understanding` when reasoning about architecture, implementing features, or debugging.

## Quick Reference

```bash
# Development
uv sync                    # Install dependencies
uv run pytest             # Run tests
uv run ruff format .      # Format code
uv run ruff check .       # Lint
uv run mypy .             # Type check

# CLI Usage (most useful first)
mailer inbox                      # Recent inbox emails
mailer inbox --unread -n 50       # 50 unread emails
mailer search "from:boss"         # Search with Gmail syntax
mailer show MESSAGE_ID            # View full email
mailer list --from @domain.com    # List emails from domain
mailer send to@x.com "Subj" "Msg" # Send email
mailer download MESSAGE_ID        # Download attachments
mailer export "@domain.com"       # Export to ~/.mailer/exports/
mailer db search "keyword"        # Full-text search in database
```

## Current Implementation Status

### ✅ Fully Implemented
| Module | Functions |
|--------|-----------|
| `auth.py` | `create_service`, `create_credentials`, `create_service_from_env` |
| `messages.py` | `send_message`, `list_messages`, `list_message_ids`, `get_message`, `delete_message`, `download_attachment` |
| `threads.py` | `list_thread_ids`, `list_threads`, `get_thread`, `get_thread_messages`, `search_threads` |
| `parsing.py` | `parse_raw_email`, `parse_gmail_payload`, `extract_latest_reply` |
| `labels.py` | `list_labels`, `get_label`, `create_label`, `update_label`, `delete_label`, `apply_label`, `remove_label`, `get_label_by_name`, `get_or_create_label` |
| `drafts.py` | `list_drafts`, `list_draft_ids`, `get_draft`, `create_draft`, `update_draft`, `send_draft`, `delete_draft` |
| `attachments.py` | `download_attachment_to_file`, `download_all_attachments`, `get_attachment_content`, `get_attachment_size` |
| `storage.py` | `EmailStorage` class for local JSON caching |
| `database.py` | SQLite with FTS5, `create_database`, `insert_emails`, `search_emails`, `get_stats` |
| `cli.py` | Full CLI with `inbox`, `search`, `show`, `send`, `list`, `download`, `get`, `export`, `db`, `labels`, `drafts`, `analyze` commands |
| `types.py` | `GmailMessage`, `GmailAttachment`, `GmailThread`, `GmailLabel`, `GmailDraft`, `ParsedEmail`, `ParsedAttachment` models |

### Key Data Flow

```
Gmail API
    ↓
messages.py (fetch with pagination)
    ↓
storage.py (JSON cache in ~/.mailer/emails/)
    ↓
database.py (SQLite in ~/.mailer/emails.db)
    ↓
cli.py (user interface)
```

## Architecture

```
mailer/
├── __init__.py         # Public API exports
├── cli.py              # Click CLI (main entry point)
├── auth.py             # OAuth 2.0 authentication
├── messages.py         # Core Gmail operations
│   ├── send_message()
│   ├── list_message_ids()  # Pagination support
│   ├── list_messages()     # Full content fetch
│   ├── get_message()       # Single message with body + attachments
│   └── download_attachment()
├── threads.py          # Thread/conversation operations
│   ├── list_thread_ids()   # Pagination support
│   ├── list_threads()      # Full content fetch
│   ├── get_thread()        # Single thread with all messages
│   ├── get_thread_messages()  # Convenience for just messages
│   └── search_threads()    # Gmail query search
├── parsing.py          # Email parsing utilities
│   ├── parse_raw_email()   # Parse RFC 5322 bytes
│   ├── parse_gmail_payload()  # Parse Gmail API payload
│   └── extract_latest_reply()  # Strip quoted text from replies
├── labels.py           # Label management
│   ├── list_labels(), get_label()
│   ├── create_label(), update_label(), delete_label()
│   ├── apply_label(), remove_label()
│   └── get_label_by_name(), get_or_create_label()
├── drafts.py           # Draft management
│   ├── list_drafts(), list_draft_ids(), get_draft()
│   ├── create_draft(), update_draft()
│   ├── send_draft(), delete_draft()
├── attachments.py      # File-based attachment operations
│   ├── download_attachment_to_file()
│   ├── download_all_attachments()
│   └── get_attachment_content(), get_attachment_size()
├── storage.py          # Local JSON file caching
│   └── EmailStorage    # Index + messages/ directory
├── database.py         # SQLite + FTS5
│   ├── create_database()
│   ├── insert_email()
│   ├── search_emails()
│   └── get_stats()
├── types.py            # Pydantic models
│   ├── GmailMessage    # Full message with computed properties
│   ├── GmailAttachment # Attachment metadata
│   ├── GmailThread     # Thread with messages
│   ├── ParsedEmail     # Parser output model
│   └── ParsedAttachment  # Parser attachment model
├── errors.py           # Exception hierarchy
└── formatters.py       # Output formatting utilities
```

## Key Design Decisions

### 1. Two-Layer Caching

**JSON Cache (`~/.mailer/emails/{pattern}/`)**
- Individual JSON files per message
- Fast lookup by message ID
- Organized by sender pattern
- Used for incremental sync

**SQLite Database (`~/.mailer/emails.db`)**
- Full-text search (FTS5)
- Aggregation queries
- Attachment tracking
- Single file, portable

### 2. Pagination Handling

Gmail API returns max 500 messages per request. `list_message_ids()` handles this:

```python
def list_message_ids(service, max_results=100, query=None) -> list[str]:
    all_ids = []
    page_token = None
    while True:
        results = service.users().messages().list(
            userId="me", maxResults=min(max_results, 500),
            q=query, pageToken=page_token
        ).execute()
        all_ids.extend(msg["id"] for msg in results.get("messages", []))
        page_token = results.get("nextPageToken")
        if not page_token or (max_results > 0 and len(all_ids) >= max_results):
            break
    return all_ids[:max_results] if max_results > 0 else all_ids
```

### 3. Body Extraction

Gmail messages have complex MIME structures. `_find_body_part()` recursively searches:

```
multipart/mixed
├── multipart/related
│   ├── multipart/alternative
│   │   ├── text/plain     ← Preferred
│   │   └── text/html      ← Fallback (converted to text)
│   └── image/jpeg (inline)
└── application/pdf (attachment)
```

### 4. Attachment Handling

Attachments are NOT downloaded by default (bandwidth). Only metadata is extracted:

```python
class GmailAttachment:
    attachment_id: str    # For download API
    message_id: str       # Parent message
    filename: str
    mime_type: str
    size: int
```

Download on demand:
```python
data = download_attachment(service, message_id, attachment_id)
```

### 5. Export Directory

Files go to `~/.mailer/exports/` by default, not current directory:
- Auto-generated names: `{pattern}_{date}.json`
- Custom names: `-o filename.json`

## CLI Command Structure

Commands are ordered by usefulness (most common first):

```
mailer
├── inbox                    # Recent inbox emails (most useful!)
├── search QUERY             # Gmail API search
├── show MESSAGE_ID          # View full email
├── send TO SUBJECT BODY     # Send email
├── list [QUERY]             # List emails with filtering
├── download MESSAGE_ID      # Download attachments
├── get emails [PATTERN]     # Fetch with caching (legacy)
├── sync PATTERN             # Incremental sync
├── status                   # Cache status
├── export PATTERN           # Export to ~/.mailer/exports/
├── db                       # Database operations
│   ├── search QUERY         # FTS5 full-text search
│   ├── stats                # Database statistics
│   ├── import SOURCE        # Import JSON/cache to SQLite
│   ├── import-all           # Import all cached emails
│   ├── query SQL            # Raw SQL
│   ├── refresh [IDS]        # Re-fetch emails
│   └── attachments          # List attachments
├── labels                   # Label management
│   ├── list                 # List all labels
│   ├── create NAME          # Create label
│   ├── delete LABEL_ID      # Delete label
│   ├── apply MSG_ID LABEL   # Apply label to message
│   └── remove MSG_ID LABEL  # Remove label from message
├── drafts                   # Draft management
│   ├── list                 # List drafts
│   ├── show DRAFT_ID        # View draft
│   ├── create TO SUBJ BODY  # Create draft
│   ├── send DRAFT_ID        # Send draft
│   └── delete DRAFT_ID      # Delete draft
└── analyze                  # Email analysis
    ├── sender-stats         # Top senders
    ├── domain-stats         # Emails by domain
    └── timeline             # Volume over time
```

## Pydantic Models

### GmailMessage

```python
class GmailMessage(BaseModel):
    id: str
    thread_id: str
    label_ids: list[str]
    snippet: str
    from_email: str           # "Name <email>"
    to: list[str]
    cc: list[str]
    subject: str
    body: str                 # Plain text
    body_html: str            # HTML version
    date: str                 # RFC 2822
    timestamp: int            # Unix ms (from internalDate)
    attachments: list[GmailAttachment]
    size_estimate: int

    # Computed
    has_attachments: bool
    datetime_utc: datetime
    date_formatted: str       # "YYYY-MM-DD HH:MM"
```

## Testing Strategy

- Mock Gmail API service calls (never call real API in tests)
- Test pagination with mock `nextPageToken`
- Test MIME parsing with various message structures
- Test FTS5 queries in SQLite
- Test incremental sync logic

## Common Tasks

### Add New CLI Command

```python
@main.command("newcmd")
@click.argument("arg")
@click.option("--opt", help="Description")
def new_command(arg: str, opt: str | None) -> None:
    """Command description."""
    credentials_file, token_file = get_credentials_paths()
    service = create_service(credentials_file, token_file)
    # ... implementation
```

### Add New Message Field

1. Update `GmailMessage` in `types.py`
2. Extract in `get_message()` in `messages.py`
3. Update database schema in `database.py`
4. Update `insert_email()` to store the field

### Support New Export Format

Add to `export_emails()` in `cli.py`:

```python
elif output_format == "newformat":
    # Format the data
    with open(output_path, "w") as f:
        f.write(formatted_data)
```

## Security Notes

- `credentials.json` and `token.json` are in `.gitignore`
- Unverified OAuth apps require test user approval
- Local cache in `~/.mailer/` contains full email content
- SQLite database is unencrypted

## Gmail API Scopes Used

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]
```

## Resources

- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
- [Gmail Search Syntax](https://support.google.com/mail/answer/7190)
- [OAuth 2.0 Scopes](https://developers.google.com/gmail/api/auth/scopes)
