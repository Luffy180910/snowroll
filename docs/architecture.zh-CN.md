# 架构

## 分层

```
┌─────────────────────────────────────────┐
│  cli.py / scripts                       │  入口 — 仅 argparse
├─────────────────────────────────────────┤
│  pipeline / scheduler                   │  唯一能同时看到 fetcher + parser + storage 的层
├─────────────────────────────────────────┤
│  fetchers       │   parsers   │ storage │
│  （按数据源）   │   （纯函数）│ （ABC） │
├─────────────────┴─────────────┴─────────┤
│  http.client          （请求 + 重试）    │  抛出类型化异常
├─────────────────────────────────────────┤
│  browser.session       （Chrome + cookie）│  持有唯一的 Chrome 实例
├─────────────────────────────────────────┤
│  config / utils                         │  通用基础设施
└─────────────────────────────────────────┘
```

## 规则（通过代码评审约束，不由工具强制）

1. **`parsers/` 仅依赖 stdlib + `utils/timeutils`。** 它们是纯函数；给定输入 X，总能产出输出 Y。易于单测与推理。

2. **`storage/` 不认识 fetchers、http 或 browser。** 存储后端可用手工构造的 `Post` 对象测试。替换 SQLite → PostgreSQL → DuckDB 不需要其他改动。

3. **`fetchers/` 不存储。** 每个 fetcher 只负责 URL、参数与响应结构，产出 `FetchResult` 页面。不写磁盘，不调用 parser。

4. **`http.client` 抛出类型化异常，而不是 None。** 调用方（fetcher）根据异常类型决定重试或终止：
   - `WafBlockedError` → 刷新后重试
   - `TokenExpiredError` → 刷新后重试
   - `EmptyResponseError` → 软重试
   - `ApiError` → 终止，不重试

5. **`browser.session` 持有唯一的 Chrome 实例。** 所有需要浏览器的逻辑都通过它，避免意外启动 N 个 Chrome。

6. **`pipeline/` 是唯一的拼接点。** 它从 fetcher 拉取，运行 parser，并通过 storage 持久化。其他层不组合这三者。

7. **`cli.py` 不含业务逻辑。** 仅解析参数并调用 pipeline / storage / scheduler。这样同一逻辑可被脚本或未来 REST 接口复用。

## 为何这样划分

最初的 `XueqiuCrawler` 是一个包揽一切的类：启动 Chrome、管理 cookie、发请求、解析 HTML、写 SQL、遍历市场。带来三类痛点：

- **不可测试。** 不启动 Chrome 就无法测试 HTML 清洗。
- **难以扩展。** “为每个帖子抓评论”必须改动那个包揽一切的类。
- **联动修改。** 迁移到 PostgreSQL 会改到 parser 同一个文件。

以上规则逐一解决这些问题。

## 数据流

```
                    ┌──────────────┐
   用户 CLI  ─────►  │  cli.py      │
                    └──────┬───────┘
                           │ 负责组装
                           ▼
            ┌─────────────────────────────┐
            │  CrawlPipeline              │
            └─┬──────────┬─────────┬──────┘
              │          │         │
              ▼          ▼         ▼
        ┌────────┐  ┌────────┐  ┌─────────┐
        │Fetcher │  │ Parser │  │ Storage │
        └───┬────┘  └────────┘  └─────────┘
            │
            ▼
        ┌────────┐
        │ Client │ ───► 抛出 WafBlockedError / TokenExpiredError / ApiError
        └───┬────┘
            ▼
        ┌─────────┐
        │ Session │ ───► Chrome（DrissionPage）
        └─────────┘
```

一页数据的流向：`Session.tab.get(url)` → `Client.get_json` → fetcher 的 `FetchResult` → pipeline 解析 → `Storage.save_posts` → SQLite/Postgres。

## 配置加载

三层覆盖，后者优先生效：

1. `configs/default.yaml` — 版本库默认值。
2. `configs/{XUEQIU_ENV}.yaml` — 环境覆盖（`dev` 或 `prod`）。
3. 以 `XUEQIU_` 为前缀的环境变量（可用 `__` 表示层级）。
4. `.env` 的值会先注入环境变量，因此第 3 步可读取。

Pydantic 校验合并后的结果。调用方始终通过 `xueqiu.config.get_settings()` 获取配置，避免直接读 `os.environ`。

## 扩展点（预留）

| 方向 | 位置 | 状态 |
|---|---|---|
| 评论抓取 | `fetchers/comments.py` | stub，抛出 NotImplementedError |
| 用户时间线 | `fetchers/user_timeline.py` | stub，抛出 NotImplementedError |
| 热门流 API | `fetchers/hot_stream.py` | stub，抛出 NotImplementedError |
| 情绪评分 | `nlp/` 包 | 空包，带 docstring 规范 |
| 未来 A 股基本面 | `fetchers/<new_file>.py` | 直接新增文件 |
| 分布式调度 | 替换 `pipeline/scheduler.py` | 单文件替换 |
