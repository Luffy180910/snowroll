"""PostgreSQL-backed storage. Optional — requires `pip install xueqiu-crawler[postgres]`."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from xueqiu.storage.base import BaseStorage
from xueqiu.storage.models import POST_FIELD_NAMES, Post
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)

_SCHEMA_FILE = Path(__file__).parent / "schema_pg.sql"

try:
    import psycopg
    from psycopg import sql as pgsql
    _HAS_PSYCOPG = True
except ImportError:  # pragma: no cover
    _HAS_PSYCOPG = False


class PostgresStorage(BaseStorage):
    """PostgreSQL implementation. Uses psycopg3."""

    def __init__(self, dsn: str):
        if not _HAS_PSYCOPG:
            raise RuntimeError(
                "psycopg is not installed. Install with: pip install -e '.[postgres]'"
            )
        self.dsn = dsn
        self._conn: psycopg.Connection | None = None

    @property
    def conn(self) -> "psycopg.Connection":
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.dsn, autocommit=False)
        return self._conn

    def init_schema(self) -> None:
        sql_text = _SCHEMA_FILE.read_text(encoding="utf-8")
        with self.conn.cursor() as cur:
            cur.execute(sql_text)
        self.conn.commit()
        log.info("postgres schema initialized")

    def save_posts(self, posts: Iterable[Post]) -> int:
        rows = [tuple(getattr(p, name) for name in POST_FIELD_NAMES) for p in posts]
        if not rows:
            return 0

        cols = pgsql.SQL(", ").join(pgsql.Identifier(n) for n in POST_FIELD_NAMES)
        placeholders = pgsql.SQL(", ").join(pgsql.Placeholder() * len(POST_FIELD_NAMES))
        query = pgsql.SQL(
            "INSERT INTO posts ({cols}) VALUES ({ph}) ON CONFLICT (id) DO NOTHING"
        ).format(cols=cols, ph=placeholders)

        new_count = 0
        with self.conn.cursor() as cur:
            for row in rows:
                cur.execute(query, row)
                new_count += cur.rowcount
        self.conn.commit()
        return new_count

    def count(self, *, symbol: str | None = None) -> int:
        with self.conn.cursor() as cur:
            if symbol:
                cur.execute(
                    "SELECT COUNT(*) FROM posts WHERE symbol = %s OR mentioned_symbols LIKE %s",
                    (symbol, f"%{symbol}%"),
                )
            else:
                cur.execute("SELECT COUNT(*) FROM posts")
            return cur.fetchone()[0]

    def query(
        self,
        *,
        symbol: str | None = None,
        limit: int | None = None,
        order_by_created_desc: bool = True,
    ) -> list[dict[str, Any]]:
        sql_str = "SELECT * FROM posts"
        params: list[Any] = []
        if symbol:
            sql_str += " WHERE symbol = %s OR mentioned_symbols LIKE %s"
            params.extend([symbol, f"%{symbol}%"])
        if order_by_created_desc:
            sql_str += " ORDER BY created_at DESC"
        if limit:
            sql_str += " LIMIT %s"
            params.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(sql_str, params)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.close()
        self._conn = None
