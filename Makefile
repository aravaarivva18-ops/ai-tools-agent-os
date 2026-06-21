.PHONY: sync lint format check check-rules check-all test clean

sync:
	uv sync --all-packages

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .

check-rules:
	python3 tools/check_rules.py

normalize-constitution:
	uv run python tools/self_improve.py
	uv run python tools/update_gem_bot_prompts.py

auto-improve:
	uv run python tools/self_improve.py
	uv run python tools/update_gem_bot_prompts.py

check: check-rules
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy tools/ geo-seo/
	uv run bandit -r . -x ./.venv,./.git,./tools/.venv,./tools/.gemini -s B101,B105,B108,B110,B112,B310,B311,B404,B603,B607

check-all: check test

test:
	uv run --package geo-seo pytest geo-seo/tests/ -v
	uv run pytest tools/tests/ -v
	uv run pytest dashboard-hand-on-pulse/ -v
	uv run pytest youtube-faceless-pipeline/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
