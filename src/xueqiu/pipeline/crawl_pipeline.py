"""End-to-end crawl pipeline: fetch raw items → parse → save.

Construct one CrawlPipeline per crawler instance and reuse it across calls.
The pipeline owns nothing about the *which* (which symbols, which schedule);
that's the scheduler's job.
"""
from __future__ import annotations

from collections.abc import Iterable

from xueqiu.fetchers.base import BaseFetcher
from xueqiu.parsers import parse_post
from xueqiu.storage.base import BaseStorage
from xueqiu.storage.models import Post
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)


class CrawlPipeline:
    """Glue: pulls pages from a fetcher, parses each item, persists batches."""

    def __init__(self, fetcher: BaseFetcher, storage: BaseStorage):
        self.fetcher = fetcher
        self.storage = storage

    def run(self, **fetcher_kwargs) -> int:
        """Drive one fetch session to completion. Returns *new* rows persisted."""
        total_new = 0
        total_seen = 0

        for result in self.fetcher.fetch(**fetcher_kwargs):
            if result.is_empty:
                continue

            posts = self._parse_batch(result.items, source_tag=result.source_tag, symbol=result.symbol)
            new_count = self.storage.save_posts(posts)
            total_seen += len(posts)
            total_new += new_count

            log.info(
                "[%s p%d] parsed=%d new=%d",
                result.symbol or result.source_tag,
                result.page,
                len(posts),
                new_count,
            )

        log.info(
            "pipeline run done: seen=%d new=%d (storage total=%d)",
            total_seen,
            total_new,
            self.storage.count(),
        )
        return total_new

    @staticmethod
    def _parse_batch(
        items: Iterable[dict],
        *,
        source_tag: str,
        symbol: str,
    ) -> list[Post]:
        out: list[Post] = []
        for raw in items:
            parsed = parse_post(raw, source_tag=source_tag, symbol=symbol)
            if parsed is None:
                continue
            out.append(Post.from_dict(parsed))
        return out
