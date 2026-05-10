# Usage Examples

Beyond the README quick-start.

## Programmatic usage

### Crawl one stock

```python
from xueqiu.browser.session import BrowserSession
from xueqiu.fetchers.stock_posts import StockPostsFetcher
from xueqiu.http.client import XueqiuClient
from xueqiu.pipeline.crawl_pipeline import CrawlPipeline
from xueqiu.storage import create_storage

with BrowserSession() as session:
    client = XueqiuClient(session)
    fetcher = StockPostsFetcher(client)
    storage = create_storage()
    storage.init_schema()
    try:
        pipeline = CrawlPipeline(fetcher, storage)
        new_count = pipeline.run(symbol="SH600519", max_pages=10)
        print(f"new rows: {new_count}")
    finally:
        storage.close()
```

### Long-running accumulator

```python
from xueqiu.pipeline.scheduler import HotMarketScheduler

# ... build session/client/fetcher/storage/pipeline as above ...

scheduler = HotMarketScheduler(pipeline)
scheduler.run_until(target_count=50_000, round_interval_seconds=1800)
```

### Read data into pandas

```python
import pandas as pd
from xueqiu.storage import create_storage

with create_storage() as storage:
    rows = storage.query(symbol="SH600519", limit=1000)
    df = pd.DataFrame(rows)

# now do analysis on df
```

## CLI patterns

### Test that the crawler works end-to-end

```bash
make check-cookie    # diagnoses browser + cookies + one API call
```

### Crawl one symbol with verbose logs

```bash
xueqiu --log-level DEBUG crawl stock --symbol SH600519 --pages 3
```

### Schedule a daily incremental crawl (cron)

Add this to crontab:

```cron
0 9,15,21 * * * cd /path/to/xueqiu_crawler && /usr/bin/env XUEQIU_ENV=prod \
    /path/to/venv/bin/xueqiu crawl hot --max-pages 5 \
    >> /path/to/xueqiu_crawler/logs/cron.log 2>&1
```

### Run forever with a target

```bash
nohup xueqiu crawl until --target 100000 --interval 1800 \
    > logs/long_run.log 2>&1 &
```

### Export

```bash
xueqiu export csv --out data/exports/all.csv
xueqiu export csv --out data/exports/maotai.csv --symbol SH600519
xueqiu export csv --out data/exports/recent.csv --limit 5000
```

## Configuration recipes

### Use logged-in browser profile (longer cookie life)

1. First run with `XUEQIU_HEADLESS=false`.
2. In the spawned Chrome window, log in to Xueqiu manually.
3. The session is saved in `/tmp/xueqiu_chrome_profile`.
4. Subsequent runs reuse it; you stay logged in for days.

```bash
XUEQIU_HEADLESS=false xueqiu crawl stock --symbol SH600519 --pages 1
# log in inside the Chrome window
# subsequent runs:
xueqiu crawl hot
```

### Switch storage to PostgreSQL

```bash
# .env
XUEQIU_STORAGE_BACKEND=postgres
XUEQIU_PG_DSN=postgresql://crawler:secret@db.example.com:5432/xueqiu

pip install -e ".[postgres]"
xueqiu db init
xueqiu crawl stock --symbol SH600519 --pages 5
```

### Override hot-stocks list

Either edit `configs/default.yaml` or create `configs/prod.yaml` with your list, then run with `XUEQIU_ENV=prod`.

```yaml
# configs/prod.yaml
hot_stocks:
  cn_a:
    - SH600519
    - SZ000858
    - SZ300750
  hk: []
  us: []
```

## Downstream sentiment analysis (planned)

The `nlp/` package is the agreed home. Expected workflow once implemented:

```python
from xueqiu.storage import create_storage
from xueqiu.nlp import LexiconScorer, ScorePipeline   # planned

with create_storage() as storage:
    scorer = LexiconScorer()                          # planned
    ScorePipeline(scorer, storage).score_unscored()   # planned
```

It would read posts whose `id` is not yet in the `sentiment` table, score them, write back. Re-running with a better model is just a backfill (delete from `sentiment` and re-run). See `src/xueqiu/nlp/__init__.py` for the planned shape.
