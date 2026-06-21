#!/usr/bin/env python3
"""Tests for context7 integration decision and knowledge base state."""

from pathlib import Path


def test_context7_integrated_in_knowledge_base():
    """Positive test: Verifies that context7.com is documented in the Gemini bot knowledge base."""
    kb_path = Path("/Users/rus/Desktop/gemini_bot_knowledge_base.md")
    assert kb_path.exists(), "gemini_bot_knowledge_base.md does not exist"

    content = kb_path.read_text(encoding="utf-8")
    assert "context7.com" in content.lower(), "context7.com not found in knowledge base"


def test_context7_not_in_invalid_files():
    """Negative test: Verifies that context7 is not mentioned in arbitrary non-config files."""
    test_file = Path("/Users/rus/ai-tools/pyproject.toml")
    assert test_file.exists()
    content = test_file.read_text(encoding="utf-8")
    assert "context7" not in content.lower(), "context7 found in pyproject.toml"


def test_context7_skill_file_exists():
    """Positive test: Verifies that the context7-mcp skill is installed and valid."""
    skill_path = Path("/Users/rus/.agent/skills/context7-mcp/SKILL.md")
    assert skill_path.exists(), "context7-mcp SKILL.md does not exist"
    content = skill_path.read_text(encoding="utf-8")
    assert "context7-mcp" in content, "Invalid skill name in file"
