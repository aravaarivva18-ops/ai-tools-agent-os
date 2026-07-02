import shutil
from pathlib import Path

import pytest

from tools.repo_mapper import generate_map, write_repo_map

TEST_WORKSPACE = Path(__file__).resolve().parents[2] / "vault" / "tmp_repo_test"


@pytest.fixture(autouse=True)
def setup_teardown_workspace():
    """Sets up a clean test workspace directory and removes it after test runs."""
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)


def test_repo_mapper_parsing():
    """Проверяет правильность AST-парсинга сигнатур классов, методов и функций."""
    core_dir = TEST_WORKSPACE / "core"
    core_dir.mkdir(parents=True, exist_ok=True)

    test_code = '''"""Module docstring."""

def top_function(x, y, *, key=None):
    """Function docstring."""
    pass

class MyClass:
    """Class docstring."""
    def my_method(self, a, b, *args, **kwargs):
        """Method docstring."""
        pass
'''
    (core_dir / "my_module.py").write_text(test_code, encoding="utf-8")

    # Генерируем карту
    repo_map = generate_map(TEST_WORKSPACE)

    # Проверяем наличие всех ключевых элементов
    assert "File: core/my_module.py" in repo_map
    assert "# Module docstring." in repo_map
    assert "def top_function(x, y, *, key)" in repo_map
    assert "# Function docstring." in repo_map
    assert "class MyClass:" in repo_map
    assert "# Class docstring." in repo_map
    assert "def my_method(a, b, *args, **kwargs)" in repo_map
    assert "# Method docstring." in repo_map


def test_write_repo_map():
    """Проверяет запись сгенерированной карты в vault/repo_map.txt."""
    core_dir = TEST_WORKSPACE / "core"
    core_dir.mkdir(parents=True, exist_ok=True)
    (core_dir / "my_module.py").write_text("def run(): pass", encoding="utf-8")

    write_repo_map(TEST_WORKSPACE)

    out_file = TEST_WORKSPACE / "vault" / "repo_map.txt"
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "my_module.py" in content
    assert "def run()" in content
