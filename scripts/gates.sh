#!/usr/bin/env bash
# gates.sh — детерминированный слой верификации (единственный источник истины "готово ли").
#
# Порядок: дешёвые проверки первыми (lint/types), дорогие последними (tests/security),
# чтобы падать быстро. Автоопределение стека — правь под свой проект руками, это
# generic-заготовка, а не магия.
#
# Режимы:
#   ./scripts/gates.sh           — полный прогон (lint+types+security+tests+architecture)
#   ./scripts/gates.sh --quick   — только дешёвое (lint+types), для PostToolUse-хука
#
# Возвращает 0, если ВСЁ прошло. Любой fail → exit 1, и loop.sh/goal-run.sh не коммитят.
# FAIL-CLOSED: если не отработала НИ ОДНА проверка (стек не распознан / команды не
# прописаны) — это тоже exit 1, а не молчаливый "PASS". Ненастроенный проект не зелёный.

set -uo pipefail
FAILED=0
RAN=0
CORE=0   # только «настоящая» верификация: lint/typecheck/tests. Security/architecture НЕ в счёт.
QUICK=0
[[ "${1:-}" == "--quick" ]] && QUICK=1

# step — supplementary-гейт (security/architecture): считается в RAN, но не в CORE.
step() {
  local name="$1"; shift
  RAN=$((RAN + 1))
  echo "── gate: ${name} ──"
  if "$@"; then
    echo "✓ ${name}"
  else
    echo "✗ ${name}"
    FAILED=1
  fi
}

# core_step — настоящая верификация: считается и в RAN, и в CORE (для fail-closed).
core_step() {
  CORE=$((CORE + 1))
  step "$@"
}

# ---------- Gate 1: Style & Correctness (lint + types) ----------
if [[ -f package.json ]]; then
  if grep -q '"lint"' package.json; then core_step "lint" npm run -s lint; fi
  if grep -q '"typecheck"' package.json; then core_step "typecheck" npm run -s typecheck; fi
elif [[ -f pyproject.toml || -f setup.py ]]; then
  # Линтим только измененные питоновские файлы
  CHANGED_PY_FILES=$(git diff --name-only --cached --diff-filter=d | grep '\.py$' || git diff --name-only --diff-filter=d | grep '\.py$' || true)
  if [[ -n "$CHANGED_PY_FILES" ]]; then
    command -v ruff >/dev/null 2>&1 && core_step "ruff" ruff check $CHANGED_PY_FILES
  else
    echo "── gate: ruff ──"
    echo "✓ ruff (no modified python files to lint)"
  fi
  command -v mypy >/dev/null 2>&1 && core_step "mypy" mypy tools/
fi

# --quick останавливается здесь: только Gate 1 (дешёвое), для PostToolUse-хука.
# Здесь fail-closed НЕ применяем: quick — это быстрый сигнал между правками, а не
# финальный вердикт (нет lint/types — просто нечего показать, полный прогон рассудит).
if [[ $QUICK -eq 1 ]]; then
  if [[ $FAILED -eq 1 ]]; then echo ""; echo "GATES(quick): FAIL"; exit 1; fi
  echo ""; echo "GATES(quick): PASS (${CORE} core-проверок)"; exit 0
fi

# ---------- Gate 2: Security scan (best-effort, не блокирует если инструмента нет) ----------
if command -v gitleaks >/dev/null 2>&1; then
  step "gitleaks (secrets)" gitleaks detect --no-banner -v
fi
# npm audit требует lockfile — без него падает с ENOLOCK (это ошибка инструмента,
# не уязвимость), что зря краснит гейты и клинит цикл. Запускаем только при lockfile.
if [[ -f package.json ]] && command -v npm >/dev/null 2>&1 \
   && { [[ -f package-lock.json ]] || [[ -f npm-shrinkwrap.json ]]; }; then
  step "npm audit (high+)" npm audit --audit-level=high
fi

# ---------- Gate 3: Tests ----------
if [[ -f package.json ]]; then
  if grep -q '"test"' package.json; then core_step "tests" npm test --silent; fi
elif [[ -f pyproject.toml || -f setup.py ]]; then
  if [[ -f .venv/bin/pytest ]]; then
    core_step "pytest" .venv/bin/pytest -q --disable-socket tools/tests/
  elif command -v pytest >/dev/null 2>&1; then
    core_step "pytest" pytest -q --disable-socket tools/tests/
  fi
fi

# ---------- Gate 4: Architecture / compliance (инварианты north-star.md) ----------
# scripts/architecture-check.sh проверяет машинную часть инвариантов из north-star.md.
if [[ -x scripts/architecture-check.sh ]]; then
  step "architecture (north-star инварианты)" scripts/architecture-check.sh
fi

if [[ $FAILED -eq 1 ]]; then
  echo ""
  echo "GATES: FAIL — что-то красное выше. Не коммитим."
  exit 1
fi

# FAIL-CLOSED, но ОТДЕЛЬНЫМ кодом (exit 3): ноль НАСТОЯЩИХ проверок (lint/typecheck/tests) —
# это НЕ «красный код», а «проверять пока нечего» (фаза планирования, проект ещё не
# настроен, нет package.json). Отличается от exit 1 (реальный провал), чтобы Stop-хук мог
# НЕ блокировать планирование, а loop.sh — всё равно не коммитил непроверенный код.
if [[ $CORE -eq 0 ]]; then
  echo ""
  echo "GATES: NO-CHECKS (exit 3) — не отработала ни одна настоящая проверка"
  echo "(lint/typecheck/tests). Это нормально в фазе планирования; для авто-цикла"
  echo "пропиши команды в gates.sh (lint/typecheck/test в package.json или"
  echo "ruff/mypy/pytest для Python) — иначе код не считается верифицированным."
  exit 3
fi

echo ""
echo "GATES: PASS (${CORE} core + $((RAN - CORE)) supplementary)"
exit 0
