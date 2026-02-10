"""CLI for mailer - Gmail interaction tool."""

import fnmatch
import json
import os
import re
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from mailer.auth import create_service
from mailer.database import (
    create_database,
    get_default_db_path,
    get_stats,
    insert_emails,
)
from mailer.database import (
    search_emails as db_search,
)
from mailer.messages import download_attachment, get_message, list_message_ids
from mailer.storage import EmailStorage, get_default_storage_dir
from mailer.types import GmailMessage

console = Console()


def get_default_export_dir() -> Path:
    """Get the default export directory."""
    export_dir = Path.home() / ".mailer" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def get_default_config_dir() -> Path:
    """Get the default config directory for mailer."""
    config_dir = Path.home() / ".mailer"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_credentials_paths() -> tuple[str, str]:
    """Get credentials and token file paths from env or defaults.

    Defaults to ~/.mailer/credentials.json and ~/.mailer/token.json.
    Override with GMAIL_CREDENTIALS_FILE and GMAIL_TOKEN_FILE env vars.
    """
    config_dir = get_default_config_dir()
    credentials = os.environ.get(
        "GMAIL_CREDENTIALS_FILE", str(config_dir / "credentials.json")
    )
    token = os.environ.get("GMAIL_TOKEN_FILE", str(config_dir / "token.json"))
    return credentials, token


def check_credentials_exist() -> bool:
    """Check if credentials file exists and provide setup guidance if not."""
    credentials_file, _ = get_credentials_paths()
    creds_path = Path(credentials_file)

    if not creds_path.exists():
        config_dir = get_default_config_dir()
        console.print("\n[red bold]Gmail credentials not found![/red bold]\n")
        console.print("To set up the mailer tool:\n")
        console.print("1. Go to [cyan]https://console.cloud.google.com/[/cyan]")
        console.print("2. Create a project (or select existing)")
        console.print("3. Enable the Gmail API:")
        console.print("   APIs & Services → Library → Search 'Gmail API' → Enable")
        console.print("4. Create OAuth 2.0 credentials:")
        console.print("   APIs & Services → Credentials → Create Credentials → OAuth client ID")
        console.print("   - Application type: Desktop app")
        console.print("   - Download the JSON file")
        console.print(f"5. Save the file as: [green]{config_dir / 'credentials.json'}[/green]")
        console.print("\nOr set the environment variable:")
        console.print("   [dim]export GMAIL_CREDENTIALS_FILE=/path/to/credentials.json[/dim]\n")
        return False
    return True


def get_gmail_service():
    """Get authenticated Gmail service with proper error handling.

    Returns the service or exits with helpful error message.
    """
    if not check_credentials_exist():
        raise SystemExit(1)

    credentials_file, token_file = get_credentials_paths()

    try:
        return create_service(credentials_file, token_file)
    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise SystemExit(1)


def extract_email_address(from_header: str) -> str:
    """Extract email address from 'Name <email>' format."""
    match = re.search(r"<([^>]+)>", from_header)
    if match:
        return match.group(1).lower()
    return from_header.strip().lower()


def match_email_pattern(from_header: str, pattern: str) -> bool:
    """Match email against a pattern."""
    email = extract_email_address(from_header)
    pattern_lower = pattern.lower()

    if pattern.startswith("/") and pattern.endswith("/"):
        regex = pattern[1:-1]
        return bool(re.search(regex, email, re.IGNORECASE))

    if pattern_lower.startswith("@"):
        return email.endswith(pattern_lower)

    if "*" in pattern or "?" in pattern:
        return fnmatch.fnmatch(email, pattern_lower)

    return pattern_lower in email


class OrderedGroup(click.Group):
    """Click group that maintains command order as defined."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return commands in definition order, with priority commands first."""
        # Priority order: most useful commands first
        priority = ["inbox", "search", "show", "send", "list", "download"]
        all_cmds = list(self.commands.keys())
        ordered = [cmd for cmd in priority if cmd in all_cmds]
        ordered.extend(cmd for cmd in all_cmds if cmd not in ordered)
        return ordered


@click.group(cls=OrderedGroup)
@click.version_option(version="0.1.0")
def main() -> None:
    """Mailer CLI - interact with Gmail from the command line.

    \b
    Quick start:
      mailer inbox                      # See recent emails
      mailer search "from:boss"         # Search with Gmail syntax
      mailer show MESSAGE_ID            # View full email
      mailer send to@email.com "Hi" "Body"
    """
    pass


# ============ Primary Commands (Most Used) ============


@main.command("inbox")
@click.option("--limit", "-n", default=20, help="Number of emails (default: 20)")
@click.option("--unread", "-u", is_flag=True, help="Show only unread emails")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json", "jsonl"]), default="table"
)
def inbox(limit: int, unread: bool, output_format: str) -> None:
    """Show recent emails from your inbox.

    \b
    Examples:
      mailer inbox                  # Recent 20 emails
      mailer inbox -n 50            # Recent 50 emails
      mailer inbox --unread         # Only unread
      mailer inbox --format json    # JSON output
    """
    from mailer.formatters import format_as_json, format_as_jsonl
    from mailer.messages import list_messages

    service = get_gmail_service()

    query = "in:inbox"
    if unread:
        query += " is:unread"

    messages = list_messages(service, max_results=limit, query=query)

    if not messages:
        console.print("[yellow]No emails found.[/yellow]")
        return

    if output_format == "json":
        print(format_as_json(messages))
    elif output_format == "jsonl":
        print(format_as_jsonl(messages))
    else:
        table = Table(title=f"Inbox ({len(messages)} emails)")
        table.add_column("ID", style="dim", max_width=18)
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="white", max_width=45)
        table.add_column("Date", style="dim", max_width=12)

        for msg in messages:
            from_display = msg.from_email[:30] if msg.from_email else ""
            # Extract just the name if available
            if "<" in from_display:
                from_display = from_display.split("<")[0].strip()[:30]
            table.add_row(
                msg.id[:18],
                from_display,
                (msg.subject or "")[:45],
                msg.date_formatted[:12] if msg.date_formatted else "",
            )

        console.print(table)
        console.print("\n[dim]Use 'mailer show <ID>' to view full email[/dim]")


@main.command("list")
@click.argument("query", required=False)
@click.option("--from", "from_addr", help="Filter by sender (e.g., @domain.com)")
@click.option("--limit", "-n", default=50, help="Max emails (default: 50)")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json", "jsonl"]), default="table"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def list_emails(
    query: str | None,
    from_addr: str | None,
    limit: int,
    output_format: str,
    output: str | None,
) -> None:
    """List emails with optional filtering.

    \b
    Examples:
      mailer list                           # Recent emails
      mailer list "is:unread"               # Gmail query
      mailer list --from @company.com       # From domain
      mailer list "subject:invoice" -n 100  # Search + limit
    """
    from mailer.formatters import format_as_json, format_as_jsonl, write_output
    from mailer.messages import list_messages

    service = get_gmail_service()

    # Build query
    gmail_query = query or ""
    if from_addr:
        if from_addr.startswith("@"):
            gmail_query = f"{gmail_query} from:{from_addr[1:]}".strip()
        else:
            gmail_query = f"{gmail_query} from:{from_addr}".strip()

    messages = list_messages(service, max_results=limit, query=gmail_query or None)

    if not messages:
        console.print("[yellow]No emails found.[/yellow]")
        return

    if output_format == "json" or (output and output_format == "table"):
        formatted = format_as_json(messages)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved {len(messages)} emails to {output}[/green]")
        else:
            print(formatted)
    elif output_format == "jsonl":
        formatted = format_as_jsonl(messages)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved {len(messages)} emails to {output}[/green]")
        else:
            print(formatted)
    else:
        table = Table(title=f"Emails ({len(messages)})")
        table.add_column("ID", style="dim", max_width=18)
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="white", max_width=45)
        table.add_column("Date", style="dim", max_width=12)

        for msg in messages:
            from_display = msg.from_email[:30] if msg.from_email else ""
            if "<" in from_display:
                from_display = from_display.split("<")[0].strip()[:30]
            table.add_row(
                msg.id[:18],
                from_display,
                (msg.subject or "")[:45],
                msg.date_formatted[:12] if msg.date_formatted else "",
            )

        console.print(table)
        console.print("\n[dim]Use 'mailer show <ID>' to view full email[/dim]")


# ============ Secondary Commands ============


@main.group()
def get() -> None:
    """Get/download Gmail resources."""
    pass


@get.command("emails")
@click.argument("pattern", required=False)
@click.option("--from", "from_pattern", help="Filter by sender pattern (e.g., *@tre.co.za)")
@click.option("--endswith", "endswith_pattern", help="Filter sender ending with (e.g., @tre.co.za)")
@click.option("--limit", "-n", default=0, help="Max emails to fetch (0 = all matching)")
@click.option("--query", "-q", help="Gmail search query (e.g., 'is:unread')")
@click.option("--output", "-o", type=click.Path(), help="Output file (JSON)")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json", "jsonl"]), default="table"
)
@click.option("--storage", "-s", type=click.Path(), help="Storage directory for caching")
@click.option("--no-cache", is_flag=True, help="Skip cache, fetch fresh from Gmail")
@click.option("--sync", is_flag=True, help="Sync mode: fetch only new emails, use cached for rest")
def get_emails(
    pattern: str | None,
    from_pattern: str | None,
    endswith_pattern: str | None,
    limit: int,
    query: str | None,
    output: str | None,
    output_format: str,
    storage: str | None,
    no_cache: bool,
    sync: bool,
) -> None:
    """Get emails with full content, optionally filtered by sender.

    Uses local caching to avoid re-fetching emails. Use --sync to only
    fetch new emails since last sync.

    PATTERN can be:

    \b
      @example.com      - Emails from *@example.com
      *@example.com     - Same as above (glob pattern)
      user*@*.com       - Glob with wildcards
      /regex/           - Regular expression

    Examples:

    \b
      mailer get emails "@tre.co.za"              # Get all from tre.co.za
      mailer get emails "@tre.co.za" --sync       # Only fetch new ones
      mailer get emails "@gmail.com" -n 100       # Limit to 100
      mailer get emails -q "has:attachment"       # Gmail query
    """
    effective_pattern = pattern or from_pattern or endswith_pattern
    if endswith_pattern and not endswith_pattern.startswith("@"):
        effective_pattern = f"@{endswith_pattern}"

    service = get_gmail_service()

    # Setup storage
    storage_dir = Path(storage) if storage else get_default_storage_dir()
    # Create a subdirectory based on the pattern/query for organization
    if effective_pattern:
        safe_name = re.sub(r"[^\w@.-]", "_", effective_pattern)
        storage_dir = storage_dir / safe_name
    email_storage = EmailStorage(storage_dir)

    # Build Gmail query
    gmail_query = query or ""
    if effective_pattern:
        if effective_pattern.startswith("@") and "*" not in effective_pattern:
            domain = effective_pattern[1:]
            gmail_query = f"{gmail_query} from:{domain}".strip()

    # Get message IDs with pagination
    console.print("[dim]Searching emails...[/dim]")
    if gmail_query:
        console.print(f"[dim]Query: {gmail_query}[/dim]")

    # Fetch ALL matching message IDs first (with pagination)
    all_message_ids = list_message_ids(service, max_results=limit, query=gmail_query or None)
    console.print(f"[dim]Found {len(all_message_ids)} emails matching query[/dim]")

    # Determine which emails need fetching
    if no_cache:
        ids_to_fetch = all_message_ids
        console.print(f"[dim]Fetching all {len(ids_to_fetch)} emails (--no-cache)[/dim]")
    elif sync:
        ids_to_fetch = email_storage.get_new_message_ids(all_message_ids)
        cached_count = len(all_message_ids) - len(ids_to_fetch)
        console.print(f"[dim]Found {cached_count} cached, {len(ids_to_fetch)} new to fetch[/dim]")
    else:
        # Default: fetch new ones, load cached ones
        ids_to_fetch = email_storage.get_new_message_ids(all_message_ids)
        cached_count = len(all_message_ids) - len(ids_to_fetch)
        if cached_count > 0:
            console.print(
                f"[dim]Using {cached_count} cached emails, fetching {len(ids_to_fetch)} new[/dim]"
            )

    # Fetch new emails with progress bar
    new_messages: list[GmailMessage] = []
    if ids_to_fetch:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching emails...", total=len(ids_to_fetch))

            for msg_id in ids_to_fetch:
                try:
                    msg = get_message(service, msg_id)
                    new_messages.append(msg)
                    progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to fetch {msg_id}: {e}[/yellow]")
                    progress.update(task, advance=1)

        # Store new messages
        if new_messages and not no_cache:
            stored = email_storage.store_messages(new_messages)
            console.print(f"[green]Cached {stored} new emails to {storage_dir}[/green]")

    # Collect all messages (new + cached)
    all_messages: list[GmailMessage] = []

    if no_cache:
        all_messages = new_messages
    else:
        # Load from cache for IDs we didn't fetch
        cached_ids = set(all_message_ids) - set(ids_to_fetch)
        for msg_id in cached_ids:
            cached_msg = email_storage.load_message(msg_id)
            if cached_msg:
                all_messages.append(cached_msg)
        all_messages.extend(new_messages)

    # Filter by pattern (for complex patterns not handled by Gmail query)
    if effective_pattern:
        filtered = [
            msg for msg in all_messages if match_email_pattern(msg.from_email, effective_pattern)
        ]
        if len(filtered) != len(all_messages):
            console.print(
                f"[dim]Filtered to {len(filtered)} emails matching '{effective_pattern}'[/dim]"
            )
        all_messages = filtered

    if not all_messages:
        console.print("[yellow]No emails found matching criteria.[/yellow]")
        return

    console.print(f"[green]Total: {len(all_messages)} emails[/green]")

    # Output results
    if output_format == "json" or output:
        data = [msg.model_dump() for msg in all_messages]
        json_output = json.dumps(data, indent=2, default=str)

        if output:
            # If output is just a filename (no path), save to exports directory
            output_path = Path(output)
            if not output_path.is_absolute() and output_path.parent == Path("."):
                output_path = get_default_export_dir() / output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_output)
            console.print(f"[green]Saved to {output_path}[/green]")
        else:
            print(json_output)

    elif output_format == "jsonl":
        for msg in all_messages:
            print(json.dumps(msg.model_dump(), default=str))

    else:  # table
        table = Table(title=f"Emails ({len(all_messages)})")
        table.add_column("From", style="cyan", max_width=40)
        table.add_column("Subject", style="white", max_width=50)
        table.add_column("Body Preview", style="dim", max_width=40)

        for msg in all_messages:
            body_preview = msg.body[:40].replace("\n", " ") if msg.body else msg.snippet[:40]
            table.add_row(
                msg.from_email[:40] if msg.from_email else "",
                msg.subject[:50] if msg.subject else "",
                body_preview,
            )

        console.print(table)


@main.command("sync")
@click.argument("pattern")
@click.option("--storage", "-s", type=click.Path(), help="Storage directory")
def sync_emails(pattern: str, storage: str | None) -> None:
    """Sync emails from a sender pattern (incremental fetch).

    This is a shortcut for: mailer get emails PATTERN --sync

    Example:

    \b
      mailer sync "@tre.co.za"
    """
    # Just call get_emails with sync=True
    ctx = click.get_current_context()
    ctx.invoke(
        get_emails,
        pattern=pattern,
        from_pattern=None,
        endswith_pattern=None,
        limit=0,
        query=None,
        output=None,
        output_format="table",
        storage=storage,
        no_cache=False,
        sync=True,
    )


@main.command("send")
@click.argument("to")
@click.argument("subject")
@click.argument("body")
def send_email(to: str, subject: str, body: str) -> None:
    """Send an email.

    Example:

    \b
      mailer send user@example.com "Hello" "This is the body"
    """
    from mailer.messages import send_message

    service = get_gmail_service()

    try:
        message_id = send_message(service, to=to, subject=subject, body=body)
        console.print(f"[green]Email sent![/green] Message ID: {message_id}")
    except Exception as e:
        console.print(f"[red]Failed to send:[/red] {e}")
        raise SystemExit(1)


@main.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Max results (default: 20)")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json", "jsonl"]), default="table"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def search_emails(query: str, limit: int, output_format: str, output: str | None) -> None:
    """Search emails using Gmail query syntax.

    Examples:

    \b
      mailer search "is:unread"
      mailer search "from:boss@company.com subject:urgent"
      mailer search "has:attachment larger:5M"
      mailer search "is:important" --format json -o important.json
    """
    from mailer.formatters import format_as_json, format_as_jsonl, write_output
    from mailer.messages import list_messages

    service = get_gmail_service()

    messages = list_messages(service, max_results=limit, query=query)

    if not messages:
        console.print("[yellow]No emails found.[/yellow]")
        return

    if output_format == "json" or (output and output_format == "table"):
        formatted = format_as_json(messages)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved {len(messages)} emails to {output}[/green]")
        else:
            print(formatted)
    elif output_format == "jsonl":
        formatted = format_as_jsonl(messages)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved {len(messages)} emails to {output}[/green]")
        else:
            print(formatted)
    else:
        table = Table(title=f"Search Results ({len(messages)})")
        table.add_column("From", style="cyan", max_width=35)
        table.add_column("Subject", style="white", max_width=50)
        table.add_column("Body Preview", style="dim", max_width=35)

        for msg in messages:
            body_preview = msg.body[:35].replace("\n", " ") if msg.body else msg.snippet[:35]
            table.add_row(
                msg.from_email[:35] if msg.from_email else "",
                msg.subject[:50] if msg.subject else "",
                body_preview,
            )

        console.print(table)


@main.command("status")
@click.option("--storage", "-s", type=click.Path(), help="Storage directory")
def storage_status(storage: str | None) -> None:
    """Show storage/cache status."""
    storage_dir = Path(storage) if storage else get_default_storage_dir()

    if not storage_dir.exists():
        console.print(f"[yellow]No storage found at {storage_dir}[/yellow]")
        return

    table = Table(title="Email Storage Status")
    table.add_column("Pattern", style="cyan")
    table.add_column("Emails", style="green")
    table.add_column("Last Sync", style="dim")

    total = 0
    for subdir in storage_dir.iterdir():
        if subdir.is_dir() and (subdir / "index.json").exists():
            es = EmailStorage(subdir)
            stats = es.get_stats()
            table.add_row(
                subdir.name,
                str(stats["total_messages"]),
                stats["last_sync"][:19] if stats["last_sync"] else "Never",
            )
            total += stats["total_messages"]

    if total == 0:
        console.print(f"[yellow]No cached emails in {storage_dir}[/yellow]")
    else:
        table.add_section()
        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "")
        console.print(table)


# ============ Database Commands ============


@main.group()
def db() -> None:
    """Database operations for email storage."""
    pass


@db.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option("--database", "-d", type=click.Path(), help="Database path")
def db_import(source: str, database: str | None) -> None:
    """Import emails from JSON file or cache directory into SQLite.

    SOURCE can be:
    - A JSON file (emails.json)
    - A cache directory (~/.mailer/emails/@domain)

    Examples:

    \b
      mailer db import tre_emails_full.json
      mailer db import ~/.mailer/emails/@tre.co.za
    """
    db_path = Path(database) if database else get_default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = create_database(db_path)
    source_path = Path(source)

    emails: list[GmailMessage] = []

    if source_path.is_file() and source_path.suffix == ".json":
        # Import from JSON file
        console.print(f"[dim]Loading from {source_path}...[/dim]")
        data = json.loads(source_path.read_text())
        for item in data:
            emails.append(GmailMessage(**item))
    elif source_path.is_dir():
        # Import from cache directory
        messages_dir = source_path / "messages"
        if messages_dir.exists():
            console.print(f"[dim]Loading from cache {source_path}...[/dim]")
            for msg_file in messages_dir.glob("*.json"):
                try:
                    emails.append(GmailMessage.model_validate_json(msg_file.read_text()))
                except Exception as e:
                    console.print(f"[yellow]Warning: Skipping {msg_file.name}: {e}[/yellow]")
        else:
            console.print(f"[red]No messages directory found in {source_path}[/red]")
            raise SystemExit(1)
    else:
        console.print(f"[red]Invalid source: {source}[/red]")
        raise SystemExit(1)

    if not emails:
        console.print("[yellow]No emails found to import.[/yellow]")
        return

    new_count = insert_emails(conn, emails)
    conn.close()

    console.print(f"[green]Imported {new_count} new emails to {db_path}[/green]")
    console.print(f"[dim]({len(emails) - new_count} already existed)[/dim]")


@db.command("import-all")
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option("--storage", "-s", type=click.Path(), help="Storage directory")
def db_import_all(database: str | None, storage: str | None) -> None:
    """Import all cached emails into the database.

    Example:

    \b
      mailer db import-all
    """
    db_path = Path(database) if database else get_default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    storage_dir = Path(storage) if storage else get_default_storage_dir()

    if not storage_dir.exists():
        console.print(f"[yellow]No cache found at {storage_dir}[/yellow]")
        return

    conn = create_database(db_path)
    total_imported = 0
    total_skipped = 0

    for subdir in storage_dir.iterdir():
        if subdir.is_dir() and (subdir / "messages").exists():
            console.print(f"[dim]Importing from {subdir.name}...[/dim]")
            messages_dir = subdir / "messages"
            emails: list[GmailMessage] = []

            for msg_file in messages_dir.glob("*.json"):
                try:
                    emails.append(GmailMessage.model_validate_json(msg_file.read_text()))
                except Exception:
                    pass

            if emails:
                new_count = insert_emails(conn, emails)
                total_imported += new_count
                total_skipped += len(emails) - new_count

    conn.close()

    console.print(f"[green]Imported {total_imported} new emails to {db_path}[/green]")
    if total_skipped > 0:
        console.print(f"[dim]({total_skipped} already existed)[/dim]")


@db.command("stats")
@click.option("--database", "-d", type=click.Path(), help="Database path")
def db_stats(database: str | None) -> None:
    """Show database statistics.

    Example:

    \b
      mailer db stats
    """
    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        console.print("[dim]Run 'mailer db import' to create one.[/dim]")
        return

    conn = create_database(db_path)
    stats = get_stats(conn)
    conn.close()

    console.print(f"\n[bold]Database:[/bold] {db_path}")
    console.print(f"[bold]Size:[/bold] {db_path.stat().st_size / 1024:.1f} KB\n")

    table = Table(title="Email Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Emails", str(stats["total_emails"]))
    table.add_row("Total Threads", str(stats["total_threads"]))
    table.add_row("Unique Domains", str(stats["unique_domains"]))

    console.print(table)

    if stats["top_senders"]:
        console.print()
        sender_table = Table(title="Top Senders")
        sender_table.add_column("Sender", style="cyan")
        sender_table.add_column("Count", style="green")

        for sender in stats["top_senders"]:
            name = sender["from_name"] or sender["from_email"]
            sender_table.add_row(name, str(sender["count"]))

        console.print(sender_table)


@db.command("search")
@click.argument("query")
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option("--limit", "-n", default=20, help="Max results")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json", "jsonl"]), default="table"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def db_search_cmd(
    query: str, database: str | None, limit: int, output_format: str, output: str | None
) -> None:
    """Full-text search emails in database.

    Uses SQLite FTS5 for fast searching.

    Examples:

    \b
      mailer db search "invoice"
      mailer db search "painting OR flooring"
      mailer db search "from:christiaan" --format json -o results.json
    """
    from mailer.formatters import format_dict_as_json, format_dicts_as_jsonl, write_output

    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    conn = create_database(db_path)
    results = db_search(conn, query, limit)
    conn.close()

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    if output_format == "json" or (output and output_format == "table"):
        formatted = format_dict_as_json(results)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved {len(results)} results to {output}[/green]")
        else:
            print(formatted)
    elif output_format == "jsonl":
        formatted = format_dicts_as_jsonl(results)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved {len(results)} results to {output}[/green]")
        else:
            print(formatted)
    else:
        table = Table(title=f"Search Results: '{query}' ({len(results)} found)")
        table.add_column("From", style="cyan", max_width=30)
        table.add_column("Subject", style="white", max_width=45)
        table.add_column("Preview", style="dim", max_width=35)

        for row in results:
            body_preview = (row["body"] or row["snippet"] or "")[:35].replace("\n", " ")
            table.add_row(
                (row["from_name"] or row["from_email"] or "")[:30],
                (row["subject"] or "")[:45],
                body_preview,
            )

        console.print(table)


@db.command("query")
@click.argument("sql")
@click.option("--database", "-d", type=click.Path(), help="Database path")
def db_query(sql: str, database: str | None) -> None:
    """Run a raw SQL query on the database.

    Example:

    \b
      mailer db query "SELECT from_email, COUNT(*) as cnt FROM emails GROUP BY from_email"
    """
    import sqlite3

    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            console.print("[yellow]No results.[/yellow]")
            return

        # Get column names
        columns = rows[0].keys()

        table = Table()
        for col in columns:
            table.add_column(col, style="cyan")

        for row in rows[:100]:  # Limit display
            table.add_row(*[str(row[col])[:50] for col in columns])

        console.print(table)

        if len(rows) > 100:
            console.print(f"[dim]... and {len(rows) - 100} more rows[/dim]")

    except Exception as e:
        console.print(f"[red]SQL Error:[/red] {e}")
    finally:
        conn.close()


@main.command("export")
@click.argument("pattern")
@click.option(
    "--output", "-o", type=click.Path(), help="Output filename (saved to ~/.mailer/exports/)"
)
@click.option(
    "--format", "output_format", type=click.Choice(["json", "jsonl", "csv"]), default="json"
)
@click.option("--query", "-q", help="Additional Gmail query filter")
def export_emails(pattern: str, output: str | None, output_format: str, query: str | None) -> None:
    """Export emails to a file in ~/.mailer/exports/.

    Creates a timestamped file by default, or specify a custom name.

    Examples:

    \b
      mailer export "@tre.co.za"                    # -> ~/.mailer/exports/tre.co.za_2024-01-29.json
      mailer export "@tre.co.za" -o custom.json     # -> ~/.mailer/exports/custom.json
      mailer export "@gmail.com" --format csv       # -> CSV format
    """
    from datetime import datetime

    service = get_gmail_service()

    # Build Gmail query
    gmail_query = query or ""
    if pattern.startswith("@") and "*" not in pattern:
        domain = pattern[1:]
        gmail_query = f"{gmail_query} from:{domain}".strip()

    console.print(f"[dim]Fetching emails matching '{pattern}'...[/dim]")

    # Fetch all matching emails
    from mailer.messages import list_messages

    messages = list_messages(service, max_results=0, query=gmail_query or None)

    # Filter by pattern
    filtered = [msg for msg in messages if match_email_pattern(msg.from_email, pattern)]
    console.print(f"[dim]Found {len(filtered)} emails[/dim]")

    if not filtered:
        console.print("[yellow]No emails to export.[/yellow]")
        return

    # Determine output path
    export_dir = get_default_export_dir()
    if output:
        output_path = export_dir / output
    else:
        # Generate default filename from pattern
        safe_pattern = re.sub(r"[^\w@.-]", "_", pattern.lstrip("@"))
        date_str = datetime.now().strftime("%Y-%m-%d")
        ext = "csv" if output_format == "csv" else "json"
        output_path = export_dir / f"{safe_pattern}_{date_str}.{ext}"

    # Export based on format
    if output_format == "csv":
        import csv

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "date", "from", "to", "subject", "body_preview"])
            for msg in filtered:
                writer.writerow(
                    [
                        msg.id,
                        msg.date_formatted,
                        msg.from_email,
                        ", ".join(msg.to),
                        msg.subject,
                        msg.body[:200] if msg.body else msg.snippet[:200],
                    ]
                )
    elif output_format == "jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for msg in filtered:
                f.write(json.dumps(msg.model_dump(), default=str) + "\n")
    else:  # json
        data = [msg.model_dump() for msg in filtered]
        output_path.write_text(json.dumps(data, indent=2, default=str))

    console.print(f"[green]Exported {len(filtered)} emails to:[/green]")
    console.print(f"  {output_path}")


@main.command("show")
@click.argument("message_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
def show_email(message_id: str, output_format: str) -> None:
    """Show full details of a specific email.

    Example:

    \b
      mailer show 19bc7298359a0a13
    """
    service = get_gmail_service()

    try:
        msg = get_message(service, message_id)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if output_format == "json":
        print(json.dumps(msg.model_dump(), indent=2, default=str))
    else:
        console.print(f"[bold]ID:[/bold] {msg.id}")
        console.print(f"[bold]Thread:[/bold] {msg.thread_id}")
        console.print(f"[bold]From:[/bold] {msg.from_email}")
        console.print(f"[bold]To:[/bold] {', '.join(msg.to)}")
        if msg.cc:
            console.print(f"[bold]CC:[/bold] {', '.join(msg.cc)}")
        console.print(f"[bold]Subject:[/bold] {msg.subject}")
        console.print(f"[bold]Date:[/bold] {msg.date_formatted} ({msg.date})")
        console.print(f"[bold]Size:[/bold] {msg.size_estimate:,} bytes")
        console.print()

        if msg.attachments:
            console.print(f"[bold]Attachments ({len(msg.attachments)}):[/bold]")
            for att in msg.attachments:
                console.print(f"  • {att.filename} ({att.mime_type}, {att.size:,} bytes)")
            console.print()

        console.print("[bold]Body:[/bold]")
        console.print("-" * 60)
        console.print(msg.body if msg.body else "[dim]No body content[/dim]")


@main.command("download")
@click.argument("message_id")
@click.option("--output", "-o", type=click.Path(), help="Output directory (default: current)")
@click.option("--filename", "-f", help="Download specific file (by name)")
def download_attachments(message_id: str, output: str | None, filename: str | None) -> None:
    """Download attachments from an email.

    Example:

    \b
      mailer download 19bc7298359a0a13
      mailer download 19bc7298359a0a13 -o ./attachments
      mailer download 19bc7298359a0a13 -f "document.pdf"
    """
    output_dir = Path(output) if output else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    service = get_gmail_service()

    try:
        msg = get_message(service, message_id)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not msg.attachments:
        console.print("[yellow]No attachments found.[/yellow]")
        return

    downloaded = 0
    for att in msg.attachments:
        if filename and att.filename != filename:
            continue

        console.print(f"[dim]Downloading {att.filename}...[/dim]")
        try:
            data = download_attachment(service, message_id, att.attachment_id)
            file_path = output_dir / att.filename
            file_path.write_bytes(data)
            console.print(f"[green]✓[/green] {file_path} ({len(data):,} bytes)")
            downloaded += 1
        except Exception as e:
            console.print(f"[red]✗[/red] {att.filename}: {e}")

    console.print(f"\n[green]Downloaded {downloaded} attachment(s) to {output_dir}[/green]")


@db.command("refresh")
@click.argument("message_ids", nargs=-1)
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option("--missing-body", is_flag=True, help="Refresh emails with empty body")
def db_refresh(message_ids: tuple[str, ...], database: str | None, missing_body: bool) -> None:
    """Re-fetch and update specific emails in the database.

    Can specify message IDs or use --missing-body to find and refresh
    emails that have empty body content.

    Example:

    \b
      mailer db refresh 19bc7298359a0a13 18b67789f9123456
      mailer db refresh --missing-body
    """
    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    service = get_gmail_service()

    conn = create_database(db_path)

    # Find emails to refresh
    ids_to_refresh: list[str] = list(message_ids)

    if missing_body:
        cursor = conn.execute("SELECT id FROM emails WHERE body IS NULL OR body = ''")
        ids_to_refresh.extend(row["id"] for row in cursor.fetchall())

    if not ids_to_refresh:
        console.print("[yellow]No emails to refresh.[/yellow]")
        conn.close()
        return

    console.print(f"[dim]Refreshing {len(ids_to_refresh)} email(s)...[/dim]")

    refreshed = 0
    for msg_id in ids_to_refresh:
        try:
            msg = get_message(service, msg_id)
            insert_emails(conn, [msg])
            console.print(f"[green]✓[/green] {msg_id}: {msg.subject[:50]}")
            refreshed += 1
        except Exception as e:
            console.print(f"[red]✗[/red] {msg_id}: {e}")

    conn.close()
    console.print(f"\n[green]Refreshed {refreshed} email(s)[/green]")


@db.command("attachments")
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option("--type", "mime_type", help="Filter by MIME type (e.g., application/pdf)")
def db_attachments(database: str | None, mime_type: str | None) -> None:
    """List all attachments in the database.

    Example:

    \b
      mailer db attachments
      mailer db attachments --type application/pdf
    """
    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT a.*, e.subject, e.from_name
        FROM attachments a
        JOIN emails e ON a.message_id = e.id
    """
    params: list = []

    if mime_type:
        query += " WHERE a.mime_type = ?"
        params.append(mime_type)

    query += " ORDER BY a.size DESC"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        console.print("[yellow]No attachments found.[/yellow]")
        return

    table = Table(title=f"Attachments ({len(rows)})")
    table.add_column("Filename", style="cyan", max_width=35)
    table.add_column("Type", style="dim", max_width=20)
    table.add_column("Size", style="green")
    table.add_column("Email Subject", style="white", max_width=30)

    total_size = 0
    for row in rows:
        size_kb = row["size"] / 1024
        total_size += row["size"]
        table.add_row(
            row["filename"][:35],
            row["mime_type"][:20],
            f"{size_kb:.1f} KB",
            (row["subject"] or "")[:30],
        )

    console.print(table)
    console.print(
        f"\n[dim]Total: {total_size / 1024 / 1024:.2f} MB in {len(rows)} attachments[/dim]"
    )


# ============ Labels Commands ============


@main.group()
def labels() -> None:
    """Manage Gmail labels."""
    pass


@labels.command("list")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json"]), default="table"
)
def labels_list(output_format: str) -> None:
    """List all labels in your mailbox.

    Example:

    \b
      mailer labels list
      mailer labels list --format json
    """
    from mailer.labels import list_labels

    service = get_gmail_service()

    try:
        all_labels = list_labels(service)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if output_format == "json":
        data = [label.model_dump() for label in all_labels]
        print(json.dumps(data, indent=2))
    else:
        # Separate system and user labels
        system_labels = [l for l in all_labels if l.type == "system"]
        user_labels = [l for l in all_labels if l.type == "user"]

        table = Table(title=f"Labels ({len(all_labels)})")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Type", style="green")

        for label in user_labels:
            table.add_row(label.name, label.id, label.type)

        if system_labels:
            table.add_section()
            for label in system_labels:
                table.add_row(label.name, label.id, f"[dim]{label.type}[/dim]")

        console.print(table)


@labels.command("create")
@click.argument("name")
@click.option("--visibility", type=click.Choice(["show", "hide"]), default="show")
def labels_create(name: str, visibility: str) -> None:
    """Create a new label.

    Example:

    \b
      mailer labels create "My Label"
      mailer labels create "Work/Projects" --visibility hide
    """
    from mailer.labels import create_label

    service = get_gmail_service()

    try:
        label = create_label(service, name, message_list_visibility=visibility)
        console.print(f"[green]Created label:[/green] {label.name} (ID: {label.id})")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@labels.command("delete")
@click.argument("label_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def labels_delete(label_id: str, force: bool) -> None:
    """Delete a label.

    Example:

    \b
      mailer labels delete Label_123
      mailer labels delete Label_123 --force
    """
    from mailer.labels import delete_label, get_label

    service = get_gmail_service()

    try:

        # Get label name for confirmation
        label = get_label(service, label_id)

        if not force:
            if not click.confirm(f"Delete label '{label.name}'?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        delete_label(service, label_id)
        console.print(f"[green]Deleted label:[/green] {label.name}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@labels.command("apply")
@click.argument("message_id")
@click.argument("label")
def labels_apply(message_id: str, label: str) -> None:
    """Apply a label to a message.

    LABEL can be a label ID or name.

    Example:

    \b
      mailer labels apply 19bc7298359a0a13 Label_123
      mailer labels apply 19bc7298359a0a13 "Work"
    """
    from mailer.labels import apply_label, get_label_by_name

    service = get_gmail_service()

    try:

        # Check if label is a name or ID
        label_id = label
        if not label.startswith("Label_") and not label.isupper():
            found_label = get_label_by_name(service, label)
            if found_label:
                label_id = found_label.id
            else:
                console.print(f"[red]Label not found:[/red] {label}")
                raise SystemExit(1)

        apply_label(service, message_id, label_id)
        console.print(f"[green]Applied label to message {message_id}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@labels.command("remove")
@click.argument("message_id")
@click.argument("label")
def labels_remove(message_id: str, label: str) -> None:
    """Remove a label from a message.

    LABEL can be a label ID or name.

    Example:

    \b
      mailer labels remove 19bc7298359a0a13 Label_123
      mailer labels remove 19bc7298359a0a13 "Work"
    """
    from mailer.labels import get_label_by_name, remove_label

    service = get_gmail_service()

    try:

        # Check if label is a name or ID
        label_id = label
        if not label.startswith("Label_") and not label.isupper():
            found_label = get_label_by_name(service, label)
            if found_label:
                label_id = found_label.id
            else:
                console.print(f"[red]Label not found:[/red] {label}")
                raise SystemExit(1)

        remove_label(service, message_id, label_id)
        console.print(f"[green]Removed label from message {message_id}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


# ============ Drafts Commands ============


@main.group()
def drafts() -> None:
    """Manage Gmail drafts."""
    pass


@drafts.command("list")
@click.option("--limit", "-n", default=20, help="Max drafts to list")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json"]), default="table"
)
def drafts_list(limit: int, output_format: str) -> None:
    """List all drafts.

    Example:

    \b
      mailer drafts list
      mailer drafts list --limit 10
      mailer drafts list --format json
    """
    from mailer.drafts import list_drafts

    service = get_gmail_service()

    try:
        all_drafts = list_drafts(service, max_results=limit)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not all_drafts:
        console.print("[yellow]No drafts found.[/yellow]")
        return

    if output_format == "json":
        data = [d.model_dump() for d in all_drafts]
        print(json.dumps(data, indent=2, default=str))
    else:
        table = Table(title=f"Drafts ({len(all_drafts)})")
        table.add_column("ID", style="dim", max_width=15)
        table.add_column("To", style="cyan", max_width=30)
        table.add_column("Subject", style="white", max_width=40)
        table.add_column("Preview", style="dim", max_width=30)

        for draft in all_drafts:
            msg = draft.message
            to_str = ", ".join(msg.to)[:30] if msg.to else "-"
            table.add_row(
                draft.id[:15],
                to_str,
                (msg.subject or "-")[:40],
                (msg.snippet or "-")[:30],
            )

        console.print(table)


@drafts.command("show")
@click.argument("draft_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
def drafts_show(draft_id: str, output_format: str) -> None:
    """Show a specific draft.

    Example:

    \b
      mailer drafts show r-8234567890123456789
    """
    from mailer.drafts import get_draft

    service = get_gmail_service()

    try:
        draft = get_draft(service, draft_id)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    msg = draft.message

    if output_format == "json":
        print(json.dumps(draft.model_dump(), indent=2, default=str))
    else:
        console.print(f"[bold]Draft ID:[/bold] {draft.id}")
        console.print(f"[bold]Message ID:[/bold] {msg.id}")
        console.print(f"[bold]To:[/bold] {', '.join(msg.to) if msg.to else '-'}")
        if msg.cc:
            console.print(f"[bold]CC:[/bold] {', '.join(msg.cc)}")
        console.print(f"[bold]Subject:[/bold] {msg.subject or '-'}")
        console.print()
        console.print("[bold]Body:[/bold]")
        console.print("-" * 60)
        console.print(msg.body if msg.body else "[dim]No body content[/dim]")


@drafts.command("create")
@click.argument("to")
@click.argument("subject")
@click.argument("body")
@click.option("--cc", help="CC recipients (comma-separated)")
@click.option("--bcc", help="BCC recipients (comma-separated)")
def drafts_create(to: str, subject: str, body: str, cc: str | None, bcc: str | None) -> None:
    """Create a new draft.

    Example:

    \b
      mailer drafts create "user@example.com" "Subject" "Body text"
      mailer drafts create "user@example.com" "Subject" "Body" --cc "cc@example.com"
    """
    from mailer.drafts import create_draft

    service = get_gmail_service()

    try:
        draft = create_draft(service, to=to, subject=subject, body=body, cc=cc, bcc=bcc)
        console.print(f"[green]Draft created![/green] ID: {draft.id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@drafts.command("send")
@click.argument("draft_id")
def drafts_send(draft_id: str) -> None:
    """Send a draft.

    Example:

    \b
      mailer drafts send r-8234567890123456789
    """
    from mailer.drafts import send_draft

    service = get_gmail_service()

    try:
        message_id = send_draft(service, draft_id)
        console.print(f"[green]Draft sent![/green] Message ID: {message_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@drafts.command("delete")
@click.argument("draft_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def drafts_delete(draft_id: str, force: bool) -> None:
    """Delete a draft.

    Example:

    \b
      mailer drafts delete r-8234567890123456789
      mailer drafts delete r-8234567890123456789 --force
    """
    from mailer.drafts import delete_draft

    service = get_gmail_service()

    try:

        if not force:
            if not click.confirm(f"Delete draft {draft_id}?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        delete_draft(service, draft_id)
        console.print(f"[green]Deleted draft:[/green] {draft_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


# ============ Analyze Commands ============


@main.group()
def analyze() -> None:
    """Analyze email patterns and generate reports."""
    pass


@analyze.command("sender-stats")
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option("--limit", "-n", default=20, help="Top N senders")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def sender_stats(database: str | None, limit: int, output_format: str, output: str | None) -> None:
    """Show top email senders by message count.

    Example:

    \b
      mailer analyze sender-stats
      mailer analyze sender-stats --limit 10
      mailer analyze sender-stats --format json -o senders.json
    """
    from mailer.formatters import format_dict_as_json, write_output

    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        """
        SELECT from_email, from_name, COUNT(*) as count
        FROM emails
        GROUP BY from_email
        ORDER BY count DESC
        LIMIT ?
    """,
        (limit,),
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not results:
        console.print("[yellow]No emails in database.[/yellow]")
        return

    if output_format == "json" or output:
        formatted = format_dict_as_json(results)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved sender stats to {output}[/green]")
        else:
            print(formatted)
    else:
        table = Table(title=f"Top {len(results)} Senders")
        table.add_column("#", style="dim")
        table.add_column("Sender", style="cyan")
        table.add_column("Email", style="white")
        table.add_column("Count", style="green")

        for i, row in enumerate(results, 1):
            table.add_row(
                str(i),
                row["from_name"] or "-",
                row["from_email"] or "-",
                str(row["count"]),
            )

        console.print(table)


@analyze.command("domain-stats")
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option("--limit", "-n", default=20, help="Top N domains")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def domain_stats(database: str | None, limit: int, output_format: str, output: str | None) -> None:
    """Show email distribution by domain.

    Example:

    \b
      mailer analyze domain-stats
      mailer analyze domain-stats --format json
    """
    from mailer.formatters import format_dict_as_json, write_output

    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        """
        SELECT from_domain, COUNT(*) as count
        FROM emails
        WHERE from_domain IS NOT NULL AND from_domain != ''
        GROUP BY from_domain
        ORDER BY count DESC
        LIMIT ?
    """,
        (limit,),
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not results:
        console.print("[yellow]No emails in database.[/yellow]")
        return

    if output_format == "json" or output:
        formatted = format_dict_as_json(results)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved domain stats to {output}[/green]")
        else:
            print(formatted)
    else:
        table = Table(title=f"Top {len(results)} Domains")
        table.add_column("#", style="dim")
        table.add_column("Domain", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percent", style="dim")

        total = sum(r["count"] for r in results)
        for i, row in enumerate(results, 1):
            pct = (row["count"] / total * 100) if total > 0 else 0
            table.add_row(
                str(i),
                row["from_domain"],
                str(row["count"]),
                f"{pct:.1f}%",
            )

        console.print(table)


@analyze.command("timeline")
@click.option("--database", "-d", type=click.Path(), help="Database path")
@click.option(
    "--group-by", type=click.Choice(["day", "week", "month"]), default="day", help="Time grouping"
)
@click.option("--limit", "-n", default=30, help="Number of time periods")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def timeline(
    database: str | None,
    group_by: str,
    limit: int,
    output_format: str,
    output: str | None,
) -> None:
    """Show email volume over time.

    Example:

    \b
      mailer analyze timeline
      mailer analyze timeline --group-by week
      mailer analyze timeline --group-by month --limit 12
    """
    from mailer.formatters import format_dict_as_json, write_output

    db_path = Path(database) if database else get_default_db_path()

    if not db_path.exists():
        console.print(f"[yellow]No database found at {db_path}[/yellow]")
        return

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Date format depends on grouping
    if group_by == "day":
        date_format = "%Y-%m-%d"
    elif group_by == "week":
        date_format = "%Y-W%W"
    else:  # month
        date_format = "%Y-%m"

    cursor = conn.execute(
        f"""
        SELECT
            strftime('{date_format}', datetime(timestamp/1000, 'unixepoch')) as period,
            COUNT(*) as count
        FROM emails
        WHERE timestamp > 0
        GROUP BY period
        ORDER BY period DESC
        LIMIT ?
    """,
        (limit,),
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Reverse to show chronological order
    results.reverse()

    if not results:
        console.print("[yellow]No emails in database.[/yellow]")
        return

    if output_format == "json" or output:
        formatted = format_dict_as_json(results)
        if output:
            write_output(formatted, output)
            console.print(f"[green]Saved timeline to {output}[/green]")
        else:
            print(formatted)
    else:
        table = Table(title=f"Email Volume by {group_by.capitalize()}")
        table.add_column("Period", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Bar", style="blue")

        max_count = max(r["count"] for r in results) if results else 1
        for row in results:
            bar_len = int((row["count"] / max_count) * 30)
            bar = "█" * bar_len
            table.add_row(row["period"] or "-", str(row["count"]), bar)

        console.print(table)


if __name__ == "__main__":
    main()
