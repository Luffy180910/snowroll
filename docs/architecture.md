# Architecture

## Layering

```
┌─────────────────────────────────────────┐
│  cli.py / scripts                       │  entry points — argparse only
├─────────────────────────────────────────┤
│  pipeline / scheduler                   │  the only layer that sees fetcher + parser + storage together
├─────────────────────────────────────────┤
│  fetchers       │   parsers   │ storage │
│  (per source)   │   (pure)    │ (ABC)   │
├─────────────────┴─────────────┴─────────┤
│  http.client          (request + retry) │  raises typed exceptions
├─────────────────────────────────────────┤
│  browser.session       (Chrome + cookie)│  owns the only Chrome instance
├─────────────────────────────────────────┤
│  config / utils                         │  cross-cutting infrastructure
└─────────────────────────────────────────┘
```

## Rules (enforced by code review, not by tooling)

1. **`parsers/` imports only stdlib + `utils/timeutils`.** They are pure functions; given input X, always produce output Y. Easy to unit-test and reason about.

2. **`storage/` does not know about fetchers, http, or browser.** A storage backend can be tested with hand-crafted `Post` objects. Swapping SQLite → PostgreSQL → DuckDB requires no other changes.

3. **`fetchers/` does not store.** Each fetcher's job: know the URL, the params, the response shape. Yields `FetchResult` pages. Doesn't write to disk, doesn't call parsers.

4. **`http.client` raises typed exceptions, not None.** Callers (fetchers) decide between retry and abort by exception type:
   - `WafBlockedError` → refresh + retry
   - `TokenExpiredError` → refresh + retry
   - `EmptyResponseError` → soft retry
   - `ApiError` → terminal, no retry

5. **`browser.session` owns the only Chrome instance.** Anything that needs the browser goes through this object. Ensures we don't accidentally spawn N Chromes.

6. **`pipeline/` is the only seam.** It pulls from a fetcher, runs the parser, persists via storage. No other layer composes these three.

7. **`cli.py` contains no business logic.** It parses args and calls into pipeline / storage / scheduler. Useful so that the same logic is callable from scripts or future REST endpoints.

## Why these boundaries

The original `XueqiuCrawler` was a single class that did everything: started Chrome, managed cookies, sent requests, parsed HTML, wrote SQL, looped over markets. Three concrete pains it caused:

- **Untestable.** You couldn't test HTML cleaning without launching Chrome.
- **Hard to extend.** Adding "fetch comments for each post" meant editing the same class that does everything else.
- **Coupled change.** Moving to PostgreSQL would touch the same file as the parser.

Each rule above directly addresses one of these.

## Data flow

```
                    ┌──────────────┐
   user CLI  ─────► │  cli.py      │
                    └──────┬───────┘
                           │ wires up
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
        │ Client │ ───► raises WafBlockedError / TokenExpiredError / ApiError
        └───┬────┘
            ▼
        ┌─────────┐
        │ Session │ ───► Chrome (DrissionPage)
        └─────────┘
```

A page of items flows: `Session.tab.get(url)` → `Client.get_json` → fetcher's `FetchResult` → pipeline parses → `Storage.save_posts` → SQLite/Postgres.

## Configuration loading

Three layers, later wins:

1. `configs/default.yaml` — committed defaults.
2. `configs/{XUEQIU_ENV}.yaml` — environment override (`dev` or `prod`).
3. Environment variables prefixed `XUEQIU_` (with optional `__` for nesting).
4. Values from `.env` are loaded into the env first, so step 3 sees them.

Pydantic validates the merged result. Callers always go through `xueqiu.config.get_settings()`, never `os.environ` directly.

## Extension points (reserved)

| Area | Where it goes | Status |
|---|---|---|
| Comment fetching | `fetchers/comments.py` | stub raising NotImplementedError |
| User timeline | `fetchers/user_timeline.py` | stub raising NotImplementedError |
| Hot stream API | `fetchers/hot_stream.py` | stub raising NotImplementedError |
| Sentiment scoring | `nlp/` package | empty package with docstring spec |
| Future Chinese A-share fundamentals | `fetchers/<new_file>.py` | drop-in |
| Distributed scheduler | replace `pipeline/scheduler.py` | one-file change |
