---
name: agent-orchestration
description: Guidelines for agent state checkpointing, SPARC workflow, and Prompt Caching optimization.
---

# Управление и Оркестрация Агентов (Swarm & State Design)

Этот навык описывает стандарты оркестрации мультиагентных систем, сохранения состояния диалога для предотвращения сбоев и оптимизации запросов для промпт-кэширования (Prompt Caching).

## 🗺️ 1. Методология разработки SPARC

При декомпозиции и реализации сложных задач ИИ-агенты следуют строгому процессу из 5 шагов:

1. **Specification (Спецификация):** Сбор требований, выявление бизнес-логики и фиксация DoD (Definition of Done) в `implementation_plan.md`.
2. **Pseudocode (Псевдокод):** Написание логики работы алгоритма в виде текстового описания шагов или абстрактного кода без реализации.
3. **Architecture (Архитектура):** Определение классов, структуры таблиц БД, API-контрактов и связей между модулями.
4. **Refinement (Отладка):** Поиск уязвимостей, проверка краевых случаев, оптимизация потребления памяти/токенов.
5. **Completion (Завершение):** Написание тестов, финальный запуск `make check`, исправление замечаний линтера и выпуск релиза.

---

## 💾 2. Паттерн сохранения состояния (Checkpointing)

Чтобы агент мог продолжить выполнение задачи после перезапуска сессии или сетевого сбоя, его текущий стейт сохраняется в файл JSON на каждом шаге.

### Реализация стейт-менеджера:
```python
import json
from pathlib import Path
from typing import Dict, Any

class AgentCheckpointManager:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.state: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Загружает сохраненный чекпоинт."""
        if self.filepath.exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.state = json.load(f)

    def checkpoint(self, task_name: str, step_data: Dict[str, Any]):
        """Сохраняет текущий шаг выполнения задачи."""
        self.state[task_name] = {
            "data": step_data,
            "timestamp": time.time(),
            "status": "completed"
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def get_step_status(self, task_name: str) -> bool:
        """Проверяет, был ли этот шаг успешно завершен ранее."""
        return self.state.get(task_name, {}).get("status") == "completed"
```

---

## ⚡ 3. Оптимизация промпт-кэширования (Prompt Caching)

Кэширование промптов (особенно в моделях Claude/Anthropic через разметку `cache_control`) снижает стоимость инференса на 90%. Для этого структура запроса должна оставаться строго статической:

### Золотое правило структуры запроса:
1. **Системные инструкции (Static System Prompt):** Всегда идут первыми. Должны быть неизменными на протяжении всей сессии. Помечаются флагом кэширования.
2. **Инструменты (Tools):** Список доступных функций API.
3. **История сообщений (Chat History):** Сообщения от пользователя и ассистента.
4. **Динамический контекст (Dynamic Context):** Свежескопированный код, файлы проекта или RAG-выборка. Помещается в конец запроса.

### Пример составления payload для API (Anthropic-style):
```python
def compile_cached_payload(system_prompt: str, context: str, user_query: str) -> dict:
    return {
        "system": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Кешируем статический системный промпт
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Текущий контекст проекта:\n{context}",
                        "cache_control": {"type": "ephemeral"}  # Кешируем файлы кодовой базы
                    },
                    {
                        "type": "text",
                        "text": user_query
                    }
                ]
            }
        ]
    }

---

## 🛠️ 4. Реестр команд (Command Registry Pattern)

Для динамической регистрации инструментов агента используется паттерн декораторов (из AutoGPT):

```python
from typing import Callable, Dict, Any

class AgentToolRegistry:
    def __init__(self):
        self.commands: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str):
        """Декоратор для регистрации команды агента."""
        def decorator(func: Callable):
            self.commands[name] = {
                "func": func,
                "description": description
            }
            return func
        return decorator

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self.commands:
            raise ValueError(f"Команда '{name}' не найдена в реестре.")
        return self.commands[name]["func"](**kwargs)
```

---

## 🔀 5. Топологическое выполнение графа (DAG Resolution)

Для построения сложных цепочек агентов (Workflow) используется граф зависимостей. Для вычисления порядка выполнения применяется топологическая сортировка:

```python
import graphlib

def resolve_workflow_order(dependencies: dict[str, list[str]]) -> list[str]:
    """
    Пример:
    dependencies = {
        "test": ["build"],
        "build": ["lint", "format"],
        "lint": [],
        "format": []
    }
    Возвращает плоский список в порядке выполнения.
    """
    ts = graphlib.TopologicalSorter()
    for task, deps in dependencies.items():
        ts.add(task, *deps)
    return list(ts.static_order())
```

```
