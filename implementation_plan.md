# 🧬 Specification & Plan: Taskmaster Necessity Decision (v3.2)

Спецификация и план окончательного решения о необходимости интеграции eyaltoledano/claude-task-master под ограничения Solo Loop v10.

---

## 🏛️ 1. Context (Контекст)
Изучен репозиторий [eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master), представляющий собой Node.js систему управления задачами (Taskmaster) для AI-агентов с возможностью интеграции через CLI или MCP-сервер.

---

## 🎯 2. Scope (Границы проекта)
* **Анализ**:
  - Изучить применимость Taskmaster в стеке Antigravity.
* **Решение (Decision)**:
  - **Отклонить** интеграцию Taskmaster.
  - **Обоснование (YAGNI)**: Управление планами и отслеживание выполнения задач в Antigravity уже нативно реализовано через `PlanningWithFiles` в файле `implementation_plan.md`. Интеграция внешней Node.js системы управления задачами, поддержка её базы данных и вызовы сторонних LLM-моделей перегружают систему и не дают практической пользы. Наш легковесный подход полностью соответствует YAGNI.
* **Тестирование**:
  - Написать TDD автотесты [test_task_master.py](file:///Users/rus/ai-tools/tools/tests/test_task_master.py) для верификации YAGNI-решения.

---

## 📊 3. Prioritization (MoSCoW)
* **Must Have**:
  - Фиксация YAGNI-отклонения в `implementation_plan.md`.
  - TDD-тесты проверки зависимостей.
  - Прохождение общего тест-пакета `tools/tests/` (100% green).

---

## ✅ 4. Definition of Done (DoD)
- [x] Анализ необходимости Taskmaster выполнен.
- [x] TDD автотесты [test_task_master.py](file:///Users/rus/ai-tools/tools/tests/test_task_master.py) написаны.
- [x] Решение зафиксировано в `implementation_plan.md`.
- [ ] Все тесты `tools/tests/` зеленые (92/92 passed).
- [ ] Запущен `self_improve.py` и `collect_handoffs.py`.

---

## 📅 5. Пошаговый план (5-Line Plan)
1. **Анализ**: Изучить README и архитектуру `claude-task-master`.
2. **Обоснование**: Описать YAGNI-причины отклонения в `implementation_plan.md`.
3. **TDD тесты**: Написать [test_task_master.py](file:///Users/rus/ai-tools/tools/tests/test_task_master.py).
4. **Синхронизация**: Применить план в `implementation_plan.md`.
5. **Фиксация результатов**: Запустить тесты, `self_improve.py` и `collect_handoffs.py`.
