"""Local email storage for incremental fetching and caching."""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from mailer.types import GmailMessage


class StorageIndex(BaseModel):
    """Index of stored emails for quick lookups."""

    version: int = 1
    last_sync: str = ""
    message_ids: set[str] = Field(default_factory=set)
    total_messages: int = 0


class EmailStorage:
    """Local storage for Gmail messages with incremental sync support."""

    def __init__(self, storage_dir: Path | str) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self.messages_dir = self.storage_dir / "messages"
        self.messages_dir.mkdir(exist_ok=True)
        self._index: StorageIndex | None = None

    @property
    def index(self) -> StorageIndex:
        """Load or create the storage index."""
        if self._index is None:
            if self.index_file.exists():
                data = json.loads(self.index_file.read_text())
                # Convert list to set for message_ids
                data["message_ids"] = set(data.get("message_ids", []))
                self._index = StorageIndex(**data)
            else:
                self._index = StorageIndex()
        return self._index

    def _save_index(self) -> None:
        """Save the index to disk."""
        data = self.index.model_dump()
        # Convert set to list for JSON serialization
        data["message_ids"] = list(data["message_ids"])
        self.index_file.write_text(json.dumps(data, indent=2))

    def has_message(self, message_id: str) -> bool:
        """Check if a message is already stored."""
        return message_id in self.index.message_ids

    def get_new_message_ids(self, message_ids: list[str]) -> list[str]:
        """Filter to only message IDs not already stored."""
        return [mid for mid in message_ids if mid not in self.index.message_ids]

    def store_message(self, message: GmailMessage) -> None:
        """Store a single message."""
        msg_file = self.messages_dir / f"{message.id}.json"
        msg_file.write_text(message.model_dump_json(indent=2))
        self.index.message_ids.add(message.id)
        self.index.total_messages = len(self.index.message_ids)

    def store_messages(self, messages: list[GmailMessage]) -> int:
        """Store multiple messages, return count of newly stored."""
        stored = 0
        for msg in messages:
            if not self.has_message(msg.id):
                self.store_message(msg)
                stored += 1
        self.index.last_sync = datetime.now().isoformat()
        self._save_index()
        return stored

    def load_message(self, message_id: str) -> GmailMessage | None:
        """Load a single message from storage."""
        msg_file = self.messages_dir / f"{message_id}.json"
        if msg_file.exists():
            return GmailMessage.model_validate_json(msg_file.read_text())
        return None

    def load_all_messages(self) -> list[GmailMessage]:
        """Load all stored messages."""
        messages = []
        for msg_file in self.messages_dir.glob("*.json"):
            try:
                msg = GmailMessage.model_validate_json(msg_file.read_text())
                messages.append(msg)
            except Exception:
                continue  # Skip corrupted files
        return messages

    def get_stats(self) -> dict:
        """Get storage statistics."""
        return {
            "storage_dir": str(self.storage_dir),
            "total_messages": self.index.total_messages,
            "last_sync": self.index.last_sync,
        }


def get_default_storage_dir() -> Path:
    """Get the default storage directory."""
    return Path.home() / ".mailer" / "emails"
