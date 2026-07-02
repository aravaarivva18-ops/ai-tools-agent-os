#!/usr/bin/env python3
"""
Fast-Track Bootstrap & Verification Utility
Performs basic health checks on core configurations, tools, and the Python environment.
"""

import subprocess
import sys
from pathlib import Path


def check_file(path: Path, description: str) -> bool:
    """Checks if a file exists and is not empty."""
    if not path.exists():
        print(f"[FAIL] {description} missing: {path}")
        return False
    if path.stat().st_size == 0:
        print(f"[FAIL] {description} is empty: {path}")
        return False
    print(f"[ OK ] {description} exists and is verified.")
    return True


def check_tool_exec(python_bin: str, script_path: Path, args: list[str]) -> bool:
    """Checks if a tool runs and returns exit code 0."""
    if not script_path.exists():
        print(f"[FAIL] Script missing: {script_path}")
        return False

    cmd = [python_bin, str(script_path), *args]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            print(f"[ OK ] Tool executed successfully: {script_path.name}")
            return True
        else:
            print(f"[FAIL] Tool {script_path.name} failed with code {res.returncode}")
            print(f"Stdout:\n{res.stdout}\nStderr:\n{res.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] Exception executing {script_path.name}: {e}")
        return False


def main():
    print("=== Antigravity Fast-Track Workspace Health Check ===")

    workspace_root = Path(__file__).resolve().parent.parent
    tools_dir = workspace_root / "tools"

    # 1. Verify environment python
    python_bin = sys.executable
    print(f"Using python binary: {python_bin}")

    # 2. Check key files
    key_files = [
        (workspace_root / "CLAUDE.md", "CLAUDE.md project guide"),
        (workspace_root / "AGENTS.md", "AGENTS.md project rules"),
        (
            Path("/Users/rus/GEMINI_ANTIGRAVITY.md"),
            "GEMINI_ANTIGRAVITY.md constitution",
        ),
        (Path("/Users/rus/STUDENT_GUIDE.md"), "STUDENT_GUIDE.md student guide"),
    ]

    files_ok = True
    for path, desc in key_files:
        if not check_file(path, desc):
            files_ok = False

    # 3. Check tool scripts executable
    tools_ok = True
    tools_to_check = [
        (tools_dir / "rules_validator.py", []),
        (
            tools_dir / "test_healer.py",
            [str(tools_dir / "tests" / "test_diff_applier.py")],
        ),
    ]

    for script, args in tools_to_check:
        if not check_tool_exec(python_bin, script, args):
            tools_ok = False

    print("=====================================================")
    if files_ok and tools_ok:
        print("STATUS: SUCCESS. Fast-Track workspace is ready and healthy!")
        sys.exit(0)
    else:
        print("STATUS: FAILED. Please resolve the issues flagged above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
