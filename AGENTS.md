# DOX — Monorepo Configuration & Agent Contracts

- DOX is a highly performant AGENTS.md hierarchy installed in this workspace.
- The Agent must follow DOX instructions across all edits.

## Core Contract

- `AGENTS.md` files are binding work contracts for their subtrees.
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable `AGENTS.md` plus every parent `AGENTS.md` above it.

## Read Before Editing

1. Read this root `AGENTS.md`.
2. Identify every file or folder you expect to touch.
3. Walk from the repository root to each target path.
4. Read every `AGENTS.md` found along each route (e.g., `tools/AGENTS.md`).
5. Use the nearest `AGENTS.md` as the local contract and parent docs for repo-wide rules.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done. Update the closest owning `AGENTS.md` when a change affects:
- project scope, rules, or inputs/outputs
- folder structures or workflows
- child indexes

---

## 🗂️ Child DOX Index (Monorepo Modules)

- [[tools/AGENTS.md]] — CLI Dashboard, Diff Applier, Test Healer, and utilities.
- [[geo-seo/AGENTS.md]] — Scraping engines (`selectolax`, `curl_cffi`).
- [[ai-sales/AGENTS.md]] — Typst-based PDF report generation workflows.
- [[bitrix-knowledge/AGENTS.md]] — Persistent 1C-Bitrix knowledge base & Obsidian RAG index.

---

## 📐 Глобальные регламенты (v10)

Все разработки в монорепозитории регулируются конституцией [GEMINI_ANTIGRAVITY.md](file:///Users/rus/GEMINI_ANTIGRAVITY.md).
Основные стандарты:
- **Solo Loop v10**: Субагенты запрещены. Статус сессии считывается из `implementation_plan.md` через `PlanningWithFiles`. Выводы сжимаются через `SoloLoopV10`.
- **Валидация и Схемы**: Строгая валидация по BaseModel и экспорт Agno-style схем через `tools/tool_validator.py`.
- **Навыки**: Управление JIT-навыками через `tools/agent_skills.py`.
- **Окружение**: Python 3.12+ (`uv run`), форматирование Ruff (`ruff.toml`).
- **Плагины**: Обязательно использование `agent-skills` (слэш-команды), `fablize` (DoD и доказательства) и `ponytail` (YAGNI/контроль абстракций).
- **YAGNI**: Ponytail mode `full`, максимум 2 уровня абстракции.
- **Процесс**: Spec -> Research -> Plan -> Implement -> Test (`tools/test_healer.py` со Stealth Stop на 3-й раз) -> Ship (`tools/self_improve.py`).


