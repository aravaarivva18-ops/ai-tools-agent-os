#!/usr/bin/env python3

"""
Antigravity AI-Tools CLI (agy)
Единая точка входа для управления локальной Agentic OS.
"""

import argparse
import json
import pathlib
import shutil
import subprocess  # nosec B404
import sys

try:
    from tools import config
except ImportError:
    import config

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
    except Exception as e:
        print(f"❌ Ошибка создания файла конфигурации: {e}")
        sys.exit(1)

def cmd_run(args, extra_args):
    """Запускает цикл авто-лечения ошибок test_healer.py."""
    del args
    tools_dir = pathlib.Path(__file__).resolve().parent
    healer_script = tools_dir / "test_healer.py"

    if not healer_script.exists():
        print(f"❌ Скрипт авто-лечения не найден по пути: {healer_script}")
        sys.exit(1)

    cmd = [sys.executable, str(healer_script), *extra_args]
    try:
        result = subprocess.run(cmd, check=False)  # nosec B603
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
        result = subprocess.run(cmd, check=False)  # nosec B603
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

    cmd = [sys.executable, str(improve_script), *extra_args]
    try:
        result = subprocess.run(cmd, check=False)  # nosec B603
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
        result = subprocess.run(cmd, check=False)  # nosec B603
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
        subprocess.run([sys.executable, str(collect_script)], check=False)  # nosec B603

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
        result = subprocess.run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при логировании сессии: {e}")
        sys.exit(1)

def cmd_clean(args):
    """Очищает старые сессии в папке brain, сохраняя текущую."""
    brain_dir = pathlib.Path.home() / ".gemini" / "antigravity-cli" / "brain"
    if not brain_dir.exists():
        print("✅ Папка сессий пуста.")
        sys.exit(0)

    print(f"🧹 Очистка старых сессий в {brain_dir}...")
    count = 0
    for path in brain_dir.iterdir():
        if path.is_dir():
            if args.keep and path.name == args.keep:
                print(f"   [Сохранено] Текущая сессия: {path.name}")
                continue
            try:
                shutil.rmtree(path)
                print(f"   [Удалено] Сессия: {path.name}")
                count += 1
            except Exception as e:
                print(f"   [Ошибка] Не удалось удалить {path.name}: {e}")

    print(f"✅ Очищено сессий: {count}")
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
        result = subprocess.run(cmd, check=False)  # nosec B603
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Ошибка при запуске диагностики: {e}")
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
        result = subprocess.run(cmd, check=False)  # nosec B603
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
            print("⚠️ Оффлайн-режим: Не удалось связаться с сервером лицензий Gumroad. Проверка отложена.", file=sys.stderr)
        return

    if status == "network_error":
        print("❌ Ошибка сети: Не удалось верифицировать новый лицензионный ключ.", file=sys.stderr)
        sys.exit(1)

    print("=====================================================")
    print("🔑 Antigravity AI-Tools CLI — Требуется Активация")
    print("Купить лицензию можно на: https://altic.dev/buy")
    print("=====================================================")

    if not sys.stdin.isatty():
        print("❌ Ошибка: Требуется лицензионный ключ. Установите переменную окружения AGY_LICENSE_KEY.", file=sys.stderr)
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
            print("❌ Ошибка сети: Не удалось связаться с сервером Gumroad для проверки ключа.", file=sys.stderr)
            sys.exit(1)
        else:
            print("❌ Неверный лицензионный ключ. Проверьте правильность ввода.", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nАктивация отменена.")
        sys.exit(1)

def main():
    enforce_license()

    parser = argparse.ArgumentParser(
        description="Antigravity AI-Tools CLI (agy) — Единый консольный интерфейс для ИИ-разработчиков."
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # init
    subparsers.add_parser("init", help="Инициализировать файл конфигурации .agentic-dev.json").add_argument(
        "--force", "-f", action="store_true", help="Принудительно перезаписать существующий файл конфигурации"
    )

    # run (test_healer)
    subparsers.add_parser("run", help="Запустить авто-лечение ошибок (test_healer.py)")

    # search (semantic_search)
    subparsers.add_parser("search", help="Запустить семантический поиск по базе знаний (semantic_search.py)")

    # improve (self_improve)
    subparsers.add_parser("improve", help="Запустить цикл самосовершенствования системы (self_improve.py)")

    # validate (rules_validator)
    subparsers.add_parser("validate", help="Запустить валидатор правил кодовой базы (rules_validator.py)")

    # log (session_logger)
    parser_log = subparsers.add_parser("log", help="Собрать результаты сессии и записать лог в Obsidian")
    parser_log.add_argument("handoff", type=str, nargs="?", help="Путь к файлу HANDOFF.md")
    parser_log.add_argument("--conv-id", type=str, help="ID текущей сессии/диалога")

    # clean (clean_sessions)
    parser_clean = subparsers.add_parser("clean", help="Очистить старые временные сессии в папке brain")
    parser_clean.add_argument("--keep", type=str, help="ID сессии, которую нужно сохранить (не удалять)")

    # doctor (health_check)
    subparsers.add_parser("doctor", help="Запустить самодиагностику системы (health_check.py)")

    # build
    parser_build = subparsers.add_parser("build", help="Собрать чистый релиз проекта в zip-архив")
    parser_build.add_argument("--out", "-o", type=str, help="Путь для сохранения собранного архива")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

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
    elif cmd == "build":
        args = parser.parse_args()
        cmd_build(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
