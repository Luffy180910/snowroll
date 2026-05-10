"""Comment fetcher — RESERVED FOR FUTURE.

For each post, fetches replies via:
    https://xueqiu.com/v4/statuses/{status_id}/comments.json
"""
from __future__ import annotations

from collections.abc import Iterator

from xueqiu.fetchers.base import BaseFetcher, FetchResult


class CommentsFetcher(BaseFetcher):
    """Reserved. Will fetch comments for a given post id."""

    def fetch(self, status_id: int, max_pages: int = 5, **kwargs) -> Iterator[FetchResult]:  # noqa: ARG002
        raise NotImplementedError(
            "CommentsFetcher is reserved for future implementation."
        )
        yield  # pragma: no cover
