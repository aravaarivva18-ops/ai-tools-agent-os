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
- [[youtube-faceless-pipeline/AGENTS.md]] — Script generation, scene rendering, and upload CLI.
- [[dashboard-hand-on-pulse/AGENTS.md]] — Client Streamlit dashboard for Target Media.
- [[tools/rules_validator.py]] — нормализация и health check конституции
- [[tools/self_improve.py]] — главный автоцикл улучшения

---

## 📐 Глобальные регламенты (v10)

Все разработки в монорепозитории регулируются конституцией [GEMINI_ANTIGRAVITY.md](file:///Users/rus/GEMINI_ANTIGRAVITY.md).
Основные стандарты:
- **Solo Loop v10 + Compaction**: Субагенты запрещены. Статус сессии считывается из `implementation_plan.md` через `PlanningWithFiles`. История логов автоматически сжимается методом `compact_context` (summarize -> clean).
- **Валидация и Схемы**: Строгая валидация по BaseModel и экспорт Agno-style схем через `tools/tool_validator.py`. Внедрен жесткий AST Guard в `AgentSkillsManager` для блокировки вызовов субагентов перед генерацией схем.
- **Тест-маркеры в доках**: При редактировании инструкций и баз знаний сохранять ключевые слова и доменные имена (например, `context7.com`), используемые в TDD-тестах для верификации документов.
- **Запрет импорта из scratch/**: Черновики и прототипы пишутся строго внутри директорий `scratch/`. Запрещено импортировать модули из `scratch/` в продакшн-код.
- **Навыки**: Управление JIT-навыками через [agent_skills.py](file:///Users/rus/ai-tools/tools/agent_skills.py) с поддержкой тем: `is_ui` (Framer Motion, GSAP, Vanilla CSS, Three.js; Tailwind CSS по умолчанию запрещен), `is_seo` (Programmatic SEO, EEAT, GEO), `is_scale` (Dan Martell 10-80-10, SOP, Pre-delegation, Buyback Loop) и `is_mcp` (Anthropic MCP SDK, SQLite YAGNI).
- **Окружение**: Python 3.12+ (`uv run`), форматирование Ruff (`ruff.toml`).
- **Плагины**: Обязательно использование `agent-skills` (слэш-команды), `fablize` (DoD и доказательства) и `ponytail` (YAGNI/контроль абстракций).
- **YAGNI & Code Style**: Философия Karpathy Vibe Coding (линейный код, макс 2 уровня абстракции) и levelsio YAGNI (минималистичный стек, SQLite). В ходе YAGNI-аудита v10 удалено 14% bloat из `tools/`.
- **Безопасность (SAST)**: SAST-сканер секретов оптимизирован (выполнение за 0.33с за счет os.walk обрезки `.venv`, `vault` и `bitrix-knowledge`).
- **Процесс**: Spec -> Research -> Plan -> Implement -> Test -> Ship.
  * *Режим Fast-Track*: для задач <30 строк изменений и <=1 измененного файла пропускать Spec/Planning и писать код напрямую.
  * *JIT Testing*: в процессе кодинга запускать только точечные тесты через `tools/test_healer.py --diff`. Полный прогон pytest выполнять только перед коммитом на шаге Ship.
  * *Commit-on-DoD*: коммиты выполнять только после успешного завершения логической вехи (DoD) и зеленых тестов. Промежуточные "сырые" изменения не коммитить.
  * *Сброс истории*: при длине диалога >40-50k токенов агент сохраняет чекпоинт в `implementation_plan.md` и предлагает открыть новый чат для очистки контекста.
