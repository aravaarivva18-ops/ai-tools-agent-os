#!/usr/bin/env python3
"""
Task Observer Engine.
Служебный скрипт для фонового анализа файлов HANDOFF.md и выявления повторяющихся
ошибок/требований с автоматической генерацией правил в proposed_rules.md.
"""

import re
from pathlib import Path
from typing import Any

# Пути по умолчанию
DEFAULT_WORKSPACE_ROOT = Path("/Users/rus/ai-tools")
HANDOFFS_DIR = DEFAULT_WORKSPACE_ROOT / "vault/handoffs"
PROPOSED_RULES_FILE = DEFAULT_WORKSPACE_ROOT / "wiki/proposed_rules.md"


def extract_tag_content(text: str, tag_name: str) -> str:
    """Извлекает содержимое псевдо-XML тега с помощью регулярок."""
    pattern = f"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def jaccard_similarity(s1: str, s2: str) -> float:
    """Вычисляет сходство Жаккара для двух текстовых строк."""
    words1 = set(re.findall(r"[a-zA-Zа-яА-Я0-9_]+", s1.lower()))
    words2 = set(re.findall(r"[a-zA-Zа-яА-Я0-9_]+", s2.lower()))
    if not words1 or not words2:
        return 0.0
    return len(words1.intersection(words2)) / len(words1.union(words2))


def analyze_handoffs(workspace_root: Path = DEFAULT_WORKSPACE_ROOT) -> list[dict[str, Any]]:
    """Анализирует последние handoffs и находит повторяющиеся требования/ошибки."""
    handoffs_path = workspace_root / "vault/handoffs"
    if not handoffs_path.exists():
        return []

    # Читаем последние 5 файлов HANDOFF.md
    files = sorted(
        handoffs_path.glob("*.md"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:5]

    snapshots = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            errors_fixes = extract_tag_content(content, "errors_and_fixes")
            user_msgs = extract_tag_content(content, "all_user_messages")
            if errors_fixes or user_msgs:
                snapshots.append({
                    "file": f.name,
                    "errors_fixes": errors_fixes,
                    "user_messages": user_msgs
                })
        except Exception:
            pass

    proposed_rules = []
    # Сравниваем пары снимков
    for i in range(len(snapshots)):
        for j in range(i + 1, len(snapshots)):
            s1 = snapshots[i]
            s2 = snapshots[j]

            # Проверяем пользовательские сообщения на повторы
            msgs1 = [line.strip() for line in s1["user_messages"].splitlines() if line.strip()]
            msgs2 = [line.strip() for line in s2["user_messages"].splitlines() if line.strip()]

            for m1 in msgs1:
                for m2 in msgs2:
                    # Исключаем короткие строки вроде "ок", "да", "/goal", "уверен?"
                    if len(m1) < 10 or len(m2) < 10:
                        continue

                    sim = jaccard_similarity(m1, m2)
                    if sim >= 0.35:
                        # Нашли дублирующееся требование!
                        # Проверяем, не добавляли ли мы его уже в этом прогоне
                        if not any(jaccard_similarity(m1, r["addition"]) > 0.6 for r in proposed_rules):
                            proposed_rules.append({
                                "addition": m1,
                                "why": f"Повторяющееся требование пользователя в сессиях {s1['file']} и {s2['file']}.",
                                "prompt_scaffold": f"Всегда следуй правилу: {m1}"
                            })

    return proposed_rules


def update_proposed_rules(rules: list[dict[str, Any]], workspace_root: Path = DEFAULT_WORKSPACE_ROOT) -> None:
    """Дописывает новые правила в wiki/proposed_rules.md."""
    if not rules:
        return

    rules_file = workspace_root / "wiki/proposed_rules.md"

    # Создаем родительские папки, если их нет
    rules_file.parent.mkdir(parents=True, exist_ok=True)

    # Читаем существующий контент
    existing_content = ""
    if rules_file.exists():
        existing_content = rules_file.read_text(encoding="utf-8")

    new_blocks = []
    for r in rules:
        # Проверяем, нет ли уже такого правила в файле
        if r["addition"] in existing_content:
            continue

        block = f"""
### 💡 Предложенное правило
*   **Правило**: {r['addition']}
*   **Почему**: {r['why']}
*   **Промпт**: `{r['prompt_scaffold']}`
"""
        new_blocks.append(block)

    if new_blocks:
        header = "# Proposed Rules (Автоматические кандидаты на правила)\n" if not existing_content else ""
        updated_content = existing_content + header + "\n".join(new_blocks)
        rules_file.write_text(updated_content, encoding="utf-8")
        print(f"✅ Добавлено {len(new_blocks)} новых правил в {rules_file.name}")


def run_observer(workspace_root: Path = DEFAULT_WORKSPACE_ROOT) -> None:
    """Основной метод запуска наблюдателя."""
    rules = analyze_handoffs(workspace_root)
    update_proposed_rules(rules, workspace_root)


if __name__ == "__main__":
    run_observer()
