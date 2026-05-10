"""Persistence layer.

Currently supports SQLite (default) and PostgreSQL (optional). Choose backend
via configs/*.yaml or XUEQIU_STORAGE_BACKEND env var.
"""
from xueqiu.storage.base import BaseStorage
from xueqiu.storage.models import Post


def create_storage(backend: str | None = None) -> BaseStorage:
    """Lazy import wrapper. See xueqiu.storage.factory.create_storage for details."""
    from xueqiu.storage.factory import create_storage as _impl
    return _impl(backend)


__all__ = ["BaseStorage", "Post", "create_storage"]
