import os
import shutil
import tempfile

import pytest

from tools.context_optimizer import ContextOptimizer


@pytest.fixture
def setup_dirs():
    # Setup temporary rules directory and workspace directory
    rules_dir = tempfile.mkdtemp()
    workspace_dir = tempfile.mkdtemp()

    # Write mock rule modules
    with open(os.path.join(rules_dir, "common.md"), "w") as f:
        f.write("# Common rules content")
    with open(os.path.join(rules_dir, "python.md"), "w") as f:
        f.write("# Python rules content")
    with open(os.path.join(rules_dir, "frontend.md"), "w") as f:
        f.write("# Frontend rules content")

    yield rules_dir, workspace_dir

    shutil.rmtree(rules_dir)
    shutil.rmtree(workspace_dir)

def test_python_context(setup_dirs):
    rules_dir, workspace_dir = setup_dirs

    # Create Python project markers
    with open(os.path.join(workspace_dir, "requirements.txt"), "w") as f:
        f.write("pytest")

    optimizer = ContextOptimizer(rules_dir=rules_dir)
    optimizer.optimize_context(workspace_dir=workspace_dir)

    agents_file = os.path.join(workspace_dir, ".agents", "AGENTS.md")
    assert os.path.exists(agents_file)
    with open(agents_file) as f:
        content = f.read()

    assert "Active Stacks: Python" in content
    assert "Common rules content" in content
    assert "Python rules content" in content
    assert "Frontend rules content" not in content

def test_frontend_context(setup_dirs):
    rules_dir, workspace_dir = setup_dirs

    # Create Frontend project markers
    with open(os.path.join(workspace_dir, "package.json"), "w") as f:
        f.write('{"name": "test"}')

    optimizer = ContextOptimizer(rules_dir=rules_dir)
    optimizer.optimize_context(workspace_dir=workspace_dir)

    agents_file = os.path.join(workspace_dir, ".agents", "AGENTS.md")
    assert os.path.exists(agents_file)
    with open(agents_file) as f:
        content = f.read()

    assert "Active Stacks: Frontend" in content
    assert "Common rules content" in content
    assert "Frontend rules content" in content
    assert "Python rules content" not in content

def test_minimal_profile_context(setup_dirs):
    rules_dir, workspace_dir = setup_dirs

    # Create Python project markers
    with open(os.path.join(workspace_dir, "requirements.txt"), "w") as f:
        f.write("pytest")

    # Set minimal rules profile environment variable
    os.environ["AGY_RULES_PROFILE"] = "minimal"
    try:
        optimizer = ContextOptimizer(rules_dir=rules_dir)
        optimizer.optimize_context(workspace_dir=workspace_dir)

        agents_file = os.path.join(workspace_dir, ".agents", "AGENTS.md")
        assert os.path.exists(agents_file)
        with open(agents_file) as f:
            content = f.read()

        assert "Active Stacks: Minimal Profile" in content
        assert "Common rules content" in content
        assert "Python rules content" not in content
    finally:
        # Clean up env variable
        del os.environ["AGY_RULES_PROFILE"]
