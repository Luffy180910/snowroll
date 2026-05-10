"""End-to-end pipeline test with a fake fetcher (no browser needed)."""
from __future__ import annotations

from collections.abc import Iterator

import pytest

from xueqiu.fetchers.base import BaseFetcher, FetchResult
from xueqiu.pipeline.crawl_pipeline import CrawlPipeline
from xueqiu.storage.sqlite import SqliteStorage


class _FakeFetcher(BaseFetcher):
    """Yields canned pages without hitting the network."""

    def __init__(self, pages: list[list[dict]]):
        # Note: bypass BaseFetcher.__init__ because we don't have a client.
        self.pages = pages

    def fetch(self, symbol: str = "TEST", **kwargs) -> Iterator[FetchResult]:  # noqa: ARG002
        for i, items in enumerate(self.pages, start=1):
            yield FetchResult(items=items, source_tag="test", symbol=symbol, page=i)


@pytest.mark.integration
def test_pipeline_run_end_to_end(tmp_db, sample_response):
    storage = SqliteStorage(tmp_db)
    storage.init_schema()

    fetcher = _FakeFetcher([sample_response["list"]])  # one page of 3 items
    pipeline = CrawlPipeline(fetcher, storage)

    new = pipeline.run(symbol="SH600519")

    assert new == 3
    assert storage.count() == 3

    rows = storage.query()
    ids = {r["id"] for r in rows}
    assert ids == {12345001, 12345002, 12345003}
    storage.close()


@pytest.mark.integration
def test_pipeline_dedup_across_runs(tmp_db, sample_response):
    storage = SqliteStorage(tmp_db)
    storage.init_schema()

    fetcher = _FakeFetcher([sample_response["list"]])
    pipeline = CrawlPipeline(fetcher, storage)

    # Run twice; second time should add 0 new
    new1 = pipeline.run(symbol="SH600519")
    new2 = pipeline.run(symbol="SH600519")

    assert new1 == 3
    assert new2 == 0
    assert storage.count() == 3
    storage.close()


@pytest.mark.integration
def test_pipeline_handles_empty_pages(tmp_db, sample_response):
    storage = SqliteStorage(tmp_db)
    storage.init_schema()

    fetcher = _FakeFetcher([sample_response["list"], []])  # second page empty
    pipeline = CrawlPipeline(fetcher, storage)

    new = pipeline.run(symbol="SH600519")

    assert new == 3  # only first page contributed
    storage.close()
