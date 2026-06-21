#!/usr/bin/env python3
"""Автоматическая нормализация структуры GEMINI_ANTIGRAVITY.md (v10)."""

import re
import argparse
import difflib
from pathlib import Path
from datetime import datetime

CONSTITUTION = Path("/Users/rus/GEMINI_ANTIGRAVITY.md")
CORE_RULES = """## 🏛️ Ядро (Core Imperatives) — обязательно к исполнению

- **Solo Loop v10**: Только основной агент. Субагенты (`define_subagent`, `invoke_subagent`) запрещены.
- **Stealth Stop**: При 3-й идентичной ошибке — немедленная остановка через `test_healer.py`.
- **YAGNI**: Максимум 2–3 уровня абстракции. `ponytail-audit` перед любым релизом.
- **TDD**: Minimum 1 позитивный + 1 негативный тест перед кодом.
- **Zero-Fluff + file://**: Только русский технический язык. Все ссылки — абсолютные `file://`.
- **WAL + Retry**: При записи в `dashboard.db` — `PRAGMA journal_mode=WAL` + 5 попыток с jitter.
- **Human-in-the-Loop**: Критические операции (удаление данных, деплой, запись во внешние API) требуют подтверждения.
- **Context Economics**: Чтение файлов — диапазонами ≤100 строк. Глобальный поиск запрещён.

Полные протоколы — в соответствующих разделах ниже.
"""

def normalize_headings(text: str) -> str:
    """Перенумеровывает заголовки ## ... N. Title последовательно."""
    lines = text.splitlines(keepends=True)
    result = []
    counter = 1
    pattern = re.compile(r'^(##\s+[^0-9\r\n]*?)\s*(\d+)\.\s+(.*)$')

    for line in lines:
        m = pattern.match(line.rstrip('\r\n'))
        if m:
            prefix = m.group(1).rstrip()
            title = m.group(3)
            # Сохраняем исходное окончание строки
            ending = line[len(line.rstrip('\r\n')):]
            result.append(f"{prefix} {counter}. {title}{ending}")
            counter += 1
        else:
            result.append(line)
    return "".join(result)

def ensure_core_block(text: str) -> str:
    """Вставляет блок Core Rules после intro, если его нет."""
    if "## 🏛️ Ядро (Core Imperatives)" in text or "## 🏛️ Core Rules Summary" in text:
        return text
    lines = text.splitlines(keepends=True)
    insert_idx = 3  # после короткого intro
    for i, line in enumerate(lines[:10]):
        if line.strip().startswith("#") and "GEMINI_ANTIGRAVITY" in line:
            insert_idx = i + 2
            break
    lines.insert(insert_idx, CORE_RULES + "\n---\n\n")
    return "".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Применить изменения")
    parser.add_argument("--check", action="store_true", help="Только проверить")
    args = parser.parse_args()

    if not CONSTITUTION.exists():
        print(f"Error: Constitution file not found at {CONSTITUTION}")
        return

    original = CONSTITUTION.read_text(encoding="utf-8")
    normalized = normalize_headings(original)
    normalized = ensure_core_block(normalized)

    if normalized == original:
        print("✅ Структура уже нормализована.")
        return

    diff = "\n".join(difflib.unified_diff(
        original.splitlines(),
        normalized.splitlines(),
        fromfile="before",
        tofile="after",
        lineterm=""
    ))

    if args.check:
        print("⚠️  Требуется нормализация. Diff:\n" + diff)
        return

    if args.apply:
        backup = CONSTITUTION.with_suffix(".md.bak." + datetime.now().strftime("%Y%m%d_%H%M%S"))
        backup.write_text(original, encoding="utf-8")
        CONSTITUTION.write_text(normalized, encoding="utf-8")
        print(f"✅ Нормализовано. Backup: {backup}")
        print("Diff:\n" + diff)
    else:
        print("Используйте --apply для записи изменений.")

if __name__ == "__main__":
    main()
