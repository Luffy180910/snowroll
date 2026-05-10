#!/usr/bin/env python3
"""Initialize the database (create tables and indexes).

Equivalent to: ``xueqiu db init``
"""
from __future__ import annotations

import sys

from xueqiu.cli import main

if __name__ == "__main__":
    sys.exit(main(["db", "init"]))
