#!/usr/bin/env python3
"""
Rules and Constitution Integrity Validator.
Combines link verification, JIT skills synchronization, sequential sections check,
overlap analysis, and anti-clutter guardrails.
"""

import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools.config import get_workspace_root
except ImportError:
    from config import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()

CONSTITUTION_PATH = Path.home() / "GEMINI_ANTIGRAVITY.md"
STUDENT_GUIDE_PATH = Path.home() / "STUDENT_GUIDE.md"
CLAUDE_PATH = WORKSPACE_ROOT / "CLAUDE.md"
AGENTS_PATH = WORKSPACE_ROOT / "AGENTS.md"

RULES_FILES = [
    CLAUDE_PATH,
    AGENTS_PATH,
    WORKSPACE_ROOT / ".cursorrules",
    WORKSPACE_ROOT / "youtube-faceless-pipeline/AGENTS.md",
    CONSTITUTION_PATH,
    STUDENT_GUIDE_PATH,
]

CORE_BLOCK = """## 🏛️ Ядро (Core Imperatives) — обязательно к исполнению

- Solo Loop v10 + Stealth Stop на 3-й ошибке
- YAGNI (максимум 2–3 уровня абстракции)
- TDD (минимум 1 positive + 1 negative тест)
- Zero-Fluff + абсолютные file:// пути
- WAL + retry при записи в dashboard.db
- Human-in-the-Loop для опасных операций
"""


def check_file_links() -> bool:
    """Проверяет работоспособность всех локальных ссылок в файлах правил."""
    has_errors = False

    # Ищем как старый формат, так и новые переносимые форматы
    link_pattern = re.compile(
        r"(?:file:///Users/rus/ai-tools/|@ai-tools/|file://"
        + re.escape(str(WORKSPACE_ROOT))
        + r"/)([^\s\)\#\"\'\>]+)"
    )

    for rule_file in RULES_FILES:
        if not rule_file.exists():
            continue

        content = rule_file.read_text(encoding="utf-8")
        matches = link_pattern.findall(content)

        for rel_path_str in matches:
            rel_path_str = rel_path_str.rstrip(".,;`*\"'")
            rel_path_str = rel_path_str.split("#")[0]
            target_path = WORKSPACE_ROOT / rel_path_str

            if not target_path.exists():
                print(
                    f"[ERROR] Битая ссылка в {rule_file.name}: @ai-tools/{rel_path_str}",
                    file=sys.stderr,
                )
                has_errors = True

    return not has_errors


def check_jit_skills(fix: bool = False) -> bool:
    """Проверяет синхронизацию папок в skills/ и записей JIT-навыков в CLAUDE.md."""
    claude_file = CLAUDE_PATH
    skills_dir = WORKSPACE_ROOT / "skills"

    if not claude_file.exists() or not skills_dir.exists():
        return True

    actual_skills = {
        item.name
        for item in skills_dir.iterdir()
        if item.is_dir() and (item / "SKILL.md").exists()
    }

    content = claude_file.read_text(encoding="utf-8")
    mentioned_skills = set(re.findall(r"skills/([^/]+)/SKILL.md", content))

    has_errors = False
    missing_in_claude = actual_skills - mentioned_skills
    if missing_in_claude:
        if fix:
            print(f"⚙️ Автосинхронизация JIT-навыков: добавление {len(missing_in_claude)} навыков в CLAUDE.md...")
            if not content.endswith("\n"):
                content += "\n"

            if "## 🛠️ JIT Skills" not in content and "## JIT Skills" not in content:
                content += "\n## 🛠️ JIT Skills\n\n"

            lines = content.splitlines()
            for skill in sorted(missing_in_claude):
                link_line = f"* **{skill.title()}:** [skills/{skill}/SKILL.md](file://skills/{skill}/SKILL.md)"
                if link_line not in lines:
                    lines.append(link_line)

            try:
                try:
                    from tools.rules_validator import enforce_anti_clutter
                    enforce_anti_clutter(str(claude_file))
                except ImportError:
                    pass
                claude_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
                print("✅ CLAUDE.md успешно обновлен и JIT-навыки синхронизированы!")
                mentioned_skills = actual_skills
                missing_in_claude = set()
            except Exception as e:
                print(f"❌ Ошибка записи в CLAUDE.md: {e}", file=sys.stderr)
                has_errors = True
        else:
            # Для импортированных из Open Design скиллов выводим только INFO, чтобы не раздувать CLAUDE.md
            print(
                f"[INFO] Дополнительные навыки на диске (не упомянутые в CLAUDE.md): {len(missing_in_claude)} навыков.",
                file=sys.stdout,
            )

    missing_on_disk = mentioned_skills - actual_skills
    if missing_on_disk:
        print(
            f"[ERROR] Навыки упомянуты в CLAUDE.md, но отсутствуют в skills/: {', '.join(missing_on_disk)}",
            file=sys.stderr,
        )
        has_errors = True

    return not has_errors



def check_sequential_sections(path: Path) -> bool:
    """Проверяет последовательную нумерацию разделов в конституции."""
    if not path.exists():
        print(f"[ERROR] Constitution file not found: {path}", file=sys.stderr)
        return False

    content = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^##\s+(?:\S+)\s+(\d+)\.\s+(.+)$", re.MULTILINE)
    matches = pattern.findall(content)

    if not matches:
        print("[ERROR] No numbered sections found in constitution.", file=sys.stderr)
        return False

    expected_number = 1
    has_errors = False
    for num_str, title in matches:
        num = int(num_str)
        if num != expected_number:
            print(
                f"[ERROR] Несогласованная нумерация в конституции: ожидался раздел {expected_number}, найден {num} ({title})",
                file=sys.stderr,
            )
            has_errors = True
        expected_number = num + 1

    return not has_errors


def get_protocol_paragraphs(path: Path, keywords: list[str]) -> set[str]:
    """Извлекает нормализованные абзацы, содержащие ключевые слова протоколов."""
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")
    paragraphs = content.split("\n\n")
    protocol_paras = set()

    for p in paragraphs:
        p_clean = p.strip().lower()
        if any(kw.lower() in p_clean for kw in keywords):
            normalized = "".join(char for char in p_clean if char.isalnum())
            if len(normalized) > 20:
                protocol_paras.add(normalized)

    return protocol_paras


def check_overlap(path1: Path, path2: Path, keywords: list[str]) -> float:
    """Вычисляет коэффициент overlap (Jaccard similarity) между абзацами протоколов."""
    paras1 = get_protocol_paragraphs(path1, keywords)
    paras2 = get_protocol_paragraphs(path2, keywords)

    if not paras1 or not paras2:
        return 0.0

    intersection = paras1.intersection(paras2)
    union = paras1.union(paras2)

    return len(intersection) / len(union)


def validate_constitution_system() -> bool:
    """Проводит полный аудит системы конституции и сопутствующих правил."""
    success = True

    print("=== Аудит нумерации разделов конституции ===")
    if not check_sequential_sections(CONSTITUTION_PATH):
        success = False
    else:
        print("OK: Разделы пронумерованы последовательно.")

    print("\n=== Аудит перекрытия (Overlap) протоколов ===")
    keywords = ["Solo Loop", "Stealth Stop", "YAGNI", "Self-Healing"]

    guide_overlap = check_overlap(CONSTITUTION_PATH, STUDENT_GUIDE_PATH, keywords)
    print(f"Overlap Constitution <-> Student Guide: {guide_overlap * 100:.2f}%")
    if guide_overlap > 0.08:
        print(
            f"[ERROR] Избыточное дублирование с гайдом студента: {guide_overlap * 100:.2f}% > 8%",
            file=sys.stderr,
        )
        success = False

    claude_overlap = check_overlap(CONSTITUTION_PATH, CLAUDE_PATH, keywords)
    print(f"Overlap Constitution <-> CLAUDE.md: {claude_overlap * 100:.2f}%")
    if claude_overlap > 0.08:
        print(
            f"[ERROR] Избыточное дублирование с CLAUDE.md: {claude_overlap * 100:.2f}% > 8%",
            file=sys.stderr,
        )
        success = False

    if success:
        print("\nOK: Все проверки структуры и overlap пройдены успешно.")
    else:
        print(
            "\nFAIL: Обнаружены нарушения стандартов YAGNI и структурирования.",
            file=sys.stderr,
        )

    return success


def normalize_gemini_constitution_headings(text: str) -> str:
    """Перенумеровывает заголовки ## ... N. Title последовательно."""
    lines = text.splitlines(keepends=True)
    result = []
    counter = 1
    pattern = re.compile(r"^(##\s+[^0-9\r\n]*?)\s*(\d+)\.\s+(.*)$")

    for line in lines:
        m = pattern.match(line.rstrip("\r\n"))
        if m:
            prefix = m.group(1).rstrip()
            title = m.group(3)
            ending = line[len(line.rstrip("\r\n")) :]
            result.append(f"{prefix} {counter}. {title}{ending}")
            counter += 1
        else:
            result.append(line)
    return "".join(result)


def ensure_core_imperatives_block(text: str) -> str:
    """Вставляет ядро императивов после первого заголовка документа."""
    if "## 🏛️ Ядро (Core Imperatives)" in text or "## 🏛️ Core Rules Summary" in text:
        return text
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip().startswith("#") and "GEMINI_ANTIGRAVITY" in line:
            lines.insert(i + 2, CORE_BLOCK + "\n")
            break
    return "".join(lines)


def estimate_overlap(text: str) -> float:
    """Простая оценка дублирования по ключевым фразам."""
    keywords = ["Solo Loop", "Stealth Stop", "YAGNI", "TDD", "file://", "WAL"]
    count = sum(text.count(k) for k in keywords)
    return min(count / 20.0, 1.0)


def check_constitution_health(path: Path | None = None) -> dict[str, Any]:
    """Возвращает метрики здоровья конституции."""
    if path is None:
        path = CONSTITUTION_PATH
    if not path.exists():
        return {"status": "missing"}

    text = path.read_text(encoding="utf-8")
    sections = len(re.findall(r"^##", text, re.MULTILINE))
    overlap_score = estimate_overlap(text)
    bloat = len(text) > 55000

    return {
        "sections": sections,
        "overlap_score": overlap_score,
        "bloat": bloat,
        "health": "good"
        if sections < 45 and not bloat and overlap_score < 0.12
        else "needs_cleanup",
    }


def get_constitution_health_score(path: Path | None = None) -> int:
    """Возвращает нормализованную оценку здоровья конституции от 0 до 100."""
    health = check_constitution_health(path)
    if health.get("status") == "missing":
        return 0
    score = 100
    if health.get("bloat"):
        score -= 15
    if health.get("overlap_score", 0) > 0.08:
        score -= 10
    if health.get("sections", 0) > 45:
        score -= 5
    return max(score, 0)


def enforce_anti_clutter(file_path: str) -> bool:
    """Проверка перед созданием/изменением файлов (Anti-Clutter Guardrails)."""
    path_obj = Path(file_path).resolve()
    path_str = str(path_obj)

    if (
        "pytest" in path_str
        or "tmp_path" in path_str
        or "pytest-of-" in path_str
        or "/var/folders/" in path_str
        or "/tmp/" in path_str  # noqa: S108
        or "tempfile" in path_str
    ):
        return True

    home = Path.home()
    workspace_root = get_workspace_root()

    allowed_external_prefixes = [
        str(home / "GEMINI_ANTIGRAVITY.md"),
        str(home / "STUDENT_GUIDE.md"),
        str(home / "Desktop" / "gemini_bot_knowledge_base.md"),
    ]
    if any(path_str.startswith(prefix) for prefix in allowed_external_prefixes):
        return True

    if path_str == str(workspace_root / "handoff_notes.md"):
        return True

    allowed_dirs = {
        str(workspace_root / "tools"),
        str(workspace_root / "vault"),
        str(workspace_root / "skills"),
        str(workspace_root / "dashboard-hand-on-pulse"),
        str(workspace_root / "wiki"),
        str(workspace_root / "geo-seo"),
        str(workspace_root / "ai-sales"),
        str(workspace_root / "ai-marketing"),
        str(workspace_root / "ai-legal"),
    }
    if any(path_str.startswith(d) for d in allowed_dirs):
        return True

    raise ValueError(
        f"Anti-Clutter: запрещено изменять файл вне разрешённых путей: {file_path}"
    )


def check_stop_slop(content: str, file_path: Path) -> bool:
    """Проверяет файл на отсутствие ИИ-мусора (Stop-Slop)."""
    has_errors = False

    stop_words = [
        "delve",
        "tapestry",
        "beacon",
        "dynamic landscape",
        "underscore",
        "robust",
        "key takeaways",
        "look no further",
        "in conclusion",
        "furthermore",
        "moreover",
        "crucial",
        "paramount",
        "elevate",
        "game-changer",
        "revolutionary",
        "seamless",
        "leverage",
        "hybrid",
        "ecosystem",
        "pivot",
        "synergy",
        "agile",
        "align",
        "углубляться",
        "погружаться",
        "гобелен",
        "динамичный ландшафт",
        "робастный",
        "ключевые выводы",
        "не ищите дальше",
        "в заключение",
        "более того",
        "гейм-чейнджер",
        "революционный",
        "бесшовный",
        "экосистема",
        "пивот",
        "синергия",
        "синхронизироваться",
        "выравниваться",
        "выводить на новый уровень",
        "первостепенный",
    ]

    def get_word_pattern(word: str) -> re.Pattern:
        if re.match(r"^[a-zA-Z\s-]+$", word):
            return re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        else:
            return re.compile(
                rf"(?:^|[^a-zA-Zа-яА-Я0-9_]){re.escape(word)}(?:[^a-zA-Zа-яА-Я0-9_]|$)",
                re.IGNORECASE,
            )

    patterns = [(word, get_word_pattern(word)) for word in stop_words]

    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        line_lower = line.lower()

        # Пропускаем строки с описанием самих правил, чтобы избежать ложных срабатываний
        if any(
            kw in line_lower
            for kw in [
                "stop-slop",
                "ии-маркер",
                "ии-мусор",
                "запрет 25",
                "english:",
                "русские:",
                "25 запрещенных",
                "запрещенных ии-слов",
            ]
        ):
            continue

        found_words = []
        for word, pattern in patterns:
            if pattern.search(line):
                found_words.append(word)

        if found_words and len(found_words) <= 3:
            print(
                f"[ERROR] Найден ИИ-мусор '{', '.join(found_words)}' в {file_path.name}:{idx}: '{line.strip()}'",
                file=sys.stderr,
            )
            has_errors = True

    return not has_errors


def check_link_formatting(content: str, file_path: Path) -> bool:
    """Проверяет ссылки в формате markdown на наличие нежелательных бэктиков."""
    has_errors = False

    pattern_whole = re.compile(r"`\[([^\]]+)\]\(((?:file:///|@ai-tools/)[^\)]+)\)`")
    pattern_text = re.compile(r"\[`([^`\]]+)`\]\(((?:file:///|@ai-tools/)[^\)]+)\)")

    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        m_whole = pattern_whole.search(line)
        if m_whole:
            print(
                f"[ERROR] Ссылка полностью обернута в бэктики в {file_path.name}:{idx}: '{line.strip()}'",
                file=sys.stderr,
            )
            has_errors = True

        m_text = pattern_text.search(line)
        if m_text:
            print(
                f"[ERROR] Имя ссылки обернуто в бэктики в {file_path.name}:{idx}: '{line.strip()}'",
                file=sys.stderr,
            )
            has_errors = True

    return not has_errors


def check_rules_bloat() -> bool:
    """Проверяет файлы правил на раздувание (bloat) для экономии контекста (токенов)."""
    global_agents = Path.home() / ".agents" / "AGENTS.md"
    all_rules = list(RULES_FILES)
    if global_agents.exists() and global_agents not in all_rules:
        all_rules.append(global_agents)

    for rule_file in all_rules:
        if not rule_file.exists():
            continue

        content = rule_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) > 120:
            print(
                f"[WARNING] Файл правил {rule_file.name} разросся ({len(lines)} строк > 120). "
                f"Рекомендуется перенести примеры во внешние файлы (в /examples) или сжать инструкции.",
                file=sys.stderr,
            )
    return True


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Rules integrity validator")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Автоматически исправить несинхронизированные JIT-навыки",
    )
    args = parser.parse_args()

    success = True
    print("=== Проверка целостности регламентов и ссылок ===")

    if not check_file_links():
        success = False

    if not check_jit_skills(fix=args.fix):
        success = False

    if not validate_constitution_system():
        success = False

    # Новые проверки на ИИ-мусор и бэктики в правилах
    for rule_file in RULES_FILES:
        if not rule_file.exists():
            continue
        content = rule_file.read_text(encoding="utf-8")
        if not check_stop_slop(content, rule_file):
            success = False
        if not check_link_formatting(content, rule_file):
            success = False

    # Проверка на раздувание контекста (WARNING)
    check_rules_bloat()

    if success:
        print("OK: Все ссылки целы, JIT-навыки синхронизированы, конституция валидна.")
        sys.exit(0)
    else:
        print("FAIL: Найдены ошибки в регламентах.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
