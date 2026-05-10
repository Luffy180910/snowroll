# snowroll

面向 [雪球 (xueqiu.com)](https://xueqiu.com) 讨论区的工程化爬虫，为后续情绪分析/舆情分析提供数据基础。

English README: [README.md](README.md)

---

## 功能

- **真实浏览器绕过 WAF** — DrissionPage 启动 Chrome，通过 JS 挑战后复用会话。
- **分层架构** — browser / http / fetcher / parser / storage / pipeline / cli 各司其职。
- **双存储后端** — SQLite（默认）用于原型，PostgreSQL 用于生产。
- **配置驱动** — YAML + 环境变量，dev / prod / default 三套配置。
- **测试覆盖** — 解析器与存储单元测试，管道集成测试。
- **CLI** — `xueqiu crawl stock`、`xueqiu crawl hot`、`xueqiu crawl until`、`xueqiu export csv`、`xueqiu db init`。
- **预留扩展点** — 评论、用户时间线、热榜、NLP/情绪分析。

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/Luffy180910/snowroll
cd snowroll

# 任选其一：
make install         # 基础（仅 sqlite）
make install-dev     # + pytest, ruff, mypy
make install-all     # + postgres, nlp, dev
```

需要 Python 3.10+，并本机已安装 Chrome / Chromium。

### 2. 配置

```bash
cp .env.example .env
# 如需改动请编辑 .env（SQLite 默认即可）
```

### 3. 初始化数据库

```bash
make init-db
```

### 4. 抓取

```bash
# 单只股票，5 页：
make crawl-stock SYMBOL=SH600519 PAGES=5

# 配置的热门股票（一次轮询）：
make crawl-hot

# 或直接使用 CLI：
xueqiu crawl stock --symbol SH600519 --pages 10
xueqiu crawl hot --max-pages 3
xueqiu crawl until --target 50000 --interval 1800
```

### 5. 查看 / 导出

```bash
xueqiu db count                          # 总行数
xueqiu db count --symbol SH600519        # 含指定股票的行数
xueqiu export csv --out posts.csv
xueqiu export csv --out maotai.csv --symbol SH600519
```

---

## 架构（概览）

```
┌─────────────────────────────────────────┐
│  cli.py   (入口)                        │
├─────────────────────────────────────────┤
│  pipeline / scheduler                   │  组合 fetcher + parser + storage
├─────────────────────────────────────────┤
│  fetchers       │   parsers   │ storage │
│  (分数据源)     │   (纯函数)  │ (ABC)   │
├─────────────────┴─────────────┴─────────┤
│  http.client          (请求 + 重试)     │
├─────────────────────────────────────────┤
│  browser.session       (Chrome + cookie)│
└─────────────────────────────────────────┘
```

规则：parsers 不依赖其他模块；storage 不感知爬虫细节；fetchers 只负责请求与响应；pipeline 是三者唯一的交汇点。详见 [docs/architecture.zh-CN.md](docs/architecture.zh-CN.md)。

---

## 项目结构

```
snowroll/
├── configs/                  YAML 配置（default / dev / prod）
├── src/xueqiu/
│   ├── browser/              Chrome 生命周期（DrissionPage）
│   ├── http/                 client + 类型化异常
│   ├── fetchers/             每个数据源一个文件
│   ├── parsers/              纯函数（HTML、symbol、post）
│   ├── storage/              SQLite + PostgreSQL（ABC）
│   ├── pipeline/             编排 + 调度
│   ├── nlp/                  预留 — 情绪分析挂载点
│   ├── utils/                日志、重试、时间工具
│   ├── config.py             Pydantic 配置加载
│   └── cli.py                argparse 入口
├── tests/
│   ├── unit/                 快速单测，无网络
│   └── integration/          假 fetcher + 真 SQLite
├── scripts/                  一次性脚本（init_db, check_cookie, ...）
├── docs/
├── data/                     SQLite 与导出
├── logs/                     轮转日志
├── pyproject.toml
└── Makefile
```

---

## 常见流程

### 添加新数据源

1. 新建 `src/xueqiu/fetchers/my_source.py`，继承 `BaseFetcher`。
2. 产出 `FetchResult` 页面。
3. CLI / pipeline 无需改动即可驱动。

### 切换 SQLite → PostgreSQL

```bash
# .env
XUEQIU_STORAGE_BACKEND=postgres
XUEQIU_PG_DSN=postgresql://user:pass@localhost:5432/xueqiu

# 安装 psycopg
pip install -e ".[postgres]"

# 初始化
xueqiu db init
```

无需代码改动，`create_storage()` 根据配置返回对应后端。

### 以后添加情绪分析

`src/xueqiu/nlp/` 为预留目录。未来可实现 `SentimentScorer`，将分数写入 `sentiment` 表并与 `post.id` 关联。详见 `src/xueqiu/nlp/__init__.py` 的规划说明。

---

## 测试与质量

```bash
make test           # 所有测试
make test-unit      # 单元测试
make test-cov       # 覆盖率
make lint           # ruff check
make format         # ruff format + auto-fix
make typecheck      # mypy
```

---

## 排错

| 症状 | 可能原因 | 解决方式 |
|---|---|---|
| `WAF likely blocked us` | IP 被限流 | 等 1–2 小时、换网络或登录（挑战更少） |
| `WebSocketConnectionClosedException` | Chrome 启动崩溃 | 检查 `google-chrome --version`，补依赖 |
| 所有请求返回 `400016` | Token 失效 | 客户端会自动刷新；持续出现请在浏览器登录 |
| 返回 HTML 而非 JSON | 触发 Aliyun WAF | 浏览器会话需保持，勿中途关闭 Chrome |

可用 `make check-cookie` 排查。

---

## 许可证

MIT。
