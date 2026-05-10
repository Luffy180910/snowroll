# 使用示例

补充 README 的快速上手。

## 编程方式

### 抓取单只股票

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

### 长期累计抓取

```python
from xueqiu.pipeline.scheduler import HotMarketScheduler

# ... 按上面方式构建 session/client/fetcher/storage/pipeline ...

scheduler = HotMarketScheduler(pipeline)
scheduler.run_until(target_count=50_000, round_interval_seconds=1800)
```

### 读取数据到 pandas

```python
import pandas as pd
from xueqiu.storage import create_storage

with create_storage() as storage:
    rows = storage.query(symbol="SH600519", limit=1000)
    df = pd.DataFrame(rows)

# 现在可以在 df 上做分析
```

## CLI 用法

### 端到端验证爬虫是否正常

```bash
make check-cookie    # 诊断浏览器 + cookies + 单次 API 调用
```

### 启用详细日志抓取单个标的

```bash
xueqiu --log-level DEBUG crawl stock --symbol SH600519 --pages 3
```

### 定时增量抓取（cron）

将以下内容加入 crontab：

```cron
0 9,15,21 * * * cd /path/to/snowroll && /usr/bin/env XUEQIU_ENV=prod \
    /path/to/venv/bin/xueqiu crawl hot --max-pages 5 \
    >> /path/to/snowroll/logs/cron.log 2>&1
```

### 按目标持续运行

```bash
nohup xueqiu crawl until --target 100000 --interval 1800 \
    > logs/long_run.log 2>&1 &
```

### 导出

```bash
xueqiu export csv --out data/exports/all.csv
xueqiu export csv --out data/exports/maotai.csv --symbol SH600519
xueqiu export csv --out data/exports/recent.csv --limit 5000
```

## 配置示例

### 使用已登录的浏览器配置（更长 cookie 生命周期）

1. 首次运行设为 `XUEQIU_HEADLESS=false`。
2. 在弹出的 Chrome 窗口中手动登录雪球。
3. 会话保存在 `/tmp/xueqiu_chrome_profile`。
4. 之后运行会复用该配置，可保持登录数天。

```bash
XUEQIU_HEADLESS=false xueqiu crawl stock --symbol SH600519 --pages 1
# 在 Chrome 窗口内登录
# 之后再运行：
xueqiu crawl hot
```

### 切换存储到 PostgreSQL

```bash
# .env
XUEQIU_STORAGE_BACKEND=postgres
XUEQIU_PG_DSN=postgresql://crawler:secret@db.example.com:5432/xueqiu

pip install -e ".[postgres]"
xueqiu db init
xueqiu crawl stock --symbol SH600519 --pages 5
```

### 覆盖热门标的列表

要么编辑 `configs/default.yaml`，要么创建 `configs/prod.yaml` 写入自定义列表，再以 `XUEQIU_ENV=prod` 运行。

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

## 下游情绪分析（规划中）

`nlp/` 包是约定的归宿。预期流程如下：

```python
from xueqiu.storage import create_storage
from xueqiu.nlp import LexiconScorer, ScorePipeline   # planned

with create_storage() as storage:
    scorer = LexiconScorer()                          # planned
    ScorePipeline(scorer, storage).score_unscored()   # planned
```

它会读取 `sentiment` 表中不存在的 `post.id`，计算分数并写回。用更好的模型重跑时，只需回填（删除 `sentiment` 并重跑）。更多规划见 `src/xueqiu/nlp/__init__.py`。
