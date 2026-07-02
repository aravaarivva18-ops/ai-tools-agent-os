#!/usr/bin/env bash
# gate.sh — человек управляет жёсткими гейтами интерактивного режима.
# В интерактивном режиме PreToolUse-хук (require-gate-approval.sh) блокирует запись
# КОДА, пока человек не одобрит этап `propose` здесь. Одобрение требует реального
# терминала (TTY) — агент не может одобрить сам себя (у его Bash нет TTY).
#
# Использование:
#   ./scripts/gate.sh status          показать режим и одобренные гейты
#   ./scripts/gate.sh ok <этап>       одобрить этап (напр. propose) — спросит подтверждение
#   ./scripts/gate.sh reset           сбросить одобрения (перед новой фичей)
#   ./scripts/gate.sh on | off        включить/выключить интерактивный режим вручную

set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
mkdir -p .claude/hooks
APPROVED=".claude/hooks/.gates-approved"
MODE_MARK=".claude/hooks/.interactive-mode"

case "${1:-status}" in
  ok)
    G="${2:-}"; [[ -z "$G" ]] && { echo "Использование: ./scripts/gate.sh ok <этап>  (напр. propose)"; exit 1; }
    printf "Одобрить GATE '%s'? Это может сделать только человек. [y/N] " "$G"
    if ! read -r a </dev/tty 2>/dev/null; then
      echo; echo "Нет TTY — одобрение отклонено (агент не одобряет сам себя)."; exit 1
    fi
    [[ "$a" =~ ^[Yy]$ ]] || { echo "Отменено."; exit 1; }
    grep -qx "$G" "$APPROVED" 2>/dev/null || echo "$G" >> "$APPROVED"
    echo "✓ GATE '$G' одобрен человеком — запись кода разблокирована."
    ;;
  status)
    echo "Интерактивный режим: $([[ -f "$MODE_MARK" ]] && echo 'ON (жёсткие гейты активны)' || echo 'off')"
    echo "Одобренные гейты:"; [[ -s "$APPROVED" ]] && sed 's/^/  - /' "$APPROVED" || echo "  (нет)"
    ;;
  reset)
    rm -f "$APPROVED"; echo "Одобрения гейтов сброшены (для новой фичи)."
    ;;
  on)  : > "$MODE_MARK"; echo "Интерактивный режим ВКЛ — код нельзя писать до 'gate.sh ok propose'." ;;
  off) rm -f "$MODE_MARK"; echo "Интерактивный режим ВЫКЛ." ;;
  *) echo "Использование: ./scripts/gate.sh [status|ok <этап>|reset|on|off]"; exit 1 ;;
esac
