import pytest
from advanced_workflow import run_workflow

def test_workflow_execution_success():
    """Test standard sequential execution of registered workflow functions."""
    steps = []
    
    def step1(ctx):
        ctx["v1"] = 100
        return True

    def step2(ctx):
        val = ctx.get("v1")
        ctx["v2"] = val + 50
        return True

    # Register steps linearly
    steps.extend([step1, step2])
    
    ctx = {}
    success = run_workflow(steps, ctx)
    
    assert success is True
    assert ctx["v2"] == 150

def test_workflow_execution_failure_handling():
    """Test workflow stops execution when a step returns False or raises an error."""
    steps = []

    def failing_step(ctx):
        return False

    def should_not_run(ctx):
        ctx["ran"] = True
        return True

    steps.extend([failing_step, should_not_run])
    
    ctx = {"ran": False}
    success = run_workflow(steps, ctx)
    
    assert success is False
    assert ctx["ran"] is False
