import json
import os
import re
import subprocess
import sys
from typing import Any

SoloLoopV10: Any = None
try:
    import core.solo_loop

    SoloLoopV10 = core.solo_loop.SoloLoopV10
except ImportError:
    try:
        import tools.core.solo_loop

        SoloLoopV10 = tools.core.solo_loop.SoloLoopV10
    except ImportError:
        pass

log_change: Any = None
try:
    import tools.dashboard_logger

    log_change = tools.dashboard_logger.log_change
except ImportError:
    try:
        import dashboard_logger

        log_change = dashboard_logger.log_change
    except ImportError:
        pass

parse_blocks: Any = None
apply_blocks: Any = None
try:
    import tools.diff_applier

    parse_blocks = tools.diff_applier.parse_blocks
    apply_blocks = tools.diff_applier.apply_blocks
except ImportError:
    try:
        import diff_applier

        parse_blocks = diff_applier.parse_blocks
        apply_blocks = diff_applier.apply_blocks
    except ImportError:
        pass


def apply_patch_file(target_file, patch_file_or_text):
    """
    Applies a SEARCH/REPLACE patch to target_file using diff_applier (diff-only).
    Returns: (success, error_message)
    """
    if not parse_blocks or not apply_blocks:
        return False, "diff_applier module not found or import failed."

    if not os.path.exists(target_file):
        return False, f"Target file {target_file} not found."

    # Read target content
    with open(target_file, encoding="utf-8") as f:
        content = f.read()

    # Read patch
    if os.path.exists(patch_file_or_text):
        with open(patch_file_or_text, encoding="utf-8") as f:
            patch_text = f.read()
    else:
        patch_text = patch_file_or_text

    blocks = parse_blocks(patch_text)
    if not blocks:
        return False, "No SEARCH/REPLACE blocks found in patch."

    success, new_content, err_msg = apply_blocks(content, blocks)
    if not success:
        return False, f"Patch apply failed: {err_msg}"

    # Backup
    backup_path = target_file + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Write changes
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Verify AST
    if target_file.endswith(".py"):
        try:
            import ast

            ast.parse(new_content)
            return True, None
        except Exception as e:
            # Restore backup
            os.replace(backup_path, target_file)
            return False, f"AST verification failed: {e}"
    else:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return True, None


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
        re.IGNORECASE,
    )

    # We filter out lines indicating files inside library directories
    skip_next = False
    for line in lines:
        if 'File "' in line:
            if library_noise.search(line):
                skip_next = True
                continue
            else:
                skip_next = False
        elif (
            line.strip()
            and not line.startswith(" ")
            and not line.startswith("E ")
            and not line.startswith(">")
        ):
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
    errors: list[dict[str, Any]] = []

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


def detect_tests_from_diff(root_path) -> list:
    """Автоматически определяет список тест-файлов на основе git diff."""
    import subprocess
    from pathlib import Path

    root_dir = Path(root_path).resolve()
    changed_files = []

    try:
        # Получаем измененные файлы (рабочая копия + индекс)
        output = subprocess.check_output(
            ["git", "diff", "--name-only"], cwd=str(root_dir)
        ).decode("utf-8")
        changed_files.extend(output.splitlines())

        output_cached = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"], cwd=str(root_dir)
        ).decode("utf-8")
        changed_files.extend(output_cached.splitlines())
    except Exception as e:
        print(f"Error checking git diff: {e}", file=sys.stderr)
        return []

    # Уникальные файлы в виде путей
    unique_changed = sorted({f.strip() for f in changed_files if f.strip()})

    test_files = set()
    tests_dir = root_dir / "tools" / "tests"

    for rel_path in unique_changed:
        abs_path = root_dir / rel_path
        file_name = abs_path.name

        # 1. Если это сам тест (лежит в папке tests)
        if (
            file_name.startswith("test_")
            and file_name.endswith(".py")
            and "tests" in rel_path
        ):
            if abs_path.exists():
                test_files.add(str(abs_path))
            continue

        # 2. Если это обычный питоновский файл
        if file_name.endswith(".py"):
            base_name = file_name[:-3]  # без .py
            # Ищем тест с соответствующим именем
            candidate_test = tests_dir / f"test_{base_name}.py"
            if candidate_test.exists():
                test_files.add(str(candidate_test))

            # Сканируем всю папку тестов на предмет импорта этого модуля
            if tests_dir.exists():
                for test_file in tests_dir.glob("test_*.py"):
                    try:
                        content = test_file.read_text(encoding="utf-8")
                        # Простой поиск по ключевому слову/импорту
                        if base_name in content:
                            test_files.add(str(test_file))
                    except Exception:
                        pass

    return sorted(test_files)


if __name__ == "__main__":
    import argparse

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    loop = SoloLoopV10(project_root) if SoloLoopV10 else None

    parser = argparse.ArgumentParser(
        description="Test Healer CLI Tool with Sandbox Hardening"
    )
    parser.add_argument("test_file", nargs="?", help="Path to test file to execute")
    parser.add_argument(
        "--target", help="Target source file to patch before running tests"
    )
    parser.add_argument(
        "--patch", help="SEARCH/REPLACE patch file path or direct patch text"
    )
    parser.add_argument(
        "--timeout", type=int, default=10, help="Test execution timeout in seconds"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Auto-detect and run tests for modified files based on git diff",
    )

    args = parser.parse_args()

    # Case 1: Sandbox Patch & Verify
    if args.target and args.patch:
        if not args.test_file:
            print("Error: test_file must be specified when using --target and --patch")
            sys.exit(1)

        print(f"Applying patch to {args.target}...")
        if log_change:
            log_change(
                "Self-Healing",
                f"Attempting to patch {args.target} for test {args.test_file}",
            )

        # Check target existence
        if not os.path.exists(args.target):
            print(f"Error: Target file {args.target} not found.")
            sys.exit(1)

        # Apply patch with automatic backup and AST check
        patched_ok, patch_err = apply_patch_file(args.target, args.patch)
        if not patched_ok:
            print(f"❌ Patch application failed: {patch_err}")
            if log_change:
                log_change(
                    "Self-Healing", f"Patch failed for {args.target}: {patch_err}"
                )
            sys.exit(1)

        print(
            f"Running tests in {args.test_file} to verify patch (timeout={args.timeout}s)..."
        )
        success, stdout, stderr = run_test_file(args.test_file, timeout=args.timeout)

        # Track execution in Solo Loop
        if loop:
            track_res = loop.track_execution(
                args.test_file, success, stdout + "\n" + stderr
            )
            if track_res["stealth_stop"]:
                print(track_res["compressed_output"])
                # Rollback patch on Stealth Stop
                backup_path = args.target + ".bak"
                if os.path.exists(backup_path):
                    os.replace(backup_path, args.target)
                sys.exit(3)
            output_to_parse = track_res["compressed_output"]
        else:
            output_to_parse = stdout

        if success:
            print(
                f"✅ Success! Patch resolved the issue. Changes kept in {args.target}."
            )
            if log_change:
                log_change(
                    "Self-Healing", f"Successfully healed {args.target} via patch"
                )
            # Remove backup on success
            backup_path = args.target + ".bak"
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except Exception:
                    pass
            sys.exit(0)
        else:
            print("❌ Tests still failing after patch. Rolling back changes...")
            # Restore backup
            backup_path = args.target + ".bak"
            if os.path.exists(backup_path):
                os.replace(backup_path, args.target)

            if log_change:
                log_change(
                    "Self-Healing",
                    f"Patch failed to fix {args.target} (tests still failing)",
                )

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

    # Case 2: Process auto-heal queue OR git diff detection
    if not args.test_file or args.diff:
        from pathlib import Path

        candidates = []
        source_label = "queue"

        # 1. Если явно запрошен --diff
        if args.diff:
            candidates = detect_tests_from_diff(project_root)
            source_label = "git diff auto-detect"
        else:
            queue_path = Path(project_root) / "vault" / "auto_heal_queue.json"
            if queue_path.exists():
                try:
                    with open(queue_path, encoding="utf-8") as f:
                        data = json.load(f)
                    candidates = data.get("heal_candidates", [])
                except Exception as e:
                    print(f"Error reading auto-heal queue: {e}")

            # Фолбэк на git diff, если очередь пустая
            if not candidates:
                candidates = detect_tests_from_diff(project_root)
                source_label = "git diff auto-detect (fallback)"

        if candidates:
            print(f"Found {len(candidates)} test candidates via {source_label}.")
            all_success = True
            for cand in candidates:
                # Resolve path relative to project root
                cand_path = Path(cand)
                if not cand_path.is_absolute():
                    cand_path = Path(project_root) / cand

                if cand_path.exists():
                    print(f"\nRunning candidate tests: {cand}")

                    success, stdout, stderr = run_test_file(
                        str(cand_path), timeout=args.timeout
                    )

                    # Track execution in Solo Loop
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
                        if log_change:
                            log_change(
                                "Self-Healing",
                                f"Failed test candidate: {cand}",
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
                    print(f"Warning: Candidate file {cand} not found at {cand_path}")
            sys.exit(0 if all_success else 1)
        else:
            print(
                "Usage: python3 test_healer.py <test_file_path> [--target <target_file> --patch <patch_file>]\n"
                "Or run with --diff to auto-detect tests based on modified files."
            )
            sys.exit(1)

    # Case 3: Diagnostics for a single test file
    test_path = args.test_file
    if not os.path.exists(test_path):
        print(f"Error: File {test_path} not found.")
        sys.exit(1)

    print(f"Running tests in {test_path}...")

    success, stdout, stderr = run_test_file(test_path, timeout=args.timeout)

    # Track execution in Solo Loop
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
        if log_change:
            log_change("Self-Healing", f"Tests failed for: {test_path}")
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
