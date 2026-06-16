# Проект: AI Tools Workspace (Monorepo)

Набор профессиональных инструментов для локального SEO-анализа, маркетинговых аудитов, автоматизации продаж и юридического анализа контрактов.

## 🛠️ Технологический стек
- **Язык**: Python 3.12+
- **Менеджер зависимостей**: `uv` (workspace с поддержкой monorepo-структуры и единым виртуальным окружением `.venv`)
- **Линтер & Форматтер**: `ruff` (Google Style & PEP8 с правилами D и C90)
- **Тестирование промптов**: Встроенные возможности ИИ-ассистента (субагенты и self-evaluation)
- **TUI Интерфейсы**: `textual` (асинхронные терминальные интерфейсы)

## 📁 Структура воркспейса (Monorepo Layout)
- [Makefile](file:///Users/rus/ai-tools/Makefile) — автоматизация рутинных задач разработчика.
- [pyproject.toml](file:///Users/rus/ai-tools/pyproject.toml) — конфигурация monorepo workspace.
- [ruff.toml](file:///Users/rus/ai-tools/ruff.toml) — глобальные правила линтинга и форматирования.
- [geo-seo/](file:///Users/rus/ai-tools/geo-seo/) — парсинг сайтов, SERP-анализ, SEO-показатели и генерация `.txt` / `.md`.
- [ai-sales/](file:///Users/rus/ai-tools/ai-sales/) — аудит продаж, анализ лидов и генерация PDF-отчетов.
- [ai-marketing/](file:///Users/rus/ai-tools/ai-marketing/) — анализ маркетинговых стратегий и генерация PDF-отчетов.
- [ai-legal/](file:///Users/rus/ai-tools/ai-legal/) — анализ юридических договоров, генерация типовых контрактов и PDF.
- [skills/](file:///Users/rus/ai-tools/skills/) — специализированные навыки ИИ-агентов (модульные инструкции).
- [ollama/](file:///Users/rus/ai-tools/ollama/) — конфигурации Modelfile для локального запуска моделей.
- [tools/](file:///Users/rus/ai-tools/tools/) — общие утилиты и дашборд мониторинга (`dashboard.py`).

## 🔌 Подключение навыков по запросу (Just-In-Time Skills)
Перед выполнением любой задачи **обязательно** ознакомьтесь с соответствующим файлом навыка в папке `skills/`:
- **Скрапинг и парсинг HTML (Selectolax / curl_cffi)**: См. [skills/stealth-scraping/SKILL.md](file:///Users/rus/ai-tools/skills/stealth-scraping/SKILL.md)
- **Генерация PDF-документов (Typst)**: См. [skills/typst-pdf/SKILL.md](file:///Users/rus/ai-tools/skills/typst-pdf/SKILL.md)
- **Тестирование и валидация промптов**: См. [skills/prompt-testing/SKILL.md](file:///Users/rus/ai-tools/skills/prompt-testing/SKILL.md)
- **Хранение данных и RLS (Supabase / pgvector / Alembic)**: См. [skills/database-persistence/SKILL.md](file:///Users/rus/ai-tools/skills/database-persistence/SKILL.md)
- **Управление серверами (SSH / Cloudflare DNS по API)**: См. [skills/vps-automation/SKILL.md](file:///Users/rus/ai-tools/skills/vps-automation/SKILL.md)
- **Оркестрация агентов, стейт и кэш (SPARC / Checkpoints / Prompt Caching)**: См. [skills/agent-orchestration/SKILL.md](file:///Users/rus/ai-tools/skills/agent-orchestration/SKILL.md)
- **Стандарты фронтенда и верстки (Mobile-First / Accessibility WCAG / Web Vitals)**: См. [skills/frontend-standards/SKILL.md](file:///Users/rus/ai-tools/skills/frontend-standards/SKILL.md)
- **Адаптивная память агентов (Scoping / Consolidation Decision Engine)**: См. [skills/agent-memory/SKILL.md](file:///Users/rus/ai-tools/skills/agent-memory/SKILL.md)
- **Разработка промптов и контекст (XML Delimiters / CoT / ReAct / Caching)**: См. [skills/prompt-engineering/SKILL.md](file:///Users/rus/ai-tools/skills/prompt-engineering/SKILL.md)

## 💻 Команды сборки и разработки (Makefile CLI)
- **Синхронизация зависимостей**: `make sync`
- **Форматирование кода**: `make format`
- **Автоматическое исправление**: `make lint`
- **Проверка качества кода**: `make check`
- **Юнит-тестирование**: `make test`
- **Очистка кэша**: `make clean`
- **Конвертация документов в MD**: `uv run python tools/convert_docs.py <путь_к_файлу> [-o <выходной_файл>]`


## 📐 Глобальные правила разработки

### 1. Качество кода и Google Python Style
- **Чистота импортов**: Импортируйте только пакеты и модули (`import os`, `from pathlib import Path`), а не конкретные функции, классы или переменные из модулей (исключение: модуль `typing` для аннотаций типов). Это сохраняет пространство имен чистым.
- **Аннотации типов**: Все функции, методы и глобальные переменные должны иметь строгую аннотацию типов.
- **Управление исключениями**: Избегайте bare except (`except Exception: pass`). Всегда перехватывайте конкретные исключения (`except KeyError:`) и логируйте аномалии.
- **Контроль ресурсов**: Всегда открывайте файлы и соединения через менеджер контекста `with`.

### 2. Тестирование (TDD)
- Пишите тесты, проверяющие поведение публичных контрактов (Public API), а не детали внутренней реализации. Рефакторинг кода не должен приводить к падению тестов, если поведение не изменилось.
- Минимизируйте использование моков (mocks) — используйте их только для изоляции сетевых вызовов.
- Тесты должны запускаться локально и выполняться быстро (<100мс на юнит-тест).

### 3. Обязательное пятистрочное планирование перед работой (5-Line Planning Rule)
Перед тем как начать изменять код в нескольких файлах или вносить архитектурные изменения, ИИ-ассистент обязан сформулировать в чате лаконичный **5-строчный план** (GStack Lite) и дождаться подтверждения:
1. **Что (What)**: конкретная цель изменений.
2. **Почему (Why)**: техническое обоснование.
3. **Область изменений (Files)**: список затрагиваемых файлов.
4. **Тест-кейс (Test)**: как будет верифицирован результат.
5. **Риски (Risk)**: возможные конфликты, побочные эффекты или скрытые зависимости.

### 4. Актуализация правил и инструкций (Always Update Rules)
- После любых изменений в кодовой базе, зависимостях, технологическом стеке или соглашениях ИИ-ассистент **обязан** проверить, требуют ли внесенные изменения обновления проектных правил или файлов инструкций (`CLAUDE.md`, `.cursorrules`, `GEMINI_ANTIGRAVITY.md` или файлов навыков `SKILL.md`).
- При обнаружении расхождений соответствующие файлы правил должны быть обновлены немедленно для обеспечения согласованной и бесконфликтной работы во время будущих сессий.
- **Ограничение ADR 0005**: Категорически запрещено создавать новые файлы/папки JIT-навыков для работы со стандартными типами данных (Markdown, JSON, XML, YAML). Вся логика для них должна быть стандартной и храниться в существующих глобальных регламентах.

### 5. Стабильность окружения и безопасность (Environment & Security)
- Для запуска диагностических утилит безопасности (например, Bandit) и других автоматических скриптов необходимо использовать строго абсолютный верифицированный путь к Python из виртуального окружения: `"/Users/rus/ai-tools/.venv/bin/python" -m bandit -r ...`. Это предотвращает сбои путей и ошибки несовместимости интерпретаторов на macOS/Apple Silicon.
- Всегда верифицируйте физическое наличие исполняемых файлов (`os.path.exists`) перед их запуском через `subprocess`.

