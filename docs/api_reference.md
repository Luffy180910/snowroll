# Xueqiu API Reference

Endpoints we use (or plan to use). All require valid `xq_a_token` cookie.

## Currently used

### Per-stock discussions

```
GET https://xueqiu.com/query/v1/symbol/search/status.json
```

| Param  | Type   | Default | Description                         |
|--------|--------|---------|-------------------------------------|
| symbol | string | —       | e.g. `SH600519`, `HK00700`, `AAPL`  |
| source | string | `user`  | `user` / `all` / `trans`            |
| sort   | string | `time`  | `time` (newest) / `alpha` (popularity) |
| count  | int    | 20      | Page size; max 20                   |
| page   | int    | 1       | Page number; ~10–15 page hard ceiling |

**Response shape:**

```jsonc
{
  "list": [
    {
      "id": 12345,
      "user_id": 9999,
      "created_at": 1715337600000,   // ms timestamp
      "title": "...",
      "text": "<p>HTML body</p>",     // HTML, contains $stock(SYM)$ tags
      "reply_count": 12,
      "retweet_count": 3,
      "fav_count": 5,
      "like_count": 30,
      "view_count": 1500,
      "user": {
        "id": 9999,
        "screen_name": "...",
        "followers_count": 5000
      }
    }
  ],
  "count": 20
}
```

## Planned (reserved fetchers)

### Post comments

```
GET https://xueqiu.com/v4/statuses/<status_id>/comments.json
    ?count=20&page=1
```

Returns `{ comments: [...] }`. Useful when post discussion volume per symbol is low but per-post comment volume is high.

### User timeline

```
GET https://xueqiu.com/v4/statuses/user_timeline.json
    ?user_id=<uid>&page=<n>
```

Returns the same status shape as the discussion endpoint. Useful for tracking specific users (e.g. high-follower analysts).

### Hot stream by category

```
GET https://xueqiu.com/statuses/public_timeline_by_category.json
    ?since_id=-1&max_id=-1&count=15&category=<cat>
```

| Category | Meaning |
|----------|---------|
| -1   | All     |
| 6    | A-share (沪深) |
| 7    | HK      |
| 8    | US      |
| 105  | Funds   |
| 104  | PE      |

Pagination via `max_id` (use min id of last page minus 1).

## Error codes

| Code     | Meaning                            | Response          |
|----------|------------------------------------|-------------------|
| `0`      | Success                            | normal payload    |
| `400016` | Token rejected / suspicious request | refresh + retry   |
| (other)  | Business error                     | terminal — abort  |

## WAF behavior

Xueqiu sits behind Aliyun WAF. When suspicious, it returns an HTML page containing `aliyun_waf_aa` / `aliyun_waf_oo` markers and a JS challenge. `requests` cannot solve this; only a real browser can. That's why we route through DrissionPage.

If the API endpoint receives a request with no valid WAF cookie, you'll get this HTML rather than the JSON above. Our HTTP client detects the leading `<` and raises `WafBlockedError`.

## Cookies that matter

| Cookie name   | Purpose                                  |
|---------------|------------------------------------------|
| `xq_a_token`  | Anonymous API token (mandatory)          |
| `xqat`        | Same as `xq_a_token` (redundant copy)    |
| `u`           | Anonymous device identifier              |
| `xq_is_login` | `1` if logged in (extends token life)    |
| `xq_r_token`  | Refresh token (logged-in users)          |
| `device_id`   | Browser device fingerprint               |

Anonymous tokens last hours; logged-in tokens last days. For long-running scrapes, pre-login in the persisted browser profile.
