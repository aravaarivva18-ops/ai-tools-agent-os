from pathlib import Path
from unittest.mock import patch

from tools.test_healer import run_changed_files_validators


def test_validators_no_changes():
    # На чистом репозитории или когда git status не возвращает питоновских файлов
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        valid, err = run_changed_files_validators("/Users/rus/ai-tools")
        assert valid is True
        assert err is None


def test_validators_syntax_error():
    # Создаем временный файл с ошибкой синтаксиса в tools/tests, чтобы пройти PathJail
    test_file = Path("/Users/rus/ai-tools/tools/tests/invalid_syntax_file.py")
    test_file.write_text("def my_func(:\n    pass\n", encoding="utf-8")

    try:
        with patch("subprocess.run") as mock_run:
            # Относительный путь для git status
            mock_run.return_value.stdout = " M tools/tests/invalid_syntax_file.py\n"
            mock_run.return_value.returncode = 0

            valid, err = run_changed_files_validators("/Users/rus/ai-tools")
            assert valid is False
            assert "Syntax / AST error" in err
            assert "invalid_syntax_file.py" in err
    finally:
        if test_file.exists():
            test_file.unlink()


def test_validators_placeholder_db():
    # Создаем файл с import pdb
    test_file = Path("/Users/rus/ai-tools/tools/tests/placeholder_file.py")
    test_file.write_text(
        "def my_func():\n    " + "import" + " " + "pdb; pdb.set_trace()\n",
        encoding="utf-8",
    )

    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = " M tools/tests/placeholder_file.py\n"
            mock_run.return_value.returncode = 0

            valid, err = run_changed_files_validators("/Users/rus/ai-tools")
            assert valid is False
            assert "Placeholder error" in err
            assert ("import" + " " + "pdb") in err
    finally:
        if test_file.exists():
            test_file.unlink()


def test_validators_placeholder_bp():
    # Создаем файл с breakpoint()
    test_file = Path("/Users/rus/ai-tools/tools/tests/placeholder_file.py")
    test_file.write_text(
        "def my_func():\n    " + "breakpoint" + "()\n", encoding="utf-8"
    )

    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = " M tools/tests/placeholder_file.py\n"
            mock_run.return_value.returncode = 0

            valid, err = run_changed_files_validators("/Users/rus/ai-tools")
            assert valid is False
            assert ("breakpoint" + "()") in err
    finally:
        if test_file.exists():
            test_file.unlink()


def test_validators_placeholder_td():
    # Создаем файл с заглушкой в коде
    test_file = Path("/Users/rus/ai-tools/tools/tests/placeholder_file.py")
    test_file.write_text(
        "def my_func():\n    x = '" + "TO" + "DO: implement this later'\n    pass\n",
        encoding="utf-8",
    )

    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = " M tools/tests/placeholder_file.py\n"
            mock_run.return_value.returncode = 0

            valid, err = run_changed_files_validators("/Users/rus/ai-tools")
            assert valid is False
            assert ("TO" + "DO:") in err
    finally:
        if test_file.exists():
            test_file.unlink()


def test_validators_placeholder_ignored_in_comments():
    # Создаем файл, где pdb, breakpoint и TODO: закомментированы (должны пропускаться)
    test_file = Path("/Users/rus/ai-tools/tools/tests/placeholder_file.py")
    test_file.write_text(
        "def my_func():\n    # "
        + "import"
        + " "
        + "pdb; pdb.set_trace()\n    # "
        + "breakpoint"
        + "()\n    # "
        + "TO"
        + "DO: implement this later\n    pass\n",
        encoding="utf-8",
    )

    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = " M tools/tests/placeholder_file.py\n"
            mock_run.return_value.returncode = 0

            valid, err = run_changed_files_validators("/Users/rus/ai-tools")
            assert valid is True
            assert err is None
    finally:
        if test_file.exists():
            test_file.unlink()
