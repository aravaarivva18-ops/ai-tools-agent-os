import tempfile
from pathlib import Path

from tools.prompt_validator import (
    check_overlap,
    check_sequential_sections,
    validate_constitution_system,
)


def test_check_sequential_sections_positive():
    """Позитивный тест: разделы идут строго последовательно."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = Path(tmpdir) / "GEMINI_ANTIGRAVITY.md"
        content = (
            "## 🏛️ 1. Раздел один\n"
            "Описание один\n\n"
            "## 🧠 2. Раздел два\n"
            "Описание два\n\n"
            "## ⚡ 3. Раздел три\n"
            "Описание три\n"
        )
        temp_file.write_text(content, encoding="utf-8")
        assert check_sequential_sections(temp_file) is True


def test_check_sequential_sections_negative_missing_number():
    """Негативный тест: номер раздела пропущен."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = Path(tmpdir) / "GEMINI_ANTIGRAVITY.md"
        content = (
            "## 🏛️ 1. Раздел один\n"
            "Описание один\n\n"
            "## 🧠 3. Раздел три (пропущен 2)\n"
            "Описание два\n"
        )
        temp_file.write_text(content, encoding="utf-8")
        assert check_sequential_sections(temp_file) is False


def test_check_overlap_positive_low_overlap():
    """Позитивный тест: перекрытие протоколов минимально."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.md"
        file2 = Path(tmpdir) / "file2.md"

        file1.write_text(
            "## 🏛️ 1. Solo Loop\nThis is a strict solo loop protocol rule.\n",
            encoding="utf-8",
        )
        file2.write_text(
            "## 🧠 2. YAGNI\nWe must apply yagni concept to code design.\n",
            encoding="utf-8",
        )

        overlap = check_overlap(file1, file2, ["Solo Loop", "YAGNI"])
        assert overlap <= 0.08


def test_check_overlap_negative_high_overlap():
    """Негативный тест: перекрытие протоколов слишком высокое (абзацы дублируются)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.md"
        file2 = Path(tmpdir) / "file2.md"

        shared_paragraph = (
            "Strict Solo Loop is essential for recovery and preventing context bloat."
        )

        file1.write_text(f"## 🏛️ 1. Solo Loop\n\n{shared_paragraph}\n", encoding="utf-8")
        file2.write_text(
            f"## 🧠 2. Solo Loop\n\n{shared_paragraph}\n", encoding="utf-8"
        )

        overlap = check_overlap(file1, file2, ["Solo Loop"])
        assert overlap > 0.08


def test_current_rules_validate():
    """Проверка валидности текущей конституции на хосте."""
    assert validate_constitution_system() is True
