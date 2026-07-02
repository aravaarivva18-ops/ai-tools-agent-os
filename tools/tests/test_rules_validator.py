import tempfile
from pathlib import Path

import pytest

from tools.rules_validator import (
    check_constitution_health,
    check_jit_skills,
    check_link_formatting,
    check_overlap,
    check_rules_bloat,
    check_sequential_sections,
    check_stop_slop,
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


def test_check_jit_skills_fix(tmp_path, monkeypatch):
    """Позитивный тест: автоисправление JIT-навыков дописывает их в CLAUDE.md."""
    import tools.rules_validator

    claude_file = tmp_path / "CLAUDE.md"
    claude_file.write_text("# CLAUDE.md\n## Commands\n* **Test:** `pytest`\n", encoding="utf-8")

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_a = skills_dir / "skill_a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text("# Skill A\n", encoding="utf-8")

    monkeypatch.setattr(tools.rules_validator, "CLAUDE_PATH", claude_file)
    monkeypatch.setattr(tools.rules_validator, "WORKSPACE_ROOT", tmp_path)

    # Проверяем без fix=True, файл не должен измениться
    assert check_jit_skills(fix=False) is True
    assert "## 🛠️ JIT Skills" not in claude_file.read_text(encoding="utf-8")

    # Запускаем с fix=True
    assert check_jit_skills(fix=True) is True

    # Проверяем, что в CLAUDE.md добавилась секция и ссылка на навык
    updated_content = claude_file.read_text(encoding="utf-8")
    assert "## 🛠️ JIT Skills" in updated_content
    assert "skills/skill_a/SKILL.md" in updated_content



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
    from tools.config import get_workspace_root

    workspace_root = get_workspace_root()
    home = Path.home()

    assert enforce_anti_clutter(str(workspace_root / "tools" / "script.py")) is True
    assert (
        enforce_anti_clutter(str(workspace_root / "vault" / "some_data.json")) is True
    )
    assert (
        enforce_anti_clutter(str(workspace_root / "dashboard-hand-on-pulse" / "app.py"))
        is True
    )

    assert enforce_anti_clutter(str(home / "GEMINI_ANTIGRAVITY.md")) is True
    assert enforce_anti_clutter(str(home / "GEMINI_ANTIGRAVITY.md.bak.123")) is True
    assert enforce_anti_clutter(str(workspace_root / "handoff_notes.md")) is True

    with pytest.raises(ValueError, match="Anti-Clutter"):
        enforce_anti_clutter(str(workspace_root / "some_clutter_dir" / "test.py"))
    with pytest.raises(ValueError, match="Anti-Clutter"):
        enforce_anti_clutter(str(home / "Desktop" / "clutter.py"))
    with pytest.raises(ValueError, match="Anti-Clutter"):
        enforce_anti_clutter("/etc/hosts")


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


def test_check_stop_slop_positive():
    """Тест: текст без ИИ-маркеров проходит проверку."""
    content = "Мы пишем простой и понятный код без лишних абстракций."
    assert check_stop_slop(content, Path("dummy.md")) is True


def test_check_stop_slop_negative():
    """Тест: текст с ИИ-маркерами падает на проверке."""
    content_en = "We must delve deeper into this problem."
    assert check_stop_slop(content_en, Path("dummy.md")) is False

    content_ru = "Это бесшовный переход к новой экосистеме."
    assert check_stop_slop(content_ru, Path("dummy.md")) is False


def test_check_stop_slop_ignored():
    """Тест: строки с описанием правил Stop-Slop игнорируются."""
    content = "Строжайший запрет на ИИ-мусор: delve, tapestry, бесшовный."
    assert check_stop_slop(content, Path("dummy.md")) is True


def test_check_link_formatting_positive():
    """Тест: правильно оформленные ссылки проходят проверку."""
    content = (
        "Прочитайте [AGENTS.md](file:///Users/rus/ai-tools/AGENTS.md) для деталей."
    )
    assert check_link_formatting(content, Path("dummy.md")) is True

    content_portable = "Посмотрите [cli.py](@ai-tools/tools/cli.py)."
    assert check_link_formatting(content_portable, Path("dummy.md")) is True


def test_check_link_formatting_negative_whole():
    """Тест: полностью обернутая в бэктики ссылка вызывает ошибку."""
    content = "Прочитайте `[AGENTS.md](file:///Users/rus/ai-tools/AGENTS.md)`."
    assert check_link_formatting(content, Path("dummy.md")) is False


def test_check_link_formatting_negative_text():
    """Тест: имя ссылки в бэктиках вызывает ошибку."""
    content = "Посмотрите [`cli.py`](@ai-tools/tools/cli.py)."
    assert check_link_formatting(content, Path("dummy.md")) is False


def test_check_rules_bloat(tmp_path, monkeypatch):
    """Тест: проверяет, что предупреждение о раздувании правил срабатывает корректно."""
    import tools.rules_validator

    # 1. Позитивный случай (маленький файл)
    small_file = tmp_path / "AGENTS.md"
    small_file.write_text("Line 1\nLine 2\n", encoding="utf-8")

    monkeypatch.setattr(tools.rules_validator, "RULES_FILES", [small_file])
    assert check_rules_bloat() is True

    # 2. Негативный случай (раздутый файл > 120 строк)
    big_file = tmp_path / "CLAUDE.md"
    big_file.write_text("Line\n" * 150, encoding="utf-8")

    monkeypatch.setattr(tools.rules_validator, "RULES_FILES", [big_file])

    # Перехватываем вывод в stderr, чтобы убедиться, что WARNING пишется
    import sys
    from io import StringIO

    stderr_buf = StringIO()
    monkeypatch.setattr(sys, "stderr", stderr_buf)

    assert check_rules_bloat() is True

    output = stderr_buf.getvalue()
    assert "[WARNING]" in output
    assert "CLAUDE.md" in output
    assert "разросся" in output
