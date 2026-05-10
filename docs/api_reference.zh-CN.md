# 雪球 API 参考

我们使用（或计划使用）的接口。全部需要有效的 `xq_a_token` cookie。

## 当前已使用

### 单股讨论

```
GET https://xueqiu.com/query/v1/symbol/search/status.json
```

| 参数   | 类型   | 默认  | 说明                                   |
|--------|--------|-------|----------------------------------------|
| symbol | string | —     | 例如 `SH600519`, `HK00700`, `AAPL`     |
| source | string | `user` | `user` / `all` / `trans`              |
| sort   | string | `time` | `time`（最新）/ `alpha`（热度）       |
| count  | int    | 20    | 分页大小；最大 20                      |
| page   | int    | 1     | 页码；硬性上限约 10–15 页               |

**响应结构：**

```jsonc
{
  "list": [
    {
      "id": 12345,
      "user_id": 9999,
      "created_at": 1715337600000,   // 毫秒时间戳
      "title": "...",
      "text": "<p>HTML body</p>",     // HTML，包含 $stock(SYM)$ 标签
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

## 计划中（预留 fetcher）

### 帖子评论

```
GET https://xueqiu.com/v4/statuses/<status_id>/comments.json
    ?count=20&page=1
```

返回 `{ comments: [...] }`。当单个股票的讨论量较低、但单个帖子的评论量较高时很有用。

### 用户时间线

```
GET https://xueqiu.com/v4/statuses/user_timeline.json
    ?user_id=<uid>&page=<n>
```

返回与讨论接口相同的状态结构。适合跟踪特定用户（如高粉分析师）。

### 按分类热门流

```
GET https://xueqiu.com/statuses/public_timeline_by_category.json
    ?since_id=-1&max_id=-1&count=15&category=<cat>
```

| 分类 | 含义         |
|------|--------------|
| -1   | 全部         |
| 6    | A 股（沪深） |
| 7    | 港股         |
| 8    | 美股         |
| 105  | 基金         |
| 104  | 私募         |

通过 `max_id` 分页（取上一页最小 id 减 1）。

## 错误码

| 代码     | 含义                             | 处理                |
|----------|----------------------------------|---------------------|
| `0`      | 成功                             | 正常返回            |
| `400016` | Token 被拒 / 疑似异常请求         | 刷新后重试          |
| (其他)   | 业务错误                         | 终止 — 不再重试     |

## WAF 行为

雪球接入阿里云 WAF。被判定可疑时，会返回包含 `aliyun_waf_aa` / `aliyun_waf_oo` 标记与 JS 挑战的 HTML。`requests` 无法解决，只能用真实浏览器，这也是我们走 DrissionPage 的原因。

如果 API 接口请求没有有效的 WAF cookie，会拿到上述 HTML 而不是 JSON。我们的 HTTP 客户端检测到前缀为 `<` 时，会抛出 `WafBlockedError`。

## 关键 Cookies

| Cookie 名称  | 作用                                 |
|--------------|--------------------------------------|
| `xq_a_token` | 匿名 API token（必需）               |
| `xqat`       | 与 `xq_a_token` 相同（冗余副本）      |
| `u`          | 匿名设备标识                         |
| `xq_is_login`| 登录标记（`1` 表示登录，延长 token） |
| `xq_r_token` | 刷新 token（登录用户）               |
| `device_id`  | 浏览器设备指纹                       |

匿名 token 仅持续数小时；登录 token 可持续数天。长时间抓取建议提前在持久化浏览器配置中登录。
