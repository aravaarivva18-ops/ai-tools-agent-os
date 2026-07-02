import os
import sys
import unittest
from pathlib import Path

# Добавляем пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_scanner import verify_code_safety


class TestSecurityScanner(unittest.TestCase):
    def setUp(self):
        self.workspace_root = Path("test_workspace").resolve()
        self.workspace_root.mkdir(exist_ok=True)
        self.safe_file = self.workspace_root / "safe.py"
        self.unsafe_file = self.workspace_root / "test_unsafe.py"

    def tearDown(self):
        for f in (self.safe_file, self.unsafe_file):
            if f.exists():
                os.remove(f)
        if self.workspace_root.exists():
            os.rmdir(self.workspace_root)

    def test_safe_code(self):
        """Проверяет прохождение валидации для безопасного кода."""
        code = """
def calculate(a, b):
    return a + b
"""
        with open(self.safe_file, "w") as f:
            f.write(code)

        is_safe, reason = verify_code_safety(str(self.safe_file), self.workspace_root)
        assert is_safe
        assert reason is None

    def test_scan_for_forbidden_imports(self):
        """Проверяет блокировку запрещенных сетевых импортов в тестах."""
        code = """
import requests
def test_network():
    requests.get('https://example.com')
"""
        with open(self.unsafe_file, "w") as f:
            f.write(code)

        is_safe, reason = verify_code_safety(str(self.unsafe_file), self.workspace_root)
        assert not (is_safe)
        assert "Запрещен импорт сетевой библиотеки 'requests'" in reason

    def test_scan_for_system_calls(self):
        """Проверяет блокировку os.system в тестах."""
        code = """
import os
def test_cmd():
    os.system('rm -rf /')
"""
        with open(self.unsafe_file, "w") as f:
            f.write(code)

        is_safe, reason = verify_code_safety(str(self.unsafe_file), self.workspace_root)
        assert not (is_safe)
        assert "Обнаружен запрещенный системный вызов 'os.system'" in reason

    def test_scan_for_unsafe_rmtree(self):
        """Проверяет блокировку shutil.rmtree вне воркспейса."""
        code = """
import shutil
def test_cleanup():
    shutil.rmtree('/etc')
"""
        with open(self.unsafe_file, "w") as f:
            f.write(code)

        is_safe, reason = verify_code_safety(str(self.unsafe_file), self.workspace_root)
        assert not (is_safe)
        assert "Попытка удаления/перемещения файла за пределами воркспейса" in reason


if __name__ == "__main__":
    unittest.main()
