"""Abstract base class for fetchers.

A fetcher is a generator-like object that yields ``FetchResult`` pages.
Each page contains the raw items and a ``source_tag`` that downstream
parsers use to mark provenance.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from xueqiu.http.client import XueqiuClient


@dataclass
class FetchResult:
    """One page of raw items from a fetcher."""

    items: list[dict[str, Any]]
    source_tag: str
    symbol: str = ""           # stock symbol if applicable
    page: int = 0              # 1-based page number
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.items


class BaseFetcher(ABC):
    """All fetchers receive an HTTP client and yield FetchResult pages."""

    def __init__(self, client: "XueqiuClient"):
        self.client = client

    @abstractmethod
    def fetch(self, **kwargs) -> Iterator[FetchResult]:
        """Yield successive pages. Stops when no more data or on terminal error."""
