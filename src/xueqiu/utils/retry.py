"""Retry helpers built on tenacity.

Exposed primarily for fetcher-level retries; the http client has its own
finer-grained retry loop because it needs to inspect response bodies.
"""
from __future__ import annotations

from typing import Callable

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


def retry_on(
    exceptions: type[Exception] | tuple[type[Exception], ...],
    *,
    attempts: int = 3,
    initial_seconds: float = 2.0,
    max_seconds: float = 30.0,
) -> Callable:
    """Decorator: retry on the given exception types with exponential backoff + jitter."""
    return retry(
        retry=retry_if_exception_type(exceptions),
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=initial_seconds, max=max_seconds),
        reraise=True,
    )


__all__ = ["retry_on", "RetryError"]
