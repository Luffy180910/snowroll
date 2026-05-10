"""Hot-stream fetcher — RESERVED FOR FUTURE.

The original codebase replaced this with multi-symbol coverage because the
public hot-stream API became unstable. Keeping this stub so a future
re-introduction (e.g. the public_timeline_by_category endpoint) drops in
without touching the pipeline layer.
"""
from __future__ import annotations

from collections.abc import Iterator

from xueqiu.fetchers.base import BaseFetcher, FetchResult


class HotStreamFetcher(BaseFetcher):
    """Reserved. Will fetch from public_timeline_by_category.json or similar."""

    def fetch(self, **kwargs) -> Iterator[FetchResult]:  # noqa: ARG002
        raise NotImplementedError(
            "HotStreamFetcher is reserved for future use. "
            "Use StockPostsFetcher across multiple symbols instead "
            "(see hot_stocks list in configs/default.yaml)."
        )
        yield  # pragma: no cover  -- makes the function a generator for typing
