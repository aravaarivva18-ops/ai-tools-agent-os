#!/usr/bin/env bash
# PreToolUse hook (matcher Write|Edit): жёсткий гейт интерактивного режима.
# Пока человек не одобрил этап `propose` (./scripts/gate.sh ok propose), запись КОДА
# заблокирована — можно писать только спеки/доки/планы. Так агент физически не может
# начать реализацию до одобрения архитектуры человеком.
# Exit 2 = блокирует вызов инструмента и показывает stderr агенту.
#
# Активен ТОЛЬКО в интерактивном режиме (маркер ставит start.sh --interactive или
# ./scripts/gate.sh on). В обычном режиме — no-op, ничего не мешает.

set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

MODE_MARK=".claude/hooks/.interactive-mode"
[[ -f "$MODE_MARK" ]] || exit 0   # не интерактивный режим — не вмешиваемся

# Путь целевого файла из stdin JSON (Claude Code передаёт tool_input сюда).
FILE=$(python3 -c 'import sys,json
try:
    d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))
except Exception: print("")' 2>/dev/null)
[[ -n "$FILE" ]] || exit 0

# Файлы одобрений/режима правит ТОЛЬКО человек через gate.sh — агенту сюда нельзя.
case "$FILE" in
  *.gates-approved|*.interactive-mode)
    echo "GATE: файл одобрений редактирует только человек через ./scripts/gate.sh, не агент." >&2
    exit 2 ;;
esac

# propose одобрен? тогда код писать можно.
APPROVED=".claude/hooks/.gates-approved"
if [[ -f "$APPROVED" ]] && grep -qx "propose" "$APPROVED"; then exit 0; fi

# До одобрения propose разрешаем только спеки/доки/планы/конфиг, но не исходный код.
case "$FILE" in
  */openspec/*|openspec/*)   exit 0 ;;
  */fix_plan.md|fix_plan.md) exit 0 ;;
  *.md)                      exit 0 ;;
  */.claude/*|.claude/*)     exit 0 ;;
esac

echo "GATE (interactive): код нельзя писать до одобрения этапа propose." >&2
echo "Покажи человеку proposal.md + design.md на гейте и жди. Разблокирует человек:" >&2
echo "  ./scripts/gate.sh ok propose" >&2
exit 2
