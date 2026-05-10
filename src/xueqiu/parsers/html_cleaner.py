"""HTML → plain text cleaner for Xueqiu post bodies."""
from __future__ import annotations

import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_HTML_ENTITIES: tuple[tuple[str, str], ...] = (
    ("&nbsp;", " "),
    ("&amp;", "&"),
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&quot;", '"'),
    ("&#39;", "'"),
)


def clean_html(html: str | None) -> str:
    """Strip HTML tags, collapse whitespace, decode common entities.

    Pure function — no IO, no logging. Returns "" for None/empty input.
    """
    if not html:
        return ""
    text = _TAG_RE.sub(" ", html)
    text = _WS_RE.sub(" ", text).strip()
    for entity, replacement in _HTML_ENTITIES:
        text = text.replace(entity, replacement)
    return text
