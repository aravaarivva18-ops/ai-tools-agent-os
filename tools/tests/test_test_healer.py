import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from tools.test_healer import apply_patch_file, detect_tests_from_diff, run_test_file


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    db_path = Path(path)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            billing_type TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            vat_type TEXT,
            vat_rate REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            reason TEXT,
            expected_effect TEXT
        )
    """)
    conn.commit()
    conn.close()

    yield db_path

    os.close(fd)
    if db_path.exists():
        db_path.unlink()
    os.environ.pop("DATABASE_URL", None)


def test_apply_patch_file_success():
    fd, path = tempfile.mkstemp(suffix=".py", dir="/Users/rus/ai-tools/tools/tests")
    target_path = Path(path)
    target_path.write_text("def my_func():\n    return 41\n", encoding="utf-8")

    patch = """<<<<<<< SEARCH
def my_func():
    return 41
=======
def my_func():
    return 42
>>>>>>> REPLACE"""

    success, err = apply_patch_file(str(target_path), patch)
    assert success is True
    assert err is None
    assert "return 42" in target_path.read_text(encoding="utf-8")

    os.close(fd)
    if target_path.exists():
        target_path.unlink()


def test_apply_patch_file_invalid_ast():
    fd, path = tempfile.mkstemp(suffix=".py", dir="/Users/rus/ai-tools/tools/tests")
    target_path = Path(path)
    target_path.write_text("def my_func():\n    return 41\n", encoding="utf-8")

    patch = """<<<<<<< SEARCH
def my_func():
    return 41
=======
def my_func():
    return 42 invalid_syntax
>>>>>>> REPLACE"""

    success, err = apply_patch_file(str(target_path), patch)
    assert success is False
    assert "AST verification failed" in err
    assert "return 41" in target_path.read_text(encoding="utf-8")

    os.close(fd)
    if target_path.exists():
        target_path.unlink()


def test_healer_timeout_handling():
    # Verify that run_test_file exits with timeout handling on slow execution
    fd, path = tempfile.mkstemp(suffix=".py", dir="/Users/rus/ai-tools/tools/tests")
    test_path = Path(path)
    # Write a test that sleeps for 2 seconds
    test_path.write_text(
        "import time\ndef test_slow():\n    time.sleep(2)\n", encoding="utf-8"
    )

    success, stdout, stderr = run_test_file(str(test_path), timeout=1)
    assert success is False
    assert "TIMEOUT" in stderr or "TIMEOUT" in stdout

    os.close(fd)
    if test_path.exists():
        test_path.unlink()


def test_detect_tests_from_diff(monkeypatch):
    # Mock subprocess.check_output to return specific changed files
    def mock_check_output(cmd, *args, **kwargs):
        return b"tools/rules_validator.py\ntools/tests/test_healer.py\n"

    import subprocess

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    # We also mock os.path.exists to return True for files we check
    orig_exists = os.path.exists

    def mock_exists(path):
        p_str = str(path)
        if "test_rules_validator.py" in p_str or "test_healer.py" in p_str:
            return True
        return orig_exists(path)

    monkeypatch.setattr(os.path, "exists", mock_exists)

    # Mock open inside detect_tests_from_diff if it scans files
    # (or we can just let it search directory and return test_rules_validator.py because it exists)
    tests = detect_tests_from_diff(Path("/Users/rus/ai-tools"))

    assert any("test_rules_validator.py" in str(t) for t in tests)
    assert any("test_healer.py" in str(t) for t in tests)


def test_healer_cli_batching(tmp_path):
    t1 = tmp_path / "test_a.py"
    t1.write_text("def test_a(): assert True", encoding="utf-8")

    t2 = tmp_path / "test_b.py"
    t2.write_text("def test_b(): assert True", encoding="utf-8")

    import subprocess
    import sys

    healer_script = Path(__file__).parent.parent / "test_healer.py"

    res = subprocess.run(
        [sys.executable, str(healer_script), f"{t1},{t2}"],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0
    assert "Running tests in" in res.stdout
    assert "Success: All tests passed cleanly." in res.stdout


def test_healer_cli_batching_failure(tmp_path):
    t1 = tmp_path / "test_a.py"
    t1.write_text("def test_a(): assert True", encoding="utf-8")

    t2 = tmp_path / "test_b.py"
    t2.write_text("def test_b(): assert False", encoding="utf-8")

    import subprocess
    import sys

    healer_script = Path(__file__).parent.parent / "test_healer.py"

    res = subprocess.run(
        [sys.executable, str(healer_script), f"{t1},{t2}"],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 1
    assert "❌ Tests Failed" in res.stdout


def test_compress_traceback_large():
    from tools.test_healer import compress_traceback

    # Создаем длинный текст (>100 строк)
    long_tb = "\n".join([f"Line {i}" for i in range(1, 150)])

    # Удалим старый лог, если он был
    log_path = Path("/Users/rus/ai-tools/scratch/last_test_run.log")
    if log_path.exists():
        log_path.unlink()

    compressed = compress_traceback(long_tb)

    # Проверяем, что лог был обрезан и содержит сообщение со ссылкой на файл
    assert "ОБРЕЗАНО" in compressed
    assert "last_test_run.log" in compressed

    # Проверяем, что файл лога действительно записался
    assert log_path.exists()
    assert "Line 1" in log_path.read_text(encoding="utf-8")


def test_loop_detection_trigger():
    import pytest

    from tools.test_healer import check_loop_detection

    history_file = Path("/Users/rus/ai-tools/scratch/healer_run_history.json")
    if history_file.exists():
        history_file.unlink()

    # Первый запуск с ошибкой
    check_loop_detection("test_x.py", "AssertionError: 42 != 43")
    assert history_file.exists()

    # Второй запуск с той же ошибкой
    check_loop_detection("test_x.py", "AssertionError: 42 != 43")

    # Третий запуск должен возбудить SystemExit с кодом 3 (Stealth Stop)
    with pytest.raises(SystemExit) as excinfo:
        check_loop_detection("test_x.py", "AssertionError: 42 != 43")

    assert excinfo.value.code == 3


def test_run_test_file_syntax_validation():
    """Тестирует быструю синтаксическую пред-проверку в run_test_file."""
    fd1, path1 = tempfile.mkstemp(suffix=".py", dir="/Users/rus/ai-tools/tools/tests")
    fd2, path2 = tempfile.mkstemp(suffix=".py", dir="/Users/rus/ai-tools/tools/tests")
    test_file = Path(path1)
    target_file = Path(path2)

    try:
        # 1. Запишем битый Python код в target_file
        target_file.write_text("def broken_syntax(:\n    pass\n", encoding="utf-8")
        test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")

        success, stdout, stderr = run_test_file(str(test_file), target_file_path=str(target_file))

        # Ожидаем, что статический валидатор отклонит запуск из-за Syntax Error
        assert success is False
        assert "STATIC VALIDATION ERROR" in stderr or "STATIC VALIDATION ERROR" in stdout
        assert "Syntax / AST error" in stderr or "Syntax / AST error" in stdout
        assert os.path.basename(path2) in stderr or os.path.basename(path2) in stdout

    finally:
        os.close(fd1)
        os.close(fd2)
        if test_file.exists():
            test_file.unlink()
        if target_file.exists():
            target_file.unlink()

