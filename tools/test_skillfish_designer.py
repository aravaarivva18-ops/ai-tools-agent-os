import pytest

from tools.skillfish_designer import SkillfishDesigner


@pytest.fixture
def adapter():
    return SkillfishDesigner(workspace_path="/Users/rus/ai-tools")


def test_usability_scorer(adapter):
    result = adapter.run_usability_scorer(
        tasks_completed=8, total_tasks=10, seconds_taken=200
    )
    assert result["status"] == "success"
    assert result["completion_rate"] == "80.0%"
    assert result["average_time_seconds"] == 20.0
    assert result["usability_score"] == 80.0


def test_usability_scorer_invalid(adapter):
    with pytest.raises(ValueError, match="Tasks completed must be between"):
        adapter.run_usability_scorer(
            tasks_completed=-1, total_tasks=10, seconds_taken=200
        )
    with pytest.raises(ValueError, match="Total tasks must be greater than"):
        adapter.run_usability_scorer(
            tasks_completed=5, total_tasks=0, seconds_taken=200
        )


def test_design_critique(adapter):
    result_fail = adapter.run_design_critique(
        "PrimaryButton", has_contrast=False, has_aria=False
    )
    assert result_fail["passed"] is False
    assert result_fail["score"] == 50
    assert len(result_fail["improvements"]) == 2

    result_pass = adapter.run_design_critique(
        "PrimaryButton", has_contrast=True, has_aria=True
    )
    assert result_pass["passed"] is True
    assert result_pass["score"] == 100
