# Спецификация DESIGN.md для ИИ-агентов

Используется для предоставления ИИ-агенту долговечного, структурированного понимания дизайн-системы проекта.

## 📐 Правило использования

1. **При создании/доработке веб-интерфейсов** всегда проверять наличие файла `DESIGN.md` в корневом каталоге проекта.
2. **Если файл присутствует**, прочитать его и использовать описанные в YAML-блоке токены (`colors`, `typography`, `rounded`, `spacing`, `components`) для стилизации элементов.
3. **Перед деплоем интерфейса** запускать линтинг контрастности и структуры:
   ```bash
   npx @google/design.md lint DESIGN.md
   ```
4. **Для интеграции с CSS-фреймворками** генерировать стили автоматически:
   * Для Tailwind v3: `npx @google/design.md export --format json-tailwind DESIGN.md`
   * Для Tailwind v4: `npx @google/design.md export --format css-tailwind DESIGN.md`

## 🎨 Шаблон базовой структуры DESIGN.md

```markdown
---
name: ProjectTheme
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Inter, sans-serif
    fontSize: 2.25rem
    fontWeight: 700
  body:
    fontFamily: Inter, sans-serif
    fontSize: 1rem
rounded:
  md: 8px
spacing:
  md: 16px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.md}"
    padding: 12px 24px
---

## Overview
Краткое описание стилистики бренда и ключевых UX/UI принципов.
```
