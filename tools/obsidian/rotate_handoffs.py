#!/usr/bin/env python3
"""
Скрипт ротации файлов HANDOFF.md для оптимизации RAG-индекса в Obsidian.
Переносит сессионные логи старше 14 дней в папку archive/, ускоряя векторный поиск.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

try:
    from tools.config import get_workspace_root, load_config
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.config import get_workspace_root, load_config

def rotate_logs(days_threshold=14):
    config = load_config()
    workspace_root = get_workspace_root()
    handoffs_dir = Path(workspace_root) / config.get("vault", {}).get("handoffs_dir", "vault/handoffs")
    archive_dir = handoffs_dir / "archive"

    if not handoffs_dir.exists():
        print(f"❌ Директория хандоффов не найдена: {handoffs_dir}")
        return

    archive_dir.mkdir(exist_ok=True)

    now = datetime.now()
    threshold_date = now - timedelta(days=days_threshold)
    print(f"⚙️ Запуск ротации хандоффов старше {days_threshold} дней (порог: {threshold_date.strftime('%Y-%m-%d')})...")

    # Регулярные выражения для поиска дат в именах файлов
    # Примеры: handoff_01607a73-c010-4cef-bc48-8e0a151c60e5_2026-06-27_232004.md
    # HANDOFF_2026-06-21_session_1a2c6af4.md
    date_patterns = [
        re.compile(r"_(\d{4}-\d{2}-\d{2})_"),
        re.compile(r"HANDOFF_(\d{4}-\d{2}-\d{2})_")
    ]

    moved_count = 0
    for item in handoffs_dir.iterdir():
        if not item.is_file() or not item.name.endswith(".md"):
            continue

        # Защищаем глобальные/универсальные промпты и важные доки
        if "universal_prompt" in item.name or item.name == "handoff_notes.md":
            continue

        file_date = None
        # Пытаемся извлечь дату из имени файла
        for pattern in date_patterns:
            match = pattern.search(item.name)
            if match:
                try:
                    file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                    break
                except ValueError:
                    pass

        # Если дату не извлекли из имени, берем дату изменения файла
        if file_date is None:
            file_date = datetime.fromtimestamp(item.stat().st_mtime)

        if file_date < threshold_date:
            try:
                with open(item, encoding="utf-8") as f:
                    content = f.read()

                def extract_tag(text, tag):
                    match = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL | re.IGNORECASE)
                    return match.group(1).strip() if match else ""

                intent = extract_tag(content, "primary_request_and_intent")
                current_work = extract_tag(content, "current_work")

                if not intent:
                    intent_match = re.search(r"##\s*(?:Что было сделано|Work Accomplished)(.*?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE)
                    intent = intent_match.group(1).strip() if intent_match else "Сделано без описания"

                date_str = file_date.strftime('%Y-%m-%d')
                compact_entry = (
                    f"### Сессия {date_str} (Файл: {item.name})\n"
                    f"* **Задача:** {intent[:300].replace('\n', ' ').strip()}...\n"
                    f"* **Статус:** {current_work or 'Завершена'}\n\n"
                )

                compacted_file = archive_dir / "compacted_history.md"
                with open(compacted_file, "a", encoding="utf-8") as f:
                    f.write(compact_entry)

                item.unlink()
                print(f"  📦 Сжат и архивирован: {item.name} (Дата: {date_str})")
                moved_count += 1
            except Exception as e:
                print(f"  ❌ Ошибка сжатия {item.name}: {e}")

    print(f"✅ Архивирование завершено. Перенесено файлов: {moved_count}")

    if moved_count > 0:
        # Перезапускаем индексацию
        print("⚙️ Перестраиваем RAG-индекс...")
        try:
            import subprocess
            # Вызываем semantic_search.py с флагом --index
            search_script = Path(__file__).parent / "semantic_search.py"
            subprocess.run([sys.executable, str(search_script), "--index"], check=True)
            print("✅ Индекс успешно перестроен!")
        except Exception as e:
            print(f"⚠️ Ошибка вызова индексатора: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ротация старых сессионных логов.")
    parser.add_argument("--days", "-d", type=int, default=7, help="Порог ротации в днях (по умолчанию 7).")
    args = parser.parse_args()
    rotate_logs(days_threshold=args.days)
