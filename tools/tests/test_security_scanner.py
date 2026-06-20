import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.security.security_scanner import (
    build_bandit_command,
    get_verified_python_path,
    run_security_scan,
)


def test_verified_python_path():
    """Test that get_verified_python_path returns the exact venv python executable."""
    path = get_verified_python_path()
    assert path == "/Users/rus/ai-tools/.venv/bin/python"
    assert os.path.exists(path)


def test_build_bandit_command_structure():
    """Test build_bandit_command constructs the command correctly with target and options."""
    targets = ["tools/"]
    exclude_dirs = [".venv", "tests"]
    skip_tests = ["B101", "B310"]

    cmd = build_bandit_command(
        targets=targets, exclude_dirs=exclude_dirs, skip_tests=skip_tests, quiet=True
    )

    assert cmd[0] == "/Users/rus/ai-tools/.venv/bin/python"
    assert cmd[1] == "-m"
    assert cmd[2] == "bandit"
    assert "-r" in cmd
    assert "tools/" in cmd
    assert "-x" in cmd
    assert ".venv,tests" in cmd
    assert "-s" in cmd
    assert "B101,B310" in cmd
    assert "-q" in cmd


def test_run_security_scan_success(tmp_path):
    """Test a basic run of security scan on a temporary directory with a clean python file."""
    temp_file = tmp_path / "clean.py"
    temp_file.write_text("def main():\n    pass\n")

    returncode, stdout, stderr = run_security_scan(
        targets=[str(temp_file)], exclude_dirs=None, skip_tests=None, quiet=True
    )

    # It should run bandit successfully and return 0 (no issues found)
    assert returncode == 0
    assert "Run started" in stdout or "Code scanned" in stdout or stdout == ""
    assert stderr == ""


def test_run_security_scan_with_invalid_python(monkeypatch):
    """Test that if python path is invalid, run_security_scan returns 127 without shell errors."""
    # Force get_verified_python_path to return a non-existent path
    monkeypatch.setattr(
        "tools.security.security_scanner.get_verified_python_path",
        lambda: "/invalid/path/to/python",
    )

    returncode, stdout, stderr = run_security_scan(targets=["."])

    assert returncode == 127
    assert "Python executable not found at /invalid/path/to/python" in stderr
    assert stdout == ""
