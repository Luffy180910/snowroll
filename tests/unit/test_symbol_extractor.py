"""Tests for parsers.symbol_extractor."""
from __future__ import annotations

import pytest

from xueqiu.parsers.symbol_extractor import extract_symbols


def test_empty_input():
    assert extract_symbols(None) == []
    assert extract_symbols("") == []


def test_no_symbols():
    assert extract_symbols("just plain text without anything special") == []


def test_dollar_pattern_a_share():
    text = "看好 $贵州茅台(SH600519)$ 长期"
    assert extract_symbols(text) == ["SH600519"]


def test_dollar_pattern_us_share():
    text = "$Apple(AAPL)$ very strong"
    assert extract_symbols(text) == ["AAPL"]


def test_dollar_pattern_hk_share():
    text = "$腾讯控股(HK00700)$"
    assert extract_symbols(text) == ["HK00700"]


def test_data_code_attr():
    text = '<a data-code="SZ000858">五粮液</a>'
    assert extract_symbols(text) == ["SZ000858"]


def test_multiple_unique_sorted():
    text = "$A(SZ300750)$ and $B(SH600519)$ and $C(SH600519)$"
    # deduplicated and sorted
    assert extract_symbols(text) == ["SH600519", "SZ300750"]


def test_mixed_dollar_and_link():
    text = '$茅台(SH600519)$ <a data-code="SZ000858">五粮液</a>'
    assert extract_symbols(text) == ["SH600519", "SZ000858"]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$test(SH600000)$", ["SH600000"]),
        ("$test(SZ000001)$", ["SZ000001"]),
        ("$test(NVDA)$", ["NVDA"]),
        ("$test(GOOGL)$", ["GOOGL"]),
    ],
)
def test_various_formats(text, expected):
    assert extract_symbols(text) == expected
