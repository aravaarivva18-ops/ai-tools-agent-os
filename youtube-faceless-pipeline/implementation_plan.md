# Spec: YouTube Faceless Pipeline v2.1 — Production Video Run

## Objective
Произвести и оптимизировать первое полноценное видео для публикации на YouTube по теме: `"Autonomous AI Agents 2026: Как ИИ ведёт бизнес без человека"`. Видео должно соответствовать требованиям долгого формата (длительность $T_{video} > 90\text{ с}$), иметь оптимизированный SEO-пакет с A/B заголовками, превью-обложку и пройти проверку на уникальность сценария (сходство по Жаккару $< 40\%$).

## Tech Stack
- **Язык**: Python 3.12+ (Google Python Style Guide)
- **Библиотеки**: `Pillow`, `FastAPI`, `uvicorn`, `jinja2`
- **Инструменты**: `ffmpeg` (локальная сборка), macOS `say` CLI (генерация речи)
- **Внешние API**: Pollinations AI (генерация изображений)
- **Тестирование**: `pytest`, `pytest-asyncio`

## Commands
- **Тестирование**: `uv run pytest youtube-faceless-pipeline/tests/test_pipeline.py`
- **Проверка Ruff**: `uv run ruff check youtube-faceless-pipeline`
- **Проверка Bandit**: `uv run python -m bandit -r youtube-faceless-pipeline -x youtube-faceless-pipeline/tests`
- **Локальный запуск**: `python3 youtube-faceless-pipeline/main.py --serve --port 8000`

## Project Structure
- [youtube-faceless-pipeline/](file:///Users/rus/ai-tools/youtube-faceless-pipeline/)
  - [tools/content_gen.py](file:///Users/rus/ai-tools/youtube-faceless-pipeline/tools/content_gen.py) — Генератор видео, TTS и сшивки FFmpeg.
  - [seo_optimizer.py](file:///Users/rus/ai-tools/youtube-faceless-pipeline/seo_optimizer.py) — Оптимизация метаданных, A/B заголовки и Jaccard check.
  - [upload_cli.py](file:///Users/rus/ai-tools/youtube-faceless-pipeline/upload_cli.py) — Сборка upload package и чеклист AdSense.
  - [main.py](file:///Users/rus/ai-tools/youtube-faceless-pipeline/main.py) — FastAPI бэкенд и CLI точка входа.
  - [ui/index.html](file:///Users/rus/ai-tools/youtube-faceless-pipeline/ui/index.html) — Premium Dark BI веб-панель.
  - [tests/test_pipeline.py](file:///Users/rus/ai-tools/youtube-faceless-pipeline/tests/test_pipeline.py) — Тесты пайплайна.

## Code Style
Соблюдение Google Python Style Guide: импорт только модулей и пакетов.
```python
import os
import urllib.request
from typing import Any  # Исключение для typing
```

## Testing Strategy
- Юнит-тесты на генерацию длинных видео ($T_{video} > 90\text{ с}$).
- Тесты на корректность парсинга A/B вариантов заголовков.
- Офлайн-тестирование пайплайна (с моками сетевых запросов).

## Boundaries
- **Always**: Запускать линтеры Ruff и SAST Bandit перед фиксацией изменений.
- **Ask first**: Изменение параметров сборки FFmpeg.
- **Never**: Передавать секреты или API-ключи в открытом виде.

## Success Criteria (DoD)
* **Длительность видео**: $T_{video} > 90\text{ с}$.
* **Уникальность сценария**: $U_{jaccard} > 60\%$ (сходство $S_{jaccard} < 40\%$).
* **Экономия времени**: $T_{saved} \ge 6\text{ ч/видео}$.
* **SEO-пакет**: Генерация A/B вариантов заголовков, описания с таймкодами, тегов и обложки.
* **Быстродействие UI**: $t_{ui} < 2\text{ с}$.
* **Тесты**: $100\%$ успешное прохождение.

---

## Technical Plan (Phase 2: Plan)
1. **Расширение `content_gen.py` для длинных видео**:
   - Переписать генератор сценариев, чтобы для целевой ниши генерировалось 6 длинных сцен.
   - Метод `generate_speech` нарезать на предложения, синтезировать через `say` по частям во избежание переполнения буфера CLI, склеивать через FFmpeg в один `.wav`.
   - Внедрить жесткое ограничение сходства по Жаккару $S_{jaccard} < 40\%$ (уникальность сценария $> 60\%$).
2. **Интеграция A/B вариантов заголовков в `seo_optimizer.py`**:
   - Метод `optimize_metadata` должен возвращать `title_a` и `title_b`.
   - Вариант A строится на основе прямого вхождения темы, вариант B — вовлекающий/кликбейтный стиль.
3. **Обновление структуры `upload_package.json` в `upload_cli.py`**:
   - Сохранять оба варианта `title_a` и `title_b`.
4. **Обновление веб-интерфейса**:
   - Добавить A/B варианты заголовков в превью-панель.
   - Убедиться, что CSS содержит все неоновые акценты.
5. **Обновление тестов**:
   - Добавить тесты на проверку длительности сгенерированного видео $> 90\text{ с}$ и проверку лимита уникальности Жаккара.

---

## Tasks (Phase 3: Tasks)
- [ ] **Task 1: Обновление лимита уникальности и сценария в `content_gen.py`**
  - *Acceptance*: Сходство $S_{jaccard} > 40\%$ вызывает `ContentPolicyError`, а сценарий для ИИ-агентов содержит 6 сцен с общим количеством слов $> 130$.
  - *Verify*: `pytest -k test_pipeline`
  - *Files*: `youtube-faceless-pipeline/tools/content_gen.py`
- [ ] **Task 2: Реализация A/B заголовков в `seo_optimizer.py` и `upload_cli.py`**
  - *Acceptance*: Метод возвращает `title_a` и `title_b`, пакет метаданных содержит оба поля.
  - *Verify*: `pytest`
  - *Files*: `youtube-faceless-pipeline/seo_optimizer.py`, `youtube-faceless-pipeline/upload_cli.py`
- [ ] **Task 3: Интеграция A/B превью в `ui/index.html`**
  - *Acceptance*: В интерфейсе выводятся оба варианта заголовка для копирования.
  - *Verify*: Визуальный осмотр разметки.
  - *Files*: `youtube-faceless-pipeline/ui/index.html`
- [ ] **Task 4: Написание тестов на длину видео и A/B логику**
  - *Acceptance*: Тесты проверяют $T_{video} > 90\text{ с}$ и наличие полей A/B заголовков.
  - *Verify*: `uv run pytest`
  - *Files*: `youtube-faceless-pipeline/tests/test_pipeline.py`
