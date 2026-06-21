# Проект: AI Tools Workspace (Monorepo)

Набор профессиональных инструментов для локального SEO-анализа, маркетинговых аудитов, автоматизации продаж и юридического анализа контрактов.

## 🛠️ Технологический стек
- **Язык**: Python 3.12+
- **Менеджер зависимостей**: `uv` (workspace с поддержкой monorepo-структуры и единым виртуальным окружением `.venv`)
- **Линтер & Форматтер**: `ruff` (Google Style & PEP8 с правилами D и C90)
- **Тестирование промптов**: Встроенные возможности ИИ-ассистента (тестирование на моках и self-evaluation)
- **TUI Интерфейсы**: `textual` (асинхронные терминальные интерфейсы)

## 📁 Структура воркспейса (Monorepo Layout)
- [Makefile](file:///Users/rus/ai-tools/Makefile) — автоматизация рутинных задач разработчика.
- [pyproject.toml](file:///Users/rus/ai-tools/pyproject.toml) — конфигурация monorepo workspace.
- [ruff.toml](file:///Users/rus/ai-tools/ruff.toml) — глобальные правила линтинга и форматирования.
- [geo-seo/](file:///Users/rus/ai-tools/geo-seo/) — парсинг сайтов, SERP-анализ, SEO-показатели и генерация `.txt` / `.md`.
- [ai-sales/](file:///Users/rus/ai-tools/ai-sales/) — аудит продаж, анализ лидов и генерация PDF-отчетов.
- [ai-marketing/](file:///Users/rus/ai-tools/ai-marketing/) — анализ маркетинговых стратегий и генерация PDF-отчетов.
- [ai-legal/](file:///Users/rus/ai-tools/ai-legal/) — анализ юридических договоров, генерация типовых контрактов и PDF.
- [youtube-faceless-pipeline/](file:///Users/rus/ai-tools/youtube-faceless-pipeline/) — автогенерация сценариев, озвучка, рендеринг сцен и загрузка видео на YouTube.
- [dashboard-hand-on-pulse/](file:///Users/rus/ai-tools/dashboard-hand-on-pulse/) — Streamlit-дашборд «Рука на пульсе» для Таргет Медиа (клиентский продукт).
- [skills/](file:///Users/rus/ai-tools/skills/) — специализированные навыки ИИ-агентов (модульные инструкции).
- [tools/](file:///Users/rus/ai-tools/tools/) — вспомогательные скрипты разработки и утилиты.

## 🔌 Подключение навыков по запросу (Just-In-Time Skills)
Перед выполнением любой задачи **обязательно** ознакомьтесь с соответствующим файлом навыка в папке `skills/`:
- **Скрапинг и парсинг HTML (Selectolax / curl_cffi)**: См. [skills/stealth-scraping/SKILL.md](file:///Users/rus/ai-tools/skills/stealth-scraping/SKILL.md)
- **Генерация PDF-документов (Typst)**: См. [skills/typst-pdf/SKILL.md](file:///Users/rus/ai-tools/skills/typst-pdf/SKILL.md)
- **Хранение данных и RLS (Supabase / pgvector / Alembic)**: См. [skills/database-persistence/SKILL.md](file:///Users/rus/ai-tools/skills/database-persistence/SKILL.md)
- **Создание и стандартизация JIT-навыков (Pydantic / Agno-style)**: См. [skills/skill-creator/SKILL.md](file:///Users/rus/ai-tools/skills/skill-creator/SKILL.md)



## 💻 Команды сборки и разработки (Makefile CLI)
- **Синхронизация зависимостей**: `make sync`
- **Форматирование кода**: `make format`
- **Автоматическое исправление**: `make lint`
- **Проверка качества кода**: `make check`
- **Юнит-тестирование**: `make test`
- **Очистка кэша**: `make clean`
- **Импорт документов в Wiki**: `uv run python tools/llm_wiki.py injest`
- **Запрос из Wiki**: `uv run python tools/llm_wiki.py query <заметка> [--depth <глубина>]`



## 📐 Глобальные правила разработки (v10)
Все разработки регулируются конституцией [GEMINI_ANTIGRAVITY.md](file:///Users/rus/GEMINI_ANTIGRAVITY.md).
Основные принципы:
- **Solo Loop v10**: Субагенты отключены. Статус сессии восстанавливается из `implementation_plan.md` через `PlanningWithFiles`. Вывод сжимается через `SoloLoopV10`.
- **Валидация и Схемы**: Валидировать выходы LLM по Pydantic моделям и генерировать схемы инструментов через `tools/tool_validator.py`.
- **Целостность документации**: При обновлении конституций, гайдов и баз знаний сохранять точные тестовые маркеры (например, домены вида `context7.com`), проверяемые TDD-тестами.
- **Изоляция прототипов**: Временный код (Spikes) сохраняется строго в папках `scratch/`. Импорт файлов из `scratch/` в основные рабочие модули категорически запрещен.
- **Навыки**: Использовать [agent_skills.py](file:///Users/rus/ai-tools/tools/agent_skills.py) для JIT-генерации шаблонов: `is_ui` (Framer Motion, GSAP, Vanilla CSS, Three.js; Tailwind CSS по умолчанию запрещен), `is_seo` (Programmatic SEO, EEAT, GEO), `is_scale` (Dan Martell 10-80-10, SOP, Pre-delegation Checklist, Buyback Loop) и `is_mcp` (Anthropic MCP SDK, JSON-RPC, SQLite YAGNI).
- **Плагины**: Обязательно использование `agent-skills` (слэш-команды), `fablize` (DoD и доказательства) и `ponytail` (YAGNI/контроль абстракций).
- **YAGNI (Ponytail) & TDD**: Философия Karpathy Vibe Coding (плоский линейный код, макс 2 уровня абстракции) и levelsio YAGNI (минималистичный стек, SQLite). Любой код сопровождается тестами. В ходе YAGNI-аудита v10 удалено 14% bloat из `tools/` (избыточные файлы данных).
- **Self-Healing & Self-Improvement**: При ошибках раннер `tools/test_healer.py` перехватывает сбои (Stealth Stop на 3-й раз). В конце сессии - [self_improve.py](file:///Users/rus/ai-tools/tools/self_improve.py) с классификацией навыков и подсчетом времени выкупа (Buyback Time).
- **Абсолютные пути**: Использовать `file:///Users/rus/` для локального хоста macOS. Пути `/home/workdir/` запрещены.
- **Безопасность (SAST)**: Для запуска Bandit использовать `python3 -m bandit` из окружения `uv`. SAST-сканер секретов оптимизирован (выполнение за 0.33с за счет os.walk обрезки `.venv`, `vault` и `bitrix-knowledge`).

