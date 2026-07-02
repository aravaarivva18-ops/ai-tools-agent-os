#!/usr/bin/env bash
# new-change.sh — ручной шорткат для создания openspec change без агента
# (когда проще самому накидать структуру, чем звать /opsx:propose).
#
# Использование: ./scripts/new-change.sh add-dark-mode

set -euo pipefail
NAME="${1:-}"
if [[ -z "$NAME" ]]; then
  echo "Использование: ./scripts/new-change.sh <change-name>"
  exit 1
fi

DIR="openspec/changes/${NAME}"
if [[ -d "$DIR" ]]; then
  echo "Уже существует: $DIR"
  exit 1
fi

mkdir -p "$DIR/specs"
cp openspec/changes/_example-change/proposal.md "$DIR/proposal.md"
cp openspec/changes/_example-change/design.md "$DIR/design.md"
cp openspec/changes/_example-change/tasks.md "$DIR/tasks.md"
cp openspec/changes/_example-change/specs/delta.md "$DIR/specs/delta.md"

echo "Создано: $DIR"
echo "Дальше: заполни proposal.md → design.md → tasks.md, потом ./scripts/loop.sh ${NAME} (или goal-run.sh ${NAME})"
