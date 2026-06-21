# 🧬 Specification & Plan: Architecture Decisions & UI Stack Integration (v3.2)

Сводный план архитектурных решений, интеграции современных библиотек анимации (UI Stack) и оценки сторонних AI-инструментов.

---

## 🏛️ 1. Context (Контекст)
В рамках эволюции Antigravity Solo Loop v10 проведено исследование и аудит сторонних решений на соответствие принципам YAGNI, TDD и минимизации абстракций.

---

## 🎯 2. Scope (Границы проекта)

### Решение 1. Интеграция Context7 (Принято)
* **Статус**: Интегрировано.
* **Описание**: Установлен и настроен инструмент [context7.com](https://context7.com/) с помощью `npx ctx7 setup --antigravity --yes`. Он предоставляет актуальную документацию по библиотекам через MCP-сервер (инструменты `resolve-library-id`, `query-docs`).

### Решение 2. Claude Code Router (Отклонено / Rejected)
* **Статус**: Отклонен (Rejected).
* **Обоснование (YAGNI)**: Наш локальный Python-агент `agy` работает напрямую через SDK и не требует развертывания Node.js HTTP-прокси для перенаправления запросов.

### Решение 3. Spec Kit (Отклонено / Rejected)
* **Статус**: Отклонен (Rejected).
* **Обоснование (YAGNI)**: Внедрение CLI `specify-cli` дублирует существующий легковесный функционал планирования `PlanningWithFiles` на базе Markdown-плана.

### Решение 4. Claude Taskmaster (Отклонено / Rejected)
* **Статус**: Отклонен (Rejected).
* **Обоснование (YAGNI)**: Управление планами задач и шагами полностью закрывается простым инструментом `PlanningWithFiles` в Python, база данных задач и зависимости излишни.

### Решение 5. Интеграция UI Stack (Принято)
* **Статус**: Интегрировано.
* **Описание**: Улучшен генератор навыков [agent_skills.py](file:///Users/rus/ai-tools/tools/agent_skills.py). При создании UI-навыков генерируется папка `components/` и `styles/` вместо `scripts/`, а шаблон `SKILL.md` дополняется рекомендациями по стеку: **Framer Motion, GSAP, Tailwind CSS, Three.js**.

---

## ✅ 4. Definition of Done (DoD)
- [x] Все YAGNI-решения зафиксированы и обоснованы.
- [x] Оптимизирован pre-commit хук для staged-файлов.
- [x] Написаны TDD автотесты для всех принятых решений.
- [ ] Все тесты `tools/tests/` зеленые (94/94 passed).
- [ ] Запущен `self_improve.py` и `collect_handoffs.py`.
