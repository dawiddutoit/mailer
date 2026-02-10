# Mailer Library Examples

This directory contains practical examples demonstrating how to use the mailer library.

## Prerequisites

1. **Install dependencies:**
   ```bash
   cd /Users/dawiddutoit/projects/ref/tools/mailer
   uv sync  # or: pip install -e .
   ```

2. **Set up Gmail API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download as `credentials.json` and place in project root

3. **First run authentication:**
   - First run will open browser for OAuth consent
   - Token will be saved to `token.json` for future use

## Examples

### basic_usage.py

Demonstrates core functionality:
- Authentication with Gmail API
- Sending messages
- Listing recent messages
- Reading specific messages
- Searching with Gmail query syntax

**Run:**
```bash
python examples/basic_usage.py
```

**Required scopes:**
- `gmail.send` - Send messages
- `gmail.readonly` - Read messages

### export_house_project_emails.py

Real-world example: Export emails for a construction project.

Shows how to:
- Create project-specific search queries
- Filter by sender
- Export emails organized by sender and topic
- Save attachments
- Generate searchable index

**Run:**
```bash
python examples/export_house_project_emails.py
```

**Required scopes:**
- `gmail.readonly` - Read messages and attachments

**Customize:**
Edit the script to change:
- `project_terms` - Your project keywords
- `contractor_emails` - Specific sender emails to filter
- `output_dir` - Where to save exported emails

## Gmail Query Syntax

The library supports Gmail's powerful query syntax:

- `from:sender@example.com` - Messages from specific sender
- `to:recipient@example.com` - Messages to specific recipient
- `subject:keywords` - Messages with keywords in subject
- `has:attachment` - Messages with attachments
- `is:unread` - Unread messages
- `is:important` - Important messages
- `after:2024/01/01` - Messages after date
- `before:2024/12/31` - Messages before date

Combine with AND/OR:
- `from:alice@example.com OR from:bob@example.com`
- `subject:"project alpha" has:attachment`

[Full query syntax documentation](https://support.google.com/mail/answer/7190?hl=en)

## Troubleshooting

**Import errors:**
- Make sure you've installed the package: `pip install -e .`

**Authentication errors:**
- Delete `token.json` and re-authenticate
- Check that Gmail API is enabled in Google Cloud Console
- Verify `credentials.json` is in the correct location

**Rate limit errors:**
- Gmail API has daily quotas
- Add delays between operations if processing many messages
- Use `max_results` parameter to limit batch sizes
