"""Browser session: launches Chrome via DrissionPage and exposes tabs.

The session also handles cookie warmup and refresh — but does NOT make
HTTP requests itself. Use it via :class:`xueqiu.http.client.XueqiuClient`.
"""
from __future__ import annotations

import os
import time
from typing import Any

from xueqiu.browser.process import find_free_port, kill_chrome_by_marker
from xueqiu.config import BrowserConfig, get_settings
from xueqiu.utils.logger import get_logger

log = get_logger(__name__)


class BrowserSession:
    """Owns a single Chrome instance and its cookie state.

    Lazy lifecycle:
        - ``open()`` starts Chrome and warms it up (visits homepage + a stock page)
        - ``new_tab(url)`` opens a tab, used by the http client
        - ``refresh()`` revisits homepage to extend cookie lifetime
        - ``close()`` quits Chrome
    """

    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or get_settings().browser
        self._browser: Any | None = None
        self._last_refresh: float = 0.0

    # ---------- lifecycle ----------
    def open(self) -> None:
        """Launch Chrome and warm up the session. Idempotent."""
        if self._browser is not None:
            return

        # Imported lazily so unit tests don't need DrissionPage installed.
        from DrissionPage import ChromiumOptions, ChromiumPage

        kill_chrome_by_marker(_marker_from_dir(self.config.user_data_dir))
        # Disable proxy for localhost — websocket to Chrome must not go through proxies.
        os.environ["no_proxy"] = "127.0.0.1,localhost"

        co = ChromiumOptions()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-dev-shm-usage")
        co.set_argument("--disable-gpu")
        co.set_argument("--disable-blink-features=AutomationControlled")
        if self.config.headless:
            co.headless(True)
        if self.config.browser_path:
            co.set_browser_path(self.config.browser_path)

        port = find_free_port(self.config.port_range)
        co.set_local_port(port)
        co.set_user_data_path(self.config.user_data_dir)

        log.info("launching Chrome on port %d (headless=%s)", port, self.config.headless)
        self._browser = ChromiumPage(co)

        self._warmup()

    def _warmup(self) -> None:
        """Visit homepage + a stock page to trigger WAF challenge & cookie issuance."""
        log.info("warming up — visiting homepage")
        self._browser.get(self.config.warmup_url)
        time.sleep(self.config.warmup_wait_seconds)

        log.info("warming up — visiting stock page")
        self._browser.get(self.config.warmup_stock_url)
        time.sleep(self.config.warmup_wait_seconds * 0.6)

        if not self._has_token():
            raise RuntimeError(
                "warmup did not yield xq_a_token — WAF likely blocked us. "
                "Try headless=false to see the browser, or change network/IP."
            )
        self._last_refresh = time.time()
        log.info("warmup complete; cookies acquired")

    def refresh(self) -> None:
        """Revisit homepage to refresh the WAF/auth cookies."""
        if self._browser is None:
            self.open()
            return

        log.info("refreshing cookies via homepage visit")
        try:
            self._browser.get(self.config.warmup_url)
            time.sleep(self.config.warmup_wait_seconds * 0.7)
            if not self._has_token():
                log.warning("refresh did not yield token; restarting browser")
                self.close()
                self.open()
                return
            self._last_refresh = time.time()
        except Exception as e:
            log.warning("refresh failed: %s; restarting browser", e)
            self.close()
            self.open()

    def close(self) -> None:
        if self._browser is not None:
            try:
                self._browser.quit()
            except Exception as e:
                log.warning("browser.quit() raised: %s", e)
            self._browser = None

    # ---------- accessors ----------
    @property
    def browser(self):
        """Underlying ChromiumPage. Auto-opens if not yet running."""
        if self._browser is None:
            self.open()
        return self._browser

    @property
    def last_refresh(self) -> float:
        return self._last_refresh

    def cookies(self) -> list[dict[str, Any]]:
        """Return all cookies as DrissionPage gives them."""
        return self.browser.cookies()

    def has_token(self) -> bool:
        """Public alias for token presence check."""
        return self._has_token()

    def _has_token(self) -> bool:
        try:
            return any(c.get("name") == "xq_a_token" for c in self._browser.cookies())
        except Exception:
            return False

    # ---------- context manager ----------
    def __enter__(self) -> BrowserSession:
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _marker_from_dir(path: str) -> str:
    """Extract the trailing component of a path; used as a process-grep marker."""
    return path.rstrip("/").split("/")[-1] or path
