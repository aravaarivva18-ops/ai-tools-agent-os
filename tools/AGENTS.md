# DOX Contract — Tools Module

- This folder contains core CLI panels and self-healing agent pipelines.
- All modifications here must pass local verification (`make check` and `make test`).

## ⚙️ Module Responsibilities

- `dashboard.py`: Terminal control dashboard for all automated tools.
- `diff_applier.py`: Search/Replace patches applying logic.
- `test_healer.py`: Catch-and-heal testing loop daemon.
- `llm_wiki.py`: Local knowledge core manager (RWS pipeline).
- `obsidian_cli.py`: Connector to Obsidian API.
- `prompts.py`: Unified SQLite FTS5 prompts database manager with CLI interface (WAL mode).
- `rules_validator.py`: Unified rules/constitution validator (merged check_rules + prompt_validator).
- `uupm_adapter.py`: Design tokens compiler for layouts.
- `video_skills_adapter.py`: Wrapper for Remotion video pipelines.

## 📐 Guidelines

- No external dependencies allowed without verification.
- All helpers must contain complete type annotations.
- Every script must be covered by a unit test in `tools/tests/` or `tools/test_*.py`.
