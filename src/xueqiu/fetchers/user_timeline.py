"""User-timeline fetcher — RESERVED FOR FUTURE.

For each tracked user, fetches their post history via:
    https://xueqiu.com/v4/statuses/user_timeline.json?user_id={uid}&page=N
"""
from __future__ import annotations

from collections.abc import Iterator

from xueqiu.fetchers.base import BaseFetcher, FetchResult


class UserTimelineFetcher(BaseFetcher):
    """Reserved. Will page through a user's post history."""

    def fetch(self, user_id: int, max_pages: int = 5, **kwargs) -> Iterator[FetchResult]:  # noqa: ARG002
        raise NotImplementedError(
            "UserTimelineFetcher is reserved for future implementation."
        )
        yield  # pragma: no cover
