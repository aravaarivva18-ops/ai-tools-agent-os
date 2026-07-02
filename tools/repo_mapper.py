#!/usr/bin/env python3
"""
Генератор Repository Map.
Строит компактную карту символов (классы, методы, функции, docstrings)
для предоставления ИИ-агенту контекста структуры проекта.
"""

import ast
import os
from pathlib import Path


def get_function_sig(node: ast.FunctionDef) -> str:
    """Собирает читаемую сигнатуру функции из AST узла."""
    args = []
    for arg in node.args.args:
        # Игнорируем self для краткости методов
        if arg.arg != "self":
            args.append(arg.arg)

    # Keyword-only аргументы
    if node.args.kwonlyargs:
        args.append("*")
        for arg in node.args.kwonlyargs:
            args.append(arg.arg)

    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")

    return f"def {node.name}({', '.join(args)})"


def parse_py_file(file_path: Path) -> str:
    """Парсит питоновский файл и возвращает его текстовое описание."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        return f"  [Ошибка парсинга: {e}]\n"

    lines = []
    # Извлекаем docstring модуля
    module_doc = ast.get_docstring(tree)
    if module_doc:
        doc_line = module_doc.strip().splitlines()[0]
        lines.append(f"  # {doc_line}")

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            sig = get_function_sig(node)
            doc = ast.get_docstring(node)
            doc_suffix = f"  # {doc.strip().splitlines()[0]}" if doc else ""
            lines.append(f"  - {sig}{doc_suffix}")

        elif isinstance(node, ast.ClassDef):
            lines.append(f"  - class {node.name}:")
            class_doc = ast.get_docstring(node)
            if class_doc:
                lines.append(f"    # {class_doc.strip().splitlines()[0]}")

            for sub_node in node.body:
                if isinstance(sub_node, ast.FunctionDef):
                    sig = get_function_sig(sub_node)
                    doc = ast.get_docstring(sub_node)
                    doc_suffix = f"  # {doc.strip().splitlines()[0]}" if doc else ""
                    lines.append(f"    - {sig}{doc_suffix}")

    return "\n".join(lines) + "\n" if lines else ""


def generate_map(workspace_root: Path) -> str:
    """Сканирует core/ и tools/ и генерирует карту символов репозитория."""
    map_parts = []

    # Папки для сканирования
    dirs_to_scan = ["core", "tools"]

    for dir_name in dirs_to_scan:
        scan_dir = workspace_root / dir_name
        if not scan_dir.exists():
            continue

        map_parts.append(f"=== Directory: {dir_name}/ ===")

        # Обходим файлы рекурсивно
        for root, _, files in os.walk(scan_dir):
            # Игнорируем тесты и служебные директории
            if "tests" in root or "__pycache__" in root:
                continue

            for file in sorted(files):
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(workspace_root)

                    file_map = parse_py_file(full_path)
                    if file_map:
                        map_parts.append(f"\nFile: {rel_path}")
                        map_parts.append(file_map)

    return "\n".join(map_parts)


def write_repo_map(workspace_root: Path) -> None:
    """Записывает карту репозитория в файл vault/repo_map.txt."""
    repo_map = generate_map(workspace_root)
    out_file = workspace_root / "vault" / "repo_map.txt"
    try:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(repo_map, encoding="utf-8")
    except Exception:
        pass
