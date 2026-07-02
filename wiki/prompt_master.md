# Методология Prompt Master

Система оптимизации промптов под различные ИИ-инструменты, минимизирующая расход токенов и количество итераций (re-prompts).

## 🚀 Основные принципы

1. **Зависимость от архитектуры модели:**
   * **Reasoning-native (o3, o4-mini, DeepSeek-R1, Qwen3-thinking):** Короткие, чистые инструкции. **Запрещено** добавлять "think step by step" или разметку CoT (это ухудшает качество вывода и тратит внутренний бюджет размышлений).
   * **Claude (Claude API, Claude Code, Claude 4.x):** Требует максимальной буквальности и точности. Эффективно использование XML-тегов (`<task>`, `<constraints>`, `<context>`). Opus 4.x перестраховывается/переписывает лишнее, поэтому обязательно указывать: *"Only make changes directly requested. Do not add extra files, abstractions, or features."*
   * **Gemini:** Отлично работает с большими контекстами, но склонна к галлюцинациям в цитатах. Обязательны правила заземления: *"Cite only sources you are certain of. If uncertain, say so."*
2. **Параметры интента (9 измерений):** Task, Target tool, Output format, Constraints, Input, Context, Audience, Success criteria, Examples.
3. **Memory Block:** Предотвращает забывание контекста в длинных сессиях. Содержит зафиксированный стек, conventions и неудачные попытки в первых 30% промпта (чтобы не подвергаться attention decay).

## 📐 Ключевые шаблоны промптов

* **RTF (Role, Task, Format):** Простые задачи.
* **CO-STAR (Context, Objective, Style, Tone, Audience, Response):** Бизнес-документы, копирайтинг.
* **RISEN (Role, Instructions, Steps, End Goal, Narrowing):** Сложные проекты и ТЗ.
* **Visual Descriptor:** Midjourney/Stable Diffusion (описание через запятую, параметры, негативный промпт).

## 🚫 35 паттернов-убийц токенов (Credit-Killing Patterns)

* В промптах для агентов (Claude Code, Antigravity) **обязательно** указывать:
  1. **Starting state:** Исходное состояние файлов.
  2. **Target state:** Ожидаемый результат.
  3. **Stop condition & Checkpoints:** Условия остановки и отметки выполнения.
  4. **Filesystem locks:** Четкие границы доступных для редактирования папок.
  5. **Human review triggers:** "Stop and ask before deleting files, adding dependencies, changing DB schema."
