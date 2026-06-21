#!/usr/bin/env python3
"""
Security scanner module to invoke Bandit SAST checks on the codebase using
the absolute virtual environment path of Python.
"""

import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path


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
    output_format: str | None = None,
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

    if output_format:
        cmd.extend(["-f", output_format])

    return cmd


def run_security_scan(
    targets: list[str],
    exclude_dirs: list[str] | None = None,
    skip_tests: list[str] | None = None,
    quiet: bool = False,
    output_format: str | None = None,
) -> tuple[int, str, str]:
    """
    Runs the Bandit scan command in a subprocess.
    Returns a tuple of (returncode, stdout, stderr).
    """
    cmd = build_bandit_command(targets, exclude_dirs, skip_tests, quiet, output_format)

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


def scan_for_secrets(target_path: str = ".") -> list[dict]:
    """
    Scans files in target_path for hardcoded secrets, keys, and tokens.
    Excludes common virtual env and version control directories.
    """
    patterns = {
        "OpenAI API Key": re.compile(r"sk-proj-[a-zA-Z0-9]{48}"),
        "Anthropic API Key": re.compile(r"sk-ant-api03-[a-zA-Z0-9-_]{80,150}"),
        "Google Gemini API Key": re.compile(r"AIzaSy[a-zA-Z0-9-_]{33}"),
        "Generic Private Key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    }

    # Generic pattern to catch variables like token = 'xxx' or password = "xxx"
    generic_pattern = re.compile(
        r"\b(password|secret|passwd|token|api_key)\s*=\s*['\"]([^'\"]{8,})['\"]",
        re.IGNORECASE,
    )

    findings = []
    exclude_dirs = {".venv", ".git", ".obsidian", "__pycache__", "node_modules"}

    path = Path(target_path)
    if not path.exists():
        return findings

    # Walk files
    files_to_scan = []
    if path.is_file():
        files_to_scan.append(path)
    else:
        for root, dirs, files in os.walk(target_path):
            # Prune excluded, hidden and documentation-heavy directories in-place to avoid walking down them
            dirs[:] = [
                d
                for d in dirs
                if d not in exclude_dirs
                and not d.startswith(".")
                and d not in ("bitrix-knowledge", "vault")
            ]
            for file in files:
                p = Path(root) / file
                # Skip binary files by extension
                if p.suffix.lower() in {
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".ico",
                    ".pdf",
                    ".zip",
                    ".tar",
                    ".gz",
                    ".db",
                }:
                    continue
                files_to_scan.append(p)

    for f in files_to_scan:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                # 1. Check strong patterns
                for name, regex in patterns.items():
                    if regex.search(line):
                        findings.append(
                            {
                                "type": name,
                                "file": str(f),
                                "line": idx,
                                "context": line.strip(),
                            }
                        )
                # 2. Check generic pattern
                match = generic_pattern.search(line)
                if match:
                    # Skip common test mock data and env lookups
                    val = match.group(2)
                    if not any(
                        x in val.lower()
                        for x in (
                            "mock",
                            "test",
                            "env",
                            "dummy",
                            "placeholder",
                            "os.get",
                        )
                    ):
                        findings.append(
                            {
                                "type": "Generic Secret",
                                "file": str(f),
                                "line": idx,
                                "context": line.strip(),
                            }
                        )
        except Exception:
            pass

    return findings


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
