"""Tests for parsers.html_cleaner."""
from __future__ import annotations

import pytest

from xueqiu.parsers.html_cleaner import clean_html


@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, ""),
        ("", ""),
        ("plain text", "plain text"),
        ("<p>hello</p>", "hello"),
        ("<p>a</p><p>b</p>", "a b"),
        ("a&nbsp;b", "a b"),
        ("a&amp;b", "a&b"),
        ("&lt;tag&gt;", "<tag>"),
        ("&quot;quoted&quot;", '"quoted"'),
        ("it&#39;s", "it's"),
        ("  multi   space  ", "multi space"),
        ("<p>line1</p>\n<p>line2</p>", "line1 line2"),
    ],
)
def test_clean_html(raw, expected):
    assert clean_html(raw) == expected


def test_clean_html_real_post():
    raw = '<p>$贵州茅台(SH600519)$ 业绩稳健,&nbsp;现金流充沛。<a data-code="SH600519">链接</a></p>'
    cleaned = clean_html(raw)
    # tags stripped, entities decoded, dollar tags preserved (they're not HTML)
    assert "$贵州茅台(SH600519)$" in cleaned
    assert "业绩稳健" in cleaned
    assert "<" not in cleaned
    assert "&nbsp;" not in cleaned
