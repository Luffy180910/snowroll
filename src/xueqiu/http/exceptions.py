"""Domain-specific exceptions for the HTTP layer.

Raising typed exceptions (instead of returning None) lets callers decide:
    - WafBlockedError / TokenExpiredError → refresh cookie + retry
    - EmptyResponseError → soft retry
    - HttpError → unrecoverable, fail fast
"""
from __future__ import annotations


class HttpError(Exception):
    """Base for all HTTP-layer failures."""


class WafBlockedError(HttpError):
    """Returned a non-JSON page (typically the Aliyun WAF challenge HTML)."""


class TokenExpiredError(HttpError):
    """Xueqiu API responded with error_code 400016 (token rejected)."""


class EmptyResponseError(HttpError):
    """Page rendered empty body (transient)."""


class ApiError(HttpError):
    """Xueqiu API responded with a business error code != 0/400016."""

    def __init__(self, code: str, description: str = ""):
        super().__init__(f"API error {code}: {description}")
        self.code = code
        self.description = description
