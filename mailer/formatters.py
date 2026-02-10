"""Output formatters for email data - JSON and JSONL formats."""

import json
from datetime import datetime
from typing import Any

from mailer.types import GmailMessage, GmailThread


def format_as_json(messages: list[GmailMessage], indent: int = 2) -> str:
    """Format messages as pretty-printed JSON."""
    data = [msg.model_dump() for msg in messages]
    return json.dumps(data, indent=indent, default=_json_serializer)


def format_as_jsonl(messages: list[GmailMessage]) -> str:
    """Format messages as JSON Lines (one JSON object per line)."""
    lines = [json.dumps(msg.model_dump(), default=_json_serializer) for msg in messages]
    return "\n".join(lines)


def format_thread_as_json(thread: GmailThread, indent: int = 2) -> str:
    """Format a thread as pretty-printed JSON."""
    return json.dumps(thread.model_dump(), indent=indent, default=_json_serializer)


def format_threads_as_json(threads: list[GmailThread], indent: int = 2) -> str:
    """Format threads as pretty-printed JSON."""
    data = [t.model_dump() for t in threads]
    return json.dumps(data, indent=indent, default=_json_serializer)


def format_threads_as_jsonl(threads: list[GmailThread]) -> str:
    """Format threads as JSON Lines."""
    lines = [json.dumps(t.model_dump(), default=_json_serializer) for t in threads]
    return "\n".join(lines)


def format_dict_as_json(data: dict[str, Any] | list[dict[str, Any]], indent: int = 2) -> str:
    """Format arbitrary dict/list data as JSON."""
    return json.dumps(data, indent=indent, default=_json_serializer)


def format_dicts_as_jsonl(data: list[dict[str, Any]]) -> str:
    """Format list of dicts as JSON Lines."""
    lines = [json.dumps(item, default=_json_serializer) for item in data]
    return "\n".join(lines)


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for complex types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "model_dump"):  # Pydantic models
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def write_output(content: str, output_path: str | None) -> None:
    """Write content to file or stdout."""
    if output_path:
        from pathlib import Path

        Path(output_path).write_text(content)
    else:
        print(content)
