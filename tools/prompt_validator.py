#!/usr/bin/env python3
import re
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

CONSTITUTION_PATH = Path("/Users/rus/GEMINI_ANTIGRAVITY.md")
STUDENT_GUIDE_PATH = Path("/Users/rus/STUDENT_GUIDE.md")
CLAUDE_PATH = WORKSPACE_ROOT / "CLAUDE.md"
AGENTS_PATH = WORKSPACE_ROOT / "AGENTS.md"


def check_sequential_sections(path: Path) -> bool:
    """Проверяет последовательную нумерацию разделов в конституции."""
    if not path.exists():
        print(f"[ERROR] Constitution file not found: {path}", file=sys.stderr)
        return False

    content = path.read_text(encoding="utf-8")
    # Ищем заголовки вида: ## 🏛️ 1. Название
    # Паттерн: ## [emoji] [номер]. [название]
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


def get_protocol_paragraphs(path: Path, keywords: list) -> set:
    """Извлекает нормализованные абзацы, содержащие ключевые слова протоколов."""
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")
    # Разделяем на абзацы по двойному переносу строки
    paragraphs = content.split("\n\n")
    protocol_paras = set()

    for p in paragraphs:
        p_clean = p.strip().lower()
        if any(kw.lower() in p_clean for kw in keywords):
            # Нормализуем текст (удаляем пунктуацию и пробелы)
            normalized = "".join(char for char in p_clean if char.isalnum())
            if len(normalized) > 20:  # игнорируем слишком короткие строки
                protocol_paras.add(normalized)

    return protocol_paras


def check_overlap(path1: Path, path2: Path, keywords: list) -> float:
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

    # Сравниваем конституцию с гайдом студента
    guide_overlap = check_overlap(CONSTITUTION_PATH, STUDENT_GUIDE_PATH, keywords)
    print(f"Overlap Constitution <-> Student Guide: {guide_overlap * 100:.2f}%")
    if guide_overlap > 0.08:
        print(
            f"[ERROR] Избыточное дублирование с гайдом студента: {guide_overlap * 100:.2f}% > 8%",
            file=sys.stderr,
        )
        success = False

    # Сравниваем конституцию с CLAUDE.md
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


CORE_BLOCK = """## 🏛️ Ядро (Core Imperatives) — обязательно к исполнению

- Solo Loop v10 + Stealth Stop на 3-й ошибке
- YAGNI (максимум 2–3 уровня абстракции)
- TDD (минимум 1 positive + 1 negative тест)
- Zero-Fluff + абсолютные file:// пути
- WAL + retry при записи в dashboard.db
- Human-in-the-Loop для опасных операций
"""

def normalize_gemini_constitution_headings(text: str) -> str:
    """Перенумеровывает заголовки ## ... N. Title последовательно."""
    lines = text.splitlines(keepends=True)
    result = []
    counter = 1
    pattern = re.compile(r'^(##\s+[^0-9\r\n]*?)\s*(\d+)\.\s+(.*)$')

    for line in lines:
        m = pattern.match(line.rstrip('\r\n'))
        if m:
            prefix = m.group(1).rstrip()
            title = m.group(3)
            # Сохраняем исходное окончание строки
            ending = line[len(line.rstrip('\r\n')):]
            result.append(f"{prefix} {counter}. {title}{ending}")
            counter += 1
        else:
            result.append(line)
    return "".join(result)

def ensure_core_imperatives_block(text: str) -> str:
    if "## 🏛️ Ядро (Core Imperatives)" in text or "## 🏛️ Core Rules Summary" in text:
        return text
    # Вставляем после первого заголовка документа
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip().startswith("#") and "GEMINI_ANTIGRAVITY" in line:
            lines.insert(i + 2, CORE_BLOCK + "\n")
            break
    return "".join(lines)


def check_constitution_health(path: Path = None) -> dict:
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
        "health": "good" if sections < 45 and not bloat and overlap_score < 0.12 else "needs_cleanup",
    }


def estimate_overlap(text: str) -> float:
    """Простая оценка дублирования (по ключевым фразам)."""
    keywords = ["Solo Loop", "Stealth Stop", "YAGNI", "TDD", "file://", "WAL"]
    count = sum(text.count(k) for k in keywords)
    return min(count / 20.0, 1.0)  # нормализованный score


def get_constitution_health_score(path: Path = None) -> int:
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

    # 1. Разрешаем временные директории pytest для тестов
    if "pytest" in path_str or "tmp_path" in path_str or "pytest-of-" in path_str:
        return True

    # 2. Разрешено писать в конституцию, гайд студента и их бакапы в /Users/rus/
    allowed_external_prefixes = [
        "/Users/rus/GEMINI_ANTIGRAVITY.md",
        "/Users/rus/STUDENT_GUIDE.md"
    ]
    if any(path_str.startswith(prefix) for prefix in allowed_external_prefixes):
        return True

    # 3. Разрешено писать в handoff_notes.md в корне воркспейса
    if path_str == "/Users/rus/ai-tools/handoff_notes.md":
        return True

    # 4. Разрешенные директории согласно правилам
    allowed_dirs = {
        "/Users/rus/ai-tools/tools",
        "/Users/rus/ai-tools/vault",
        "/Users/rus/ai-tools/dashboard-hand-on-pulse"
    }
    if any(path_str.startswith(d) for d in allowed_dirs):
        return True

    raise ValueError(f"Anti-Clutter: запрещено изменять файл вне разрешённых путей: {file_path}")



def main():
    if not validate_constitution_system():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
