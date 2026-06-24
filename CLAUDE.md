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
- **Проектирование архитектуры автоматизации и навыков (Solo Loop / Harness)**: См. [skills/harness/SKILL.md](file:///Users/rus/ai-tools/skills/harness/SKILL.md)
- **Воркфлоу и генерация контента (ComfyUI / Vast.ai)**: См. [skills/comfyui/SKILL.md](file:///Users/rus/ai-tools/skills/comfyui/SKILL.md)
- **Клонирование и реверс-инжиниринг сайтов (Browser Automation / Next.js)**: См. [skills/website-cloner/SKILL.md](file:///Users/rus/ai-tools/skills/website-cloner/SKILL.md)



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
Все разработки в монорепозитории регулируются конституцией [GEMINI_ANTIGRAVITY.md](file:///Users/rus/GEMINI_ANTIGRAVITY.md).

Ключевые регламенты (подробнее см. в соответствующих разделах [GEMINI_ANTIGRAVITY.md](file:///Users/rus/GEMINI_ANTIGRAVITY.md)):
- **Strict Solo Loop & ACI** (раздел 3, 15): Использование субагентов полностью запрещено, Stealth Stop на 3-й ошибке, чтение файлов диапазонами.
- **Инструменты и Плагины** (раздел 20, 21): Нативные инструменты имеют приоритет, обязательное использование `agent-skills`, `fablize` и `ponytail`.
- **Karpathy Vibe Coding & YAGNI** (раздел 13): Плоский линейный код, максимум 2-3 уровня абстракции.
- **TDD & Self-Healing** (раздел 5, 23): Разработка строго через тесты, автоисправление через `test_healer.py`.
- **Безопасность (SAST) & Пути** (раздел 6, 10): Только абсолютные пути `file:///Users/rus/`, запуск Bandit из окружения `uv`.
- **Self-Improvement** (раздел 22): Автоциклы улучшения и нормализация — см. раздел «Протокол Самообучения и Эволюции» в [GEMINI_ANTIGRAVITY.md](file:///Users/rus/GEMINI_ANTIGRAVITY.md).
- **Изоляция прототипов**: Временный код (Spikes) сохраняется строго в папках `scratch/`. Импорт файлов из `scratch/` в основные рабочие модули категорически запрещен.


