#!/usr/bin/env python3
"""Tests for Spec Kit necessity decision and YAGNI compliance."""

from pathlib import Path


def test_speckit_rejected_by_yagni():
    """Positive test: Verifies that the decision to reject Spec Kit is documented in implementation_plan.md."""
    plan_path = Path("/Users/rus/ai-tools/implementation_plan.md")
    assert plan_path.exists(), "implementation_plan.md does not exist"

    content = plan_path.read_text(encoding="utf-8")
    assert "reject" in content.lower() or "отклонен" in content.lower(), (
        "Architecture decision regarding Spec Kit rejection is not documented"
    )
    assert "yagni" in content.lower(), "YAGNI rationale not mentioned in plan"


def test_no_speckit_dependencies():
    """Negative test: Verifies that no specify-cli or spec-kit packages are present in pyproject.toml."""
    pyproject_path = Path("/Users/rus/ai-tools/pyproject.toml")
    assert pyproject_path.exists()
    content = pyproject_path.read_text(encoding="utf-8")
    assert "specify-cli" not in content.lower(), (
        "spec-kit should not be added to dependencies"
    )
    assert "spec-kit" not in content.lower(), (
        "spec-kit should not be added to dependencies"
    )
