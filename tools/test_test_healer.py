import os
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_healer import compress_traceback, parse_pytest_error, run_test_file


class TestTestHealer(unittest.TestCase):
    def test_run_passing_test(self):
        # Создаем временный файл с успешным тестом
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def test_ok(): assert True")
            temp_path = f.name

        try:
            success, _stdout, _stderr = run_test_file(temp_path, timeout=5)
            assert success
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_run_failing_test_and_parse(self):
        # Создаем временный файл с падающим тестом
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def test_fail(): assert 1 == 2")
            temp_path = f.name

        try:
            success, stdout, _stderr = run_test_file(temp_path, timeout=5)
            assert not success

            # Парсим ошибку
            errors = parse_pytest_error(stdout)
            assert len(errors) == 1
            assert "test_fail" in errors[0]["test_name"]
            assert "assert 1 == 2" in errors[0]["message"]
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_timeout_handling(self):
        # Создаем временный файл с зависающим тестом
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("import time\ndef test_sleep(): time.sleep(10)")
            temp_path = f.name

        try:
            success, _stdout, stderr = run_test_file(temp_path, timeout=1)
            assert not success
            assert "TIMEOUT" in stderr
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_compress_traceback_positive(self):
        """Positive test: Verifies that library-specific noise is removed from tracebacks."""
        raw_tb = (
            "Traceback (most recent call last):\n"
            '  File "/opt/homebrew/lib/python3.14/unittest/case.py", line 500, in run\n'
            "    self._callTestMethod(testMethod)\n"
            '  File "tools/tests/test_demo.py", line 12, in test_fail\n'
            "    assert 1 == 2\n"
            '  File "/Users/rus/ai-tools/.venv/lib/python3.14/site-packages/pytest/__init__.py", line 42, in check\n'
            "    raise AssertionError()\n"
        )
        compressed = compress_traceback(raw_tb)
        # Should retain project files, and strip library files
        assert "tools/tests/test_demo.py" in compressed
        assert "unittest/case.py" not in compressed
        assert "pytest/__init__.py" not in compressed

    def test_compress_traceback_negative(self):
        """Negative test: Verifies that a clean traceback without library noise is returned unchanged."""
        raw_tb = (
            '  File "tools/tests/test_demo.py", line 12, in test_fail\n'
            "    assert 1 == 2\n"
        )
        compressed = compress_traceback(raw_tb)
        assert compressed.strip() == raw_tb.strip()


if __name__ == "__main__":
    unittest.main()
