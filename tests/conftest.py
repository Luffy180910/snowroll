"""Shared pytest fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_response() -> dict:
    """Load the canned Xueqiu API response sample."""
    with (FIXTURES_DIR / "sample_response.json").open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_post(sample_response: dict) -> dict:
    """First post from the sample response."""
    return sample_response["list"][0]


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Path to a temp SQLite database file."""
    return tmp_path / "test.db"
