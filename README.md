# snowroll

Engineering-grade scraper for [雪球 (xueqiu.com)](https://xueqiu.com) discussions, designed for downstream sentiment analysis.

Routes API calls through a real Chrome instance (via DrissionPage) to bypass the Aliyun WAF JS challenge that blocks plain `requests`. Layered architecture so storage, parsing, and fetching can each be swapped or extended without touching the rest.

---

## Features

- **WAF-bypass via real browser** — DrissionPage opens Chrome, passes the JS challenge once, then API calls reuse that session.
- **Layered architecture** — browser / http / fetcher / parser / storage / pipeline / cli, each with one job.
- **Two storage backends** — SQLite (default) for prototyping, PostgreSQL for production.
- **Configuration driven** — YAML + env, three environments (dev / prod / default).
- **Tested** — unit tests for parsers and storage, integration tests for the pipeline.
- **CLI** — `xueqiu crawl stock`, `crawl hot`, `crawl until`, `export csv`, `db init`.
- **Reserved extension points** — comments, user timeline, hot stream, NLP/sentiment.

---

## Quick start

### 1. Install

```bash
git clone https://github.com/Luffy180910/snowroll
cd snowroll

# Pick one:
make install         # base (sqlite only)
make install-dev     # + pytest, ruff, mypy
make install-all     # + postgres, nlp, dev
```

Requires Python 3.10+ and Chrome / Chromium installed locally.

### 2. Configure

```bash
cp .env.example .env
# edit .env if needed (defaults work for SQLite)
```

### 3. Initialize database

```bash
make init-db
```

### 4. Crawl

```bash
# One stock, 5 pages:
make crawl-stock SYMBOL=SH600519 PAGES=5

# All configured hot stocks (one round):
make crawl-hot

# Or use the CLI directly:
xueqiu crawl stock --symbol SH600519 --pages 10
xueqiu crawl hot --max-pages 3
xueqiu crawl until --target 50000 --interval 1800
```

### 5. Inspect / export

```bash
xueqiu db count                          # total rows
xueqiu db count --symbol SH600519        # rows mentioning a symbol
xueqiu export csv --out posts.csv
xueqiu export csv --out maotai.csv --symbol SH600519
```

---

## Architecture (one screen)

```
┌─────────────────────────────────────────┐
│  cli.py   (entry point)                 │
├─────────────────────────────────────────┤
│  pipeline / scheduler                   │  composes fetcher + parser + storage
├─────────────────────────────────────────┤
│  fetchers       │   parsers   │ storage │
│  (per source)   │   (pure)    │ (ABC)   │
├─────────────────┴─────────────┴─────────┤
│  http.client          (request + retry) │
├─────────────────────────────────────────┤
│  browser.session       (Chrome + cookie)│
└─────────────────────────────────────────┘
```

Rules: parsers depend on nothing; storage depends on nothing crawler-specific; fetchers don't store; pipelines are the only place all three meet. See [docs/architecture.md](docs/architecture.md) for full details.

---

## Project layout

```
xueqiu_crawler/
├── configs/                  YAML config (default / dev / prod)
├── src/xueqiu/
│   ├── browser/              Chrome lifecycle (DrissionPage)
│   ├── http/                 client + typed exceptions
│   ├── fetchers/             one file per data source
│   ├── parsers/              pure functions (HTML, symbol, post)
│   ├── storage/              SQLite + PostgreSQL behind ABC
│   ├── pipeline/             orchestration + scheduler
│   ├── nlp/                  RESERVED — sentiment analysis hooks
│   ├── utils/                logging, retry, time helpers
│   ├── config.py             Pydantic settings loader
│   └── cli.py                argparse entry
├── tests/
│   ├── unit/                 fast, no network
│   └── integration/          fake fetcher, real SQLite
├── scripts/                  one-off utilities (init_db, check_cookie, ...)
├── docs/
├── data/                     SQLite DB and exports
├── logs/                     rotating crawler logs
├── pyproject.toml
└── Makefile
```

---

## Common workflows

### Add a new data source

1. Add a fetcher: `src/xueqiu/fetchers/my_source.py` extending `BaseFetcher`.
2. Yield `FetchResult` pages.
3. The CLI / pipeline can then drive it without changes elsewhere.

### Switch SQLite → PostgreSQL

```bash
# .env
XUEQIU_STORAGE_BACKEND=postgres
XUEQIU_PG_DSN=postgresql://user:pass@localhost:5432/xueqiu

# install psycopg
pip install -e ".[postgres]"

# init
xueqiu db init
```

No code changes — `create_storage()` reads config and returns the right backend.

### Add sentiment analysis later

`src/xueqiu/nlp/` is reserved. Plug in a `SentimentScorer` ABC, write scores to a `sentiment` table keyed on `post.id`. See the package docstring there for the planned shape.

---

## Tests & quality

```bash
make test           # all tests
make test-unit      # fast unit tests only
make test-cov       # with coverage
make lint           # ruff check
make format         # ruff format + auto-fix
make typecheck      # mypy
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `WAF likely blocked us` on warmup | Your IP got rate-limited | Wait 1–2h, switch network, or login (reduces challenges) |
| `WebSocketConnectionClosedException` | Chrome crashed at launch | Check `google-chrome --version`, install missing libs |
| All requests return `400016` | Token rejected (token aging) | The client auto-refreshes; if persistent, login in browser |
| Returns HTML instead of JSON | Aliyun WAF challenge page | Browser session must stay alive; don't kill Chrome between calls |

`make check-cookie` prints what's wrong.

---

## License

MIT.
# snowroll
