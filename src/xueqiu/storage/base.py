"""Storage backend abstract interface.

Any concrete backend (SQLite, PostgreSQL, ...) must implement these methods.
Pipelines depend on this ABC, not concrete classes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from xueqiu.storage.models import Post


class BaseStorage(ABC):
    """Abstract storage interface for posts.

    Implements the context-manager protocol so callers can use ``with``.
    """

    @abstractmethod
    def init_schema(self) -> None:
        """Create tables and indexes if they don't exist. Idempotent."""

    @abstractmethod
    def save_posts(self, posts: Iterable[Post]) -> int:
        """Bulk insert (with dedup on PK). Returns count of *new* rows."""

    @abstractmethod
    def count(self, *, symbol: str | None = None) -> int:
        """Count rows, optionally filtered by symbol."""

    @abstractmethod
    def query(
        self,
        *,
        symbol: str | None = None,
        limit: int | None = None,
        order_by_created_desc: bool = True,
    ) -> list[dict[str, Any]]:
        """Generic read for inspection / export. Returns list of dicts."""

    @abstractmethod
    def close(self) -> None:
        """Release any underlying resources."""

    # Context manager plumbing
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
