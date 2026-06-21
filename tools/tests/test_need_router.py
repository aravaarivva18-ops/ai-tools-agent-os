#!/usr/bin/env python3
"""Tests for Claude Code Router necessity decision and YAGNI compliance."""

from pathlib import Path


def test_router_necessity_rejected():
    """Positive test: Verifies that the final decision to reject CCR is documented in implementation_plan.md."""
    plan_path = Path("/Users/rus/ai-tools/implementation_plan.md")
    assert plan_path.exists(), "implementation_plan.md does not exist"

    content = plan_path.read_text(encoding="utf-8")
    assert "reject" in content.lower() or "отклонен" in content.lower(), (
        "Necessity decision regarding CCR is not documented"
    )
    assert "yagni" in content.lower(), "YAGNI rationale not mentioned in plan"


def test_no_ccr_dependencies():
    """Negative test: Verifies that no ccr packages are present in pyproject.toml."""
    pyproject_path = Path("/Users/rus/ai-tools/pyproject.toml")
    assert pyproject_path.exists()
    content = pyproject_path.read_text(encoding="utf-8")
    assert "claude-code-router" not in content.lower(), (
        "claude-code-router should not be added to dependencies"
    )
