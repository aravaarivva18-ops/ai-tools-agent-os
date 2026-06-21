#!/usr/bin/env python3
"""Tests for Agent Skills Manager."""

import shutil
import time
from pathlib import Path

import pytest
from agent_skills import AgentSkillsManager, LLMValidationError
from pydantic import BaseModel, Field

# Define a temporary test workspace under the project vault to avoid clutter
TEST_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_test_workspace"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)


class TaskResult(BaseModel):
    task_id: int = Field(description="Unique task ID")
    status: str = Field(description="Execution status")
    logs: list[str] = Field(default_factory=list, description="Associated logs")


def test_create_skill():
    """Tests creation of standardized skill structures and metadata files."""
    start = time.perf_counter()
    manager = AgentSkillsManager(workspace_path=TEST_WORKSPACE)

    skill_md = manager.create_skill(
        name="test-automation-helper",
        description="Assists in validating test run outputs.",
    )

    assert skill_md.exists()
    assert skill_md.name == "SKILL.md"

    # Check parent folder name
    skill_dir = skill_md.parent
    assert skill_dir.name == "test-automation-helper"

    # Verify subfolders are created
    assert (skill_dir / "scripts").is_dir()
    assert (skill_dir / "examples").is_dir()
    assert (skill_dir / "tests").is_dir()

    # Check file content
    content = skill_md.read_text(encoding="utf-8")
    assert "name: test-automation-helper" in content
    assert "description: Assists in validating test run outputs." in content
    assert "# Test Automation Helper" in content

    assert (time.perf_counter() - start) < 0.1


def test_create_prototype_skill():
    """Positive test: Verifies creation of a throwaway prototype skill."""
    manager = AgentSkillsManager(workspace_path=TEST_WORKSPACE)
    skill_md = manager.create_skill(
        name="test-prototype-draft",
        description="Throwaway prototype to check ideas.",
    )

    assert skill_md.exists()
    content = skill_md.read_text(encoding="utf-8")
    assert "name: test-prototype-draft" in content
    assert "Throwaway Prototyping" in content
    assert "scratch/" in content


def test_create_grill_skill():
    """Positive test: Verifies creation of a doc-driven alignment grill skill."""
    manager = AgentSkillsManager(workspace_path=TEST_WORKSPACE)
    skill_md = manager.create_skill(
        name="api-docs-grill",
        description="Docs-first alignment and grilling.",
    )

    assert skill_md.exists()
    content = skill_md.read_text(encoding="utf-8")
    assert "name: api-docs-grill" in content
    assert "context7.com" in content
    assert "/grill-me" in content


def test_validate_skill_output():
    """Tests validation of skill outputs wrapper logic."""
    start = time.perf_counter()
    manager = AgentSkillsManager(workspace_path=TEST_WORKSPACE)

    data = {"task_id": 101, "status": "completed", "logs": ["Start", "Process", "Done"]}

    result = manager.validate_skill_output(data, TaskResult)
    assert isinstance(result, TaskResult)
    assert result.task_id == 101
    assert result.status == "completed"
    assert result.logs == ["Start", "Process", "Done"]

    # Negative test case
    bad_data = {"status": "failed"}  # Missing task_id
    with pytest.raises(LLMValidationError):
        manager.validate_skill_output(bad_data, TaskResult)

    assert (time.perf_counter() - start) < 0.1


def test_get_skill_tool_schema():
    """Tests declarative schema extraction wrapper logic."""
    start = time.perf_counter()
    manager = AgentSkillsManager(workspace_path=TEST_WORKSPACE)

    def example_skill_tool(arg_a: str, arg_b: int = 42) -> bool:
        """Runs a mock skill action.

        Args:
            arg_a: Argument description A.
            arg_b: Argument description B.
        """
        return True

    schema = manager.get_skill_tool_schema(example_skill_tool)
    assert schema["name"] == "example_skill_tool"
    assert "Runs a mock skill action" in schema["description"]

    params = schema["parameters"]["properties"]
    assert params["arg_a"]["type"] == "STRING"
    assert params["arg_a"]["description"] == "Argument description A."
    assert params["arg_b"]["type"] == "INTEGER"
    assert params["arg_b"]["description"] == "Argument description B."

    assert schema["parameters"]["required"] == ["arg_a"]

    assert (time.perf_counter() - start) < 0.1
