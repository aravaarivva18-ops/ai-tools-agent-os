#!/usr/bin/env python3
"""
Security scanner module to invoke Bandit SAST checks on the codebase using
the absolute virtual environment path of Python.
"""

import os
import subprocess  # nosec B404
import sys


def get_verified_python_path() -> str:
    """Returns the absolute path to the verified virtual environment python interpreter."""
    venv_python = "/Users/rus/ai-tools/.venv/bin/python"
    if os.path.exists(venv_python):
        return venv_python
    # Fallback to the current running interpreter if venv path does not exist
    return sys.executable


def build_bandit_command(
    targets: list[str],
    exclude_dirs: list[str] | None = None,
    skip_tests: list[str] | None = None,
    quiet: bool = False,
) -> list[str]:
    """Builds the shell command list for executing Bandit using the verified python path."""
    python_path = get_verified_python_path()
    cmd = [python_path, "-m", "bandit"]

    for target in targets:
        cmd.extend(["-r", target])

    if exclude_dirs:
        cmd.extend(["-x", ",".join(exclude_dirs)])

    if skip_tests:
        cmd.extend(["-s", ",".join(skip_tests)])

    if quiet:
        cmd.append("-q")

    return cmd


def run_security_scan(
    targets: list[str],
    exclude_dirs: list[str] | None = None,
    skip_tests: list[str] | None = None,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """
    Runs the Bandit scan command in a subprocess.
    Returns a tuple of (returncode, stdout, stderr).
    """
    cmd = build_bandit_command(targets, exclude_dirs, skip_tests, quiet)

    # Verify that the executable file exists before running to avoid "no such file or directory"
    if not os.path.exists(cmd[0]):
        return 127, "", f"Error: Python executable not found at {cmd[0]}"

    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


if __name__ == "__main__":
    # If run as CLI, default to scanning the current workspace
    default_targets = ["."]
    exit_code, stdout, stderr = run_security_scan(
        targets=default_targets,
        exclude_dirs=[".venv", ".git"],
        skip_tests=["B101", "B110", "B112", "B310", "B311", "B404", "B603", "B607"],
    )
    print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    sys.exit(exit_code)
