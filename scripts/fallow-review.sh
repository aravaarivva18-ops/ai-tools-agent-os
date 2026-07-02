#!/usr/bin/env bash
# fallow-review.sh — прогоняет fallow по изменённому коду и печатает результат для РЕВЬЮЕРА.
#
# fallow (github.com/fallow-rs/fallow) — детерминированный анализатор TS/JS: dead code,
# дубли, сложность, нарушения границ архитектуры, гигиена зависимостей и PR-risk verdict
# (pass/warn/fail) по изменённому коду. НЕ ИИ — воспроизводимо.
#
# Ревьюер (subagent verifier и кросс-модельное ревью в loop.sh) ВСЕГДА запускает это и
# учитывает вывод в вердикте. Best-effort: нет fallow / не TS-JS проект → печатает пометку,
# а НЕ падает (exit 0 всегда) — «не запустился» видно в отчёте, а не молча пропущено.
#
# Использование: ./scripts/fallow-review.sh [base-ref]   (по умолчанию HEAD)

set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BASE="${1:-HEAD}"

# Как запускать fallow: cargo-бинарь, затем локальный npm-devDep через npx (--no-install,
# чтобы npx не тянул случайный пакет из сети — supply-chain-гигиена).
if command -v fallow >/dev/null 2>&1; then
  RUN=(fallow)
elif [[ -f package.json ]] && npx --no-install fallow --version >/dev/null 2>&1; then
  RUN=(npx --no-install fallow)
else
  echo "FALLOW: не установлен или проект не TS/JS — анализ пропущен."
  echo "  Поставить: npm i -D fallow   или   cargo install fallow-cli"
  exit 0
fi

echo "=== FALLOW audit (изменения с ${BASE}) ==="
# fallow audit возвращает ненулевой код при verdict warn/fail — это НЕ ошибка запуска,
# а сигнал ревьюеру; поэтому вывод захватываем в любом случае.
"${RUN[@]}" audit --changed-since "$BASE" --format json --quiet 2>&1 || true
echo "=== /FALLOW ==="
exit 0
