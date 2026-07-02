# Технический дизайн: Точный токенизатор в SoloLoopV10

## Логика интеграции в `core/solo_loop.py`

Внедряем ленивый импорт функции `count_tokens_exact` в метод `compact_context`:

```python
from tools.context_utils import count_tokens_exact
```

### Алгоритм сжатия Exact Token Compression:
1. Для каждого шага в `history_steps` формируем базовый словарь:
   - `command`
   - `success`
   - `output` (обрезанный через `compress_log`).
2. Считаем суммарные токены:
   `total_tokens = sum(count_tokens_exact(s["command"]) + count_tokens_exact(s["output"]) for s in cleaned_steps)`
3. Если `total_tokens <= max_tokens` (по умолчанию `2000`), возвращаем как есть.
4. **Фаза 1 (Схлопывание успешных шагов)**:
   - Итерируемся по `cleaned_steps` (от старых к новым).
   - Если шаг успешный (`success == True`) и его `output` не пустой:
     - Очищаем `output` шага: `step["output"] = "[success output trimmed]"`.
     - Пересчитываем `total_tokens`. Если уложились в `max_tokens` — останавливаемся.
5. **Фаза 2 (Прунинг старых шагов)**:
   - Если `total_tokens` все еще больше `max_tokens`:
     - Начинаем удалять шаги с начала списка (самые старые), пока `total_tokens <= max_tokens`.
     - *Важное правило*: Никогда не удаляем последний шаг истории (чтобы агент всегда видел результат предыдущей команды).

## Тестирование
Добавить тесты в `tools/tests/test_solo_loop_v10.py`, проверяющие обе фазы сжатия на моковых шагах истории с длинными логами.
