# Spec: Security Scanner UI Integration & Lint Cleanups (v4.0)

## Objective
Интегрировать инструмент статического анализа безопасности `security_scanner.py` в веб-интерфейс аналитического дашборда `dashboard_mvp`. Устранить все накопившиеся ошибки Ruff линтера в монорепозитории для успешного прохождения проверок качества кода. Добавить `ai-ads/` в `.gitignore` для предотвращения коммита временных отчетов рекламы.

## Tech Stack
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, SQLite
- **Frontend**: Vanilla JS, Tailwind CSS (via CDN), FontAwesome (icons), Google Fonts (Outfit, Inter)
- **SAST / Security**: Bandit SAST, Custom RegExp Secrets Scanner
- **Formatting / Linter**: Ruff (v0.3+)
- **Testing**: Pytest

## Commands
- **Синхронизация зависимостей**: `make sync`
- **Проверка линтером**: `make check`
- **Запуск автоисправления**: `make lint`
- **Запуск тестов**: `make test`
- **Запуск дашборда**: `uv run python tools/dashboard_mvp/main.py`

## Project Structure
- `tools/security/security_scanner.py` — Логика SAST сканирования Bandit и поиска секретов.
- `tools/dashboard_mvp/main.py` — FastAPI бэкенд, раздача статики и новые API-роуты безопасности.
- `tools/dashboard_mvp/static/` — HTML/JS фронтенд дашборда.
- `tools/dashboard_mvp/test_api.py` — Интеграционные тесты API бэкенда.
- `tools/clean_image_metadata/clean_image_metadata.py` — Утилита очистки метаданных изображений (исправление линтов).
- `ai-ads/scripts/generate_ads_pdf.py` — Генератор PDF рекламы (исправление линтов).
- `ai-legal/scratch/extract.py` — Скрипт извлечения текста контрактов (исправление линтов).
- `.gitignore` — Список игнорируемых файлов.

## Code Style
- **Karpathy Vibe Coding**: Плоский линейный код, минимальное число уровней абстракции (макс 2), понятные имена функций, отсутствие избыточных интерфейсов.
- **Pydantic**: Использование строгих схем для API запросов и ответов (при необходимости).
- **Ruff Clean**: Отсутствие неиспользуемых импортов, неиспользуемых переменных, соответствие PEP8 и Google Style.

```python
# Пример стиля
def get_security_scan_results(path: str) -> dict:
    """Выполняет сканирование директории и форматирует результаты."""
    findings = []
    # Линейный, понятный код без лишних фабрик и оберток
    return {"status": "completed", "findings": findings}
```

## Testing Strategy
- Расширить `tools/dashboard_mvp/test_api.py` тестом эндпоинта `@app.post("/api/security/scan")`.
- Убедиться, что вызов эндпоинта возвращает корректную структуру JSON с ключами `bandit` и `secrets`.
- Проверить работоспособность Bandit-сканера в тестовом режиме.

## Boundaries
- **Always**: Запускать `make check` и `make test` перед финализацией сессии.
- **Ask first**: Изменение параметров запуска Bandit или добавление сторонних npm/pip пакетов.
- **Never**: Коммитить реальные API ключи или пароли (всегда использовать моки и сканировать на секреты перед пушем).

## Success Criteria
1. Все ошибки Ruff линтера устранены. Команда `make check` завершается успешно (exit code 0).
2. Папка `ai-ads` добавлена в `.gitignore`.
3. Создан эндпоинт `/api/security/scan`, возвращающий результаты Bandit SAST в формате JSON и список найденных секретов.
4. Разработан интерфейс вкладки "Безопасность" в `dashboard_mvp`:
   - Красивая кнопка "Запустить сканирование" с лоадером.
   - Сводные карточки метрик (Всего угроз, Утечки секретов, Ошибки Bandit).
   - Интерактивный список уязвимостей с разметкой критичности (High/Medium/Low) и указанием файлов/строк.
   - Поддержка Glassmorphism темного стиля.
5. Написан тест для нового эндпоинта в `test_api.py`. Все 106+ тестов проходят успешно.

## Open Questions
*В данный момент открытых вопросов нет. План составлен в соответствии с требованиями YAGNI.*

---

# Implementation Plan

## Phase 1: Lint Fixes & Gitignore (A)
1. Исправить Ruff ошибки в `tools/security/security_scanner.py` (перенос импортов, исправление try-except-continue).
2. Добавить поддержку формата JSON в `build_bandit_command` и `run_security_scan` (флаги `-f json`).
3. Исправить Ruff ошибки в `tools/clean_image_metadata/clean_image_metadata.py` (удалить ttk, переформатировать docstrings, заменить лямбда-аргументы на `_`, убрать неиспользуемую переменную `app`).
4. Исправить Ruff ошибки в `ai-ads/scripts/generate_ads_pdf.py` (удалить неиспользуемую переменную `bars_markup` и лишние пробелы в пустых строках).
5. Исправить Ruff ошибки в `ai-legal/scratch/extract.py` (заменить `attrs` на `_attrs`).
6. Добавить строку `/ai-ads/` в `.gitignore`.
7. Запустить `make check`, убедиться, что все ошибки исправлены.

## Phase 2: Backend API Endpoint (B)
1. В `tools/dashboard_mvp/main.py` импортировать функции сканера.
2. Реализовать эндпоинт `/api/security/scan`. Эндпоинт должен запускать Bandit с опцией `-f json` и возвращать отформатированный результат вместе с найденными секретами.
3. Реализовать обработку ошибок на случай, если Bandit не установлен или завершился сбоем.

## Phase 3: Frontend Integration (B)
1. В `tools/dashboard_mvp/static/index.html` добавить вкладку "Безопасность" в боковое/верхнее меню.
2. Добавить блок интерфейса безопасности (карточки метрик, кнопка запуска, таблица уязвимостей).
3. В `tools/dashboard_mvp/static/app.js` добавить функции для работы с вкладкой безопасности: переключение вкладки, запрос на сканирование, рендеринг результатов.

## Phase 4: Verification & Testing
1. Добавить юнит-тест в `tools/dashboard_mvp/test_api.py`.
2. Запустить `make test` и `make check`.
3. Сделать отчет по DoD.

---

## Decisions History (YAGNI Compliance)
В рамках прошлых сессий были приняты и отклонены следующие решения:
- **Claude Code Router**: Отклонен (Rejected) по принципу YAGNI. Локальный агент `agy` работает напрямую через SDK, внешние прокси избыточны.
- **Spec Kit / specify-cli**: Отклонен (Rejected) по принципу YAGNI. Дублирует функционал планирования `PlanningWithFiles`.
- **Claude Taskmaster**: Отклонен (Rejected) по принципу YAGNI. Вся координация задач закрывается Markdown-планом.
- **n8n Server (Workflow Orchestration)**: Отклонен (Rejected) по принципам YAGNI и Solo Loop v10.
  - *Обоснование*: n8n требует запуска тяжелого Node.js Docker-контейнера (потребление 1-2 ГБ ОЗУ в простое), что нерационально на macOS (MacBook Air M5). Лицензия Sustainable Use License накладывает коммерческие ограничения на продажу готовых workflows клиентам. Интеграция с локальной файловой системой хоста и выполнение Python-кода из изолированного контейнера требует проброса SSH/Docker sockets, что усложняет систему.
  - *Альтернатива*: Задачи автоматизации, OSINT и self-healing полностью решаются нативно через `tools/advanced_workflow.py` (легковесный Python-оркестратор), локальный планировщик `cron`/`make` и прямой запуск скриптов с помощью `subprocess`/`run_command` без накладных расходов на Docker.

---

## 🗺️ Vibe Coding Course Project Audit & Remediation Plan (v5.0)

В результате аудита проекта [Vibe_Coding_Course_Project](file:///Users/rus/Desktop/Vibe_Coding_Course_Project/) были сделаны следующие выводы и сформирован план доработки:

### 1. Оценка полноты (Completeness)
*   **Выявленный Gap**: В `README.md` заявлен файл `gemini_researcher_prompt.md`, который физически отсутствовал в папке `Marketing_and_Planning/` и в сборном документе `full_project_documentation.md`.
*   **Действие**: Восстановлен и создан файл [gemini_researcher_prompt.md](file:///Users/rus/Desktop/Vibe_Coding_Course_Project/Marketing_and_Planning/gemini_researcher_prompt.md) с детальным промптом для исследования рынка, сегментации ЦА и анализа конкурентов.
*   **Добавочный файл**: Обнаружен файл [council-prompt.md](file:///Users/rus/Desktop/Vibe_Coding_Course_Project/Marketing_and_Planning/council-prompt.md) («AI-Совет директоров»), не описанный в `README.md`. Карта проекта в `README.md` актуализирована.

### 2. Бизнес-логика и Маркетинг (Business & Marketing Gaps)
*   **Заниженные расходы на трафик**: В планах воронки заложена цена клика (CPC) в 50 руб. Для узкой тематики ИИ-разработки в СНГ реальный CPC в качественных каналах (Telegram Ads, Яндекс.Директ) составляет 100-200+ руб.
    *   *Решение*: Скорректировать финансовый план в `vibe_coding_course_plan.md`, добавив консервативный сценарий с CPC = 120 руб. и ROMI = 150%.
*   **Игнорирование комиссий и налогов**: ROMI 353% рассчитан без учета эквайринга (Prodamus: 3.5%-5%) и налога (НПД: 6%).
    *   *Решение*: Внедрить в калькулятор окупаемости вычет налогов и транзакционных издержек.
*   **Отсутствие LTV-модели (Rebilling)**: После прохождения основного курса ученик теряется.
    *   *Решение*: Интегрировать в воронку подписочный клуб поддержки (Rebilling) с тарифом 2900 руб/мес.

### 3. UI/UX и Квиз-Лидмагнит (UI/UX Gaps)
*   **Спецификации квиза**: Нет точного списка вопросов для квиза проверки жизнеспособности MVP.
    *   *Решение*: Разработать структуру из 4 простых вопросов с интерактивными карточками для квиза (Цель, Бюджет, Сроки, Стек).
*   **KeyCastr для Windows**: Инструкция упоминает KeyCastr только для macOS.
    *   *Решение*: Добавить Carnac в список софта для Windows в `additional_preparations.md`.

### 4. YAGNI-аудит
*   **Сложность окружения**: Обучение Python-парсерам создает трудности с установкой библиотек (pip, CORS, С-компиляторы для lxml) для новичков.
    *   *Решение*: Рекомендовать Google IDX / Replit как основную песочницу для Python-скриптов, чтобы избежать локальной настройки на ПК ученика.

---

## 🎨 Визуальный Концепт Продукта
Сгенерирован и скопирован в папку брендинга файл визуального концепта личного кабинета ученика Vibecode (Glassmorphism, Neon Cyan/Deep Indigo):
🔗 [vibecode_concept.jpg](file:///Users/rus/Desktop/Vibe_Coding_Course_Project/Branding/vibecode_concept.jpg)



