"""Configuration loader.

Layered loading order (later overrides earlier):
    1. configs/default.yaml
    2. configs/{env}.yaml   where env = dev | prod (from XUEQIU_ENV, default 'dev')
    3. environment variables prefixed with XUEQIU_
    4. .env file (loaded into env vars before step 3)

Returns a typed Pydantic settings object. All callers should depend on this
object instead of reading os.environ directly.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------- Sub-models ----------
class BrowserConfig(BaseModel):
    headless: bool = True
    user_data_dir: str = "/tmp/xueqiu_chrome_profile"
    port_range: tuple[int, int] = (9222, 9999)
    warmup_url: str = "https://xueqiu.com/"
    warmup_stock_url: str = "https://xueqiu.com/S/SZ002580"
    warmup_wait_seconds: float = 5.0
    browser_path: str | None = None  # auto-detect if None


class HttpConfig(BaseModel):
    max_retries: int = 3
    request_delay_min: float = 3.0
    request_delay_max: float = 6.0
    cookie_refresh_interval_seconds: float = 1200.0
    retry_backoff_min: float = 10.0
    retry_backoff_max: float = 20.0


class StorageConfig(BaseModel):
    backend: str = "sqlite"  # sqlite | postgres
    sqlite_path: str = "data/xueqiu.db"
    pg_dsn: str | None = None


class CrawlConfig(BaseModel):
    default_max_pages: int = 10
    default_source: str = "user"
    default_sort: str = "time"
    page_size: int = 20
    inter_stock_delay_min: float = 5.0
    inter_stock_delay_max: float = 10.0


class LoggingConfig(BaseModel):
    level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "crawler.log"
    rotation_size_mb: int = 10
    retention_count: int = 5


class HotStocksConfig(BaseModel):
    cn_a: list[str] = Field(default_factory=list)
    hk: list[str] = Field(default_factory=list)
    us: list[str] = Field(default_factory=list)

    def all_symbols(self) -> list[str]:
        return [*self.cn_a, *self.hk, *self.us]


# ---------- Top-level settings ----------
class Settings(BaseSettings):
    """Top-level settings object. Pull this once via `get_settings()`."""

    model_config = SettingsConfigDict(
        env_prefix="XUEQIU_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    http: HttpConfig = Field(default_factory=HttpConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    logging_: LoggingConfig = Field(default_factory=LoggingConfig, alias="logging")
    hot_stocks: HotStocksConfig = Field(default_factory=HotStocksConfig)

    # Derived: project root, useful for resolving relative paths
    project_root: Path = Field(default_factory=lambda: _find_project_root())

    # Optional pre-logged cookie (rarely set, used for stable sessions)
    cookie_string: str | None = None


def _find_project_root() -> Path:
    """Walk up from this file until we find pyproject.toml."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursive dict merge (override wins on leaves)."""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings. Call this from anywhere; it's idempotent."""
    root = _find_project_root()

    # Step 1: load .env first so env vars are populated for pydantic
    load_dotenv(root / ".env", override=False)

    # Step 2 & 3: layer YAML files
    env_name = os.getenv("XUEQIU_ENV", "dev")
    default_yaml = _load_yaml(root / "configs" / "default.yaml")
    overlay_yaml = _load_yaml(root / "configs" / f"{env_name}.yaml")
    merged = _deep_merge(default_yaml, overlay_yaml)

    # Step 4: pydantic reads env vars on top
    settings = Settings(**merged)

    # Resolve sqlite path relative to project root
    if not Path(settings.storage.sqlite_path).is_absolute():
        settings.storage.sqlite_path = str(root / settings.storage.sqlite_path)

    return settings


def reset_settings_cache() -> None:
    """Test helper: clear cached settings."""
    get_settings.cache_clear()
