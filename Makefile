.PHONY: sync lint format check check-rules check-all test clean

sync:
	uv sync --all-packages

lint:
	@DIFF_FILES=$$(git diff --name-only | grep '\.py$$' || true); \
	if [ -n "$$DIFF_FILES" ]; then \
		echo "Linting modified files: $$DIFF_FILES"; \
		uv run ruff check $$DIFF_FILES --fix; \
	else \
		echo "No modified Python files to lint."; \
		uv run ruff check . --fix; \
	fi

format:
	@DIFF_FILES=$$(git diff --name-only | grep '\.py$$' || true); \
	if [ -n "$$DIFF_FILES" ]; then \
		echo "Formatting modified files: $$DIFF_FILES"; \
		uv run ruff format $$DIFF_FILES; \
	else \
		echo "No modified Python files to format."; \
		uv run ruff format .; \
	fi


check-rules:
	python3 tools/rules_validator.py

normalize-constitution:
	uv run python tools/self_improve.py

auto-improve:
	uv run python tools/self_improve.py

check: check-rules
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy tools/ geo-seo/
	uv run bandit -r . -x ./.venv,./.git,./tools/.venv,./tools/.gemini -s B101,B105,B106,B108,B110,B112,B310,B311,B404,B603,B607

check-all: check test

test:
	uv run --package geo-seo pytest geo-seo/tests/ -v --disable-socket --allow-unix-socket
	uv run pytest tools/tests/ -v --disable-socket --allow-unix-socket
	uv run pytest youtube-faceless-pipeline/ -v --disable-socket --allow-unix-socket

mcp:
	uv run python tools/mcp_server.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
