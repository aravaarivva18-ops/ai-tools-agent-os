import json
import os
import re
import subprocess
import sys

try:
    from core.solo_loop import SoloLoopV10
except ImportError:
    try:
        from tools.core.solo_loop import SoloLoopV10
    except ImportError:
        SoloLoopV10 = None


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


def compress_traceback(tb_text):
    """
    Removes traceback noise from external libraries (pytest, unittest, python site-packages)
    and retains only frames from our workspace files.
    """
    if not tb_text:
        return ""
    lines = tb_text.splitlines()
    clean_lines = []

    library_noise = re.compile(
        r"(/unittest/|/pytest/|site-packages|/importlib/|python3\.\d+|/opt/homebrew/)",
        re.IGNORECASE
    )

    # We filter out lines indicating files inside library directories
    skip_next = False
    for line in lines:
        if "File \"" in line:
            if library_noise.search(line):
                skip_next = True
                continue
            else:
                skip_next = False
        elif line.strip() and not line.startswith(" ") and not line.startswith("E ") and not line.startswith(">"):
            # Not a code indent, likely part of python traceback framework
            pass

        if skip_next and line.startswith("    "):
            # Skip code frames associated with excluded library files
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


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

            message = compress_traceback(message)
            errors.append({"test_name": test_name, "message": message})

    return errors


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    loop = SoloLoopV10(project_root) if SoloLoopV10 else None

    # CLI Интерфейс
    if len(sys.argv) < 2:
        from pathlib import Path

        # Пытаемся прочитать из очереди авто-исцеления
        queue_path = Path(project_root) / "vault" / "auto_heal_queue.json"
        if queue_path.exists():
            try:
                with open(queue_path, encoding="utf-8") as f:
                    data = json.load(f)
                candidates = data.get("heal_candidates", [])
                if candidates:
                    print(
                        f"Found {len(candidates)} heal candidates in auto-heal queue."
                    )
                    all_success = True
                    for cand in candidates:
                        # Разрешаем путь относительно корня
                        cand_path = Path(cand)
                        if not cand_path.is_absolute():
                            cand_path = Path(project_root) / cand

                        if cand_path.exists():
                            print(f"\nHealing candidate: {cand}")
                            success, stdout, stderr = run_test_file(str(cand_path))

                            # Отслеживаем выполнение в Solo Loop
                            if loop:
                                track_res = loop.track_execution(
                                    str(cand_path), success, stdout + "\n" + stderr
                                )
                                if track_res["stealth_stop"]:
                                    print(track_res["compressed_output"])
                                    sys.exit(3)
                                output_to_parse = track_res["compressed_output"]
                            else:
                                output_to_parse = stdout

                            if success:
                                print(f"✅ Success: Tests in {cand} passed cleanly.")
                            else:
                                print(
                                    f"❌ Tests Failed in {cand}. Generating Clean Traceback for AI:"
                                )
                                print("=" * 60)
                                errors = parse_pytest_error(output_to_parse)
                                if errors:
                                    for err in errors:
                                        print(f"Target Test: {err['test_name']}")
                                        print(f"Traceback Summary:\n{err['message']}")
                                        print("-" * 60)
                                else:
                                    print(output_to_parse)
                                all_success = False
                        else:
                            print(
                                f"Warning: Candidate file {cand} not found at {cand_path}"
                            )
                    sys.exit(0 if all_success else 1)
            except Exception as e:
                print(f"Error reading auto-heal queue: {e}")

        print("Usage: python3 test_healer.py <test_file_path>")
        sys.exit(1)

    test_path = sys.argv[1]
    if not os.path.exists(test_path):
        print(f"Error: File {test_path} not found.")
        sys.exit(1)

    print(f"Running tests in {test_path}...")
    success, stdout, stderr = run_test_file(test_path)

    # Отслеживаем выполнение в Solo Loop
    if loop:
        track_res = loop.track_execution(test_path, success, stdout + "\n" + stderr)
        if track_res["stealth_stop"]:
            print(track_res["compressed_output"])
            sys.exit(3)
        output_to_parse = track_res["compressed_output"]
    else:
        output_to_parse = stdout

    if success:
        print("Success: All tests passed cleanly.")
        sys.exit(0)
    else:
        print("\n❌ Tests Failed. Generating Clean Traceback for AI:")
        print("=" * 60)
        errors = parse_pytest_error(output_to_parse)
        if errors:
            for err in errors:
                print(f"Target Test: {err['test_name']}")
                print(f"Traceback Summary:\n{err['message']}")
                print("-" * 60)
        else:
            print(output_to_parse)
        sys.exit(1)
