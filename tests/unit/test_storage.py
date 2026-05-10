"""Tests for storage.sqlite."""
from __future__ import annotations

from xueqiu.storage.models import Post
from xueqiu.storage.sqlite import SqliteStorage


def _make_post(post_id: int, **overrides) -> Post:
    base = {
        "id": post_id,
        "symbol": "SH600519",
        "user_id": 1001,
        "user_name": "tester",
        "title": "t",
        "text": "hello",
        "created_at": "2024-05-10 10:00:00",
        "crawled_at": "2024-05-10 11:00:00",
        "source_api": "stock",
    }
    base.update(overrides)
    return Post(**base)


def test_init_schema_creates_table(tmp_db):
    s = SqliteStorage(tmp_db)
    s.init_schema()
    rows = s.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
    ).fetchall()
    assert len(rows) == 1
    s.close()


def test_save_and_count(tmp_db):
    s = SqliteStorage(tmp_db)
    s.init_schema()

    posts = [_make_post(1), _make_post(2), _make_post(3)]
    new = s.save_posts(posts)
    assert new == 3
    assert s.count() == 3
    s.close()


def test_save_dedup_by_id(tmp_db):
    s = SqliteStorage(tmp_db)
    s.init_schema()

    s.save_posts([_make_post(1), _make_post(2)])
    # second save with same ids: nothing new should land
    new = s.save_posts([_make_post(1), _make_post(2), _make_post(3)])
    assert new == 1
    assert s.count() == 3
    s.close()


def test_query_filter_by_symbol(tmp_db):
    s = SqliteStorage(tmp_db)
    s.init_schema()
    s.save_posts(
        [
            _make_post(1, symbol="SH600519"),
            _make_post(2, symbol="SZ000858"),
            _make_post(3, symbol="OTHER", mentioned_symbols="SH600519,SZ000858"),
        ]
    )

    result = s.query(symbol="SH600519")
    # post 1 matches by symbol; post 3 matches by mentioned_symbols
    ids = {r["id"] for r in result}
    assert ids == {1, 3}
    s.close()


def test_query_limit(tmp_db):
    s = SqliteStorage(tmp_db)
    s.init_schema()
    s.save_posts([_make_post(i) for i in range(1, 11)])

    result = s.query(limit=3)
    assert len(result) == 3
    s.close()


def test_count_with_symbol_filter(tmp_db):
    s = SqliteStorage(tmp_db)
    s.init_schema()
    s.save_posts(
        [
            _make_post(1, symbol="SH600519"),
            _make_post(2, symbol="SZ000858"),
            _make_post(3, symbol="SH600519"),
        ]
    )

    assert s.count(symbol="SH600519") == 2
    assert s.count() == 3
    s.close()


def test_post_from_dict_ignores_unknown_keys():
    """Parser output may have extra keys; from_dict should drop them."""
    parsed = {
        "id": 99,
        "text": "x",
        "extra_field_we_dont_know": "ignored",
    }
    p = Post.from_dict(parsed)
    assert p.id == 99
    assert p.text == "x"


def test_context_manager(tmp_db):
    with SqliteStorage(tmp_db) as s:
        s.init_schema()
        s.save_posts([_make_post(1)])
        assert s.count() == 1
    # connection closed after context exit; reopening should still work
    s2 = SqliteStorage(tmp_db)
    assert s2.count() == 1
    s2.close()
