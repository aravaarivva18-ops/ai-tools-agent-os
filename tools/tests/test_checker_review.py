from pathlib import Path

from tools.checker_review import CheckerReview


def test_checker_review_patch_success():
    checker = CheckerReview()

    # Корректный патч
    patch = """<<<<<<< SEARCH
def hello():
    return "hello"
=======
def hello():
    return "hello world"
>>>>>>> REPLACE"""

    ok, err = checker.review_patch("some_file.py", patch)
    assert ok is True
    assert err is None


def test_checker_review_patch_stop_slop():
    checker = CheckerReview()

    # Патч с английским ИИ-маркером (del + ve)
    marker_en = "del" + "ve"
    patch_en = f"""<<<<<<< SEARCH
def hello():
    pass
=======
def hello():
    # Let's {marker_en} into this function
    pass
>>>>>>> REPLACE"""

    ok, err = checker.review_patch("some_file.py", patch_en)
    assert ok is False
    assert "Stop-Slop" in err
    assert marker_en in err

    # Патч с русским ИИ-маркером (гейм- + чейнджер)
    marker_ru = "гейм-" + "чейнджер"
    patch_ru = f"""<<<<<<< SEARCH
def hello():
    pass
=======
def hello():
    # Это настоящий {marker_ru} для проекта
    pass
>>>>>>> REPLACE"""

    ok, err = checker.review_patch("some_file.py", patch_ru)
    assert ok is False
    assert "Stop-Slop" in err
    assert marker_ru in err


def test_checker_review_patch_link_formatting():
    checker = CheckerReview()

    # Ссылки с бэктиками
    link = "[`my_file.py`](file://" + "/path)"
    patch = f"""<<<<<<< SEARCH
def hello():
    pass
=======
def hello():
    # See details in {link}
    pass
>>>>>>> REPLACE"""

    ok, err = checker.review_patch("some_file.py", patch)
    assert ok is False
    assert "Link Formatting" in err


def test_checker_review_patch_yagni_bloat():
    checker = CheckerReview()

    # REPLACE блок более 150 строк
    large_replace = "\n".join([f"    x_{i} = {i}" for i in range(160)])
    patch = f"""<<<<<<< SEARCH
def hello():
    pass
=======
def hello():
{large_replace}
>>>>>>> REPLACE"""

    ok, err = checker.review_patch("some_file.py", patch)
    assert ok is False
    assert "YAGNI Bloat" in err


def test_checker_review_file_audit():
    # Создаем временную директорию внутри tools/tests, чтобы пройти PathJail
    tmp_dir = Path("/Users/rus/ai-tools/tools/tests/tmp_review_dir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    test_file = tmp_dir / "audit_file.py"
    checker = CheckerReview(workspace_root=tmp_dir)

    try:
        # 1. Корректный файл
        test_file.write_text("def hello():\n    pass\n", encoding="utf-8")
        ok, warnings = checker.review_file(str(test_file))
        assert ok is True
        assert len(warnings) == 0

        # 2. Файл с нарушениями (Stop-Slop и бэктики)
        marker_en = "del" + "ve"
        link = "[`my_file.py`](file://" + "/path)"
        test_file.write_text(
            f"# Let's {marker_en} here\n# Link: {link}\n", encoding="utf-8"
        )

        ok, warnings = checker.review_file(str(test_file))
        assert ok is False
        assert len(warnings) == 2
        assert any("Stop-Slop" in w for w in warnings)
        assert any("Link Formatting" in w for w in warnings)

    finally:
        if test_file.exists():
            test_file.unlink()
        if tmp_dir.exists():
            tmp_dir.rmdir()
