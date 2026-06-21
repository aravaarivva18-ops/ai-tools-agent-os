#!/usr/bin/env python3
"""Tests for n8n evaluation decision, YAGNI compliance, and advanced_workflow functionality."""

from pathlib import Path

from tools.advanced_workflow import run_workflow


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


def test_advanced_workflow_success():
    """Positive test: Verifies that run_workflow executes all steps successfully."""
    execution_order = []

    def step_one(ctx):
        execution_order.append(1)
        ctx["val"] = 42
        return True

    def step_two(ctx):
        execution_order.append(2)
        assert ctx["val"] == 42
        ctx["val"] += 1
        return True

    context = {}
    result = run_workflow([step_one, step_two], context)

    assert result is True
    assert execution_order == [1, 2]
    assert context["val"] == 43


def test_advanced_workflow_failure():
    """Negative test: Verifies that run_workflow stops on failure and returns False."""
    execution_order = []

    def step_one(ctx):
        execution_order.append(1)
        return False

    def step_two(ctx):
        execution_order.append(2)
        return True

    context = {}
    result = run_workflow([step_one, step_two], context)

    assert result is False
    assert execution_order == [1]
