"""Process-level utilities for managing Chrome instances."""
from __future__ import annotations

import os
import random
import signal
import socket

from xueqiu.utils.logger import get_logger

log = get_logger(__name__)


def kill_chrome_by_marker(profile_marker: str) -> int:
    """Kill any Chrome processes whose command line contains the given marker.

    Used to clean up before launching a fresh browser session, avoiding
    stale-port and locked-profile errors.

    Returns the number of processes killed.
    """
    killed = 0
    try:
        with os.popen(f'ps aux | grep "{profile_marker}" | grep -v grep') as f:
            lines = f.readlines()
    except OSError as e:
        log.warning("ps lookup failed: %s", e)
        return 0

    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[1])
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except (ValueError, ProcessLookupError, PermissionError):
            continue

    if killed:
        log.info("killed %d stale Chrome processes", killed)
    return killed


def find_free_port(port_range: tuple[int, int], max_attempts: int = 10) -> int:
    """Pick a random unused TCP port in the given inclusive range."""
    low, high = port_range
    for _ in range(max_attempts):
        port = random.randint(low, high)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"no free port found in [{low}, {high}] after {max_attempts} attempts")
