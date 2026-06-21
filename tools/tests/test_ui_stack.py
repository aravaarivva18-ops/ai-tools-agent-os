#!/usr/bin/env python3
"""Tests for modern UI stack integration into Agent Skills creation."""

import shutil
from pathlib import Path

import pytest

from tools.agent_skills import AgentSkillsManager

TEST_SKILLS_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_skills_test"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_SKILLS_WORKSPACE.exists():
        shutil.rmtree(TEST_SKILLS_WORKSPACE)
    TEST_SKILLS_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_SKILLS_WORKSPACE.exists():
        shutil.rmtree(TEST_SKILLS_WORKSPACE)


def test_create_ui_skill_includes_modern_stack():
    """Positive test: Verifies that creating a UI-themed skill includes Framer Motion and GSAP in the template."""
    manager = AgentSkillsManager(TEST_SKILLS_WORKSPACE)
    skill_path = manager.create_skill(
        name="fancy-landing",
        description="A beautiful landing page with advanced hover masks and scroll animations.",
    )
    
    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")
    
    # Verify that the generated skill recommends modern UI tools for fancy elements
    assert "framer motion" in content.lower(), "Framer Motion should be recommended in UI-themed skill templates"
    assert "gsap" in content.lower(), "GSAP should be recommended in UI-themed skill templates"
    assert "tailwind" in content.lower(), "Tailwind CSS should be recommended in UI-themed skill templates"


def test_create_non_ui_skill_does_not_include_ui_stack():
    """Negative test: Verifies that data/backend-themed skills do not have redundant UI stack bloat."""
    manager = AgentSkillsManager(TEST_SKILLS_WORKSPACE)
    skill_path = manager.create_skill(
        name="data-parser",
        description="A simple SQLite database data parser.",
    )
    
    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")
    
    assert "framer motion" not in content.lower(), "Framer Motion should not be bloated in non-UI skills"
    assert "gsap" not in content.lower(), "GSAP should not be bloated in non-UI skills"
