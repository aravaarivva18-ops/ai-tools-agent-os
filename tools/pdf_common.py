"""Shared PDF report generation utilities for AI Tools workspace.

Provides common helpers for Typst-based PDF report generators used
across ai-sales, ai-marketing, and ai-legal subprojects.
"""

import os
import tempfile
from typing import Any

import typst


def compile_typst_to_pdf(typst_content: str, output_path: str) -> None:
    """Compile Typst markup string to a PDF file.

    Creates a temporary .typ file, compiles it via the Typst Python binding,
    and cleans up the temp file regardless of success or failure.

    Args:
        typst_content: Valid Typst markup as a string.
        output_path: Destination path for the generated PDF.
    """
    with tempfile.NamedTemporaryFile(
        suffix=".typ", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(typst_content)
        temp_name = f.name

    try:
        typst.compile(temp_name, output=output_path)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)


def get_score_color(score: int) -> str:
    """Return a hex color code based on score threshold.

    Score ranges:
        80+  → Green (Strong)
        60+  → Blue (Good)
        40+  → Amber (Needs Work)
        <40  → Red (Critical)
    """
    if score >= 80:
        return "#10B981"
    if score >= 60:
        return "#0EA5E9"
    if score >= 40:
        return "#F59E0B"
    return "#EF4444"


def get_grade(score: int) -> str:
    """Convert a numeric score to a letter grade.

    Grade scale:
        90+ → A+
        80+ → A
        70+ → B
        60+ → C
        50+ → D
        <50 → F
    """
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def get_status_label(score: int) -> str:
    """Return a human-readable status label based on score.

    Status ranges:
        80+ → Strong
        60+ → Good
        40+ → Needs Work
        <40 → Critical
    """
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Needs Work"
    return "Critical"


def esc_typst(val: Any) -> Any:
    """Escape special Typst characters (e.g., dollar signs) in string values.

    Non-string values are returned unchanged.
    """
    if isinstance(val, str):
        return val.replace("$", r"\$")
    return val


def typst_page_setup(
    paper: str = "us-letter",
    header_text: str = "Report",
    header_color: str = "#64748B",
) -> str:
    """Generate a reusable Typst page setup block.

    Args:
        paper: Paper size (e.g., "us-letter", "a4").
        header_text: Text displayed in the page header.
        header_color: Hex color for the header text.

    Returns:
        Typst markup string with page, text, and heading configuration.
    """
    return f"""#set page(
  paper: "{paper}",
  margin: (x: 2cm, y: 2.5cm),
  header: align(right, text(size: 8.5pt, fill: rgb("{header_color}"), font: "Arial")[{header_text}]),
  footer: align(center, text(size: 8.5pt, fill: rgb("{header_color}"), font: "Arial")[
    Page #context counter(page).display("1 of 1", both: true)
  ])
)

#set text(
  font: "Arial",
  size: 11pt,
  fill: rgb("#1E293B")
)

#show heading: set text(fill: rgb("#1B2A4A"), weight: "bold")"""
