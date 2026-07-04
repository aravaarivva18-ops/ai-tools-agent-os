#!/usr/bin/env python3

"""
Antigravity AI-Tools CLI (agy)
Единая точка входа для управления локальной Agentic OS.
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess  # nosec B404
import sys

try:
    from tools import config
except ImportError:
    import config


def is_safe_command(cmd: list[str]) -> bool:
    """
    Проверяет безопасность шелл-команды.
    Разрешены только безопасные утилиты: pytest, ruff, uv, python3, python, make.
    Отклоняет sudo, rm -rf вне scratch папки, curl | bash и т.д.
    """
    if not cmd:
        return False

    cmd_str = " ".join(cmd)

    # 0.5 Проверка деструктивных действий (git reset --hard, force push, drop table)
    try:
        from tools.command_safety_gate import is_destructive_command
        if is_destructive_command(cmd_str):
            if os.environ.get("FORCE_DANGER") != "1":
                print("\n❌ Ошибка безопасности: перехвачено потенциально опасное (деструктивное) действие!")
                print("Для принудительного выполнения установите переменную окружения FORCE_DANGER=1")
                return False
    except ImportError:
        pass

    # 1. Запрет sudo
    if "sudo" in cmd:
        return False

    # 2. Запрет curl/wget с bash/sh
    if ("curl" in cmd_str or "wget" in cmd_str) and (
        "bash" in cmd_str or "sh" in cmd_str
    ):
        return False

    # 3. Проверка rm
    if "rm" in cmd_str:
        # Убедимся, что удаление происходит строго в scratch папке
        for arg in cmd:
            if "rm" in arg:
                continue
            if "scratch" not in cmd_str:
                return False

    # 4. Проверка разрешенных исполняемых файлов
    executable = os.path.basename(cmd[0])
    allowed_executables = {"pytest", "ruff", "uv", "python3", "python", "make"}

    if executable == os.path.basename(sys.executable):
        return True

    if executable in allowed_executables:
        return True

    for allowed in allowed_executables:
        if allowed in executable:
            return True

    return False


def safe_subprocess_run(cmd, *args, **kwargs):
    if not is_safe_command(cmd):
        print(f"❌ Ошибка безопасности: команда отклонена политикой Whitelist: {cmd}")
        sys.exit(1)
    return subprocess.run(cmd, *args, **kwargs)


def cmd_init(args):
    """Инициализирует .agentic-dev.json в текущем воркспейсе."""
    root = config.get_workspace_root()
    config_path = root / ".agentic-dev.json"

    if config_path.exists() and not args.force:
        print(f"⚠️ Файл конфигурации уже существует по пути: {config_path}")
        print("Используйте флаг --force (-f) для перезаписи.")
        sys.exit(0)

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        print(f"✅ Успешно инициализирован файл конфигурации: {config_path}")

        # Установка git-хука pre-commit
        git_dir = root / ".git"
        if git_dir.exists():
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir(exist_ok=True)
            pre_commit_hook = hooks_dir / "pre-commit"

            hook_content = (
                "#!/bin/sh\n"
                "# AI-Tools Linter Config Guard pre-commit hook\n"
                'python3 -m tools.linter_config_guard --cached\n'
            )

            pre_commit_hook.write_text(hook_content, encoding="utf-8")
            pre_commit_hook.chmod(0o755)
            print("✅ Установлен Git хук pre-commit для защиты конфигураций линтеров.")
    except Exception as e:
        print(f"❌ Ошибка создания файла конфигурации или установки хуков: {e}")
        sys.exit(1)


def run_in_background(cmd_args: list[str], job_type: str) -> None:
    import time
    from datetime import datetime
    from pathlib import Path

    workspace_root = config.get_workspace_root()
    jobs_dir = workspace_root / "vault" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    job_id = f"job_{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    runner_path = Path(__file__).resolve().parent / "job_runner.py"

    background_cmd = [sys.executable, str(runner_path), job_id, *cmd_args]

    subprocess.Popen( # nosec B603
        background_cmd,
        cwd=str(workspace_root),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(0.3)

    print(f"✅ Задача '{job_type}' успешно запущена в фоновом режиме.")
    print(f"🆔 ID задачи: {job_id}")
    print(f"📝 Лог-файл: vault/jobs/{job_id}.log")
    print(f"📊 Проверить статус: agy status {job_id}")
    sys.exit(0)


def cmd_run(args, extra_args):
    """Запускает цикл авто-лечения ошибок test_healer.py."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    healer_script = tools_dir / "test_healer.py"

    if not healer_script.exists():
        print(f"❌ Скрипт авто-лечения не найден по пути: {healer_script}")
        sys.exit(1)

    cmd = [sys.executable, str(healer_script)]

    run_bg = False
    filtered_args = []
    for arg in extra_args:
        if arg in ("--background", "-b"):
            run_bg = True
        else:
            filtered_args.append(arg)

    cmd.extend(filtered_args)

    if run_bg:
        run_in_background(cmd, "run")
        return

    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске авто-лечения: {e}")
        sys.exit(1)


def cmd_search(args, extra_args):
    """Запускает семантический поиск по хандоффам памяти semantic_search.py."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    search_script = tools_dir / "obsidian" / "semantic_search.py"

    if not search_script.exists():
        print(f"❌ Скрипт семантического поиска не найден по пути: {search_script}")
        sys.exit(1)

    cmd = [sys.executable, str(search_script), *extra_args]
    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске семантического поиска: {e}")
        sys.exit(1)


def cmd_improve(args, extra_args):
    """Запускает цикл самосовершенствования системы self_improve.py."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    improve_script = tools_dir / "self_improve.py"

    if not improve_script.exists():
        print(f"❌ Скрипт самосовершенствования не найден по пути: {improve_script}")
        sys.exit(1)

    cmd = [sys.executable, str(improve_script)]

    run_bg = False
    filtered_args = []
    for arg in extra_args:
        if arg in ("--background", "-b"):
            run_bg = True
        else:
            filtered_args.append(arg)

    cmd.extend(filtered_args)

    if run_bg:
        run_in_background(cmd, "improve")
        return

    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске самосовершенствования: {e}")
        sys.exit(1)


def cmd_validate(args, extra_args):
    """Запускает валидатор правил rules_validator.py."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    validator_script = tools_dir / "rules_validator.py"

    if not validator_script.exists():
        print(f"❌ Валидатор правил не найден по пути: {validator_script}")
        sys.exit(1)

    cmd = [sys.executable, str(validator_script), *extra_args]
    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске валидатора правил: {e}")
        sys.exit(1)


def cmd_log(args):
    """Сбор результатов сессии, создание хандоффа и логирование в Obsidian."""
    tools_dir = pathlib.Path(__file__).resolve().parent

    # 1. Сбор хандоффов
    collect_script = tools_dir / "collect_handoffs.py"
    if collect_script.exists():
        print("⚙️ Сбор файлов HANDOFF.md...")
        safe_subprocess_run([sys.executable, str(collect_script)], check=False)  # nosec B603

    # 2. Запись в Daily Note
    logger_script = tools_dir / "obsidian" / "session_logger.py"
    if not logger_script.exists():
        print(f"❌ Скрипт логирования сессии не найден по пути: {logger_script}")
        sys.exit(1)

    cmd = [sys.executable, str(logger_script)]
    if args.handoff:
        cmd += [args.handoff]
    if args.conv_id:
        cmd += ["--conv-id", args.conv_id]

    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при логировании сессии: {e}")
        sys.exit(1)


def cmd_clean(args):
    """Очищает старые сессии в папке brain и выполняет глубокую очистку воркспейса от мусора."""
    # 1. Очистка старых сессий
    brain_dir = pathlib.Path.home() / ".gemini" / "antigravity-cli" / "brain"
    if brain_dir.exists():
        print(f"🧹 Очистка старых сессий в {brain_dir}...")
        session_count = 0
        for path in brain_dir.iterdir():
            if path.is_dir():
                if args.keep and path.name == args.keep:
                    print(f"   [Сохранено] Текущая сессия: {path.name}")
                    continue
                try:
                    shutil.rmtree(path)
                    print(f"   [Удалено] Сессия: {path.name}")
                    session_count += 1
                except Exception as e:
                    print(f"   [Ошибка] Не удалось удалить {path.name}: {e}")
        print(f"✅ Очищено сессий: {session_count}")
    else:
        print("✅ Папка сессий пуста.")

    # 2. Глубокая очистка воркспейса от временного мусора
    import time

    workspace_root = config.get_workspace_root()
    print(f"🧹 Глубокая очистка воркспейса от временного мусора в {workspace_root}...")

    clutter_files = 0
    clutter_dirs = 0

    # Рекурсивный обход воркспейса, исключая .git и .venv
    for root_dir, dirs, files in os.walk(workspace_root):
        dirs[:] = [d for d in dirs if d not in (".venv", ".git")]

        # Очистка директорий кэша
        for d in list(dirs):
            if d in ("__pycache__", ".ruff_cache", ".pytest_cache"):
                dir_path = pathlib.Path(root_dir) / d
                try:
                    shutil.rmtree(dir_path)
                    dirs.remove(d)
                    clutter_dirs += 1
                except Exception as e:
                    print(f"   [Ошибка] Не удалось удалить папку кэша {dir_path}: {e}")

        # Очистка временных файлов .bak и .lock
        for f in files:
            file_path = pathlib.Path(root_dir) / f
            if f.endswith(".bak"):
                try:
                    file_path.unlink()
                    clutter_files += 1
                except Exception as e:
                    print(f"   [Ошибка] Не удалось удалить бэкап {file_path}: {e}")
            elif f.endswith(".lock"):
                try:
                    # Удаляем только старые блокировки (старше 10 секунд)
                    mtime = file_path.stat().st_mtime
                    if time.time() - mtime > 10.0:
                        file_path.unlink()
                        clutter_files += 1
                except Exception as e:
                    print(f"   [Ошибка] Не удалось удалить блокировку {file_path}: {e}")

    print(
        f"✅ Глубокая очистка завершена. Удалено файлов: {clutter_files}, папок кэша: {clutter_dirs}"
    )
    sys.exit(0)


def cmd_doctor(args):
    """Запускает скрипт самодиагностики health_check.py."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    health_script = tools_dir / "health_check.py"

    if not health_script.exists():
        print(f"❌ Скрипт диагностики не найден по пути: {health_script}")
        sys.exit(1)

    cmd = [sys.executable, str(health_script)]
    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске диагностики: {e}")
        sys.exit(1)


def cmd_test(args):
    """Запускает pytest с автоматическим определением изменившихся файлов."""
    project_root = config.get_workspace_root()

    # Ищем pytest в локальном .venv
    venv_pytest = project_root / "tools" / ".venv" / "bin" / "pytest"
    if not venv_pytest.exists():
        venv_pytest = project_root / ".venv" / "bin" / "pytest"

    pytest_bin = str(venv_pytest) if venv_pytest.exists() else "pytest"

    # Базовая команда pytest
    cmd = [pytest_bin, "-v", "--disable-socket", "--allow-unix-socket"]

    if args.all:
        print("🚀 Запуск ВСЕХ тестов монорепозитория...")
        existing_paths = []
        for folder in [
            "tools/tests",
            "youtube-faceless-pipeline/tests",
            "geo-seo/tests",
        ]:
            full_p = project_root / folder
            if full_p.exists():
                existing_paths.append(str(full_p))
        cmd.extend(existing_paths)
    else:
        # Инкрементальный запуск по умолчанию
        try:
            from tools.test_healer import detect_tests_from_diff
        except ImportError:
            from test_healer import detect_tests_from_diff

        candidates = detect_tests_from_diff(project_root)
        if not candidates:
            print("ℹ️ Нет измененных файлов по сравнению с git diff. Тесты не запущены.")
            print("Используйте 'agy test --all' для запуска всех тестов.")
            sys.exit(0)

        print(f"🚀 Запуск тестов для измененных файлов ({len(candidates)} шт.):")
        for cand in candidates:
            print(f"   - {pathlib.Path(cand).name}")
        cmd.extend(candidates)

    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        sys.exit(1)


def cmd_mcp(args):
    """Запускает локальный MCP-сервер (mcp_server.py)."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    mcp_script = tools_dir / "mcp_server.py"

    if not mcp_script.exists():
        print(f"❌ MCP-сервер не найден по пути: {mcp_script}")
        sys.exit(1)

    cmd = [sys.executable, str(mcp_script)]
    try:
        # MCP-сервер stdio общается через стандартные потоки, поэтому мы не перехватываем их,
        # а отдаем процессу напрямую для связи с внешним ИИ-клиентом
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске MCP-сервера: {e}")
        sys.exit(1)


def cmd_build(args):
    """Запускает сборщик чистых релизов build_release.py."""
    tools_dir = pathlib.Path(__file__).resolve().parent
    build_script = tools_dir / "build_release.py"

    if not build_script.exists():
        print(f"❌ Скрипт сборки релиза не найден по пути: {build_script}")
        sys.exit(1)

    cmd = [sys.executable, str(build_script)]
    if args.out:
        cmd += ["--out", args.out]

    try:
        result = safe_subprocess_run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при сборке релиза: {e}")
        sys.exit(1)


def enforce_license():
    """Проверяет лицензию и запрашивает ввод при необходимости."""
    if any(arg in sys.argv for arg in ("-h", "--help")):
        return

    try:
        from tools import config as config_mod
    except ImportError:
        import config as config_mod

    allowed, status = config_mod.check_license_status()
    if allowed:
        if status == "offline_grace":
            print(
                "⚠️ Оффлайн-режим: Не удалось связаться с сервером лицензий Gumroad. Проверка отложена.",
                file=sys.stderr,
            )
        return

    if status == "network_error":
        print(
            "❌ Ошибка сети: Не удалось верифицировать новый лицензионный ключ.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("=====================================================")
    print("🔑 Antigravity AI-Tools CLI — Требуется Активация")
    print("Купить лицензию можно на: https://altic.dev/buy")
    print("=====================================================")

    if not sys.stdin.isatty():
        print(
            "❌ Ошибка: Требуется лицензионный ключ. Установите переменную окружения AGY_LICENSE_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        key = input("Введите ваш лицензионный ключ Gumroad: ").strip()
        if not key:
            print("❌ Ключ не может быть пустым.")
            sys.exit(1)

        print("Проверка лицензии через Gumroad API...")
        is_valid, is_net_error = config_mod.verify_license_online(key)

        if is_valid:
            import datetime

            global_cfg = config_mod.load_global_config()
            global_cfg["license_key"] = key
            global_cfg["license_verified_at"] = datetime.datetime.now().isoformat()
            config_mod.save_global_config(global_cfg)
            print("✅ Лицензия успешно активирована! Спасибо за покупку.")
            print("=====================================================")

            try:
                from tools import dashboard_logger

                dashboard_logger.log_change("System", "License activated successfully")
            except Exception:
                pass
            return
        elif is_net_error:
            print(
                "❌ Ошибка сети: Не удалось связаться с сервером Gumroad для проверки ключа.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            print(
                "❌ Неверный лицензионный ключ. Проверьте правильность ввода.",
                file=sys.stderr,
            )
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nАктивация отменена.")
        sys.exit(1)


def show_dashboard():
    """Выводит интерактивный дашборд состояния разработки и предлагает следующие шаги."""
    print("=====================================================================")
    print("🛸 Antigravity OS Developer Dashboard — Единый Продуктовый Центр")
    print("=====================================================================")

    # 1. Считываем текущий план и статус шагов
    from pathlib import Path

    try:
        from tools import config
        from tools.planning_with_files import PlanningWithFiles
    except ImportError:
        from planning_with_files import PlanningWithFiles

        import config

    root = config.get_workspace_root()
    planner = PlanningWithFiles(root)

    plan_exists = planner.plan_path.exists()
    state = None
    if plan_exists:
        try:
            state = planner.restore_state()
            print(
                f"🧬 Текущая цель: \033[1;36m{state.get('title', 'Без названия')}\033[0m"
            )
            print("📋 Ход выполнения шагов плана:")

            completed_set = {
                c.replace(" - COMPLETED", "").strip().lower()
                for c in state.get("completed_steps", [])
            }

            for idx, step in enumerate(state.get("steps", []), 1):
                is_done = False
                for comp in completed_set:
                    if step.lower() in comp or comp in step.lower():
                        is_done = True
                        break

                status_char = "🟢 [x]" if is_done else "⚪️ [ ]"
                color_start = "\033[90m" if is_done else "\033[1m"
                color_end = "\033[0m"
                print(f"   {status_char} {color_start}{idx}. {step}{color_end}")

            next_step = state.get("next_step")
            if next_step:
                print(f"\n👉 Следующий шаг: \033[1;33m{next_step}\033[0m")
            else:
                print("\n🎉 Все шаги плана выполнены!")
        except Exception as e:
            print(f"⚠️ Ошибка чтения плана: {e}")
    else:
        print("ℹ️ План реализации (implementation_plan.md) отсутствует.")
        print("💡 Создайте план, чтобы Antigravity могла вести вас по шагам.")

    # 2. Статус измененных файлов и тестов
    print("\n📦 Состояние воркспейса:")
    try:
        from tools.test_healer import detect_tests_from_diff
    except ImportError:
        from test_healer import detect_tests_from_diff

    changed_tests = []
    try:
        changed_tests = detect_tests_from_diff(root)
        if changed_tests:
            print(
                f"   ⚠️ Обнаружено измененных файлов с тестами: {len(changed_tests)} шт."
            )
            for t in changed_tests[:3]:
                print(f"      - {Path(t).name}")
            if len(changed_tests) > 3:
                print("      - ... и другие")
        else:
            print("   ✅ Изменений в коде по сравнению с git diff не обнаружено.")
    except Exception:
        print("   ⚠️ Не удалось определить git diff статус.")

    # 3. Валидация правил
    print("\n📐 Статус регламентов и навыков:")
    try:
        import contextlib
        import io

        from tools.rules_validator import check_jit_skills

        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            skills_ok = check_jit_skills(fix=False)

        if skills_ok:
            print("   ✅ JIT-навыки полностью синхронизированы с CLAUDE.md.")
        else:
            print("   ❌ Обнаружены несинхронизированные JIT-навыки!")
    except Exception:
        skills_ok = True
        print("   ⚠️ Не удалось проверить статус навыков.")

    # 4. Предложение следующего лучшего действия (Smart Recommendations)
    print("\n🧠 Умная рекомендация (Smart Suggestion):")
    if not plan_exists:
        print(
            "   \033[1;32magy init\033[0m — Инициализировать проект и настроить окружение."
        )
    elif not skills_ok:
        print(
            "   \033[1;32magy validate --fix\033[0m — Синхронизировать новые JIT-навыки с CLAUDE.md."
        )
    elif changed_tests:
        print("   \033[1;32magy test\033[0m — Запустить тесты для измененных файлов.")
        print(
            "   \033[1;32magy run\033[0m  — Запустить авто-лечение Healer, если тесты падают."
        )
    elif state and not state.get("next_step"):
        print(
            "   \033[1;32magy log\033[0m — Зафиксировать результаты сессии и отправить лог в Obsidian."
        )
    else:
        print("   \033[1;32magy test\033[0m — Проверить стабильность текущей версии.")

    print("=====================================================================")
def cmd_fast(args):
    """Запускает быстрый режим с минимальным контекстом без RAG."""
    from tools.context_utils import count_tokens_exact, trim_context
    from tools.prompt_loader import load_prompt

    print(f"🚀 Запуск FAST режима для запроса: '{args.prompt}'")
    try:
        sys_prompt = load_prompt("hermes_system")
    except Exception:
        sys_prompt = "System guidelines"

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": args.prompt}
    ]

    # Быстрая оценка и обрезка
    trimmed = trim_context(messages, max_tokens=4096)
    total_tokens = sum(count_tokens_exact(m["content"]) for m in trimmed)

    print(f"📦 Собрано сообщений: {len(trimmed)}")
    print(f"📊 Итоговый размер контекста: {total_tokens} токенов")
    print("💬 Ответ LLM (FAST-симуляция): Запрос обработан успешно.")
    sys.exit(0)


def cmd_deep(args):
    """Запускает глубокий режим с RAG поиском по Wiki и Obsidian."""
    from tools.context_utils import count_tokens_exact, trim_context
    from tools.knowledge.search import global_search
    from tools.prompt_loader import load_prompt

    print(f"🚀 Запуск DEEP режима для запроса: '{args.prompt}'")
    try:
        sys_prompt = load_prompt("hermes_system")
    except Exception:
        sys_prompt = "System guidelines"

    # Выполняем RAG-поиск
    print("🔍 Поиск по Wiki и Obsidian...")
    rag_data = global_search(args.prompt)

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "system", "content": f"Дополнительный контекст знаний:\n{rag_data}"},
        {"role": "user", "content": args.prompt}
    ]

    # Обрезаем до большего лимита
    trimmed = trim_context(messages, max_tokens=8192)
    total_tokens = sum(count_tokens_exact(m["content"]) for m in trimmed)

    print(f"📦 Собрано сообщений (включая RAG): {len(trimmed)}")
    print(f"📊 Итоговый размер контекста: {total_tokens} токенов")
    print("💬 Ответ LLM (DEEP-симуляция): Глубокий анализ завершен.")
    sys.exit(0)


def cmd_ask(args):
    """Универсальная команда ask с поддержкой --auto роутера."""
    prompt_len = len(args.prompt)

    if args.auto:
        keywords = ["найди", "поиск", "wiki", "obsidian", "память", "rust", "python", "как", "почему"]
        is_complex = prompt_len > 120 or any(kw in args.prompt.lower() for kw in keywords)

        if is_complex:
            print("🧠 [Auto-Router] Запрос определен как сложный -> перенаправление в DEEP.")
            class DummyArgs:
                prompt = args.prompt
            cmd_deep(DummyArgs())
        else:
            print("⚡ [Auto-Router] Запрос определен как простой -> перенаправление в FAST.")
            class DummyArgs:
                prompt = args.prompt
            cmd_fast(DummyArgs())
    else:
        print("⚡ Режим по умолчанию -> перенаправление в FAST. (Для авто-выбора используйте --auto)")
        class DummyArgs:
            prompt = args.prompt
        cmd_fast(DummyArgs())


def cmd_status(args):
    """Показывает статус фоновых задач."""
    workspace_root = config.get_workspace_root()
    jobs_dir = workspace_root / "vault" / "jobs"

    if not jobs_dir.exists():
        print("ℹ️ Нет активных или завершенных фоновых задач.")
        sys.exit(0)

    if getattr(args, "job_id", None):
        job_id = args.job_id
        json_path = jobs_dir / f"{job_id}.json"
        log_path = jobs_dir / f"{job_id}.log"

        if not json_path.exists():
            print(f"❌ Фоновая задача с ID {job_id} не найдена.")
            sys.exit(1)

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check if actually running by PID
        if data["status"] == "running":
            pid = data["pid"]
            try:
                os.kill(pid, 0)
            except OSError:
                data["status"] = "failed"
                data["error"] = "Процесс неожиданно завершился без обновления статуса."
                with open(json_path, "w", encoding="utf-8") as wf:
                    json.dump(data, wf, ensure_ascii=False, indent=2)

        print(f"\n📊 СТАТУС ЗАДАЧИ: {data['id']}")
        print(f"   Команда:    {data['command']}")
        print(f"   Статус:     {data['status'].upper()}")
        print(f"   PID:        {data['pid']}")
        print(f"   Начало:     {data['start_time']}")
        if data.get('end_time'):
            print(f"   Конец:      {data['end_time']}")
        if data.get('exit_code') is not None:
            print(f"   Exit Code:  {data['exit_code']}")
        if "error" in data:
            print(f"   Ошибка:     {data['error']}")

        if log_path.exists():
            print("\n📝 Последние 20 строк лога:")
            print("=" * 60)
            lines = log_path.read_text(encoding="utf-8").splitlines()
            for line in lines[-20:]:
                print(line)
            print("=" * 60)
    else:
        # List all jobs
        json_files = sorted(jobs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not json_files:
            print("ℹ️ Нет сохраненных фоновых задач.")
            sys.exit(0)

        print(f"\n📋 Список фоновых задач ({len(json_files)}):")
        print(f"{'ID Задачи':<25} | {'Статус':<10} | {'Начало':<20} | {'Команда'}")
        print("-" * 80)
        for jf in json_files[:15]:
            try:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
                print(f"{data['id']:<25} | {data['status'].upper():<10} | {data['start_time'][:19]:<20} | {data['command'][:30]}")
            except Exception:
                pass
        sys.exit(0)


def cmd_cancel(args):
    """Останавливает фоновую задачу."""
    if not args.job_id:
        print("❌ Укажите ID задачи: agy cancel <job_id>")
        sys.exit(1)

    workspace_root = config.get_workspace_root()
    json_path = workspace_root / "vault" / "jobs" / f"{args.job_id}.json"

    if not json_path.exists():
        print(f"❌ Задача {args.job_id} не найдена.")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if data["status"] != "running":
        print(f"ℹ️ Задача {args.job_id} уже завершена (статус: {data['status']}).")
        sys.exit(0)

    pid = data["pid"]
    try:
        import signal
        os.kill(pid, signal.SIGTERM)
        data["status"] = "cancelled"
        data["exit_code"] = -15
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Задача {args.job_id} успешно отменена (SIGTERM отправлен PID {pid}).")
    except Exception as e:
        print(f"❌ Не удалось остановить задачу {args.job_id}: {e}")
        sys.exit(1)


def main():
    enforce_license()

    parser = argparse.ArgumentParser(
        description="Antigravity AI-Tools CLI (agy) — Единый консольный интерфейс для ИИ-разработчиков."
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # init
    subparsers.add_parser(
        "init", help="Инициализировать файл конфигурации .agentic-dev.json"
    ).add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Принудительно перезаписать существующий файл конфигурации",
    )

    # run (test_healer)
    subparsers.add_parser("run", help="Запустить авто-лечение ошибок (test_healer.py)")

    # search (semantic_search)
    subparsers.add_parser(
        "search",
        help="Запустить семантический поиск по базе знаний (semantic_search.py)",
    )

    # improve (self_improve)
    subparsers.add_parser(
        "improve", help="Запустить цикл самосовершенствования системы (self_improve.py)"
    )

    # validate (rules_validator)
    subparsers.add_parser(
        "validate", help="Запустить валидатор правил кодовой базы (rules_validator.py)"
    )

    # log (session_logger)
    parser_log = subparsers.add_parser(
        "log", help="Собрать результаты сессии и записать лог в Obsidian"
    )
    parser_log.add_argument(
        "handoff", type=str, nargs="?", help="Путь к файлу HANDOFF.md"
    )
    parser_log.add_argument("--conv-id", type=str, help="ID текущей сессии/диалога")

    # clean (clean_sessions)
    parser_clean = subparsers.add_parser(
        "clean", help="Очистить старые временные сессии в папке brain"
    )
    parser_clean.add_argument(
        "--keep", type=str, help="ID сессии, которую нужно сохранить (не удалять)"
    )

    # doctor (health_check)
    subparsers.add_parser(
        "doctor", help="Запустить самодиагностику системы (health_check.py)"
    )

    # mcp
    subparsers.add_parser("mcp", help="Запустить локальный MCP-сервер (mcp_server.py)")

    # build
    parser_build = subparsers.add_parser(
        "build", help="Собрать чистый релиз проекта в zip-архив"
    )
    parser_build.add_argument(
        "--out", "-o", type=str, help="Путь для сохранения собранного архива"
    )

    # test (pytest incremental runner)
    parser_test = subparsers.add_parser(
        "test", help="Запустить тесты (по умолчанию только для измененных файлов)"
    )
    parser_test.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Запустить абсолютно все тесты во всех модулях",
    )

    # fast
    parser_fast = subparsers.add_parser("fast", help="Быстрый запрос к LLM без RAG")
    parser_fast.add_argument("prompt", type=str, help="Текст запроса")

    # deep
    parser_deep = subparsers.add_parser("deep", help="Глубокий запрос к LLM с RAG по знаниям и Obsidian")
    parser_deep.add_argument("prompt", type=str, help="Текст запроса")

    # ask
    parser_ask = subparsers.add_parser("ask", help="Универсальный запрос к LLM")
    parser_ask.add_argument("prompt", type=str, help="Текст запроса")
    parser_ask.add_argument(
        "--auto",
        action="store_true",
        help="Включить автоматический выбор режима",
    )

    # status
    parser_status = subparsers.add_parser("status", help="Показать статус фоновых задач")
    parser_status.add_argument("job_id", type=str, nargs="?", help="ID задачи")

    # cancel
    parser_cancel = subparsers.add_parser("cancel", help="Остановить фоновую задачу")
    parser_cancel.add_argument("job_id", type=str, nargs="?", help="ID задачи")

    if len(sys.argv) < 2:
        show_dashboard()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "init":
        args = parser.parse_args()
        cmd_init(args)
    elif cmd == "run":
        cmd_run(None, sys.argv[2:])
    elif cmd == "search":
        cmd_search(None, sys.argv[2:])
    elif cmd == "improve":
        cmd_improve(None, sys.argv[2:])
    elif cmd == "validate":
        cmd_validate(None, sys.argv[2:])
    elif cmd == "log":
        args = parser.parse_args()
        cmd_log(args)
    elif cmd == "clean":
        args = parser.parse_args()
        cmd_clean(args)
    elif cmd == "doctor":
        cmd_doctor(None)
    elif cmd == "mcp":
        cmd_mcp(None)
    elif cmd == "build":
        args = parser.parse_args()
        cmd_build(args)
    elif cmd == "test":
        args = parser.parse_args()
        cmd_test(args)
    elif cmd == "fast":
        args = parser.parse_args()
        cmd_fast(args)
    elif cmd == "deep":
        args = parser.parse_args()
        cmd_deep(args)
    elif cmd == "ask":
        args = parser.parse_args()
        cmd_ask(args)
    elif cmd == "status":
        args = parser.parse_args()
        cmd_status(args)
    elif cmd == "cancel":
        args = parser.parse_args()
        cmd_cancel(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
