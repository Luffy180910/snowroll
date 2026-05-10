"""Storage backend factory.

Usage:
    from xueqiu.storage import create_storage
    storage = create_storage()  # reads config
    storage.init_schema()
    storage.save_posts([...])
"""
from __future__ import annotations

from xueqiu.config import get_settings
from xueqiu.storage.base import BaseStorage


def create_storage(backend: str | None = None) -> BaseStorage:
    """Construct a storage backend per config (or explicit override).

    :param backend: ``sqlite`` or ``postgres``. None = read from config.
    """
    cfg = get_settings().storage
    backend = (backend or cfg.backend).lower()

    if backend == "sqlite":
        from xueqiu.storage.sqlite import SqliteStorage
        return SqliteStorage(cfg.sqlite_path)

    if backend == "postgres":
        from xueqiu.storage.postgres import PostgresStorage
        if not cfg.pg_dsn:
            raise ValueError("postgres backend selected but pg_dsn not configured")
        return PostgresStorage(cfg.pg_dsn)

    raise ValueError(f"unknown storage backend: {backend!r}")
