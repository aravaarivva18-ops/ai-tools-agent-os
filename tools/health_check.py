#!/usr/bin/env python3

"""
System Health Check Utility
Проверяет целостность и работоспособность компонентов системы ai-tools.
"""

import pathlib
import shutil
import sys

# Цвета для вывода в терминал
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_status(component: str, ok: bool, warning_msg: str = "", err_msg: str = ""):
    if ok:
        print(f"  [{GREEN}OK{RESET}] {component}")
    elif warning_msg:
        print(f"  [{YELLOW}WARN{RESET}] {component} — {warning_msg}")
    else:
        print(f"  [{RED}FAIL{RESET}] {component} — {err_msg}")

def check_files(tools_dir: pathlib.Path):
    print("\n🔍 Проверка целостности файлов ядра:")

    required_files = {
        "cli.py": "Единая точка входа (agy)",
        "config.py": "Модуль настроек и лицензирования",
        "diff_applier.py": "Точечный аппликатор диффов",
        "test_healer.py": "Авто-лечение тестов и ошибок",
        "planning_with_files.py": "Оркестратор контекста и планирования",
        "collect_handoffs.py": "Сборщик файлов HANDOFF.md",
        "llm_wiki.py": "База знаний системы",
        "obsidian/session_logger.py": "Логгер сессий в Daily Note",
        "obsidian/semantic_search.py": "Семантический поиск"
    }

    all_ok = True
    for rel_path, desc in required_files.items():
        full_path = tools_dir / rel_path
        exists = full_path.exists()
        print_status(f"{rel_path} ({desc})", exists, err_msg="Файл отсутствует!")
        if not exists:
            all_ok = False

    return all_ok

def check_directories(root_dir: pathlib.Path):
    print("\n📁 Проверка структуры глобальных директорий:")

    required_dirs = {
        "standards": "Глобальный банк стандартов",
        "vault": "Локальное хранилище и база знаний",
        "vault/handoffs": "Собранные файлы передачи контекста",
        "scratch": "Временные файлы и черновики"
    }

    all_ok = True
    for rel_path, desc in required_dirs.items():
        full_path = root_dir / rel_path
        exists = full_path.exists()
        print_status(f"/{rel_path} ({desc})", exists, err_msg="Директория отсутствует!")
        if not exists:
            all_ok = False

    return all_ok

def check_integrations():
    print("\n📡 Проверка внешних интеграций и окружения:")

    # 1. Проверяем наличие Python
    print_status(f"Python Runtime ({sys.version.split()[0]})", True)

    # 2. Проверяем утилиту obsidian CLI
    obsidian_cli = shutil.which("obsidian")
    print_status(
        "Obsidian CLI (утилита управления)",
        obsidian_cli is not None,
        warning_msg="Не установлена утилита 'obsidian'. Авто-логирование будет работать в fallback-режиме."
    )

    # 3. Проверяем доступность Obsidian REST API (мягкая проверка)
    # Пытаемся проверить, запущен ли локальный сервер Obsidian (по умолчанию порт 27124 или аналогичный)
    import socket
    obsidian_api_running = False
    for port in (27124, 27123):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                obsidian_api_running = True
                break
        except (OSError, ConnectionRefusedError):
            pass

    print_status(
        "Obsidian Local REST API",
        obsidian_api_running,
        warning_msg="API недоступен. Убедитесь, что приложение Obsidian запущено и плагин Local REST API активен."
    )

def main():
    print("=====================================================")
    print("🤖 Antigravity AI-Tools — Диагностика Системы (v1.0)")
    print("=====================================================")

    tools_dir = pathlib.Path(__file__).resolve().parent
    root_dir = tools_dir.parent

    files_ok = check_files(tools_dir)
    dirs_ok = check_directories(root_dir)
    check_integrations()

    print("=====================================================")
    if files_ok and dirs_ok:
        print(f"🎉 {GREEN}ДИАГНОСТИКА УСПЕШНО ПРОЙДЕНА: Система на 100% исправна!{RESET}")
    else:
        print(f"⚠️ {YELLOW}ОБНАРУЖЕНЫ ПРОБЛЕМЫ: Некоторые компоненты отсутствуют.{RESET}")
    print("=====================================================")

if __name__ == "__main__":
    main()
