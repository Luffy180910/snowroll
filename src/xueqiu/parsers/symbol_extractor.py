"""Extract stock symbols mentioned in a Xueqiu post body."""
from __future__ import annotations

import re

# Matches Xueqiu's $StockName(SYMBOL)$ syntax inside post text.
_DOLLAR_PATTERN = re.compile(r"\$[^$()]+\(([A-Z]{0,2}\d{4,6}|[A-Z]+)\)\$")
# Matches data-code attributes in rendered <a> tags.
_LINK_PATTERN = re.compile(r'data-code="([A-Z]{0,2}\d{4,6}|[A-Z]+)"')


def extract_symbols(html: str | None) -> list[str]:
    """Return sorted list of unique stock symbols mentioned in the HTML.

    Recognizes:
        - $茅台(SH600519)$ — the Xueqiu inline tag
        - <a data-code="SH600519"> — rendered links

    Returns [] for None/empty input.
    """
    if not html:
        return []
    found = set(_DOLLAR_PATTERN.findall(html)) | set(_LINK_PATTERN.findall(html))
    return sorted(found)
