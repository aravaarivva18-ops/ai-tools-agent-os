#!/usr/bin/env python3
"""Tests for Solo Loop v10 Engine and Planning with Files."""

import shutil
import time
from pathlib import Path

import pytest

from core.solo_loop import SoloLoopV10
from tools.planning_with_files import PlanningWithFiles

TEST_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_solo_test"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)


def test_planning_with_files_restore_and_log():
    """Tests context restoration from implementation_plan.md and progress logging."""
    start = time.perf_counter()
    planner = PlanningWithFiles(TEST_WORKSPACE)

    # 1. Create a dummy implementation_plan.md
    plan_content = """# 🧬 Test Title
Some context.

## 📅 5. Пошаговый план (5-Line Plan)
1. **Шаг 1**: Реализовать фичу А.
2. **Шаг 2**: Написать тесты Б.
3. **Шаг 3**: Сделать ревью В.
"""
    planner.plan_path.write_text(plan_content, encoding="utf-8")

    state = planner.restore_state()
    assert state["title"] == "🧬 Test Title"
    assert len(state["steps"]) == 3
    assert state["steps"][0] == "Реализовать фичу А."
    assert state["next_step"] == "Реализовать фичу А."

    # 2. Record progress on Step 1
    planner.record_progress("Реализовать фичу А.", "completed")

    # Re-restore
    state_new = planner.restore_state()
    assert state_new["completed_steps"] == ["Реализовать фичу А. - COMPLETED"]
    assert state_new["next_step"] == "Написать тесты Б."

    # 3. Record finding
    planner.record_finding("Тест Факта", "Все работает отлично.")
    assert planner.findings_path.exists()
    assert "Тест Факта" in planner.findings_path.read_text(encoding="utf-8")

    assert (time.perf_counter() - start) < 0.1


def test_solo_loop_v10_execution_and_stealth_stop():
    """Tests execution tracking, log compression, and Stealth Stop triggering after 3 errors."""
    start = time.perf_counter()
    loop = SoloLoopV10(TEST_WORKSPACE)

    # 1. Track success
    res = loop.track_execution(
        "pytest", True, "Success! Passed 10 tests.\nNo warnings.\nDone."
    )
    assert res["success"] is True
    assert "Success!" in res["compressed_output"]
    assert not res["stealth_stop"]

    # 2. Track failures (identically repeating error)
    err_output = "FAIL: test_something failed\nE AssertionError: True is not False\nError inside core."

    # Error 1
    res1 = loop.track_execution("pytest", False, err_output)
    assert res1["success"] is False
    assert not res1["stealth_stop"]
    assert "AssertionError" in res1["compressed_output"]

    # Error 2
    res2 = loop.track_execution("pytest", False, err_output)
    assert res2["success"] is False
    assert not res2["stealth_stop"]

    # Error 3: Trigger Stealth Stop!
    res3 = loop.track_execution("pytest", False, err_output)
    assert res3["success"] is False
    assert res3["stealth_stop"] is True
    assert "STEALTH STOP" in res3["compressed_output"]
    assert "AssertionError: True is not False" in res3["compressed_output"]

    assert (time.perf_counter() - start) < 0.1


def test_solo_loop_log_compression():
    """Tests Headroom-style log compression logic."""
    start = time.perf_counter()
    loop = SoloLoopV10(TEST_WORKSPACE)

    # Create very long log
    long_success = "\n".join([f"Line {i} - info log message" for i in range(100)])
    compressed = loop.compress_log(long_success, max_lines=10)
    assert "Логи обрезаны для экономии контекста" in compressed
    assert len(compressed.splitlines()) <= 12

    long_error = (
        "Traceback (most recent call last):\n"
        + "\n".join([f"  File 'file_{i}.py', line 10" for i in range(50)])
        + "\nE AssertionError: error occurred"
    )
    comp_error = loop.compress_log(long_error, max_lines=10, is_error=True)
    assert "AssertionError: error occurred" in comp_error

    assert (time.perf_counter() - start) < 0.1


def test_solo_loop_compaction_positive():
    """Positive test for context compaction."""
    from core.solo_loop import SoloLoopV10

    loop = SoloLoopV10(TEST_WORKSPACE)

    history = [
        {
            "command": "pytest",
            "success": True,
            "output": "Passed 10 tests.\nEverything ok.",
        },
        {"command": "ruff check .", "success": True, "output": "No issues found."},
        {
            "command": "mypy .",
            "success": False,
            "output": "Error: Incompatible types in assignment\nFound 1 error.",
        },
    ]

    res = loop.compact_context(history)
    assert "Successfully executed: pytest, ruff check ." in res["summary_text"]
    assert "Failed commands: mypy ." in res["summary_text"]
    assert "Error: Incompatible types in assignment" in res["summary_text"]

    # Check that individual outputs are kept but potentially cleaned
    assert len(res["cleaned_steps"]) == 3
    assert res["cleaned_steps"][0]["command"] == "pytest"
    assert res["cleaned_steps"][0]["success"] is True


def test_solo_loop_compaction_negative():
    """Negative test for context compaction with empty history."""
    from core.solo_loop import SoloLoopV10

    loop = SoloLoopV10(TEST_WORKSPACE)

    res = loop.compact_context([])
    assert res["summary_text"] == "No history to compact."
    assert res["cleaned_steps"] == []
