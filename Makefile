.PHONY: help install install-dev install-all clean test test-unit test-cov \
        lint format typecheck crawl crawl-stock crawl-hot export init-db check-cookie

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

help:
	@echo "Xueqiu Crawler — Make targets"
	@echo "  install       — base install"
	@echo "  install-dev   — install with dev tools (pytest/ruff/mypy)"
	@echo "  install-all   — install everything (postgres + nlp + dev)"
	@echo "  test          — run all tests"
	@echo "  test-unit     — run unit tests only"
	@echo "  test-cov      — run tests with coverage report"
	@echo "  lint          — run ruff check"
	@echo "  format        — run ruff format"
	@echo "  typecheck     — run mypy"
	@echo "  init-db       — initialize SQLite database"
	@echo "  crawl-stock   — crawl one stock (SYMBOL=SH600519 PAGES=5)"
	@echo "  crawl-hot     — crawl all hot markets"
	@echo "  export        — export DB to CSV"
	@echo "  check-cookie  — diagnose cookie/WAF status"
	@echo "  clean         — remove build artifacts"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

install-all:
	$(PIP) install -e ".[dev,postgres,nlp]"

test:
	$(PYTHON) -m pytest

test-unit:
	$(PYTHON) -m pytest tests/unit

test-cov:
	$(PYTHON) -m pytest --cov=xueqiu --cov-report=term-missing --cov-report=html

lint:
	$(PYTHON) -m ruff check src tests

format:
	$(PYTHON) -m ruff format src tests
	$(PYTHON) -m ruff check --fix src tests

typecheck:
	$(PYTHON) -m mypy src/xueqiu

init-db:
	$(PYTHON) scripts/init_db.py

SYMBOL ?= SH600519
PAGES ?= 5
crawl-stock:
	$(PYTHON) -m xueqiu.cli crawl stock --symbol $(SYMBOL) --pages $(PAGES)

crawl-hot:
	$(PYTHON) -m xueqiu.cli crawl hot

export:
	$(PYTHON) -m xueqiu.cli export csv --out data/exports/posts.csv

check-cookie:
	$(PYTHON) scripts/check_cookie.py

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
