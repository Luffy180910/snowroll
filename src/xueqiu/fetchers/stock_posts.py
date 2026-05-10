"""Fetch discussion posts for one stock symbol."""
from __future__ import annotations

from collections.abc import Iterator

from xueqiu.config import get_settings
from xueqiu.fetchers.base import BaseFetcher, FetchResult
from xueqiu.http.exceptions import ApiError
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)

# Endpoint constant — kept here because it's specific to this fetcher.
_API_URL = "https://xueqiu.com/query/v1/symbol/search/status.json"


class StockPostsFetcher(BaseFetcher):
    """Pages through Xueqiu's per-stock discussion API."""

    def fetch(
        self,
        symbol: str,
        *,
        max_pages: int | None = None,
        source: str | None = None,
        sort: str | None = None,
    ) -> Iterator[FetchResult]:
        """Yield pages of raw API items for a given symbol.

        :param symbol: e.g. ``SH600519``
        :param source: ``user`` (discussions) | ``all`` | ``trans`` (trades)
        :param sort: ``time`` (newest) | ``alpha`` (popularity)
        """
        cfg = get_settings().crawl
        max_pages = max_pages or cfg.default_max_pages
        source = source or cfg.default_source
        sort = sort or cfg.default_sort

        log.info("fetching %s posts (source=%s, sort=%s, max_pages=%d)", symbol, source, sort, max_pages)

        for page in range(1, max_pages + 1):
            params = {
                "symbol": symbol,
                "source": source,
                "sort": sort,
                "count": cfg.page_size,
                "page": page,
            }
            try:
                data = self.client.get_json(_API_URL, params)
            except ApiError as e:
                log.error("[%s] API error %s; stopping", symbol, e.code)
                return

            if data is None:
                log.warning("[%s] page %d failed after retries; stopping", symbol, page)
                return

            items = data.get("list") or []
            yield FetchResult(items=items, source_tag="stock", symbol=symbol, page=page)

            if not items:
                log.info("[%s] page %d empty; stopping", symbol, page)
                return

            self.client.request_delay()
