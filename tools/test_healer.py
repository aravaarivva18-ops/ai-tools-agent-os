import os
import re
import subprocess
import sys


def run_test_file(test_file_path, timeout=10):
    """
    Запускает тест-файл через pytest в фоновом режиме.
    Возвращает (success, stdout, stderr)
    """
    # Пытаемся найти pytest в локальном .venv проекта
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_pytest = os.path.join(project_root, ".venv", "bin", "pytest")

    cmd = []
    env = os.environ.copy()

    if os.path.exists(venv_pytest):
        cmd = [venv_pytest, "-v", "--tb=short", test_file_path]
    else:
        # Проверяем глобальный pytest
        try:
            subprocess.run(
                ["pytest", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            cmd = ["pytest", "-v", "--tb=short", test_file_path]
        except FileNotFoundError:
            # Если pytest вообще нет, возвращаем ошибку
            return False, "", "Pytest not found in .venv or globally."

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        success = proc.returncode == 0
        return success, stdout, stderr
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return (
            False,
            stdout,
            f"{stderr}\nTIMEOUT: Test execution exceeded {timeout} seconds.",
        )


def parse_pytest_error(stdout_text):
    """
    Парсит лог pytest и извлекает очищенные трейсбеки.
    Возвращает список словарей: [{'test_name': '...', 'message': '...'}]
    """
    errors = []

    # 1. Поиск блока сбоев (FAILURES)
    if "=== FAILURES ===" not in stdout_text and "___" not in stdout_text:
        return errors

    # Парсинг для pytest
    # Находим каждый упавший тест (начинается с ___ test_name ___)
    blocks = re.split(r"___+ (test_\w+) ___+", stdout_text)
    if len(blocks) > 1:
        # blocks[0] - текст до первого сбоя
        # blocks[1] - имя первого теста, blocks[2] - трейсбек первого теста
        for i in range(1, len(blocks), 2):
            test_name = blocks[i]
            traceback = blocks[i + 1]

            # Очищаем трейсбек, оставляя только суть ошибки
            lines = traceback.splitlines()
            clean_lines = []
            capture = False

            for line in lines:
                # Начинаем собирать строки, где происходит сбой (обычно с > или E)
                if line.startswith(">") or line.startswith("E "):
                    capture = True
                # Прекращаем при выходе из блока ошибки
                if line.startswith("===") or line.startswith("___"):
                    break
                if capture:
                    clean_lines.append(line)

            message = "\n".join(clean_lines).strip()
            if not message:
                message = traceback.strip()  # Фолбэк на весь трейсбек

            errors.append({"test_name": test_name, "message": message})

    return errors


if __name__ == "__main__":
    # CLI Интерфейс
    if len(sys.argv) < 2:
        print("Usage: python3 test_healer.py <test_file_path>")
        sys.exit(1)

    test_path = sys.argv[1]
    if not os.path.exists(test_path):
        print(f"Error: File {test_path} not found.")
        sys.exit(1)

    print(f"Running tests in {test_path}...")
    success, stdout, stderr = run_test_file(test_path)

    if success:
        print("Success: All tests passed cleanly.")
        sys.exit(0)
    else:
        print("\n❌ Tests Failed. Generating Clean Traceback for AI:")
        print("=" * 60)
        errors = parse_pytest_error(stdout)
        if errors:
            for err in errors:
                print(f"Target Test: {err['test_name']}")
                print(f"Traceback Summary:\n{err['message']}")
                print("-" * 60)
        else:
            # Если не распарсилось, выводим сырой вывод
            print(stdout)
            print(stderr)
        sys.exit(1)
