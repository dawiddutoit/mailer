# Mailer CLI Complete Reference

## Table of Contents

- [Primary Commands](#primary-commands)
  - [inbox](#inbox)
  - [search](#search)
  - [show](#show)
  - [send](#send)
  - [list](#list)
  - [download](#download)
- [Data Commands](#data-commands)
  - [get emails](#get-emails)
  - [sync](#sync)
  - [export](#export)
  - [status](#status)
- [Database Commands](#database-commands)
  - [db search](#db-search)
  - [db stats](#db-stats)
  - [db import](#db-import)
  - [db import-all](#db-import-all)
  - [db query](#db-query)
  - [db refresh](#db-refresh)
  - [db attachments](#db-attachments)
- [Labels Commands](#labels-commands)
  - [labels list](#labels-list)
  - [labels create](#labels-create)
  - [labels delete](#labels-delete)
  - [labels apply](#labels-apply)
  - [labels remove](#labels-remove)
- [Drafts Commands](#drafts-commands)
  - [drafts list](#drafts-list)
  - [drafts show](#drafts-show)
  - [drafts create](#drafts-create)
  - [drafts send](#drafts-send)
  - [drafts delete](#drafts-delete)
- [Analysis Commands](#analysis-commands)
  - [analyze sender-stats](#analyze-sender-stats)
  - [analyze domain-stats](#analyze-domain-stats)
  - [analyze timeline](#analyze-timeline)

---

## Primary Commands

### inbox

Show recent emails from inbox.

```bash
mailer inbox [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--limit, -n` | 20 | Number of emails |
| `--unread, -u` | false | Only unread |
| `--format` | table | table\|json\|jsonl |

```bash
mailer inbox
mailer inbox --unread -n 50
mailer inbox --format json
```

### search

Search emails using Gmail query syntax.

```bash
mailer search QUERY [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--limit, -n` | 20 | Max results |
| `--format` | table | table\|json\|jsonl |
| `--output, -o` | - | Output file path |

```bash
mailer search "is:unread"
mailer search "from:boss@company.com subject:urgent"
mailer search "has:attachment larger:5M" --format json -o results.json
```

### show

Display full details of a specific email.

```bash
mailer show MESSAGE_ID [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--format` | text | text\|json |

Shows: ID, thread ID, from, to, CC, subject, date, size, attachments list, full body.

### send

Send an email.

```bash
mailer send TO SUBJECT BODY
```

```bash
mailer send user@example.com "Meeting Tomorrow" "Hi, can we meet at 3pm?"
```

### list

List emails with optional filtering.

```bash
mailer list [QUERY] [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--from` | - | Filter by sender (e.g. @domain.com) |
| `--limit, -n` | 50 | Max emails |
| `--format` | table | table\|json\|jsonl |
| `--output, -o` | - | Output file path |

```bash
mailer list --from @company.com
mailer list "is:unread" --limit 100
mailer list --from @bank.co.za --format json -o bank_emails.json
```

### download

Download attachments from an email.

```bash
mailer download MESSAGE_ID [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output, -o` | . | Output directory |
| `--filename, -f` | - | Download specific file by name |

```bash
mailer download 19bc7298359a0a13
mailer download 19bc7298359a0a13 -f "invoice.pdf" -o ./invoices/
```

---

## Data Commands

### get emails

Fetch emails with full content, optional sender filtering and caching.

```bash
mailer get emails [PATTERN] [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--from` | - | Filter by sender pattern |
| `--endswith` | - | Filter sender ending with |
| `--limit, -n` | - | Max emails |
| `--query, -q` | - | Gmail search query |
| `--output, -o` | - | Output file (JSON) |
| `--format` | table | table\|json\|jsonl |
| `--storage, -s` | - | Storage directory |
| `--no-cache` | false | Skip cache, fetch fresh |
| `--sync` | false | Incremental sync mode |

Pattern formats: `@domain.com`, `*@domain.com`, `/regex/`, glob patterns.

```bash
mailer get emails "@company.com" --limit 200
mailer get emails "@bank.co.za" --sync --format json -o bank.json
mailer get emails --query "has:attachment" --no-cache
```

### sync

Incremental sync emails from a sender pattern (shortcut for `get emails --sync`).

```bash
mailer sync PATTERN [OPTIONS]
```

### export

Export emails to a file in `~/.mailer/exports/`.

```bash
mailer export PATTERN [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output, -o` | auto | Output filename |
| `--format` | json | json\|jsonl\|csv |
| `--query, -q` | - | Additional Gmail query filter |

```bash
mailer export "@company.com"
mailer export "@gmail.com" --format csv -o contacts.csv
```

### status

Show storage/cache status.

```bash
mailer status [OPTIONS]
```

---

## Database Commands

All `db` commands use `~/.mailer/emails.db` by default. Override with `--database, -d`.

### db search

Full-text search using SQLite FTS5.

```bash
mailer db search QUERY [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--limit, -n` | - | Max results |
| `--format` | table | table\|json\|jsonl |
| `--output, -o` | - | Output file |

```bash
mailer db search "invoice"
mailer db search "painting OR flooring"
mailer db search "contract renewal" --format json
```

### db stats

Show database statistics (total emails, threads, domains, top senders).

```bash
mailer db stats
```

### db import

Import emails from JSON file or cache directory into SQLite.

```bash
mailer db import SOURCE
```

### db import-all

Import all cached emails into the database.

```bash
mailer db import-all
```

### db query

Run raw SQL against the database.

```bash
mailer db query SQL
```

```bash
mailer db query "SELECT from_email, COUNT(*) as cnt FROM emails GROUP BY from_email ORDER BY cnt DESC LIMIT 10"
```

### db refresh

Re-fetch and update specific emails in database.

```bash
mailer db refresh [MESSAGE_IDS...]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--missing-body` | false | Refresh emails with empty body |

### db attachments

List all attachments tracked in the database.

```bash
mailer db attachments [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--type` | - | Filter by MIME type |

---

## Labels Commands

### labels list

```bash
mailer labels list [--format table|json]
```

### labels create

```bash
mailer labels create NAME [--visibility show|hide]
```

### labels delete

```bash
mailer labels delete LABEL_ID [--force]
```

### labels apply

Apply a label to a message. LABEL can be label ID or name.

```bash
mailer labels apply MESSAGE_ID LABEL
```

### labels remove

```bash
mailer labels remove MESSAGE_ID LABEL
```

---

## Drafts Commands

### drafts list

```bash
mailer drafts list [--limit 20] [--format table|json]
```

### drafts show

```bash
mailer drafts show DRAFT_ID [--format text|json]
```

### drafts create

```bash
mailer drafts create TO SUBJECT BODY [--cc EMAILS] [--bcc EMAILS]
```

### drafts send

```bash
mailer drafts send DRAFT_ID
```

### drafts delete

```bash
mailer drafts delete DRAFT_ID [--force]
```

---

## Analysis Commands

All analysis commands require a populated local database (`mailer db import-all` first).

### analyze sender-stats

Top email senders by message count.

```bash
mailer analyze sender-stats [--limit 20] [--format table|json] [--output FILE]
```

### analyze domain-stats

Email distribution by domain.

```bash
mailer analyze domain-stats [--limit 20] [--format table|json] [--output FILE]
```

### analyze timeline

Email volume over time.

```bash
mailer analyze timeline [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--group-by` | day | day\|week\|month |
| `--limit, -n` | 30 | Number of time periods |
| `--format` | table | table\|json |
| `--output, -o` | - | Output file |

```bash
mailer analyze timeline --group-by week
mailer analyze timeline --group-by month --limit 12 --format json
```
