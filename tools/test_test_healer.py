import os
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_healer import parse_pytest_error, run_test_file


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


if __name__ == "__main__":
    unittest.main()
