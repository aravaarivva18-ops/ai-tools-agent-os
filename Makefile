.PHONY: sync lint format check test clean

sync:
	uv sync --all-packages

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run bandit -r . -x ./.venv,./.git -s B101,B110,B112,B310,B311,B404,B603,B607


test:
	uv run --package geo-seo pytest
	uv run --package ai-agency pytest ai-agency/
	uv run pytest tools/



clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
