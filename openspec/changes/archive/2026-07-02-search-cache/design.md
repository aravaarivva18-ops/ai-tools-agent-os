# Технический дизайн: Кэширование RAG-поиска

## Реализация кэша в `tools/obsidian/semantic_search.py`

### 1. Определение путей и вспомогательных функций
Добавить в `tools/obsidian/semantic_search.py`:
- Путь к файлу кэша: `CACHE_FILE = os.path.join(workspace_root, "vault/search_cache.json")`
- Функция вычисления актуального `mtime` папки хандоффов (по максимальному mtime всех `.md` файлов):
  ```python
  def get_handoffs_mtime() -> float:
      if not os.path.exists(VAULT_HANDOFFS_DIR):
          return 0.0
      mtimes = []
      for root, _, files in os.walk(VAULT_HANDOFFS_DIR):
          for file in files:
              if file.endswith(".md"):
                  mtimes.append(os.path.getmtime(os.path.join(root, file)))
      return max(mtimes) if mtimes else 0.0
  ```

### 2. Кэширование в `get_semantic_brief`
Изменить метод `get_semantic_brief(query: str, limit: int = 3, semantic: bool = False) -> str`:
- Считывать `current_mtime = get_handoffs_mtime()`.
- Считывать кэш из `CACHE_FILE`.
- Если `query` найден в кэше и `cache[query]["mtime"] == current_mtime`:
  - Вернуть сохраненный `brief` мгновенно.
- Если совпадения нет:
  - Выполнить стандартный поиск (текстовый или векторный).
  - Записать результат в кэш:
    ```python
    cache["queries"][query] = {
        "mtime": current_mtime,
        "brief": brief_result
    }
    ```
  - Сохранить кэш на диск в `CACHE_FILE`.

## Тестирование
Создать файл тестов `tools/tests/test_semantic_search.py`, проверяющий:
1. Запись результатов поиска в кэш.
2. Мгновенную отдачу из кэша при повторном запросе без вызова векторного поиска.
3. Инвалидацию кэша при изменении `mtime` файлов в папке хандоффов.
