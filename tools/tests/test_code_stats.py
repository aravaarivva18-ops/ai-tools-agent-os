"""Unit tests for the Python code statistics utility."""

import pytest

from tools.code_stats import analyze_file, analyze_path


def test_analyze_file_simple(tmp_path: pytest.TempPathFactory) -> None:
    # Create a temporary file with typical Python content
    p = tmp_path / "simple.py"  # type: ignore[operator]
    content = (
        "def hello() -> None:\n"
        "    # This is a comment\n"
        "    print('Hello')\n"
        "\n"
        "    return\n"
    )
    p.write_text(content, encoding="utf-8")

    stats = analyze_file(str(p))
    assert stats["total"] == 5
    assert stats["code"] == 3
    assert stats["comment"] == 1
    assert stats["blank"] == 1


def test_analyze_file_empty(tmp_path: pytest.TempPathFactory) -> None:
    p = tmp_path / "empty.py"  # type: ignore[operator]
    p.write_text("", encoding="utf-8")

    stats = analyze_file(str(p))
    assert stats["total"] == 0
    assert stats["code"] == 0
    assert stats["comment"] == 0
    assert stats["blank"] == 0


def test_analyze_file_only_comments(tmp_path: pytest.TempPathFactory) -> None:
    p = tmp_path / "comments.py"  # type: ignore[operator]
    content = "# comment 1\n# comment 2\n"
    p.write_text(content, encoding="utf-8")

    stats = analyze_file(str(p))
    assert stats["total"] == 2
    assert stats["code"] == 0
    assert stats["comment"] == 2
    assert stats["blank"] == 0


def test_analyze_path_file(tmp_path: pytest.TempPathFactory) -> None:
    p = tmp_path / "simple.py"  # type: ignore[operator]
    content = "print('hello')"
    p.write_text(content, encoding="utf-8")

    stats = analyze_path(str(p))
    assert stats["total"] == 1
    assert stats["code"] == 1
    assert stats["comment"] == 0
    assert stats["blank"] == 0


def test_analyze_path_directory(tmp_path: pytest.TempPathFactory) -> None:
    # Create a directory structure
    dir1 = tmp_path / "dir1"  # type: ignore[operator]
    dir1.mkdir()

    p1 = dir1 / "file1.py"
    p1.write_text("print('1')\n# comment\n", encoding="utf-8")

    p2 = dir1 / "file2.py"
    p2.write_text("print('2')\n\n", encoding="utf-8")

    p3 = dir1 / "not_python.txt"
    p3.write_text("some text", encoding="utf-8")

    stats = analyze_path(str(dir1))
    assert stats["total"] == 4  # file1: 2 lines, file2: 2 lines
    assert stats["code"] == 2  # print('1') and print('2')
    assert stats["comment"] == 1  # # comment
    assert stats["blank"] == 1  # empty line in file2


def test_analyze_path_nonexistent() -> None:
    with pytest.raises(FileNotFoundError):
        analyze_path("nonexistent_file_or_directory_path_12345")
