#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess  # nosec B404
import sys
from datetime import datetime


def parse_handoff(handoff_path):
    """Парсит HANDOFF.md для извлечения ключевых данных."""
    if not os.path.exists(handoff_path):
        print(f"❌ Файл хандоффа не найден: {handoff_path}")
        return None

    try:
        with open(handoff_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла хандоффа: {e}")
        return None

    # Извлекаем заголовок проекта (обычно первая строка вида # HANDOFF: Имя)
    project_match = re.search(r"^#\s+HANDOFF:\s*(.*)$", content, re.MULTILINE)
    project_name = project_match.group(1).strip() if project_match else "Системный проект"

    # Парсим Work Accomplished (Сделано)
    work_done = []
    # Ищем секцию сделанного (игнорируем регистр и номера)
    work_section = re.search(r"##\s*(?:\d+\.\s*)?(?:Work Accomplished|Выполненная работа|Что было сделано)(.*?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if work_section:
        # Извлекаем первые 3-4 ненулевых пункта (строки, начинающиеся с * или -)
        items = re.findall(r"^[*-]\s*(.*?)$", work_section.group(1), re.MULTILINE)
        work_done = [item.strip() for item in items if item.strip()][:4]

    # Парсим Next Steps (Следующие шаги)
    next_steps = []
    next_section = re.search(r"##\s*(?:\d+\.\s*)?(?:Next Steps|Current Work and Next Steps|Следующие шаги)(.*?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if next_section:
        items = re.findall(r"^[*-]|\d+\.\s*(.*?)$", next_section.group(1), re.MULTILINE)
        next_steps = [item.strip() for item in items if item.strip()][:3]
        # Если регулярка выше пропустила нумерованные списки, попробуем еще раз:
        if not next_steps:
            items = re.findall(r"^\d+\.\s*(.*?)$", next_section.group(1), re.MULTILINE)
            next_steps = [item.strip() for item in items if item.strip()][:3]

    return {
        "project": project_name,
        "work_done": work_done,
        "next_steps": next_steps,
        "abs_path": os.path.abspath(handoff_path)
    }

def format_log(data, conv_id):
    """Форматирует лог-запись в Markdown."""
    now_str = datetime.now().strftime("%H:%M")
    log_lines = [
        f"\n#### 🤖 Авто-лог ИИ-сессии: {data['project']} ({now_str})",
        f"* **Сессия ID:** `{conv_id[:8]}`"
    ]

    if data["work_done"]:
        log_lines.append("* **Что сделано:**")
        for item in data["work_done"]:
            log_lines.append(f"  * {item}")

    if data["next_steps"]:
        log_lines.append("* **Что делать дальше:**")
        for item in data["next_steps"]:
            log_lines.append(f"  * {item}")

    log_lines.append(f"* 👉 [Подробный файл передачи контекста (HANDOFF)](file://{data['abs_path']})")
    log_lines.append("-" * 40)

    return "\n".join(log_lines)

def append_to_daily(log_content):
    """Отправляет лог-запись в Obsidian Daily Note через официальный CLI."""
    # Проверяем доступность утилиты obsidian в PATH
    obsidian_path = shutil.which("obsidian")
    if not obsidian_path:
        print("❌ Ошибка: Утилита 'obsidian' CLI не найдена в системе (PATH).")
        return False

    try:
        # Запускаем команду daily:append
        subprocess.run(  # nosec B603
            [obsidian_path, "daily:append", f"content={log_content}"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Запись лога в Daily Note выполнена успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка вызова CLI 'obsidian': {e.stderr.strip() or e.stdout.strip()}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Автоматический логгер ИИ-сессий в Obsidian Daily Note.")
    parser.add_argument("handoff_path", help="Путь к файлу HANDOFF.md текущего проекта.")
    parser.add_argument("--conv-id", required=True, help="Conversation ID текущей сессии.")
    args = parser.parse_args()

    data = parse_handoff(args.handoff_path)
    if not data:
        sys.exit(1)

    log_content = format_log(data, args.conv_id)
    success = append_to_daily(log_content)

    if not success:
        sys.exit(1)

    # Автоматически переиндексируем файлы хандоффов
    try:
        print("⚙️ Запуск автоматической переиндексации базы знаний...")
        python_exe = sys.executable
        search_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "semantic_search.py")
        subprocess.run(  # nosec B603
            [python_exe, search_script, "--index"],
            check=True
        )
        print("✅ База знаний успешно переиндексирована!")
    except Exception as e:
        print(f"⚠️ Предупреждение: Не удалось обновить индекс: {e}")


if __name__ == "__main__":
    main()
