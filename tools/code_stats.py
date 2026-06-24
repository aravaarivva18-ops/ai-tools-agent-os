"""Utility to calculate line statistics for Python files."""


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
