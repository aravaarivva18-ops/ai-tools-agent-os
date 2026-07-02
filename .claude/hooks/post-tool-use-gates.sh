#!/usr/bin/env bash
# PostToolUse hook: после Write/Edit прогоняет ТОЛЬКО дешёвые гейты (lint/types).
# Полный набор (tests/security/architecture) после каждой правки одного файла — слишком
# дорого и медленно для автономного прогона; он гоняется на Stop и в loop.sh/goal-run.sh.
# PostToolUse не может отменить уже сделанную правку — он лишь пишет свежий статус,
# который читает Stop-хук и PROMPT.md на следующей итерации.

set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

mkdir -p logs .claude/hooks
STATUS_FILE=".claude/hooks/.last-gate-status"
if [[ -x scripts/gates.sh ]]; then
  if ./scripts/gates.sh --quick >> logs/loop.log 2>&1; then
    echo "gates: PASS" > "$STATUS_FILE"   # truncate, не append — залипший старый статус нам не нужен
  else
    echo "gates: FAIL" > "$STATUS_FILE"
  fi
fi

exit 0
