"""Schedulers — long-running drivers that orchestrate many pipeline runs.

The hot-market scheduler walks each market's representative symbols and
loops on demand to accumulate volume over time.
"""
from __future__ import annotations

import random
import time
from datetime import datetime

from xueqiu.config import get_settings
from xueqiu.pipeline.crawl_pipeline import CrawlPipeline
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)


class HotMarketScheduler:
    """Cycles through representative stocks across markets and accumulates posts."""

    def __init__(self, pipeline: CrawlPipeline):
        self.pipeline = pipeline
        self.settings = get_settings()

    def run_one_round(self, *, max_pages: int | None = None) -> int:
        """Run one full pass over all configured hot stocks. Returns total new rows."""
        crawl_cfg = self.settings.crawl
        max_pages = max_pages or crawl_cfg.default_max_pages

        markets = {
            "cn_a": self.settings.hot_stocks.cn_a,
            "hk":   self.settings.hot_stocks.hk,
            "us":   self.settings.hot_stocks.us,
        }
        log.info("====== %s — round start ======", datetime.now().isoformat(timespec="seconds"))

        total_new = 0
        for market, symbols in markets.items():
            if not symbols:
                continue
            log.info("--- market: %s (%d symbols) ---", market, len(symbols))
            for sym in symbols:
                new = self.pipeline.run(symbol=sym, max_pages=max_pages)
                total_new += new
                self._inter_stock_sleep()

        log.info("====== round done — new=%d total_in_db=%d ======",
                 total_new, self.pipeline.storage.count())
        return total_new

    def run_until(self, target_count: int, *, round_interval_seconds: float = 1800.0) -> None:
        """Loop rounds until storage holds ``target_count`` rows.

        :param round_interval_seconds: sleep between rounds (default 30 min).
        """
        while True:
            current = self.pipeline.storage.count()
            if current >= target_count:
                log.info("target reached: %d ≥ %d — stopping", current, target_count)
                return
            self.run_one_round()
            log.info("sleeping %.0f min before next round", round_interval_seconds / 60)
            time.sleep(round_interval_seconds)

    def _inter_stock_sleep(self) -> None:
        cfg = self.settings.crawl
        time.sleep(random.uniform(cfg.inter_stock_delay_min, cfg.inter_stock_delay_max))
