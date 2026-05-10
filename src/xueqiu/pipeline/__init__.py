"""Pipeline layer — orchestrates fetcher → parser → storage.

This is the only layer that knows about all three; fetchers don't store,
storage doesn't fetch, parsers do neither. Pipelines are the seams where
business logic lives.

    from xueqiu.pipeline.crawl_pipeline import CrawlPipeline
    from xueqiu.pipeline.scheduler import HotMarketScheduler
"""
from xueqiu.pipeline.crawl_pipeline import CrawlPipeline

__all__ = ["CrawlPipeline"]
