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

apply_patch_file: Any = None
try:
    import tools.diff_applier

    apply_patch_file = tools.diff_applier.apply_patch_file
except ImportError:
    try:
        import diff_applier

        apply_patch_file = diff_applier.apply_patch_file
    except ImportError:
        pass

log_healer_event: Any = None
try:
    import tools.dashboard_logger

    log_healer_event = tools.dashboard_logger.log_healer_event
except ImportError:
    try:
        import dashboard_logger

        log_healer_event = dashboard_logger.log_healer_event
    except ImportError:
        pass


def run_ruff_autofix(project_root: str, explicit_files: list[str] = None) -> None:
    """Запускает ruff check --fix и ruff format для автоматического исправления стиля."""
    import shutil

    ruff_path = os.path.join(project_root, ".venv", "bin", "ruff")
    if not os.path.exists(ruff_path):
        ruff_path = shutil.which("ruff")
    if not ruff_path:
        return

    targets = []
    if explicit_files:
        targets = [f for f in explicit_files if os.path.exists(f)]

    if not targets:
        # Фолбэк на дефолтные папки
        targets = []
        for folder in ("tools", "dashboard-hand-on-pulse", "youtube-faceless-pipeline"):
            if os.path.exists(os.path.join(project_root, folder)):
                targets.append(folder)

    if not targets:
        return

    try:
        # Исправляем ошибки импортов и стиля
        subprocess.run(
            [ruff_path, "check", "--fix", *targets],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )  # nosec B603
        # Форматируем код
        subprocess.run(
            [ruff_path, "format", *targets],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )  # nosec B603
    except Exception:
        pass


def run_changed_files_validators(
    project_root: str, explicit_files: list[str] = None
) -> tuple[bool, str | None]:
    """
    Выявляет измененные файлы через git status и запускает легковесные статические проверки
    (синтаксическая корректность, отсутствие отладочных placeholders, YAGNI соответствие).
    """
    import ast

    changed_files = []
    if explicit_files:
        changed_files = [
            f for f in explicit_files if os.path.exists(f) and f.endswith(".py")
        ]

    # Также пробуем получить измененные файлы из git
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )  # nosec B603
        for line in res.stdout.splitlines():
            if not line.strip():
                continue
            path_str = line[2:].strip()
            full_path = os.path.join(project_root, path_str)
            if path_str.endswith(".py") and os.path.exists(full_path):
                if ".venv" not in path_str and ".git" not in path_str:
                    if full_path not in changed_files:
                        changed_files.append(full_path)
    except Exception:
        pass

    for file_path in changed_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 1. Синтаксический анализ (AST-проверка)
            try:
                ast.parse(content, filename=file_path)
            except SyntaxError as se:
                return (
                    False,
                    f"Syntax / AST error in {os.path.basename(file_path)}: L{se.lineno} {se.msg}",
                )

            # 2. Проверка на отладочные placeholders
            p_pdb = "import" + " " + "pdb"
            p_bp = "breakpoint" + "()"
            p_pr = "print" + "()"
            p_todo = "TO" + "DO:"

            forbidden_patterns = {
                p_pdb: f"Обнаружен отладочный импорт '{p_pdb}'.",
                p_bp: f"Обнаружен отладочный вызов '{p_bp}'.",
                p_pr: f"Обнаружен пустой {p_pr}, используйте логгер.",
                p_todo: f"Обнаружена заглушка {p_todo} доведите код до рабочего состояния.",
            }
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                clean_line = line.strip()
                if clean_line.startswith("#"):
                    continue
                for pat, msg in forbidden_patterns.items():
                    if pat in clean_line:
                        if pat == p_pr and p_pr not in clean_line:
                            continue
                        return (
                            False,
                            f"Placeholder error in {os.path.basename(file_path)}: L{i} — {msg}",
                        )

        except Exception as e:
            return (
                False,
                f"Failed to read/validate file {os.path.basename(file_path)}: {e}",
            )

    return True, None


def run_test_file(test_file_path, target_file_path=None, timeout=10):
    """
    Запускает один тестовый файл через pytest.
    Возвращает (success, stdout, stderr)
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Статическая проверка безопасности кода перед запуском тестов
    verify_code_safety = None
    try:
        from tools import security_scanner

        verify_code_safety = security_scanner.verify_code_safety
    except ImportError:
        try:
            import security_scanner

            verify_code_safety = security_scanner.verify_code_safety
        except ImportError:
            pass

    if verify_code_safety is not None:
        from pathlib import Path

        is_safe, reason = verify_code_safety(test_file_path, Path(project_root))
        if not is_safe:
            return (
                False,
                "",
                f"SECURITY ERROR: Running tests in {test_file_path} was BLOCKED.\nReason: {reason}",
            )

    explicit_files = [test_file_path]
    if target_file_path:
        explicit_files.append(target_file_path)

    # Запуск статических валидаторов по измененным файлам
    valid, err_msg = run_changed_files_validators(project_root, explicit_files)
    if not valid:
        return (
            False,
            "",
            f"STATIC VALIDATION ERROR: Fast validator rejected changes before running tests.\nReason: {err_msg}",
        )

    # Авто-исправление форматирования и импортов перед запуском тестов
    run_ruff_autofix(project_root, explicit_files)

    # Пытаемся найти pytest в локальном .venv проекта
    venv_pytest = os.path.join(project_root, "tools", ".venv", "bin", "pytest")
    if not os.path.exists(venv_pytest):
        venv_pytest = os.path.join(project_root, ".venv", "bin", "pytest")

    cmd = []
    env = os.environ.copy()

    if os.path.exists(venv_pytest):
        cmd = [
            venv_pytest,
            "-v",
            "--tb=short",
            "--disable-socket",
            "--allow-unix-socket",
            test_file_path,
        ]
    else:
        # Проверяем глобальный pytest
        try:
            subprocess.run(
                ["pytest", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            cmd = [
                "pytest",
                "-v",
                "--tb=short",
                "--disable-socket",
                "--allow-unix-socket",
                test_file_path,
            ]
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

    # Интеллектуальное сжатие при превышении 100 строк
    if len(clean_lines) > 100:
        try:
            from pathlib import Path

            scratch_dir = Path("/Users/rus/ai-tools/scratch")
            scratch_dir.mkdir(parents=True, exist_ok=True)
            log_file = scratch_dir / "last_test_run.log"
            log_file.write_text(tb_text, encoding="utf-8")
        except Exception:
            pass

        msg = (
            f"... [ОБРЕЗАНО {len(clean_lines) - 40} СТРОК. "
            f"ПОЛНЫЙ ЛОГ: file:///Users/rus/ai-tools/scratch/last_test_run.log] ..."
        )
        compressed = [*clean_lines[:20], msg, *clean_lines[-20:]]
        return "\n".join(compressed).strip()

    return "\n".join(clean_lines).strip()


def check_loop_detection(test_file: str, error_message: str) -> None:
    """Отслеживает хэши ошибок тестов. Прерывает выполнение при обнаружении цикла."""
    import hashlib
    import json
    from pathlib import Path

    scratch_dir = Path("/Users/rus/ai-tools/scratch")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    history_file = scratch_dir / "healer_run_history.json"

    # Вычисляем хэш ошибки (убираем пробелы)
    clean_err = "".join(error_message.split()).lower()
    err_hash = hashlib.sha256(clean_err.encode("utf-8")).hexdigest()

    history = []
    if history_file.exists():
        try:
            from tools.json_utils import safe_load_json
            history_data = safe_load_json(history_file.read_text(encoding="utf-8"))
            history = history_data if isinstance(history_data, list) else []
        except Exception:
            pass

    # Добавляем новую запись
    history.append({"test_file": test_file, "error_hash": err_hash})

    # Оставляем только последние 5 записей
    history = history[-5:]

    # Сохраняем историю
    try:
        history_file.write_text(json.dumps(history), encoding="utf-8")
    except Exception:
        pass

    # Проверяем на зацикливание: 3 одинаковых подряд
    if len(history) >= 3:
        last_three = history[-3:]
        if all(
            h["test_file"] == test_file and h["error_hash"] == err_hash
            for h in last_three
        ):
            print(
                f"\n❌ LoopDetected: Test '{test_file}' failed with the exact same error 3 times in a row.\n"
                f"Stealth Stop triggered to prevent token burn. Please review your edits manually.",
                file=sys.stderr,
            )
            # Очищаем историю при аварийной остановке
            try:
                history_file.unlink(missing_ok=True)
            except Exception:
                pass
            sys.exit(3)

    # Проверяем общий лимит попыток (бюджет итераций): 5 падений подряд для одного файла
    if len(history) >= 5:
        if all(h["test_file"] == test_file for h in history):
            print(
                f"\n❌ BudgetExhausted: Test '{test_file}' failed 5 times in a row (different errors).\n"
                f"Iteration budget exhausted to prevent token burn. Please review your edits manually.",
                file=sys.stderr,
            )
            # Очищаем историю при аварийной остановке
            try:
                history_file.unlink(missing_ok=True)
            except Exception:
                pass
            sys.exit(3)


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


def resolve_conv_id(arg_id: str | None) -> str:
    if arg_id:
        return arg_id
    import os
    from pathlib import Path

    env_id = os.environ.get("CONVERSATION_ID") or os.environ.get(
        "GEMINI_CONVERSATION_ID"
    )
    if env_id:
        return env_id
    try:
        brain_dir = Path.home() / ".gemini" / "antigravity-cli" / "brain"
        if brain_dir.exists():
            sessions = [d for d in brain_dir.iterdir() if d.is_dir()]
            if sessions:
                sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return sessions[0].name
    except Exception:
        pass
    return "unknown"


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
    parser.add_argument(
        "--conv-id",
        help="Conversation ID текущей сессии для логирования",
    )

    args = parser.parse_args()
    args.conv_id = resolve_conv_id(args.conv_id)

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
            if log_healer_event:
                try:
                    log_healer_event(
                        session_id=args.conv_id,
                        test_file=args.test_file,
                        target_file=args.target,
                        error_category="PatchApplicationError",
                        iterations=1,
                        status="failed",
                        time_saved_min=0,
                    )
                except Exception:
                    pass
            sys.exit(1)

        test_files = [tf.strip() for tf in args.test_file.split(",")]
        for tf in test_files:
            if not os.path.exists(tf):
                print(f"Error: Test file {tf} not found.")
                # Rollback patch if test file is not found
                backup_path = args.target + ".bak"
                if os.path.exists(backup_path):
                    os.replace(backup_path, args.target)
                sys.exit(1)

        print(
            f"Running tests in {', '.join(test_files)} to verify patch (timeout={args.timeout}s)..."
        )
        all_success = True
        outputs_to_parse = []

        for tf in test_files:
            success, stdout, stderr = run_test_file(
                tf, target_file_path=args.target, timeout=args.timeout
            )

            # Track execution in Solo Loop
            if loop:
                track_res = loop.track_execution(tf, success, stdout + "\n" + stderr)
                if track_res["stealth_stop"]:
                    print(track_res["compressed_output"])
                    # Rollback patch on Stealth Stop
                    backup_path = args.target + ".bak"
                    if os.path.exists(backup_path):
                        os.replace(backup_path, args.target)
                    if log_healer_event:
                        try:
                            log_healer_event(
                                session_id=args.conv_id,
                                test_file=tf,
                                target_file=args.target,
                                error_category="StealthStop",
                                iterations=3,
                                status="stealth_stop",
                                time_saved_min=0,
                            )
                        except Exception:
                            pass
                    sys.exit(3)
                output_to_parse = track_res["compressed_output"]
            else:
                output_to_parse = stdout

            outputs_to_parse.append((tf, success, output_to_parse))
            if not success:
                all_success = False

        if all_success:
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
            # Очищаем историю при успехе
            try:
                from pathlib import Path

                Path("/Users/rus/ai-tools/scratch/healer_run_history.json").unlink(
                    missing_ok=True
                )
            except Exception:
                pass
            if log_healer_event:
                try:
                    lines_count = 10
                    try:
                        with open(args.target, encoding="utf-8") as f:
                            lines_count = len(f.read().splitlines())
                    except Exception:
                        pass
                    time_saved = max(10, 10 + lines_count // 10)
                    log_healer_event(
                        session_id=args.conv_id,
                        test_file=args.test_file,
                        target_file=args.target,
                        error_category=None,
                        iterations=1,
                        status="healed",
                        time_saved_min=time_saved,
                    )
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

            # Запускаем Loop Detection
            failed_output = ""
            for tf, success, output_to_parse in outputs_to_parse:
                if not success:
                    failed_output += output_to_parse + "\n"

            error_cat = "AssertionError"
            errors = parse_pytest_error(failed_output)
            if errors and errors[0].get("message"):
                first_err_msg = errors[0]["message"].splitlines()[0]
                if ":" in first_err_msg:
                    error_cat = first_err_msg.split(":")[0].strip()

            if log_healer_event:
                try:
                    log_healer_event(
                        session_id=args.conv_id,
                        test_file=args.test_file,
                        target_file=args.target,
                        error_category=error_cat,
                        iterations=1,
                        status="failed",
                        time_saved_min=0,
                    )
                except Exception:
                    pass

            check_loop_detection(args.test_file, failed_output)

            print("\n❌ Tests Failed. Generating Clean Traceback for AI:")
            print("=" * 60)
            for tf, success, output_to_parse in outputs_to_parse:
                if not success:
                    print(f"--- Failed Test File: {tf} ---")
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
                        if log_healer_event:
                            try:
                                log_healer_event(
                                    session_id=args.conv_id,
                                    test_file=cand,
                                    target_file=None,
                                    error_category=None,
                                    iterations=1,
                                    status="healed",
                                    time_saved_min=10,
                                )
                            except Exception:
                                pass
                    else:
                        check_loop_detection(cand, output_to_parse)
                        print(
                            f"❌ Tests Failed in {cand}. Generating Clean Traceback for AI:"
                        )
                        if log_change:
                            log_change(
                                "Self-Healing",
                                f"Failed test candidate: {cand}",
                            )

                        error_cat = "AssertionError"
                        errors = parse_pytest_error(output_to_parse)
                        if errors and errors[0].get("message"):
                            first_err_msg = errors[0]["message"].splitlines()[0]
                            if ":" in first_err_msg:
                                error_cat = first_err_msg.split(":")[0].strip()

                        if log_healer_event:
                            try:
                                log_healer_event(
                                    session_id=args.conv_id,
                                    test_file=cand,
                                    target_file=None,
                                    error_category=error_cat,
                                    iterations=1,
                                    status="failed",
                                    time_saved_min=0,
                                )
                            except Exception:
                                pass

                        print("=" * 60)
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
            if all_success:
                try:
                    Path("/Users/rus/ai-tools/scratch/healer_run_history.json").unlink(
                        missing_ok=True
                    )
                except Exception:
                    pass
            sys.exit(0 if all_success else 1)
        else:
            print(
                "Usage: python3 test_healer.py <test_file_path> [--target <target_file> --patch <patch_file>]\n"
                "Or run with --diff to auto-detect tests based on modified files."
            )
            sys.exit(1)

    # Case 3: Diagnostics for a single or multiple (comma-separated) test files
    test_files = [tf.strip() for tf in args.test_file.split(",")]
    for tf in test_files:
        if not os.path.exists(tf):
            print(f"Error: File {tf} not found.")
            sys.exit(1)

    print(f"Running tests in {', '.join(test_files)}...")
    all_success = True
    outputs_to_parse = []

    for tf in test_files:
        success, stdout, stderr = run_test_file(tf, timeout=args.timeout)

        # Track execution in Solo Loop
        if loop:
            track_res = loop.track_execution(tf, success, stdout + "\n" + stderr)
            if track_res["stealth_stop"]:
                print(track_res["compressed_output"])
                sys.exit(3)
            output_to_parse = track_res["compressed_output"]
        else:
            output_to_parse = stdout

        outputs_to_parse.append((tf, success, output_to_parse))
        if not success:
            all_success = False

    if all_success:
        print("Success: All tests passed cleanly.")
        try:
            from pathlib import Path

            Path("/Users/rus/ai-tools/scratch/healer_run_history.json").unlink(
                missing_ok=True
            )
        except Exception:
            pass
        sys.exit(0)
    else:
        # Запускаем Loop Detection
        failed_output = ""
        for tf, success, output_to_parse in outputs_to_parse:
            if not success:
                failed_output += output_to_parse + "\n"
        check_loop_detection(args.test_file, failed_output)

        print("\n❌ Tests Failed. Generating Clean Traceback for AI:")
        if log_change:
            log_change("Self-Healing", f"Tests failed for: {args.test_file}")
        print("=" * 60)
        for tf, success, output_to_parse in outputs_to_parse:
            if not success:
                print(f"--- Failed Test File: {tf} ---")
                errors = parse_pytest_error(output_to_parse)
                if errors:
                    for err in errors:
                        print(f"Target Test: {err['test_name']}")
                        print(f"Traceback Summary:\n{err['message']}")
                        print("-" * 60)
                else:
                    print(output_to_parse)
        sys.exit(1)
