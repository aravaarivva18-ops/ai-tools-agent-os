# PRD: Python Code Statistics Utility

## Introduction

Create a command-line utility `tools/code_stats.py` that analyzes Python source files to calculate metrics: total lines, code lines, comment lines, and blank lines. The utility must support single files and directory-wide scanning.

## Goals

- Implement a Python command-line tool `tools/code_stats.py`.
- Calculate line statistics (total, code, comment, blank) for Python files.
- Support both individual file analysis and recursive directory analysis.
- Include unit tests in `tools/tests/test_code_stats.py`.
- Adhere to the project's Ruff configuration and ensure pytest test suite passes.

## User Stories

### US-001: Implement Core Logic for File Statistics Analysis
**Description:** As a developer, I want to parse a single Python file to count total lines, blank lines, comment lines, and actual code lines.

**Acceptance Criteria:**
- [ ] Implement `analyze_file(filepath: str) -> dict` in `tools/code_stats.py`.
- [ ] Count total lines.
- [ ] Count blank lines (only whitespace).
- [ ] Count comment lines (lines starting with `#` after stripping whitespace; ignore multiline strings for simplicity).
- [ ] Count code lines (total - blank - comments).
- [ ] Returns a dictionary with keys: `total`, `code`, `comment`, `blank`.
- [ ] Typecheck passes.

### US-002: Add Directory Scanning and CLI Interface
**Description:** As a user, I want a CLI interface to run the analysis on a file or a folder (recursively scanning all `.py` files) and print the results as formatted JSON to stdout.

**Acceptance Criteria:**
- [ ] Add argument parsing to `tools/code_stats.py` using `argparse`.
- [ ] The CLI accepts a single positional argument `path` (file or folder).
- [ ] If `path` is a directory, recursively find and analyze all `.py` files.
- [ ] Output the results to stdout as formatted JSON.
- [ ] Handle missing file errors gracefully with an appropriate error message and exit code.
- [ ] Typecheck passes.

### US-003: Write Unit Tests for Code Statistics Utility
**Description:** As a QA engineer, I want unit tests for the statistics utility to verify correct counts for various file cases.

**Acceptance Criteria:**
- [ ] Create tests in `tools/tests/test_code_stats.py`.
- [ ] Cover `analyze_file` with tests for empty files, files with only comments, files with only code, and mixed files.
- [ ] Cover directory scanning logic using temporary directories (e.g. via `tmp_path` fixture in pytest).
- [ ] Running `pytest tools/tests/test_code_stats.py` passes successfully.
- [ ] Typecheck passes.
- [ ] Tests pass.

## Functional Requirements

- FR-1: Analyze a single Python file and count:
  - Total lines.
  - Blank lines (empty or containing only whitespace).
  - Comment lines (lines starting with `#` after leading whitespace is removed).
  - Code lines (lines that contain Python code, not blank, and not comments).
- FR-2: Accept file/directory path as a command-line argument.
- FR-3: Recursively find all `.py` files if a directory is passed.
- FR-4: Output a single consolidated JSON report with aggregated statistics.
- FR-5: Return exit code 0 on success, non-zero on error (e.g. file not found).

## Non-Goals

- Do not count docstrings (`"""`) as comments; treat them as code lines for simplicity.
- Do not support parsing files in languages other than Python.
- Do not generate graphical reports or visual charts.

## Technical Considerations

- Use Python's built-in libraries (`os`, `argparse`, `json`).
- Ensure compatibility with Python 3.12+.
- Run Ruff linting and formatting on changes.

## Success Metrics

- Running `python tools/code_stats.py [path]` prints valid JSON statistics.
- Code changes pass project check pipeline (`make check` or `ruff check` + `pytest`).
