#!/usr/bin/env bash
# architecture-check.sh — машинная проверка инвариантов из openspec/north-star.md.
# Это Gate 4 в gates.sh (тот вызывает этот скрипт, если он исполняемый).
#
# Смысл: инварианты, которые МОЖНО проверить кодом, должны ловиться гейтом, а не
# держаться на дисциплине агента. Прозаические инварианты остаются в north-star.md
# для чтения агентом; сюда выноси их проверяемую часть (fitness-функции).
#
# Заготовка со «всё-разрешено по умолчанию» — впиши свои правила ниже.
# Возвращает 0, если все проверки прошли; 1 — если хоть одна нарушена.

set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

FAILED=0
fail() { echo "  ✗ INV нарушен: $1"; FAILED=1; }

# Проверяем только то, что изменено в этом проходе (дёшево и по делу).
# Пусто на первом коммите — тогда падать не на чем, это нормально.
CHANGED=$(git diff --name-only HEAD 2>/dev/null; git diff --name-only --cached 2>/dev/null)
CHANGED=$(printf '%s\n' "$CHANGED" | sort -u | grep -v '^$' || true)

# ---------- Универсальный инвариант: openspec/specs/ только через archive ----------
# specs/ — source of truth, правится процессом archive, а не руками в change-проходе.
if printf '%s\n' "$CHANGED" | grep -q '^openspec/specs/'; then
  fail "прямая правка openspec/specs/ (source of truth правится только через archive)"
fi

# ---------- Пример INV-3: секреты не утекают в код ----------
# Раскомментируй/подправь под свой north-star. Ищем подозрительные литералы в коде.
# if printf '%s\n' "$CHANGED" | grep -E '\.(js|ts|py|go|rb)$' | while read -r f; do
#     [[ -f "$f" ]] && grep -HnE '(api[_-]?key|secret|password)\s*=\s*["'\''][A-Za-z0-9]{16,}' "$f"
#   done | grep -q .; then
#   fail "похоже на захардкоженный секрет (INV-3)"
# fi

# ---------- Пример INV-1: слоевые границы (замени billing на свой модуль) ----------
# if printf '%s\n' "$CHANGED" | grep -vE '^billing/' | while read -r f; do
#     [[ -f "$f" ]] && grep -Hn 'stripe\.\|paymentApi' "$f"
#   done | grep -q .; then
#   fail "обращение к платёжному API вне billing/ (INV-1)"
# fi

if [[ $FAILED -eq 1 ]]; then
  echo "ARCHITECTURE: FAIL — нарушены инварианты north-star.md"
  exit 1
fi
exit 0
