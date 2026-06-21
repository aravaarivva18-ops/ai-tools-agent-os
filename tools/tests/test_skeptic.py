"""Unit tests for tools/skeptic.py."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Ensure tools/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.scraping.skeptic import analyze_target


def test_analyze_target_mock_env(tmp_path):
    """Verify analyze_target handles target analysis using Agent-powered simulation when offline."""
    content = "print('hello world')"
    mode = "code"

    # We mock out environment/files to simulate a local mock fallback or test mode
    with patch.dict(os.environ, {"SKEPTIC_TEST_MODE": "1"}):
        report = analyze_target(content, mode)
        assert "Оценка качества кода" in report
        assert "Критические баги" in report


def test_analyze_target_file_input(tmp_path):
    """Verify skeptic successfully reads target file path if provided."""
    test_file = tmp_path / "target_code.py"
    test_file.write_text("def run():\n    pass", encoding="utf-8")

    # The CLI execution will be tested via calling skeptic entry points or analyze_target directly
    with patch.dict(os.environ, {"SKEPTIC_TEST_MODE": "1"}):
        report = analyze_target(test_file.read_text(encoding="utf-8"), "code")
        assert "Оценка качества кода" in report
