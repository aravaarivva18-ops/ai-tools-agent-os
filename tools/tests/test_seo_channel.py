#!/usr/bin/env python3
"""Tests for SEO and GEO JIT skills creation patterns based on OSINT audits."""

import shutil
from pathlib import Path

import pytest

from tools.agent_skills import AgentSkillsManager

TEST_SEO_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_seo_test"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_SEO_WORKSPACE.exists():
        shutil.rmtree(TEST_SEO_WORKSPACE)
    TEST_SEO_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_SEO_WORKSPACE.exists():
        shutil.rmtree(TEST_SEO_WORKSPACE)


def test_create_seo_skill_includes_optimizations():
    """Positive test: Verifies that creating an SEO/GEO themed skill includes AI crawler and EEAT principles."""
    manager = AgentSkillsManager(TEST_SEO_WORKSPACE)
    skill_path = manager.create_skill(
        name="ai-seo-campaign",
        description="A programmatic SEO generator that optimizes brand presence on AI search engines.",
    )

    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")

    # Verify SEO & GEO best practices are generated
    assert "programmatic seo" in content.lower(), (
        "Programmatic SEO should be recommended in SEO skill templates"
    )
    assert "eeat" in content.lower(), (
        "EEAT credentials should be recommended in SEO skill templates"
    )
    assert "ai search engine" in content.lower() or "geo" in content.lower(), (
        "AI Search / GEO optimization should be recommended in SEO skill templates"
    )


def test_create_non_seo_skill_clean():
    """Negative test: Verifies that data/backend-themed skills do not have redundant SEO stack bloat."""
    manager = AgentSkillsManager(TEST_SEO_WORKSPACE)
    skill_path = manager.create_skill(
        name="db-connector",
        description="A simple SQLite connector.",
    )

    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")

    assert "programmatic seo" not in content.lower(), (
        "SEO bloat should not exist in db-connector"
    )
    assert "eeat" not in content.lower(), "EEAT bloat should not exist in db-connector"
