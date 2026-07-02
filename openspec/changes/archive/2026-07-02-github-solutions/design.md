# Технический дизайн: Генератор Repository Map

## Реализация в `tools/repo_mapper.py`

### 1. Архитектура парсера (на базе Python AST)
- Модуль будет использовать стандартную библиотеку `ast` для парсинга исходного кода без добавления тяжелых зависимостей.
- Метод `generate_map(workspace_root: Path) -> str`:
  - Обходит папки `core/` и `tools/` (игнорируя тесты `tests/`, `.venv`, `scratch`, `_archive`).
  - Читает каждый файл `.py` и парсит его структуру:
    - Извлекает имя класса (`ast.ClassDef`), его методы (`ast.FunctionDef` внутри класса) и их сигнатуры.
    - Извлекает функции верхнего уровня.
    - Для каждого символа берет первую строку docstring.
  - Форматирует вывод в дерево:
    ```text
    - core/solo_loop.py
      - Class: SoloLoopV10
        - def compact_context(self, history_steps, max_tokens)
          # Summarizes history steps and cleans up detailed logs...
    ```
- Метод `write_repo_map(workspace_root: Path)` записывает сгенерированную карту в `vault/repo_map.txt`.

### 2. Интеграция в PlanningWithFiles
В файле `tools/planning_with_files.py` в методе `restore_state` добавить вызов:
```python
from tools.repo_mapper import write_repo_map
write_repo_map(self.workspace_root)
```
Это гарантирует автоматическое обновление карты символов при каждом старте или прогреве сессии.

## Тестирование
Создать файл тестов `tools/tests/test_repo_mapper.py`, который:
1. Создает фиктивный Python-файл со структурой классов и методов во временной папке.
2. Запускает генератор карты и проверяет, что сигнатуры классов, методов и docstring извлечены корректно.
3. Проверяет запись в `vault/repo_map.txt`.
