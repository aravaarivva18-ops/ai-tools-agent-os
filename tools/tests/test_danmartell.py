#!/usr/bin/env python3
"""Tests for Business Scaling and Productivity JIT skills creation patterns based on Dan Martell's philosophy."""

import shutil
from pathlib import Path

import pytest

from tools.agent_skills import AgentSkillsManager

TEST_DANMARTELL_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_danmartell_test"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_DANMARTELL_WORKSPACE.exists():
        shutil.rmtree(TEST_DANMARTELL_WORKSPACE)
    TEST_DANMARTELL_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_DANMARTELL_WORKSPACE.exists():
        shutil.rmtree(TEST_DANMARTELL_WORKSPACE)


def test_create_scale_skill_includes_productivity_principles():
    """Positive test: Verifies that creating a scale/productivity themed skill includes Dan Martell's core rules."""
    manager = AgentSkillsManager(TEST_DANMARTELL_WORKSPACE)
    skill_path = manager.create_skill(
        name="team-delegation-flow",
        description="A system that automates tasks delegation and audits time saved to optimize buyback rate.",
    )

    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")

    # Verify productivity & scaling best practices are generated
    assert "10-80-10 rule" in content.lower(), "10-80-10 Rule should be recommended in scale/productivity skill templates"
    assert "drip matrix" in content.lower() or "sop" in content.lower(), "SOP / DRIP matrix should be recommended in scale templates"
    assert "buyback" in content.lower() or "time saved" in content.lower(), "Buyback loop / Time saved metrics should be in scale templates"
    assert "pre-delegation checklist" in content.lower(), "Pre-delegation checklist should be recommended in scale templates"


def test_create_non_scale_skill_clean():
    """Negative test: Verifies that backend-themed skills do not have redundant scaling/productivity principles."""
    manager = AgentSkillsManager(TEST_DANMARTELL_WORKSPACE)
    skill_path = manager.create_skill(
        name="redis-cache-connector",
        description="A lightweight redis cache integration script.",
    )

    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")

    assert "10-80-10 rule" not in content.lower(), "Productivity bloat should not exist in redis connector"
    assert "buyback" not in content.lower(), "Productivity bloat should not exist in redis connector"
