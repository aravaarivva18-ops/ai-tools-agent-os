"""Tests for tools/pdf_common.py shared PDF generation utilities."""

from unittest.mock import MagicMock, patch

from tools.pdf_common import (
    esc_typst,
    get_grade,
    get_score_color,
    get_status_label,
    typst_page_setup,
)


class TestGetScoreColor:
    """Tests for score-to-color mapping."""

    def test_high_score_returns_green(self):
        assert get_score_color(80) == "#10B981"
        assert get_score_color(100) == "#10B981"

    def test_medium_score_returns_blue(self):
        assert get_score_color(60) == "#0EA5E9"
        assert get_score_color(79) == "#0EA5E9"

    def test_low_score_returns_amber(self):
        assert get_score_color(40) == "#F59E0B"
        assert get_score_color(59) == "#F59E0B"

    def test_critical_score_returns_red(self):
        assert get_score_color(0) == "#EF4444"
        assert get_score_color(39) == "#EF4444"


class TestGetGrade:
    """Tests for score-to-grade mapping."""

    def test_a_plus(self):
        assert get_grade(90) == "A+"
        assert get_grade(100) == "A+"

    def test_a(self):
        assert get_grade(80) == "A"

    def test_b(self):
        assert get_grade(70) == "B"

    def test_c(self):
        assert get_grade(60) == "C"

    def test_d(self):
        assert get_grade(50) == "D"

    def test_f(self):
        assert get_grade(0) == "F"
        assert get_grade(49) == "F"


class TestGetStatusLabel:
    """Tests for score-to-status mapping."""

    def test_strong(self):
        assert get_status_label(80) == "Strong"

    def test_good(self):
        assert get_status_label(60) == "Good"

    def test_needs_work(self):
        assert get_status_label(40) == "Needs Work"

    def test_critical(self):
        assert get_status_label(0) == "Critical"


class TestEscTypst:
    """Tests for Typst character escaping."""

    def test_escapes_dollar_sign(self):
        assert esc_typst("Price: $100") == r"Price: \$100"

    def test_returns_non_string_unchanged(self):
        assert esc_typst(42) == 42
        assert esc_typst(None) is None

    def test_no_dollar_returns_unchanged(self):
        assert esc_typst("Hello world") == "Hello world"


class TestTypstPageSetup:
    """Tests for Typst page setup generation."""

    def test_default_paper_size(self):
        result = typst_page_setup()
        assert '"us-letter"' in result

    def test_custom_paper_size(self):
        result = typst_page_setup(paper="a4")
        assert '"a4"' in result

    def test_header_text_included(self):
        result = typst_page_setup(header_text="My Report")
        assert "My Report" in result

    def test_includes_font_setup(self):
        result = typst_page_setup()
        assert "Arial" in result
        assert "11pt" in result


class TestCompileTypstToPdf:
    """Tests for the Typst-to-PDF compilation helper."""

    @patch("tools.pdf_common.typst.compile")
    @patch("tools.pdf_common.tempfile.NamedTemporaryFile")
    @patch("tools.pdf_common.os.remove")
    @patch("tools.pdf_common.os.path.exists", return_value=True)
    def test_compile_and_cleanup(
        self, mock_exists, mock_remove, mock_tmp, mock_compile
    ):
        """Verify that compile is called and temp file is cleaned up."""
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.typ"
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value = mock_file

        from tools.pdf_common import compile_typst_to_pdf

        compile_typst_to_pdf("#set page()", "/tmp/output.pdf")

        mock_compile.assert_called_once_with("/tmp/test.typ", output="/tmp/output.pdf")
        mock_remove.assert_called_once_with("/tmp/test.typ")
