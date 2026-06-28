# 📐 Локальные правила разработки (Monorepo Agent Contract v10)

## 🗂️ Структура модулей
- [[tools/AGENTS.md]] — CLI Dashboard, Diff Applier, Test Healer и утилиты.
- [[geo-seo/AGENTS.md]] — Парсинг и обход защит (`selectolax`, `curl_cffi`).
- [[ai-sales/AGENTS.md]] — Шаблоны PDF и генерация отчетов Typst.
- [[youtube-faceless-pipeline/AGENTS.md]] — Скрипты, рендеринг и YouTube API.
- [[dashboard-hand-on-pulse/AGENTS.md]] — Streamlit-панель мониторинга Target Media.

## 📐 Регламенты сессии
- **Solo Loop v10 + Compaction**: Субагенты запрещены. Статус сессии считывается из `implementation_plan.md` через `PlanningWithFiles`.
- **Авто-инжект стандартов (Agent OS)**: При запуске `PlanningWithFiles` автоматически генерируется файл `vault/standards.md` на основе используемых технологий (Python, Frontend, Marketing). Агент ОБЯЗАН прочитать этот файл при инициализации и строго следовать стандартам.
- **Слэш-команды ИИ (Mental Commands)**:
  - `/discover-standards` — извлечь найденные в коде паттерны качества и сохранить в `/Users/rus/ai-tools/standards/`.
  - `/inject-standards` — принудительно обновить файл `vault/standards.md` в текущем проекте.
- **CLI-команды `agy`**:
  - `agy run` — запуск авто-лечения ошибок через `test_healer.py`.
  - `agy search "<query>"` — семантический поиск по хандоффам.
  - `agy init` — инициализация конфига проекта.
- **Karpathy & levelsio**: Линейный плоский код (макс 2-3 уровня абстракции), SQLite по умолчанию.
- **JIT Testing**: Запуск только связанных тестов через `agy run` (или `test_healer.py --diff`). pytest запускать только перед шипингом.
- **Commit-on-DoD**: Коммиты делать только после закрытия логической вехи (DoD) и зеленых тестов.
- **Внутренний состязательный цикл (Adversarial Loop)**: Для нетривиальных задач (КП, ТЗ, стратегии, код >30 строк) агент обязан сгенерировать черновик (Draft) и жестко раскритиковать его (проверка на воду, ИИ-мусор Stop-Slop, оверхед) в размышлении (thinking) перед выводом финального ответа.
- **Obsidian**: Логировать хандоффы в Daily Note через `session_logger.py`.
