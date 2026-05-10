"""Parse a raw Xueqiu API item into our normalized post dict."""
from __future__ import annotations

from typing import Any

from xueqiu.parsers.html_cleaner import clean_html
from xueqiu.parsers.symbol_extractor import extract_symbols
from xueqiu.utils.timeutils import now_str, ts_ms_to_str


def parse_post(
    raw: dict[str, Any],
    *,
    source_tag: str,
    symbol: str = "",
) -> dict[str, Any] | None:
    """Convert one raw API item to a normalized post dict.

    Returns None if the item lacks an id (malformed/empty).

    The ``raw`` dict can be either:
        - A direct status dict (most endpoints), or
        - A wrapper dict with a nested ``status`` key (some hot-stream endpoints).
    """
    nested = raw.get("status")
    item = nested if isinstance(nested, dict) else raw

    post_id = item.get("id")
    if not post_id:
        return None

    text_html = item.get("text") or item.get("description") or ""
    user = item.get("user") or {}

    return {
        "id": post_id,
        "symbol": symbol,
        "user_id": item.get("user_id") or user.get("id"),
        "user_name": user.get("screen_name"),
        "user_followers": user.get("followers_count", 0),
        "created_at": ts_ms_to_str(item.get("created_at")),
        "title": item.get("title") or "",
        "text": clean_html(text_html),
        "mentioned_symbols": ",".join(extract_symbols(text_html)),
        "reply_count": item.get("reply_count", 0),
        "retweet_count": item.get("retweet_count", 0),
        "fav_count": item.get("fav_count", 0),
        "like_count": item.get("like_count", 0),
        "view_count": item.get("view_count", 0),
        "source_api": source_tag,
        "category": str(item.get("category", "")),
        "crawled_at": now_str(),
    }
