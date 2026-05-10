"""Command-line interface.

Usage:
    xueqiu crawl stock --symbol SH600519 --pages 5
    xueqiu crawl hot --max-pages 3
    xueqiu crawl until --target 50000
    xueqiu export csv --out posts.csv [--symbol SH600519]
    xueqiu db init
    xueqiu db count [--symbol SH600519]

Each subcommand is a thin wrapper around the pipeline / storage / scheduler.
No business logic lives here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from xueqiu import __version__
from xueqiu.utils.logger import get_logger, setup_logging

log = get_logger(__name__)


# ---------- handlers ----------
def _build_pipeline():
    """Wire up browser → client → fetcher → storage → pipeline. Heavy import here."""
    from xueqiu.browser.session import BrowserSession
    from xueqiu.fetchers.stock_posts import StockPostsFetcher
    from xueqiu.http.client import XueqiuClient
    from xueqiu.pipeline.crawl_pipeline import CrawlPipeline
    from xueqiu.storage import create_storage

    session = BrowserSession()
    session.open()
    client = XueqiuClient(session)
    fetcher = StockPostsFetcher(client)
    storage = create_storage()
    storage.init_schema()
    pipeline = CrawlPipeline(fetcher, storage)
    return session, pipeline, storage


def cmd_crawl_stock(args: argparse.Namespace) -> int:
    session, pipeline, storage = _build_pipeline()
    try:
        new = pipeline.run(symbol=args.symbol, max_pages=args.pages, source=args.source, sort=args.sort)
        print(f"new rows: {new} | total in DB: {storage.count()}")
        return 0
    finally:
        storage.close()
        session.close()


def cmd_crawl_hot(args: argparse.Namespace) -> int:
    from xueqiu.pipeline.scheduler import HotMarketScheduler

    session, pipeline, storage = _build_pipeline()
    try:
        scheduler = HotMarketScheduler(pipeline)
        new = scheduler.run_one_round(max_pages=args.max_pages)
        print(f"round complete | new rows: {new} | total in DB: {storage.count()}")
        return 0
    finally:
        storage.close()
        session.close()


def cmd_crawl_until(args: argparse.Namespace) -> int:
    from xueqiu.pipeline.scheduler import HotMarketScheduler

    session, pipeline, storage = _build_pipeline()
    try:
        scheduler = HotMarketScheduler(pipeline)
        scheduler.run_until(args.target, round_interval_seconds=args.interval)
        return 0
    finally:
        storage.close()
        session.close()


def cmd_export_csv(args: argparse.Namespace) -> int:
    import pandas as pd

    from xueqiu.storage import create_storage

    storage = create_storage()
    try:
        rows = storage.query(symbol=args.symbol, limit=args.limit)
        df = pd.DataFrame(rows)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"exported {len(df)} rows to {out}")
        return 0
    finally:
        storage.close()


def cmd_db_init(args: argparse.Namespace) -> int:  # noqa: ARG001
    from xueqiu.storage import create_storage

    storage = create_storage()
    storage.init_schema()
    storage.close()
    print("database initialized.")
    return 0


def cmd_db_count(args: argparse.Namespace) -> int:
    from xueqiu.storage import create_storage

    storage = create_storage()
    try:
        print(storage.count(symbol=args.symbol))
        return 0
    finally:
        storage.close()


# ---------- arg parser ----------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="xueqiu", description="Xueqiu discussion crawler.")
    p.add_argument("--version", action="version", version=f"xueqiu-crawler {__version__}")
    p.add_argument("--log-level", default=None, help="DEBUG | INFO | WARNING | ERROR")

    sub = p.add_subparsers(dest="cmd", required=True)

    # crawl
    crawl = sub.add_parser("crawl", help="Run the crawler.").add_subparsers(dest="action", required=True)

    s = crawl.add_parser("stock", help="Crawl one stock.")
    s.add_argument("--symbol", required=True, help="e.g. SH600519")
    s.add_argument("--pages", type=int, default=10)
    s.add_argument("--source", default=None, choices=[None, "user", "all", "trans"])
    s.add_argument("--sort", default=None, choices=[None, "time", "alpha"])
    s.set_defaults(func=cmd_crawl_stock)

    h = crawl.add_parser("hot", help="One round across all configured hot stocks.")
    h.add_argument("--max-pages", type=int, default=3)
    h.set_defaults(func=cmd_crawl_hot)

    u = crawl.add_parser("until", help="Loop hot rounds until target row count.")
    u.add_argument("--target", type=int, required=True)
    u.add_argument("--interval", type=float, default=1800.0, help="seconds between rounds")
    u.set_defaults(func=cmd_crawl_until)

    # export
    export = sub.add_parser("export", help="Export data.").add_subparsers(dest="action", required=True)
    e = export.add_parser("csv")
    e.add_argument("--out", required=True)
    e.add_argument("--symbol", default=None)
    e.add_argument("--limit", type=int, default=None)
    e.set_defaults(func=cmd_export_csv)

    # db
    db = sub.add_parser("db", help="Database utilities.").add_subparsers(dest="action", required=True)
    di = db.add_parser("init", help="Create tables and indexes.")
    di.set_defaults(func=cmd_db_init)
    dc = db.add_parser("count", help="Count rows.")
    dc.add_argument("--symbol", default=None)
    dc.set_defaults(func=cmd_db_count)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    setup_logging(level=args.log_level)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
