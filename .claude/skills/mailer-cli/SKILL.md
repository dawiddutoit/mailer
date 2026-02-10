---
user-invocable: false
name: mailer-cli
description: |
  Provides Gmail operations through the `mailer` CLI including inbox reading, email search,
  message sending, label/draft management, attachment downloads, and email pattern analysis.
  Use when users say "check email", "search inbox", "send email", "read emails", "get emails from",
  "download attachments", "find emails about", "email analysis", "unread emails", "show my inbox",
  "gmail", "label emails", "draft email", or any email/inbox/correspondence task.
  Works with Gmail API, SQLite FTS5, local caching, incremental sync.
  Key terms: mailer, gmail, inbox, email, send, search, attachments, labels, drafts, correspondence.
---

# Mailer CLI

## Quick Start

View your recent inbox immediately:
```bash
mailer inbox
mailer inbox --unread -n 50
```

Search for specific emails:
```bash
mailer search "from:boss subject:urgent"
mailer search "has:attachment after:2024/01/01"
```

The `mailer` CLI is globally installed -- invoke directly without `uv run` prefix.

## When to Use This Skill

**Explicit triggers:**
- User asks to check email, read inbox, search emails
- User requests to send email, create draft, manage labels
- User wants to download attachments or export email data
- User asks for email analytics or pattern analysis

**Implicit triggers:**
- Questions about correspondence with specific people/domains
- Requests to find emails matching certain criteria
- Tasks requiring bulk email operations or data extraction

## What This Skill Does

Teaches how to use and configure the `mailer` CLI for Gmail operations:
- Reading and searching emails (inbox, search, show)
- Sending messages and managing drafts
- Downloading attachments and exporting data
- Organizing with labels
- Local caching and full-text search with SQLite FTS5
- Email pattern analysis and statistics

## Critical Usage Rules

- **ACT IMMEDIATELY** -- do not read source files or explore the repo before running commands
- Output formats: `--format table` (default), `--format json`, `--format jsonl`
- Exports default to `~/.mailer/exports/`
- Attachments are NOT downloaded by default -- use `mailer download` explicitly

## Configuration

**Authentication:** Automatic via OAuth token at `~/.mailer/token.json`. First run triggers browser OAuth flow.

**Credentials file:** `~/.mailer/credentials.json` (Google Cloud OAuth client -- must exist before first use).

**File locations:**
| Path | Purpose |
|------|---------|
| `~/.mailer/credentials.json` | Google OAuth client credentials |
| `~/.mailer/token.json` | Auth token (auto-refreshed) |
| `~/.mailer/emails/` | JSON cache (per-sender directories) |
| `~/.mailer/emails.db` | SQLite + FTS5 local database |
| `~/.mailer/exports/` | Default export output directory |

**Gmail API scopes:** `gmail.readonly`, `gmail.send`, `gmail.modify`

**If auth fails:** Delete `~/.mailer/token.json` and re-run any command to trigger fresh OAuth.

## Quick Command Reference

```bash
# Read emails
mailer inbox                              # 20 recent inbox emails
mailer inbox --unread -n 50               # 50 unread emails
mailer show MESSAGE_ID                    # Full email content

# Search
mailer search "from:boss subject:urgent"  # Gmail query syntax
mailer list --from @company.com           # Filter by sender domain
mailer db search "keyword"                # FTS5 full-text search (local DB)

# Send
mailer send to@email.com "Subject" "Body"

# Attachments
mailer download MESSAGE_ID                # All attachments
mailer download MESSAGE_ID -f "file.pdf"  # Specific file
mailer download MESSAGE_ID -o ./dir/      # To specific directory

# Labels
mailer labels list
mailer labels apply MESSAGE_ID "Work"
mailer labels create "Projects/Active"

# Drafts
mailer drafts create to@x.com "Subj" "Body" --cc "cc@x.com"
mailer drafts list
mailer drafts send DRAFT_ID

# Analysis (requires populated local DB)
mailer analyze sender-stats
mailer analyze domain-stats
mailer analyze timeline --group-by week

# Database
mailer db stats
mailer db import-all                      # Populate DB from cache
mailer db query "SELECT from_email, COUNT(*) c FROM emails GROUP BY from_email ORDER BY c DESC"
```

## Gmail Search Syntax

Used with `mailer search` and `mailer list`:

| Operator | Example | Purpose |
|----------|---------|---------|
| `from:` | `from:boss@co.com` | From sender |
| `to:` | `to:me@co.com` | To recipient |
| `subject:` | `subject:invoice` | Subject contains |
| `is:` | `is:unread` | Status filter |
| `has:` | `has:attachment` | Has attachments |
| `after:` | `after:2024/01/01` | After date |
| `before:` | `before:2024/12/31` | Before date |
| `larger:` | `larger:5M` | Size filter |
| `label:` | `label:work` | By label |
| Combined | `from:fnb subject:payment has:attachment` | Multiple filters |

## Common Workflows

**Bulk fetch from a domain, then search locally:**
```bash
mailer get emails "@company.com" --limit 500  # Fetch + cache
mailer db import-all                          # Import to SQLite
mailer db search "contract renewal"           # FTS5 search
```

**Find and download invoice attachments:**
```bash
mailer search "from:billing has:attachment subject:invoice" -n 10 --format json
mailer download MESSAGE_ID -o ./invoices/
```

**Analyze email patterns:**
```bash
mailer db import-all
mailer analyze sender-stats --limit 10
mailer analyze timeline --group-by month
```

## Red Flags to Avoid

- Do not read source code before using CLI -- just run commands
- Do not use `uv run mailer` -- it's globally installed, use `mailer` directly
- Do not expect attachments to download automatically -- use `mailer download` explicitly
- Exports go to `~/.mailer/exports/` by default, not the current directory
- Analysis commands require `mailer db import-all` first
- Use `--sync` or `--no-cache` for fresh data

## Supporting Files

- **references/cli-reference.md** - Complete command reference with all options, parameters, and examples for every command
