import pytest
from advanced_workflow import AdvancedWorkflow, StepResult, WorkflowContext


def test_workflow_execution_success():
    """Test standard sequential execution of registered workflow steps."""
    wf = AdvancedWorkflow()

    @wf.step("step1")
    def run_step1(ctx: WorkflowContext) -> StepResult:
        ctx.set("v1", 100)
        return StepResult(success=True, message="Step 1 completed")

    @wf.step("step2", depends_on=["step1"])
    def run_step2(ctx: WorkflowContext) -> StepResult:
        val = ctx.get("v1")
        ctx.set("v2", val + 50)
        return StepResult(success=True, message="Step 2 completed")

    results = wf.run()

    assert results["step1"].success is True
    assert results["step2"].success is True
    assert wf.context.get("v2") == 150

def test_workflow_conditional_branching():
    """Test conditional execution based on values set in preceding steps."""
    wf = AdvancedWorkflow()

    @wf.step("check_balance")
    def check_balance(ctx: WorkflowContext) -> StepResult:
        ctx.set("balance", 200)
        return StepResult(success=True)

    @wf.step("approve_payment", depends_on=["check_balance"])
    def approve_payment(ctx: WorkflowContext) -> StepResult:
        balance = ctx.get("balance")
        if balance > 100:
            ctx.set("status", "approved")
            return StepResult(success=True)
        else:
            ctx.set("status", "rejected")
            return StepResult(success=False, message="Insufficient funds")

    results = wf.run()
    assert results["approve_payment"].success is True
    assert wf.context.get("status") == "approved"

def test_workflow_execution_failure_handling():
    """Test workflow behavior when a required dependency fails."""
    wf = AdvancedWorkflow()

    @wf.step("failing_step")
    def failing_step(ctx: WorkflowContext) -> StepResult:
        return StepResult(success=False, message="Something went wrong")

    @wf.step("dependent_step", depends_on=["failing_step"])
    def dependent_step(ctx: WorkflowContext) -> StepResult:
        return StepResult(success=True)

    results = wf.run()
    assert results["failing_step"].success is False
    assert "dependent_step" not in results
    assert "dependent_step" in wf.skipped_steps
