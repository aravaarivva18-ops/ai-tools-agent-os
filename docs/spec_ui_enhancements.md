# Spec: UI Skills Enhancements with Component Frameworks (v3.2)

## Objective
Расширить генератор JIT-навыков в `tools/agent_skills.py`, интегрировав рекомендации современных каталогов готовых UI-компонентов (Magic UI, Animata, Uiverse, Cult-ui) на основе OSINT канала Матвея Шульги. Это повысит скорость разработки (time-to-market) интерфейсов и снизит потребление токенов за счет переиспользования готовых анимированных паттернов.

## Tech Stack
* Language: Python 3.12+
* Linter/Formatter: Ruff
* Testing: pytest

## Commands
* Test: `uv run pytest tools/tests/test_ui_stack.py`
* Lint: `uv run ruff check tools/agent_skills.py`

## Project Structure
* `tools/agent_skills.py` → Генератор JIT-навыков.
* `tools/tests/test_ui_stack.py` → Тесты верификации.
* `docs/spec_ui_enhancements.md` → Данная спецификация.

## Code Style
```python
# Использование type hints и чистого Python без лишних абстракций
def is_ui_themed(name: str, description: str) -> bool:
    keywords = ["ui", "landing", "animation", "hover", "scroll", "frontend", "css", "web"]
    return any(kw in name.lower() or kw in description.lower() for kw in keywords)
```

## Testing Strategy
* Framework: pytest
* Location: `tools/tests/test_ui_stack.py`
* Coverage: Позитивный (проверка наличия новых библиотек Magic UI, Animata в сгенерированных UI-навыках) и негативный (отсутствие в backend-навыках).

## Boundaries
* **Always**: Писать тесты перед модификацией кода, соблюдать standard Conventional Commits.
* **Ask first**: Изменение глобальной структуры директорий `skills/`.
* **Never**: Использовать субагентов или выходить за рамки Solo Loop.

## Success Criteria
1. Вызов `create_skill` для UI-навыков включает в шаблон `SKILL.md` библиотеки: `Magic UI`, `Animata`, `Uiverse`, `Cult-ui` в качестве рекомендованных UI-компонентов.
2. Тесты проходят успешно (100% green).
3. Все изменения закоммичены по Conventional Commits.
