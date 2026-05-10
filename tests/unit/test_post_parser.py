"""Tests for parsers.post_parser."""
from __future__ import annotations

from xueqiu.parsers.post_parser import parse_post


def test_parse_returns_none_for_empty():
    assert parse_post({}, source_tag="x") is None
    assert parse_post({"foo": "bar"}, source_tag="x") is None


def test_parse_basic_post(sample_post):
    result = parse_post(sample_post, source_tag="stock", symbol="SH600519")

    assert result is not None
    assert result["id"] == 12345001
    assert result["symbol"] == "SH600519"
    assert result["user_id"] == 9999001
    assert result["user_name"] == "价值投资者"
    assert result["user_followers"] == 5000
    assert result["title"] == "茅台年报点评"
    # html stripped
    assert "<p>" not in result["text"]
    assert "业绩稳健" in result["text"]
    # symbols extracted
    assert "SH600519" in result["mentioned_symbols"]
    # numeric counters preserved
    assert result["reply_count"] == 12
    assert result["like_count"] == 30
    assert result["view_count"] == 1500
    # source_tag passed through
    assert result["source_api"] == "stock"
    # timestamps converted
    assert result["created_at"] is not None
    assert result["crawled_at"] is not None


def test_parse_multi_symbol_post(sample_response):
    raw = sample_response["list"][1]
    result = parse_post(raw, source_tag="stock", symbol="SH600519")

    # post mentioned 2 different symbols (neither equals the one we passed)
    assert "SZ300750" in result["mentioned_symbols"]
    assert "SZ002594" in result["mentioned_symbols"]


def test_parse_nested_status_wrapper(sample_response):
    """Some endpoints wrap the status in {'status': {...}}."""
    raw = sample_response["list"][2]
    assert "status" in raw

    result = parse_post(raw, source_tag="hot")

    assert result is not None
    assert result["id"] == 12345003
    assert result["text"] == "纯文本帖子,无标签"
    assert result["mentioned_symbols"] == ""  # no symbols in this one


def test_parse_missing_optional_fields():
    minimal = {
        "id": 999,
        "text": "hello",
        "user": {"screen_name": "x"},
    }
    result = parse_post(minimal, source_tag="test")

    assert result["id"] == 999
    assert result["user_followers"] == 0
    assert result["reply_count"] == 0
    assert result["like_count"] == 0
    assert result["category"] == ""
