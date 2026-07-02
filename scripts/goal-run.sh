#!/usr/bin/env bash
# goal-run.sh — auto-блок через встроенный Claude Code /goal (только claude, без bash-цикла).
# Альтернатива scripts/loop.sh: проще, но привязана к Claude Code (для codex/opencode
# используй loop.sh — там мультиагентный вариант).
#
# ВАЖНО про /goal vs /loop (легко перепутать):
#   /goal  — держит агента в работе, пока не выполнится проверяемое условие. Именно
#            это нужно для "доделай пока не green". Реализован как session-scoped
#            Stop-хук с отдельным evaluator'ом (по умолчанию Haiku), который после
#            каждого хода читает диалог и решает done/not done.
#   /loop  — перезапускает промпт по таймеру (поллинг/мониторинг: "проверяй раз в 5
#            минут, не закончился ли деплой"). НЕ конвергирует к результату сам по
#            себе — для e2e-выполнения спеки это НЕ тот инструмент.
#
# Evaluator сам файлы не читает и команды не гоняет — он смотрит только на то, что
# Claude уже показал в диалоге. Поэтому условие ниже явно требует показать вывод
# gates.sh и содержимое tasks.md, а не просто "закончи задачу".
#
# Использование:
#   ./scripts/goal-run.sh <change-name> [--turns N]
#   ./scripts/goal-run.sh --all [--turns N]     # весь проект: все changes по очереди
#
# Примечание: наш .claude/settings.json уже вешает свой Stop-хук (stop-require-green.sh)
# и PostToolUse-хук (post-tool-use-gates.sh) — они продолжают работать параллельно с
# /goal (Claude Code поддерживает несколько хуков на одно событие). Если на первом
# прогоне увидишь странное поведение на стыке — это точка, которую стоит проверить
# первой.

set -uo pipefail

TURNS=40
ALL=0
TARGETS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) ALL=1; shift ;;
    --turns) TURNS="$2"; shift 2 ;;
    --*) echo "Неизвестный флаг: $1"; exit 1 ;;
    *) TARGETS+=("$1"); shift ;;
  esac
done

if [[ $ALL -eq 1 ]]; then
  for dir in openspec/changes/*/; do
    name=$(basename "$dir")
    [[ "$name" == "archive" || "$name" == "_example-change" ]] && continue
    [[ -f "${dir}tasks.md" ]] || continue
    TARGETS+=("$name")
  done
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "Использование: ./scripts/goal-run.sh <change-name> [--turns N]  ИЛИ  ./scripts/goal-run.sh --all [--turns N]"
  exit 1
fi

mkdir -p logs
LOG="logs/loop.log"
OVERALL_EXIT=0

for CHANGE in "${TARGETS[@]}"; do
  TASKS_FILE="openspec/changes/${CHANGE}/tasks.md"
  if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Пропуск ${CHANGE}: нет ${TASKS_FILE}" | tee -a "$LOG"
    continue
  fi

  CONDITION="все пункты [ ] в openspec/changes/${CHANGE}/tasks.md отмечены на [x] (покажи финальное содержимое файла), для каждой реализованной задачи subagent verifier был вызван и вернул PASS (покажи вердикт), последний запуск ./scripts/gates.sh в этом диалоге завершился с exit 0 (покажи вывод), реализация не нарушает инварианты openspec/north-star.md, и git status показывает чистое дерево (все закоммичено) — или останови работу и опиши причину блокера после ${TURNS} ходов"

  echo "[$(date +%Y-%m-%dT%H:%M:%S)] /goal старт change=${CHANGE} лимит=${TURNS} ходов" | tee -a "$LOG"

  if claude -p "/goal ${CONDITION}" --permission-mode acceptEdits 2>&1 | tee -a "$LOG"; then
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] /goal завершён для ${CHANGE}" | tee -a "$LOG"
  else
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] /goal упал для ${CHANGE} — смотри лог, следующий change не запускаю" | tee -a "$LOG"
    OVERALL_EXIT=1
    break
  fi
done

exit $OVERALL_EXIT
