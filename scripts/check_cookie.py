#!/usr/bin/env python3
"""Diagnose cookie / WAF status.

Opens a browser, warms it up, prints which key cookies were obtained, then
makes one test API call against the stock posts endpoint.

Useful when the crawler stops working: tells you whether (a) the browser
can reach Xueqiu at all, (b) WAF is letting cookies through, (c) the API
returns business errors.
"""
from __future__ import annotations

import sys

from xueqiu.browser.session import BrowserSession
from xueqiu.http.client import XueqiuClient
from xueqiu.utils.logger import setup_logging


def main() -> int:
    setup_logging("INFO")
    session = BrowserSession()
    try:
        session.open()
        cookies = {c["name"]: c["value"] for c in session.cookies()}
        print(f"\nGot {len(cookies)} cookies. Critical fields:")
        for key in ("xq_a_token", "xqat", "u", "xq_is_login", "device_id"):
            present = "✓" if key in cookies else "✗"
            print(f"  [{present}] {key}")

        client = XueqiuClient(session)
        print("\nTest API call: SH600519 page 1 ...")
        data = client.get_json(
            "https://xueqiu.com/query/v1/symbol/search/status.json",
            {"symbol": "SH600519", "source": "user", "sort": "time", "count": 5, "page": 1},
        )
        if data is None:
            print("FAILED — see logs above")
            return 1

        items = data.get("list", [])
        print(f"  -> got {len(items)} items")
        if items:
            print(f"  -> first item id={items[0].get('id')}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
