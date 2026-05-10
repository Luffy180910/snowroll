#!/usr/bin/env python3
"""Export posts to CSV.

Equivalent to: ``xueqiu export csv --out OUT [--symbol SYM] [--limit N]``
"""
from __future__ import annotations

import argparse
import sys

from xueqiu.cli import main

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Export Xueqiu posts to CSV.")
    p.add_argument("--out", default="data/exports/posts.csv")
    p.add_argument("--symbol", default=None)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    argv = ["export", "csv", "--out", args.out]
    if args.symbol:
        argv += ["--symbol", args.symbol]
    if args.limit is not None:
        argv += ["--limit", str(args.limit)]
    sys.exit(main(argv))
