#!/usr/bin/env python3
import os
import sys

PROPOSED_RULES_FILE = "/Users/rus/ai-tools/wiki/proposed_rules.md"
AGENTS_RULES_FILE = "/Users/rus/.agents/AGENTS.md"

def main():
    if not os.path.exists(PROPOSED_RULES_FILE):
        print(f"ℹ️ Черновик правил не найден или пуст: {PROPOSED_RULES_FILE}")
        return

    try:
        with open(PROPOSED_RULES_FILE, "r", encoding="utf-8") as f:
            proposed_content = f.read().strip()

        if not proposed_content:
            print("ℹ️ Черновик правил пуст.")
            return

        # Дописываем правила в конец AGENTS.md
        print(f"⚙️ Перенос правил в {AGENTS_RULES_FILE}...")
        with open(AGENTS_RULES_FILE, "a", encoding="utf-8") as f:
            f.write("\n\n" + proposed_content + "\n")

        # Очищаем черновик
        with open(PROPOSED_RULES_FILE, "w", encoding="utf-8") as f:
            f.write("")

        print("✅ Правила успешно применены! Черновик очищен.")

    except Exception as e:
        print(f"❌ Ошибка при переносе правил: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
