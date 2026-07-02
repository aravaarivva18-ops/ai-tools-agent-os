#!/usr/bin/env bash
# loop.sh — Ralph-style автономный цикл поверх openspec change(ей).
# Агент-агностик: claude, codex, opencode — единый bash-драйвер снаружи.
# (Альтернатива для чистого Claude Code — goal-run.sh на нативном /goal, см. README.)
#
# Использование:
#   ./scripts/loop.sh <change-name> [--max-iters N] [--max-minutes M] [--agent claude|codex|opencode]
#   ./scripts/loop.sh --all [--max-iters N] [--max-minutes M] [--agent ...] [--keep-going]
#       # весь проект: проходит по очереди все openspec/changes/* с tasks.md
#
# Что делает на каждый change:
#   1. Проверяет, что openspec/changes/<name>/tasks.md существует.
#   2. На каждой итерации подставляет {{CHANGE}} в PROMPT.md и скармливает агенту.
#   3. После каждого прохода прогоняет gates.sh (двойная защита — хуки агента тоже это делают).
#   4. Коммитит + тегает только если гейты зелёные.
#   5. Останавливается по лимиту итераций/времени или когда tasks.md полностью отмечен.
#
# Archive (слияние change в openspec/specs/) сознательно НЕ делается автоматически —
# это финальный ручной чекпойнт с ревью человека, как и задумано в OpenSpec.

set -uo pipefail

MAX_ITERS=20
MAX_MINUTES=60
AGENT="claude"
ALL=0
KEEP_GOING=0
TARGETS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) ALL=1; shift ;;
    --keep-going) KEEP_GOING=1; shift ;;
    --max-iters) MAX_ITERS="$2"; shift 2 ;;
    --max-minutes) MAX_MINUTES="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
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
  echo "Использование: ./scripts/loop.sh <change-name> [флаги]  ИЛИ  ./scripts/loop.sh --all [флаги]"
  echo "Флаги: --max-iters N (умолч. 20)  --max-minutes M (умолч. 60)  --agent claude|codex|opencode  --keep-going"
  exit 1
fi

mkdir -p logs
LOG="logs/loop.log"

# Кросс-модельное ревью застейдженного диффа ВТОРОЙ моделью (не той, что писала код).
# codex-плагин ревьюит работу claude и наоборот — это независимее самопроверки.
# Best-effort: если второй модели нет — пропускаем (в claude-прогоне остаётся ещё
# subagent `verifier` из PROMPT.md как внутрисессионный слой). Возврат 1 = FAIL.
review_diff() {
  local CHANGE="$1"
  local DIFF
  DIFF=$(git diff --cached)
  [[ -z "$DIFF" ]] && return 0

  local REVIEWER=""
  if [[ "$AGENT" != "codex" ]] && command -v codex >/dev/null 2>&1; then
    REVIEWER="codex"
  elif [[ "$AGENT" != "claude" ]] && command -v claude >/dev/null 2>&1; then
    REVIEWER="claude"
  fi
  if [[ -z "$REVIEWER" ]]; then
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE}: ревью пропущено (нет второй модели для кросс-проверки)" | tee -a "$LOG"
    return 0
  fi

  # Детерминированный анализ изменений через fallow — ревьюер ВСЕГДА его учитывает.
  local FALLOW
  FALLOW=$(./scripts/fallow-review.sh HEAD 2>&1)

  local RPROMPT
  RPROMPT="Ты независимый ревьюер, код не пишешь. Оцени diff против пункта tasks.md, design.md и инвариантов openspec/north-star.md change '${CHANGE}'.
FAIL, если: есть заглушки/TODO/placeholder вместо логики; diff не решает пункт tasks.md (или выходит за скоуп); удалены/ослаблены тесты ради прохода; нарушен инвариант north-star.md; правится openspec/specs/ напрямую.
ОБЯЗАТЕЛЬНО учти детерминированный вывод fallow ниже (dead code, дубли, сложность, границы архитектуры, гигиена зависимостей, PR-risk verdict): fallow verdict=fail — это сильный сигнал к FAIL; warn — упомяни в причинах. Вплети находки fallow в отчёт.
Ответь ПЕРВОЙ строкой строго 'REVIEW: PASS' или 'REVIEW: FAIL', затем причины (включая релевантные находки fallow).

--- design.md ---
$(cat "openspec/changes/${CHANGE}/design.md" 2>/dev/null)
--- north-star.md ---
$(cat "openspec/north-star.md" 2>/dev/null)
--- fallow (детерминированный анализ изменений) ---
${FALLOW}
--- git diff --cached ---
${DIFF}"

  local OUT
  case "$REVIEWER" in
    codex)  OUT=$(codex exec "$RPROMPT" 2>&1) ;;
    claude) OUT=$(printf '%s' "$RPROMPT" | claude -p --permission-mode plan 2>&1) ;;
  esac
  echo "$OUT" >> "$LOG"

  if printf '%s' "$OUT" | grep -q 'REVIEW: FAIL'; then
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE}: ревью (${REVIEWER}) = FAIL — не коммичу, чинит следующая итерация" | tee -a "$LOG"
    return 1
  fi
  echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE}: ревью (${REVIEWER}) = PASS" | tee -a "$LOG"
  return 0
}

run_change() {
  local CHANGE="$1"
  local TASKS_FILE="openspec/changes/${CHANGE}/tasks.md"
  if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Не найден $TASKS_FILE — сначала создай change: /opsx:propose ${CHANGE}"
    return 1
  fi

  local START_TS
  START_TS=$(date +%s)
  echo "[$(date +%Y-%m-%dT%H:%M:%S)] loop start change=${CHANGE} agent=${AGENT} max_iters=${MAX_ITERS} max_minutes=${MAX_MINUTES}" | tee -a "$LOG"

  python3 - "$CHANGE" <<'PY'
import sys, re, pathlib
change = sys.argv[1]
p = pathlib.Path("fix_plan.md")
text = p.read_text()
text = re.sub(r"## Активный change\n.*?\n\n", f"## Активный change\n{change}\n\n", text, flags=re.S)
p.write_text(text)
PY

  local iter=0
  while (( iter < MAX_ITERS )); do
    local now elapsed_min
    now=$(date +%s)
    elapsed_min=$(( (now - START_TS) / 60 ))
    if (( elapsed_min >= MAX_MINUTES )); then
      echo "[$(date +%Y-%m-%dT%H:%M:%S)] стоп (${CHANGE}): лимит времени (${MAX_MINUTES} мин)" | tee -a "$LOG"
      break
    fi

    if ! grep -q '^[[:space:]]*- \[ \]' "$TASKS_FILE"; then
      echo "[$(date +%Y-%m-%dT%H:%M:%S)] стоп (${CHANGE}): все пункты tasks.md отмечены — прогони /opsx:archive ${CHANGE} вручную" | tee -a "$LOG"
      return 0
    fi

    iter=$((iter + 1))
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] --- ${CHANGE}: итерация ${iter}/${MAX_ITERS} ---" | tee -a "$LOG"

    local ITER_PROMPT
    ITER_PROMPT=$(mktemp)
    sed "s/{{CHANGE}}/${CHANGE}/g" PROMPT.md > "$ITER_PROMPT"

    case "$AGENT" in
      claude)
        cat "$ITER_PROMPT" | claude --permission-mode acceptEdits --max-turns 40 2>&1 | tee -a "$LOG"
        ;;
      codex)
        codex exec "$(cat "$ITER_PROMPT")" 2>&1 | tee -a "$LOG"
        ;;
      opencode)
        opencode run "$(cat "$ITER_PROMPT")" 2>&1 | tee -a "$LOG"
        ;;
      *)
        echo "Неизвестный агент: ${AGENT} (ожидался claude|codex|opencode)"; return 1 ;;
    esac
    rm -f "$ITER_PROMPT"

    if ./scripts/gates.sh >> "$LOG" 2>&1; then
      if [[ -n "$(git status --porcelain)" ]]; then
        git add -A
        # Гейты зелёные + независимое ревью PASS → только тогда коммит.
        if review_diff "$CHANGE"; then
          git commit -m "loop(${CHANGE}): iteration ${iter} — gates green, review pass" >/dev/null
          git tag "loop-${CHANGE}-$(date +%Y%m%d%H%M%S)" >/dev/null
          echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE} итерация ${iter}: commit + tag" | tee -a "$LOG"
        else
          echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE} итерация ${iter}: ревью FAIL — коммит отложен, чинит следующая итерация" | tee -a "$LOG"
        fi
      else
        echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE} итерация ${iter}: нет изменений в git — возможно агент застрял" | tee -a "$LOG"
      fi
    else
      echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE} итерация ${iter}: ГЕЙТЫ КРАСНЫЕ — изменения НЕ закоммичены, стоп по этому change" | tee -a "$LOG"
      return 1
    fi
  done

  echo "[$(date +%Y-%m-%dT%H:%M:%S)] loop end change=${CHANGE} iterations=${iter}" | tee -a "$LOG"
  return 0
}

OVERALL_EXIT=0
for CHANGE in "${TARGETS[@]}"; do
  if ! run_change "$CHANGE"; then
    OVERALL_EXIT=1
    if [[ $KEEP_GOING -eq 1 ]]; then
      echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE} упал, но --keep-going — перехожу к следующему change" | tee -a "$LOG"
      continue
    else
      echo "[$(date +%Y-%m-%dT%H:%M:%S)] ${CHANGE} упал — останавливаю весь прогон (передай --keep-going, чтобы продолжать)" | tee -a "$LOG"
      break
    fi
  fi
done

exit $OVERALL_EXIT
