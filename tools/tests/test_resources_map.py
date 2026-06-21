#!/usr/bin/env python3
"""Tests for Resources Map patterns (MCP, Karpathy vibe coding, levelsio YAGNI) in JIT skills generation."""

import shutil
from pathlib import Path

import pytest

from tools.agent_skills import AgentSkillsManager

TEST_RESOURCES_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_resources_test"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_RESOURCES_WORKSPACE.exists():
        shutil.rmtree(TEST_RESOURCES_WORKSPACE)
    TEST_RESOURCES_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_RESOURCES_WORKSPACE.exists():
        shutil.rmtree(TEST_RESOURCES_WORKSPACE)


def test_create_mcp_skill_includes_protocol_rules():
    """Positive test: Verifies that creating an MCP-themed skill includes Model Context Protocol and Karpathy/levelsio rules."""
    manager = AgentSkillsManager(TEST_RESOURCES_WORKSPACE)
    skill_path = manager.create_skill(
        name="custom-db-mcp-server",
        description="An MCP server that exposes tools to query a local SQLite database.",
    )
    
    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")
    
    # Verify MCP best practices are generated
    assert "model context protocol" in content.lower() or "mcp" in content.lower(), "MCP / Model Context Protocol should be in MCP skill templates"
    assert "json-rpc" in content.lower() or "sdk" in content.lower(), "JSON-RPC / SDK should be recommended in MCP templates"
    assert "karpathy" in content.lower() or "levelsio" in content.lower(), "Karpathy / levelsio principles should be in MCP templates"


def test_create_non_mcp_skill_clean():
    """Negative test: Verifies that non-MCP skills do not have redundant MCP protocol rules but still have Karpathy vibe coding rules."""
    manager = AgentSkillsManager(TEST_RESOURCES_WORKSPACE)
    skill_path = manager.create_skill(
        name="simple-txt-exporter",
        description="A lightweight script that exports user notes to txt files.",
    )
    
    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")
    
    assert "model context protocol" not in content.lower(), "MCP bloat should not exist in generic exporter"
    assert "json-rpc" not in content.lower(), "MCP bloat should not exist in generic exporter"
    assert "karpathy" in content.lower() or "levelsio" in content.lower(), "Karpathy / levelsio principles should be in default templates"
