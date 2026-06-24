import tempfile
from pathlib import Path

import pytest

from tools.rules_validator import (
    check_constitution_health,
    check_overlap,
    check_sequential_sections,
    enforce_anti_clutter,
    ensure_core_imperatives_block,
    estimate_overlap,
    get_constitution_health_score,
    normalize_gemini_constitution_headings,
    validate_constitution_system,
)
from tools.self_improve import detect_tool_conflicts


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


def test_normalize_headings_positive():
    src = "## 🏛️ 1. Foo\n## 🧠 5. Bar\n## 📉 7. Baz\n"
    out = normalize_gemini_constitution_headings(src)
    assert "## 🏛️ 1. Foo\n" in out
    assert "## 🧠 2. Bar\n" in out
    assert "## 📉 3. Baz\n" in out


def test_normalize_headings_idempotency():
    src = "## 🏛️ 1. Foo\n## 🧠 5. Bar\n## 📉 7. Baz\n"
    first = normalize_gemini_constitution_headings(src)
    second = normalize_gemini_constitution_headings(first)
    assert first == second


def test_ensure_core_block_added_negative():
    src = "# GEMINI_ANTIGRAVITY\n## 1. Первый раздел\n"
    out = ensure_core_imperatives_block(src)
    assert "## 🏛️ Ядро (Core Imperatives)" in out
    assert "Solo Loop v10" in out


def test_ensure_core_block_already_exists():
    src = "# GEMINI_ANTIGRAVITY\n## 🏛️ Core Rules Summary (Ядро)\n## 1. Первый раздел\n"
    out = ensure_core_imperatives_block(src)
    assert "## 🏛️ Ядро (Core Imperatives)" not in out


def test_constitution_health_positive(tmp_path):
    temp_file = tmp_path / "GEMINI_ANTIGRAVITY.md"
    temp_file.write_text(
        "# GEMINI_ANTIGRAVITY\n\n## 🏛️ Core Rules Summary\n\n## 1. Section One\nSolo Loop\n",
        encoding="utf-8",
    )
    health = check_constitution_health(temp_file)
    assert health["sections"] == 2
    assert health["health"] == "good"
    assert health["bloat"] is False


def test_constitution_health_bloat(tmp_path):
    temp_file = tmp_path / "GEMINI_ANTIGRAVITY.md"
    large_text = "# GEMINI_ANTIGRAVITY\n\n## 1. Section One\n" + ("A" * 60000)
    temp_file.write_text(large_text, encoding="utf-8")
    health = check_constitution_health(temp_file)
    assert health["bloat"] is True
    assert health["health"] == "needs_cleanup"


def test_estimate_overlap():
    assert estimate_overlap("Solo Loop and Stealth Stop") == 2.0 / 20.0
    assert estimate_overlap("No keywords") == 0.0


def test_get_constitution_health_score(tmp_path):
    temp_file = tmp_path / "GEMINI_ANTIGRAVITY.md"
    temp_file.write_text(
        "# GEMINI_ANTIGRAVITY\n\n## 🏛️ Core Rules Summary\n\n## 1. Section One\nSolo Loop\n",
        encoding="utf-8",
    )
    assert get_constitution_health_score(temp_file) == 100

    temp_file.write_text(
        "# GEMINI_ANTIGRAVITY\n\n## 🏛️ Core Rules Summary\n\n## 1. Section One\n"
        + ("A" * 60000),
        encoding="utf-8",
    )
    assert get_constitution_health_score(temp_file) == 85


def test_enforce_anti_clutter():
    assert enforce_anti_clutter("/Users/rus/ai-tools/tools/script.py") is True
    assert enforce_anti_clutter("/Users/rus/ai-tools/vault/some_data.json") is True
    assert (
        enforce_anti_clutter("/Users/rus/ai-tools/dashboard-hand-on-pulse/app.py")
        is True
    )

    assert enforce_anti_clutter("/Users/rus/GEMINI_ANTIGRAVITY.md") is True
    assert enforce_anti_clutter("/Users/rus/GEMINI_ANTIGRAVITY.md.bak.123") is True
    assert enforce_anti_clutter("/Users/rus/ai-tools/handoff_notes.md") is True

    with pytest.raises(ValueError, match="Anti-Clutter"):
        enforce_anti_clutter("/Users/rus/ai-tools/geo-seo/tests/test_x.py")
    with pytest.raises(ValueError, match="Anti-Clutter"):
        enforce_anti_clutter("/Users/rus/Desktop/clutter.py")
    with pytest.raises(ValueError, match="Anti-Clutter"):
        enforce_anti_clutter("/tmp/temp.txt")


def test_detect_tool_conflicts_positive_subagent():
    mock_logs = [
        {
            "session_id": "test_session_001",
            "friction_points": [
                {
                    "heading": "Execution Error",
                    "content": "Tried to spawn a subagent to write helper code.",
                }
            ],
        }
    ]

    conflicts = detect_tool_conflicts(mock_logs)
    assert len(conflicts) == 1
    assert "test_session_001" in conflicts[0]
    assert "Solo Loop" in conflicts[0]


def test_detect_tool_conflicts_negative_no_conflicts():
    mock_logs = [
        {
            "session_id": "test_session_002",
            "friction_points": [
                {
                    "heading": "Linter Issue",
                    "content": "Fixed imports in test file via replace_file_content.",
                }
            ],
        }
    ]

    conflicts = detect_tool_conflicts(mock_logs)
    assert len(conflicts) == 0


def test_detect_tool_conflicts_explicit_subagent_calls():
    mock_logs = [
        {
            "session_id": "test_session_003",
            "friction_points": [
                {
                    "heading": "API Misuse",
                    "content": "User requested invoke_subagent in chat, but it was blocked.",
                },
                {
                    "heading": "Tool Error",
                    "content": "Tried calling define_subagent manually.",
                },
            ],
        }
    ]

    conflicts = detect_tool_conflicts(mock_logs)
    assert len(conflicts) == 1
    assert "invoke_subagent/define_subagent" in conflicts[0]
