# 🧬 Specification & Plan: Modern UI/Animation Stack JIT Skills (v3.2)

Спецификация и план интеграции современных библиотек анимаций и UI-стека (Framer Motion, GSAP, Tailwind CSS, R3F) в автогенератор JIT-навыков.

---

## 🏛️ 1. Context (Контекст)
Изучено видео «Вайбкодим БЕЗУМНЫЕ сайты с помощью Claude», где подробно рассмотрено создание передовых интерфейсов (эффекты масок при наведении, скролл-анимации, 3D элементы). Для повышения качества генерации UI-кода в Antigravity JIT-навыки расширены шаблонами для передового frontend-стека.

---

## 🎯 2. Scope (Границы проекта)
* **Анализ стека**:
  - **Framer Motion**: Для интерактивных Hover-масок и простых переходов.
  - **GSAP (GreenSock)**: Для сложных таймлайнов, привязанных к скроллу.
  - **React Three Fiber (R3F) / Three.js**: Для внедрения 3D моделей (например, космонавтов).
  - **Tailwind CSS**: Для быстрой и лаконичной стилизации.
* **Интеграция**:
  - Модифицировать метод `create_skill` в [agent_skills.py](file:///Users/rus/ai-tools/tools/agent_skills.py). При детекции ключевых слов UI, анимаций или фронтенда, автоматически генерировать специализированный шаблон JIT-навыка с предписанным стеком и правилами дизайна.
* **Тестирование**:
  - Написать TDD автотесты [test_ui_stack.py](file:///Users/rus/ai-tools/tools/tests/test_ui_stack.py) для верификации условной генерации шаблонов.

---

## 📊 3. Prioritization (MoSCoW)
* **Must Have**:
  - Детекция UI-тегов при создании навыка.
  - TDD автотесты.
  - Прохождение общего тест-пакета `tools/tests/` (100% green).

---

## ✅ 4. Definition of Done (DoD)
- [x] Анализ видео и стека выполнен.
- [x] Метод `create_skill` в `agent_skills.py` обновлен.
- [x] TDD автотесты [test_ui_stack.py](file:///Users/rus/ai-tools/tools/tests/test_ui_stack.py) написаны.
- [x] Все тесты `tools/tests/` зеленые (94/94 passed).
- [ ] Запущен `self_improve.py` и `collect_handoffs.py`.
- [ ] Изменения закоммичены в git с соблюдением Conventional Commits.

---

## 📅 5. Пошаговый план (5-Line Plan)
1. **OSINT-анализ**: Изучить метаданные видео о «безумных» сайтах и вычленить стек.
2. **Адаптация кода**: Реализовать генерацию UI-шаблонов в `tools/agent_skills.py`.
3. **TDD тесты**: Написать [test_ui_stack.py](file:///Users/rus/ai-tools/tools/tests/test_ui_stack.py).
4. **Синхронизация**: Применить план в `implementation_plan.md`.
5. **Фиксация результатов**: Запустить тесты, `self_improve.py`, `collect_handoffs.py` и сделать коммит.
