# DOX Contract — Tools Module

- This folder contains core CLI panels and self-healing agent pipelines.
- All modifications here must pass local verification (`make check` and `make test`).

## ⚙️ Module Responsibilities

- `dashboard.py`: Terminal control dashboard for all automated tools.
- `diff_applier.py`: Search/Replace patches applying logic.
- `test_healer.py`: Catch-and-heal testing loop daemon.
- `llm_wiki.py`: Local knowledge core manager (RWS pipeline).
- `obsidian_cli.py`: Connector to Obsidian API.
- `prompts_repository.py`: Fast SQLite full-text search database manager for prompts.chat.
- `prompts_cli.py`: Command Line interface for importing, finding and getting prompts.
- `uupm_adapter.py`: Design tokens compiler for layouts.
- `video_skills_adapter.py`: Wrapper for Remotion video pipelines.

## 📐 Guidelines

- No external dependencies allowed without verification.
- All helpers must contain complete type annotations.
- Every script must be covered by a unit test in `tools/tests/` or `tools/test_*.py`.
