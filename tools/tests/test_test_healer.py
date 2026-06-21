import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from tools.tests.test_healer import apply_patch_file, run_test_file


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
    fd, path = tempfile.mkstemp(suffix=".py")
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
    fd, path = tempfile.mkstemp(suffix=".py")
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
    fd, path = tempfile.mkstemp(suffix=".py")
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
