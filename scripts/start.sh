#!/usr/bin/env bash
# start.sh — однокомандный бутстрап проекта: ставит OpenSpec, инициализирует его
# и выдаёт готовый промпт для вставки в агента (кладёт в буфер обмена на macOS).
#
# Использование:
#   ./scripts/start.sh                        greenfield, схлопнутый бутстрап (по умолчанию)
#   ./scripts/start.sh --interactive          greenfield, пошагово с гейтами (скил interactive-flow)
#   ./scripts/start.sh --brownfield           существующий код: фича/рефактор/эпик (скил brownfield)
#   ./scripts/start.sh --brownfield --interactive   brownfield + пошаговые гейты
#
# ВНИМАНИЕ: пакет именно @fission-ai/openspec. Голый `openspec` в npm — чужая
# заглушка v0.0.0 без бинаря (name collision), из-за неё бывает `command not found`.

set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INTERACTIVE=0
BROWNFIELD=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --interactive) INTERACTIVE=1; shift ;;
    --brownfield)  BROWNFIELD=1; shift ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Неизвестный флаг: $1 (см. --help)"; exit 1 ;;
  esac
done

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\n\033[33m%s\033[0m\n' "$*"; }
die()  { printf '\n\033[31m%s\033[0m\n' "$*" >&2; exit 1; }

# Интерактивный режим = жёсткие гейты: ставим маркер и сбрасываем прошлые одобрения,
# чтобы новый старт начинался с чистого листа (PreToolUse-хук блокирует код до propose).
mkdir -p .claude/hooks
if [[ $INTERACTIVE -eq 1 ]]; then
  : > .claude/hooks/.interactive-mode
  rm -f .claude/hooks/.gates-approved
else
  rm -f .claude/hooks/.interactive-mode   # обычный старт — автономный, жёсткие гейты выключены
fi

# Скрипты цикла (loop.sh/goal-run.sh) опираются на git commit/tag/status. Нет репо —
# инициализируем, чтобы это НЕ стало причиной стопа во время автономного прогона.
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  say "Нет git-репозитория — инициализирую (цикл опирается на git)…"
  if git init -q && git add -A && git commit -q -m "init: loop-starter bootstrap" 2>/dev/null; then
    say "✓ git init + первый коммит"
  else
    warn "git init сделан, но коммит не прошёл — настрой git user.name/email и сделай первый коммит вручную."
  fi
fi

# ---------- Шаг 1: PRD / бриф ----------
PRD="openspec/PRD.md"
[[ -f "$PRD" ]] || die "Нет $PRD — ты в корне проекта с распакованным шаблоном?"

# «Настоящие» строки: не комментарии <!-- -->, не цитаты >, не заголовки #, не пустые,
# не --- и не плейсхолдеры «- ...». Ноль таких строк = PRD не заполнен.
REAL=$(awk '
  /^##[[:space:]]+Что дальше/ {stop=1} stop{next}
  /<!--/{inc=1} inc{ if(/-->/){inc=0}; next }
  /^[[:space:]]*#/     {next}
  /^[[:space:]]*>/     {next}
  /^[[:space:]]*---[[:space:]]*$/ {next}
  /^[[:space:]]*$/     {next}
  /^[[:space:]]*-[[:space:]]*\.\.\.[[:space:]]*$/ {next}
  {c++} END{print c+0}
' "$PRD")

if [[ "$REAL" -eq 0 ]]; then
  if [[ $BROWNFIELD -eq 1 ]]; then
    # В brownfield PRD — это бриф текущей работы; контекст всё равно берётся из кода.
    warn "ℹ  $PRD пустой. В brownfield это ок: заполни его как бриф текущей работы"
    warn "   (фича/рефактор/эпик) — либо опиши задачу прямо агенту в диалоге."
  else
    warn "⚠  $PRD выглядит незаполненным (одни шаблонные плейсхолдеры)."
    warn "   PRD — точка входа №1: без него бутстрап не из чего выводить north-star/project."
    printf "   Продолжить всё равно? [y/N] "
    read -r ans </dev/tty 2>/dev/null || ans="n"
    [[ "$ans" =~ ^[Yy]$ ]] || die "Останавливаюсь. Заполни $PRD и запусти ./scripts/start.sh снова."
  fi
fi

# ---------- Шаг 2: OpenSpec установлен? ----------
if ! command -v openspec >/dev/null 2>&1; then
  say "OpenSpec не найден — ставлю (npm install -g @fission-ai/openspec)…"
  command -v npm >/dev/null 2>&1 || die "Нужен npm (Node.js). Поставь Node и повтори."
  npm install -g @fission-ai/openspec || die "Не удалось поставить @fission-ai/openspec. Поставь вручную и повтори."
  # Свежепоставленный глобальный бинарь часто не в PATH текущей сессии — добавим его каталог.
  NPM_BIN="$(npm prefix -g 2>/dev/null)/bin"
  [[ -d "$NPM_BIN" ]] && export PATH="$NPM_BIN:$PATH"
else
  say "OpenSpec уже установлен: $(openspec --version 2>/dev/null || echo ok)"
fi

# Жёсткая проверка ПЕРЕД init: если бинаря всё ещё нет — не притворяемся, что всё ок.
if ! command -v openspec >/dev/null 2>&1; then
  warn "openspec поставлен, но не виден в PATH ($(npm prefix -g 2>/dev/null)/bin)."
  warn "Варианты:"
  warn "  а) добавь этот каталог в PATH и запусти ./scripts/start.sh снова;"
  warn "  б) продолжи БЕЗ CLI (нативный fallback): агент создаст change через"
  warn "     ./scripts/new-change.sh и заполнит proposal/design/tasks вручную, без /opsx:."
  die "openspec недоступен — см. варианты выше."
fi

# ---------- Шаг 3: openspec init ----------
say "Запускаю openspec init (выбери свой инструмент: Claude Code / Codex / OpenCode)…"
openspec init || warn "openspec init вернул ошибку/уже инициализирован — проверь вывод выше."

# ---------- Шаг 3.5: brownfield — baseline-green (грабля №1) ----------
if [[ $BROWNFIELD -eq 1 && -x scripts/gates.sh ]]; then
  say "Brownfield: проверяю, зелёные ли гейты на НЕТРОНУТОМ репо (это грабля №1)…"
  if ./scripts/gates.sh >/tmp/ls-baseline-gates.log 2>&1; then
    say "✓ Baseline зелёный — авто-блок не будет спотыкаться о чужие падения."
  else
    warn "✗ Гейты на нетронутом репо НЕ зелёные. Авто-блок заклинит на этом ДО твоих правок."
    warn "  Почини/настрой гейты отдельным prep-коммитом ПЕРЕД циклом. Хвост вывода:"
    tail -n 8 /tmp/ls-baseline-gates.log | sed 's/^/    /'
  fi
fi

# ---------- Шаг 4: бутстрап-промпт (4 комбинации режимов) ----------
if [[ $BROWNFIELD -eq 1 && $INTERACTIVE -eq 1 ]]; then
  read -r -d '' PROMPT <<'EOF'
Это brownfield (существующий код). Работай по скилам brownfield + interactive-flow:
контекст берёшь из КОДА, идёшь пошагово и после каждого этапа показываешь GATE с
чек-листом документов — без явного «OK» дальше не идёшь; на гейте принимаешь правки.
Старт: прочитай кодовую базу и openspec/PRD.md (бриф работы), заполни openspec/project.md
(из кода) и openspec/north-star.md (инварианты = что нельзя сломать), покажи GATE 1 и жди OK.
Учти три грабли brownfield из скила. Код не пиши до GATE 3 (propose).
EOF
elif [[ $BROWNFIELD -eq 1 ]]; then
  read -r -d '' PROMPT <<'EOF'
Это brownfield (существующий код). Режим: один апрув плана на старте, дальше автономно.
Работай по скилу brownfield: контекст из КОДА, не из PRD с нуля.

ФАЗА 1 — ПЛАН: прочитай кодовую базу и openspec/PRD.md (бриф работы — фича/рефактор/эпик).
Заполни openspec/project.md (из кода) и openspec/north-star.md (инварианты = что нельзя
сломать). Декомпозируй работу в набор changes (для рефактора — дельта MODIFIED и опора на
существующие тесты; для эпика — несколько changes). Покажи ПЛАН ЦЕЛИКОМ один раз. Код не пиши.

ФАЗА 2 — после моего «go» (./scripts/goal-run.sh --all): идёшь по всем changes сам, без
остановок на одобрение, эскалация только в крайних случаях (AGENTS.md прав. 7). Учти три
грабли brownfield (baseline-green, baseline-спеки для MODIFIED, scoped gates).
EOF
elif [[ $INTERACTIVE -eq 1 ]]; then
  read -r -d '' PROMPT <<'EOF'
Работай по скилу interactive-flow: пошагово, после КАЖДОГО этапа показывай GATE с
чек-листом документов к прочтению и жди явного «OK» — без него дальше не идёшь; на
любом гейте принимаешь «правки: ...». Старт: прочитай openspec/PRD.md, заполни из него
openspec/project.md и openspec/north-star.md, покажи GATE 1 и жди OK. Код не пиши.
EOF
else
  read -r -d '' PROMPT <<'EOF'
Режим: одно одобрение плана на старте, дальше — автономная работа на дни/недели.

ФАЗА 1 — ПЛАН (сейчас, обсуждаем вживую): прочитай openspec/PRD.md, заполни из него
openspec/project.md (стек, конвенции) и openspec/north-star.md (цель + инварианты).
Затем декомпозируй ВЕСЬ PRD в набор changes: на каждую крупную фичу сделай explore +
propose (proposal.md, design.md, tasks.md, spec-дельта). Покажи мне ПЛАН ЦЕЛИКОМ один
раз — список всех changes с кратким содержанием каждого. Обсудим и поправим. Код не пиши.

ФАЗА 2 — АВТОНОМИЯ (после моего «go», я запущу ./scripts/goal-run.sh --all): идёшь по
ВСЕМ changes сам до зелёных гейтов, БЕЗ остановок на одобрение каждого. Не задавай
уточняющих/разрешающих вопросов («сделать X или Y», «продолжать ли») — решай сам и
продолжай. Останавливайся и зови меня ТОЛЬКО если без человека вообще невозможно
(см. AGENTS.md, правило эскалации 7). Рассчитывай, что меня не будет рядом сутками.
EOF
fi

MODE="greenfield"; [[ $BROWNFIELD -eq 1 ]] && MODE="brownfield"
[[ $INTERACTIVE -eq 1 ]] && MODE="$MODE + interactive"

say "════════════════════════════════════════════════════════════════"
say "ГОТОВО (режим: ${MODE}). Дальше — 2 действия:"
printf '\n1) Открой агента в этой папке (напр. `claude`) и вставь промпт:\n\n'
printf '\033[36m%s\033[0m\n' "$PROMPT"
printf '\n2) Одобри артефакты (proposal/design или на гейтах), затем авто-блок:\n\n'
printf '\033[36m   ./scripts/goal-run.sh --all\033[0m\n'

# В буфер кладём промпт ОДНОЙ строкой: при вставке многострочника в TUI (claude/codex)
# первый \n срабатывает как Enter и отправляется только первая строка. Схлопываем \n в пробелы.
if command -v pbcopy >/dev/null 2>&1; then
  printf '%s' "$PROMPT" | tr '\n' ' ' | pbcopy \
    && say "📋 Промпт (одной строкой) скопирован в буфер — открой claude и вставь (Cmd+V)."
fi
