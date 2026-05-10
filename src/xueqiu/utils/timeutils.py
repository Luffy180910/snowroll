"""Time-related helpers (pure functions)."""
from __future__ import annotations

from datetime import datetime


def ts_ms_to_str(ts_ms: int | float | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str | None:
    """Convert millisecond timestamp to local-time string. Returns None on falsy input."""
    if not ts_ms:
        return None
    return datetime.fromtimestamp(ts_ms / 1000).strftime(fmt)


def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Current local time as string."""
    return datetime.now().strftime(fmt)
