#!/usr/bin/env python3
"""Tests for n8n evaluation decision and YAGNI compliance."""

from pathlib import Path


def test_n8n_rejected_by_yagni():
    """Positive test: Verifies that the decision to reject n8n is documented in implementation_plan.md."""
    plan_path = Path("/Users/rus/ai-tools/implementation_plan.md")
    assert plan_path.exists(), "implementation_plan.md does not exist"

    content = plan_path.read_text(encoding="utf-8").lower()
    assert "n8n" in content, "n8n is not mentioned in implementation_plan.md"
    assert "reject" in content or "отклонен" in content, (
        "Rejection status for n8n is not documented"
    )
    assert "yagni" in content, "YAGNI rationale not mentioned in plan for n8n"
