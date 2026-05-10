"""SQLite-backed storage."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from xueqiu.storage.base import BaseStorage
from xueqiu.storage.models import POST_FIELD_NAMES, Post
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)

_SCHEMA_FILE = Path(__file__).parent / "schema.sql"


class SqliteStorage(BaseStorage):
    """SQLite implementation of BaseStorage.

    Connection is opened lazily and held for the lifetime of this object.
    Safe for single-thread use; for concurrent crawlers use one instance per
    thread, or upgrade to ``PostgresStorage``.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_schema(self) -> None:
        sql = _SCHEMA_FILE.read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()
        log.info("schema initialized at %s", self.db_path)

    def save_posts(self, posts: Iterable[Post]) -> int:
        placeholders = ", ".join(["?"] * len(POST_FIELD_NAMES))
        cols = ", ".join(POST_FIELD_NAMES)
        sql = f"INSERT OR IGNORE INTO posts ({cols}) VALUES ({placeholders})"

        rows = [tuple(getattr(p, name) for name in POST_FIELD_NAMES) for p in posts]
        if not rows:
            return 0

        cur = self.conn.executemany(sql, rows)
        self.conn.commit()
        return cur.rowcount or 0

    def count(self, *, symbol: str | None = None) -> int:
        if symbol:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM posts WHERE symbol = ? OR mentioned_symbols LIKE ?",
                (symbol, f"%{symbol}%"),
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COUNT(*) FROM posts").fetchone()
        return row[0]

    def query(
        self,
        *,
        symbol: str | None = None,
        limit: int | None = None,
        order_by_created_desc: bool = True,
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM posts"
        params: list[Any] = []
        if symbol:
            sql += " WHERE symbol = ? OR mentioned_symbols LIKE ?"
            params.extend([symbol, f"%{symbol}%"])
        if order_by_created_desc:
            sql += " ORDER BY created_at DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
