#!/usr/bin/env python3
"""
YAGNI Dependency Auditor for Antigravity AI-Tools.
Scans imports in Python files and maps them to pyproject.toml dependencies to detect unused libraries.
"""

import ast
import re
from pathlib import Path

PACKAGE_TO_MODULE_MAP = {
    "python-docx": "docx",
    "python-pptx": "pptx",
    "python-dotenv": "dotenv",
    "google-generativeai": "google",
    "google-genai": "google",
    "pyjwt": "jwt",
    "passlib": "passlib",
    "psycopg2-binary": "psycopg2",
    "pydantic-settings": "pydantic_settings",
}


def get_pyproject_dependencies(project_root: Path) -> set:
    import tomllib

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return set()

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        deps = data.get("project", {}).get("dependencies", [])

        clean_deps = set()
        for dep in deps:
            match = re.match(r"^([a-zA-Z0-9_\-]+)", dep.strip())
            if match:
                clean_deps.add(match.group(1).lower())
        return clean_deps
    except Exception as e:
        print(f"Warning: Failed to load pyproject.toml: {e}")
        return set()


def get_imported_modules(project_root: Path) -> set:
    imported = set()
    for path in project_root.rglob("*.py"):
        path_parts = path.parts
        # Исключаем временные файлы, виртуальное окружение и т.д.
        if any(
            p in path_parts
            for p in (
                ".venv",
                ".git",
                ".pytest_cache",
                ".ruff_cache",
                ".mypy_cache",
                "scratch",
            )
        ):
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imported.add(name.name.split(".")[0].lower())
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported.add(node.module.split(".")[0].lower())
        except Exception:
            pass

    return imported


def yagni_audit_dependencies(project_root) -> list:
    """
    Проверяет импорты во всех .py файлах репозитория и сопоставляет их с зависимостями в pyproject.toml.
    Возвращает список неиспользуемых зависимостей.
    """
    root_path = Path(project_root)
    clean_deps = get_pyproject_dependencies(root_path)
    if not clean_deps:
        return []

    imported = get_imported_modules(root_path)
    unused = []

    for dep in clean_deps:
        module_name = PACKAGE_TO_MODULE_MAP.get(dep, dep.replace("-", "_"))
        if module_name not in imported:
            if dep.replace("-", "_") not in imported:
                unused.append(dep)

    return sorted(unused)
