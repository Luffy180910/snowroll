"""HTTP client for Xueqiu API.

Why a browser-routed client?
    Direct requests/curl hits the Aliyun WAF JS challenge and gets blocked.
    A real Chrome instance has already passed the challenge, so we open a
    fresh tab on each call and read document.body.innerText.

Retry semantics (raise vs return):
    - HTML response → WafBlockedError → caller may refresh + retry
    - error_code 400016 → TokenExpiredError → refresh + retry
    - empty body → EmptyResponseError → soft retry
    - other API error → ApiError (terminal, no retry)
    - all retries exhausted → return None (treat as "stop fetching")
"""
from __future__ import annotations

import json
import random
import time
from typing import Any
from urllib.parse import urlencode

from xueqiu.browser.session import BrowserSession
from xueqiu.config import HttpConfig, get_settings
from xueqiu.http.exceptions import (
    ApiError,
    EmptyResponseError,
    TokenExpiredError,
    WafBlockedError,
)
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)


class XueqiuClient:
    """API client routed through a real browser tab.

    Owns nothing about business logic — it just executes a GET and returns
    parsed JSON, or raises typed exceptions. Pass the same instance to all
    fetchers; it manages cookie freshness internally.
    """

    def __init__(
        self,
        session: BrowserSession,
        config: HttpConfig | None = None,
    ):
        self.session = session
        self.config = config or get_settings().http

    # ---------- public API ----------
    def get_json(
        self,
        url: str,
        params: dict[str, Any],
        *,
        max_retries: int | None = None,
    ) -> dict[str, Any] | None:
        """GET ``url?params`` and return the parsed JSON dict.

        Returns None after exhausting retries. Raises ApiError for terminal
        business errors that the caller should not retry.
        """
        retries = max_retries if max_retries is not None else self.config.max_retries
        full_url = url + "?" + urlencode(params)

        for attempt in range(1, retries + 1):
            self._maybe_refresh_cookies()
            try:
                return self._request_once(full_url)
            except (WafBlockedError, TokenExpiredError) as e:
                log.warning("[attempt %d/%d] %s — refreshing", attempt, retries, type(e).__name__)
                self.session.refresh()
                self._sleep_backoff(attempt)
            except EmptyResponseError:
                log.warning("[attempt %d/%d] empty response — soft retry", attempt, retries)
                self._sleep_backoff(attempt, factor=0.5)
            except ApiError:
                # Terminal — don't retry, surface to caller.
                raise
            except Exception as e:
                log.warning("[attempt %d/%d] unexpected: %s", attempt, retries, e)
                self._sleep_backoff(attempt)

        log.error("giving up after %d retries: %s", retries, full_url)
        return None

    # ---------- internals ----------
    def _request_once(self, full_url: str) -> dict[str, Any]:
        """One attempt — open a tab, read body, parse JSON. Always raises typed errors on failure."""
        tab = self.session.browser.new_tab()
        try:
            tab.get(full_url)
            time.sleep(random.uniform(1.5, 3.0))

            body = tab.run_js("return document.body.innerText").strip()

            if not body:
                raise EmptyResponseError("empty body")

            # Aliyun WAF / login walls render HTML, not JSON
            if body.lstrip().startswith("<") or "aliyun_waf" in body.lower():
                raise WafBlockedError(f"non-JSON page: {body[:120]!r}")

            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                raise WafBlockedError(f"JSON decode failed: {body[:120]!r}") from e

            self._raise_on_business_error(data)
            return data
        finally:
            try:
                tab.close()
            except Exception:
                pass

    @staticmethod
    def _raise_on_business_error(data: dict[str, Any]) -> None:
        code = data.get("error_code")
        if not code or code == "0" or code == 0:
            return
        # 400016 — token rejected. Recoverable via refresh.
        if str(code) == "400016":
            raise TokenExpiredError(str(data.get("error_description", "")))
        raise ApiError(str(code), str(data.get("error_description", "")))

    def _maybe_refresh_cookies(self) -> None:
        last = self.session.last_refresh
        if last == 0:
            return  # session.open() already warmed up
        if time.time() - last > self.config.cookie_refresh_interval_seconds:
            log.info("cookie age exceeded threshold; refreshing")
            self.session.refresh()

    def _sleep_backoff(self, attempt: int, *, factor: float = 1.0) -> None:
        base = random.uniform(self.config.retry_backoff_min, self.config.retry_backoff_max)
        time.sleep(base * factor * attempt)

    def request_delay(self) -> None:
        """Polite inter-request sleep. Fetchers call this between pages."""
        time.sleep(random.uniform(self.config.request_delay_min, self.config.request_delay_max))
