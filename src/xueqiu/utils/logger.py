"""Centralized logging setup.

Use module-level loggers everywhere:
    from xueqiu.utils.logger import get_logger
    log = get_logger(__name__)
    log.info("...")

Call `setup_logging()` once at application start (CLI entry point).
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from xueqiu.config import get_settings

_CONFIGURED = False


def setup_logging(level: str | None = None, log_dir: str | None = None) -> None:
    """Configure the root logger. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings().logging_
    level_name = (level or settings.level).upper()
    level_num = getattr(logging, level_name, logging.INFO)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    root = logging.getLogger("xueqiu")
    root.setLevel(level_num)
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler
    log_path = Path(log_dir or settings.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / settings.log_file,
        maxBytes=settings.rotation_size_mb * 1024 * 1024,
        backupCount=settings.retention_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Quieten noisy third-party loggers
    for noisy in ("urllib3", "requests", "DrissionPage", "websocket"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Get a namespaced logger. Auto-configures on first call."""
    if not _CONFIGURED:
        setup_logging()
    # Ensure all our loggers live under the 'xueqiu' tree
    if not name.startswith("xueqiu"):
        name = f"xueqiu.{name}"
    return logging.getLogger(name)
