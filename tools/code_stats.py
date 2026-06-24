"""Utility to calculate line statistics for Python files."""

import argparse
import json
import os
import sys


def analyze_file(filepath: str) -> dict[str, int]:
    """Analyzes a single Python file to count total, code, comment, and blank lines.

    Args:
        filepath: Path to the Python file.

    Returns:
        A dictionary with keys: 'total', 'code', 'comment', 'blank'.
    """
    total = 0
    blank = 0
    comment = 0
    code = 0

    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            total += 1
            stripped = line.strip()
            if not stripped:
                blank += 1
            elif stripped.startswith("#"):
                comment += 1
            else:
                code += 1

    return {
        "total": total,
        "code": code,
        "comment": comment,
        "blank": blank,
    }


def analyze_path(path: str) -> dict[str, int]:
    """Analyzes a file or directory recursively and returns consolidated statistics.

    Args:
        path: Path to the Python file or directory.

    Returns:
        A dictionary with consolidated keys: 'total', 'code', 'comment', 'blank'.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    if os.path.isfile(path):
        return analyze_file(path)

    consolidated = {
        "total": 0,
        "code": 0,
        "comment": 0,
        "blank": 0,
    }

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                stats = analyze_file(filepath)
                for key in consolidated:
                    consolidated[key] += stats[key]

    return consolidated


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Calculate line statistics for Python files."
    )
    parser.add_argument("path", help="Path to a Python file or directory")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        results = analyze_path(args.path)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
