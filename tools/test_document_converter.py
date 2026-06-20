"""Unit tests for tools/document_converter.py."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure tools/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.text.document_converter import (
    convert_docx_to_markdown,
    convert_pdf_to_markdown,
    convert_pptx_to_markdown,
    convert_to_markdown,
    convert_xlsx_to_markdown,
)


@patch("pypdf.PdfReader")
def test_convert_pdf(mock_pdf_reader):
    """Verify PDF extraction formats text page-by-page."""
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "Hello World from Page 1"
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = "Hello World from Page 2"

    mock_reader_instance = mock_pdf_reader.return_value
    mock_reader_instance.pages = [mock_page_1, mock_page_2]

    # Call with a dummy path
    res = convert_pdf_to_markdown("dummy.pdf")

    assert "## Page 1 of 2" in res
    assert "Hello World from Page 1" in res
    assert "## Page 2 of 2" in res
    assert "Hello World from Page 2" in res


@patch("docx.Document")
def test_convert_docx(mock_docx_document):
    """Verify DOCX extraction formats headers, lists, and tables."""
    mock_doc = mock_docx_document.return_value

    # Mock paragraphs and tables using XML body structure
    mock_p1 = MagicMock()
    mock_p1.tag = "p"
    p1_obj = MagicMock()
    p1_obj.text = "Heading 1 Text"
    p1_obj.style.name = "Heading 1"
    p1_obj.paragraph_format.left_indent = None

    mock_p2 = MagicMock()
    mock_p2.tag = "p"
    p2_obj = MagicMock()
    p2_obj.text = "Normal Paragraph text."
    p2_obj.style.name = "Normal"
    p2_obj.paragraph_format.left_indent = None

    mock_tbl = MagicMock()
    mock_tbl.tag = "tbl"
    tbl_obj = MagicMock()

    # Table Mock structure
    row1 = MagicMock()
    cell1 = MagicMock()
    cell1.text = "Header 1"
    cell2 = MagicMock()
    cell2.text = "Header 2"
    row1.cells = [cell1, cell2]

    row2 = MagicMock()
    cell3 = MagicMock()
    cell3.text = "Val 1"
    cell4 = MagicMock()
    cell4.text = "Val 2"
    row2.cells = [cell3, cell4]

    tbl_obj.rows = [row1, row2]

    # Setup element to object mappings inside python-docx
    def mock_init(element, parent):
        if element == mock_p1:
            return p1_obj
        if element == mock_p2:
            return p2_obj
        if element == mock_tbl:
            return tbl_obj
        return MagicMock()

    # Stub the constructor helpers in python-docx
    with (
        patch("docx.text.paragraph.Paragraph", side_effect=mock_init),
        patch("docx.table.Table", side_effect=mock_init),
    ):
        mock_doc.element.body = [mock_p1, mock_p2, mock_tbl]
        res = convert_docx_to_markdown("dummy.docx")

    assert "# Heading 1 Text" in res
    assert "Normal Paragraph text." in res
    assert "| Header 1 | Header 2 |" in res
    assert "| --- | --- |" in res
    assert "| Val 1 | Val 2 |" in res


@patch("openpyxl.load_workbook")
def test_convert_xlsx(mock_load_workbook):
    """Verify Excel extraction converts sheets to markdown tables."""
    mock_wb = mock_load_workbook.return_value
    mock_wb.sheetnames = ["Sheet1"]

    mock_sheet = MagicMock()
    mock_wb.__getitem__.return_value = mock_sheet

    # Mock cells
    mock_sheet.iter_rows.return_value = [
        ("Col1", "Col2"),
        ("Row1Val1", "Row1Val2"),
    ]

    res = convert_xlsx_to_markdown("dummy.xlsx")

    assert "# Sheet: Sheet1" in res
    assert "| Col1 | Col2 |" in res
    assert "| --- | --- |" in res
    assert "| Row1Val1 | Row1Val2 |" in res


@patch("pptx.Presentation")
def test_convert_pptx(mock_presentation):
    """Verify PPTX extraction parses slides, shapes, tables, and notes."""
    mock_prs = mock_presentation.return_value

    mock_slide = MagicMock()
    mock_prs.slides = [mock_slide]

    # Slide structure
    mock_title_shape = MagicMock()
    mock_title_shape.text = "Slide Title"

    # Normal text shape
    mock_text_shape = MagicMock()
    mock_text_shape.has_text_frame = True
    mock_text_shape.has_table = False
    mock_p = MagicMock()
    mock_p.text = "Slide bullet text"
    mock_text_shape.text_frame.paragraphs = [mock_p]

    # Notes
    mock_slide.has_notes_slide = True
    mock_slide.notes_slide.notes_text_frame.text = "Presenter notes content."

    # All shapes on the slide (including title) as a mocked collection
    mock_shapes = MagicMock()
    mock_shapes.__iter__.return_value = [mock_title_shape, mock_text_shape]
    mock_shapes.title = mock_title_shape
    mock_slide.shapes = mock_shapes

    res = convert_pptx_to_markdown("dummy.pptx")

    assert "# Slide 1" in res
    assert "## Slide Title" in res
    assert "Slide bullet text" in res
    assert "> **Notes:** Presenter notes content." in res


def test_convert_to_markdown_routing():
    """Verify extension routing throws on unknown files."""
    with patch(
        "tools.text.document_converter.convert_pdf_to_markdown", return_value="PDF"
    ) as mock_pdf:
        assert convert_to_markdown("test.pdf") == "PDF"
        mock_pdf.assert_called_once_with("test.pdf")

    with pytest.raises(ValueError, match="Unsupported document format"):
        convert_to_markdown("test.unknown")
