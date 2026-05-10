"""Business-level fetchers — each knows the URL, params, and response shape
of one Xueqiu data source. They do NOT make HTTP calls or persist data;
they delegate I/O to ``XueqiuClient`` and yield raw API items.

Adding a new data source means: add a file here, no other layer changes.

Concrete fetchers are intentionally NOT re-exported from this package — import
them directly so that unit tests of one fetcher don't drag in unrelated
dependencies (e.g. DrissionPage from another fetcher).

    from xueqiu.fetchers.stock_posts import StockPostsFetcher
"""
from xueqiu.fetchers.base import BaseFetcher, FetchResult

__all__ = ["BaseFetcher", "FetchResult"]
