"""Domain data models. Pure dataclasses, framework-agnostic.

Why dataclass and not Pydantic?
    - Storage layer is the boundary between dicts (from API/parser) and
      typed records. We want minimal coercion and zero validation overhead
      on the hot path.
    - Pydantic is used only at the configuration boundary.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class Post:
    """A single Xueqiu discussion post."""

    id: int
    symbol: str = ""
    user_id: int | None = None
    user_name: str | None = None
    user_followers: int = 0
    created_at: str | None = None
    title: str = ""
    text: str = ""
    mentioned_symbols: str = ""
    reply_count: int = 0
    retweet_count: int = 0
    fav_count: int = 0
    like_count: int = 0
    view_count: int = 0
    source_api: str = ""
    category: str = ""
    crawled_at: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Post:
        """Build a Post from a parser-output dict, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Mirror of dataclass field order — used to build (?, ?, ...) tuples for SQL.
POST_FIELD_NAMES: tuple[str, ...] = tuple(f.name for f in fields(Post))
