#!/usr/bin/env python3
"""Tests for Claude Task Master necessity decision and YAGNI compliance."""

from pathlib import Path


def test_taskmaster_rejected_by_yagni():
    """Positive test: Verifies that the decision to reject Taskmaster is documented in implementation_plan.md."""
    plan_path = Path("/Users/rus/ai-tools/implementation_plan.md")
    assert plan_path.exists(), "implementation_plan.md does not exist"

    content = plan_path.read_text(encoding="utf-8")
    assert "reject" in content.lower() or "отклонен" in content.lower(), (
        "Architecture decision regarding Taskmaster rejection is not documented"
    )
    assert "yagni" in content.lower(), "YAGNI rationale not mentioned in plan"


def test_no_taskmaster_dependencies():
    """Negative test: Verifies that no task-master-ai packages are present in pyproject.toml."""
    pyproject_path = Path("/Users/rus/ai-tools/pyproject.toml")
    assert pyproject_path.exists()
    content = pyproject_path.read_text(encoding="utf-8")
    assert "task-master-ai" not in content.lower(), (
        "taskmaster should not be added to dependencies"
    )
