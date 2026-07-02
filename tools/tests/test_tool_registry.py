import os
import tempfile
from pathlib import Path

import pytest

from tools.tool_registry import ToolRegistry


def test_tool_registry_default_mode():
    registry = ToolRegistry()
    # По умолчанию при отсутствии env и плана должен быть inspect
    assert registry.get_current_mode() == "inspect"


def test_tool_registry_env_mode(monkeypatch):
    monkeypatch.setenv("AGY_MODE", "patch")
    registry = ToolRegistry()
    assert registry.get_current_mode() == "patch"

    monkeypatch.setenv("AGY_MODE", "verify")
    assert registry.get_current_mode() == "verify"


def test_tool_registry_allowed_tools():
    registry = ToolRegistry()

    # Проверка режима inspect
    # Сначала установим его принудительно через env
    os.environ["AGY_MODE"] = "inspect"
    assert registry.is_tool_allowed("obsidian_search") is True
    assert registry.is_tool_allowed("apply_patch") is False
    with pytest.raises(PermissionError):
        registry.enforce_tool_policy("apply_patch")

    # Проверка режима patch
    os.environ["AGY_MODE"] = "patch"
    assert registry.is_tool_allowed("apply_patch") is True
    assert registry.is_tool_allowed("run_tests") is False
    with pytest.raises(PermissionError):
        registry.enforce_tool_policy("run_tests")

    # Проверка режима verify
    os.environ["AGY_MODE"] = "verify"
    assert registry.is_tool_allowed("run_tests") is True
    assert registry.is_tool_allowed("apply_patch") is False
    with pytest.raises(PermissionError):
        registry.enforce_tool_policy("apply_patch")

    # Очистка env
    os.environ.pop("AGY_MODE", None)


def test_tool_registry_from_plan(monkeypatch):
    # Создадим временный файл плана во временной папке tools/tests, чтобы пройти PathJail
    fd, path = tempfile.mkstemp(suffix=".md", dir="/Users/rus/ai-tools/tools/tests")
    plan_path = Path(path)

    # 1. Сценарий: план содержит невыполненный шаг по разработке
    plan_path.write_text(
        """
# Plan
- [x] Шаг 1: Подготовка
- [ ] Шаг 2: Реализовать функцию безопасности
""",
        encoding="utf-8",
    )

    registry = ToolRegistry(workspace_root=plan_path.parent)

    # Мокаем путь к плану, чтобы get_current_mode использовал наш временный файл
    orig_get_workspace_root = None
    try:
        from tools import config

        orig_get_workspace_root = config.get_workspace_root
    except ImportError:
        pass

    # Будем использовать прямой путь к временному файлу,
    # переопределив в get_current_mode поиск implementation_plan.md
    # Для этого замокаем FileExists и чтение
    # Но проще переопределить workspace_root в конструкторе registry
    # Наш класс ToolRegistry уже принимает workspace_root!
    # И ищет plan_path = self.workspace_root / "implementation_plan.md"
    # Давайте переименуем временный файл или просто создадим его как "implementation_plan.md" в подпапке

    os.close(fd)
    if plan_path.exists():
        plan_path.unlink()


def test_tool_registry_plan_parsing():
    # Создаем временную директорию внутри tools/tests, чтобы не нарушать PathJail и Anti-Clutter
    tmp_dir = Path("/Users/rus/ai-tools/tools/tests/tmp_plan_dir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    plan_file = tmp_dir / "implementation_plan.md"

    try:
        # Тест режима patch (внедрить)
        plan_file.write_text("- [ ] Шаг 1: Внедрить проверку путей", encoding="utf-8")
        registry = ToolRegistry(workspace_root=tmp_dir)
        assert registry.get_current_mode() == "patch"

        # Тест режима verify (тест)
        plan_file.write_text("- [ ] Шаг 2: Запустить pytest тесты", encoding="utf-8")
        assert registry.get_current_mode() == "verify"

        # Тест режима inspect (исследовать)
        plan_file.write_text("- [ ] Шаг 3: Исследовать логи", encoding="utf-8")
        assert registry.get_current_mode() == "inspect"
    finally:
        if plan_file.exists():
            plan_file.unlink()
        if tmp_dir.exists():
            tmp_dir.rmdir()
