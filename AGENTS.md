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

---

## 🛠️ Global Workspace Preferences

- **Package Manager**: Python 3.12+ managed via `uv`. Run commands as `uv run`.
- **Formatting**: Ruff (`ruff.toml`). No legacy exceptions allowed.
- **YAGNI Standard**: Ponytail mode `full`.
- **Process**: Spec -> Research -> Plan -> Implement (Fablize logic).
- **Prompts Repository**: Использовать `tools/prompts_cli.py` для локального поиска промптов prompts.chat.

## 🛡️ Жесткие требования к качеству (Mandatory Guardrails)

- **Абсолютное соблюдение Конституции**: Агент обязан неукоснительно выполнять все правила из `GEMINI_ANTIGRAVITY.md` на каждом шаге.
- **Приоритет TDD**: Любые изменения в рабочей логике или создание новых скриптов должны сопровождаться написанием тестов. Тестовое покрытие создается в первую очередь.
- **Использование тест-хилера**: Для запуска тестов и самоисправления ошибок агент обязан использовать локальный инструмент `test_healer.py`.
- **Валидация регламентов (Check Rules)**: При изменении любых файлов регламентов (включая `GEMINI_ANTIGRAVITY.md`, `STUDENT_GUIDE.md`, `CLAUDE.md`, `.cursorrules`, `AGENTS.md`) или файлов навыков агент обязан запускать `make check-rules` для проверки целостности ссылок и синхронизации JIT-навыков. Неиспользуемые правила и навыки должны своевременно удаляться (YAGNI).
- **Обязательное использование плагинов**:
  * **agent-skills**: Применять слэш-команды (`/spec`, `/planning`, `/build`, `/test`, `/code-simplify`, `/ship`) для пошагового контроля качества.
  * **fablize**: Всегда фиксировать Definition of Done (DoD) и предоставлять явные доказательства прохождения тестов перед завершением сессии.
  * **ponytail**: Регулярно проводить аудит кода на предмет overengineering и удалять неиспользуемые абстракции согласно стандарту YAGNI.
