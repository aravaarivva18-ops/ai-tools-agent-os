import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.mcp_server import (
    apply_patch,
    fs_read_skeleton,
    fs_read_slice,
    goto,
    restore_checkpoint,
    scroll_down,
    scroll_up,
)
from tools.tool_registry import ToolRegistry


def run_coro(coro):
    """
    Вспомогательная функция для ручного выполнения корутины без запуска event loop,
    чтобы обойти блокировку сокетов pytest (pytest-socket).
    """
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    return None


def test_fs_read_slice_success():
    # Создаем файл внутри jail
    test_file = Path("/Users/rus/ai-tools/tools/tests/slice_test_file.txt")
    test_file.write_text(
        "\n".join([f"Line {i}" for i in range(1, 151)]), encoding="utf-8"
    )

    try:
        # Устанавливаем режим patch, в котором разрешен fs_read_slice
        with patch.dict(os.environ, {"AGY_MODE": "patch"}):
            # Читаем первые 50 строк
            res = run_coro(fs_read_slice(str(test_file), start_line=10, num_lines=50))
            assert "slice_test_file.txt" in res
            assert "Lines 10-59 of 150" in res
            assert "10: Line 10" in res
            assert "59: Line 59" in res
            assert "60: Line 60" not in res

    finally:
        if test_file.exists():
            test_file.unlink()


def test_fs_read_slice_max_limit():
    test_file = Path("/Users/rus/ai-tools/tools/tests/slice_test_file.txt")
    test_file.write_text(
        "\n".join([f"Line {i}" for i in range(1, 151)]), encoding="utf-8"
    )

    try:
        with patch.dict(os.environ, {"AGY_MODE": "patch"}):
            # Запрашиваем 120 строк, должно вернуться 100
            res = run_coro(fs_read_slice(str(test_file), start_line=1, num_lines=120))
            assert "Lines 1-100 of 150" in res

    finally:
        if test_file.exists():
            test_file.unlink()


def test_fs_read_slice_navigation():
    test_file = Path("/Users/rus/ai-tools/tools/tests/slice_test_file.txt")
    test_file.write_text(
        "\n".join([f"Line {i}" for i in range(1, 150)]), encoding="utf-8"
    )

    try:
        with patch.dict(os.environ, {"AGY_MODE": "patch"}):
            # Читаем сначала
            run_coro(fs_read_slice(str(test_file), start_line=1, num_lines=10))

            # Скроллим вниз
            res_down = run_coro(scroll_down())
            assert "Lines 11-20 of 149" in res_down

            # Скроллим вверх
            res_up = run_coro(scroll_up())
            assert "Lines 1-10 of 149" in res_up

    finally:
        if test_file.exists():
            test_file.unlink()


def test_tool_registry_viewer_role_blocks_mutation():
    registry = ToolRegistry()

    # Если роль - viewer
    with patch.dict(os.environ, {"AGY_ROLE": "viewer", "AGY_MODE": "patch"}):
        # Разрешено читать слайсы
        assert registry.is_tool_allowed("fs_read_slice") is True
        assert registry.is_tool_allowed("goto") is True

        # Мутирующие инструменты должны бросать PermissionError
        with pytest.raises(PermissionError) as exc:
            registry.enforce_tool_policy("apply_patch")
        assert "is mutating" in str(exc.value)

        with pytest.raises(PermissionError) as exc_test:
            registry.enforce_tool_policy("run_tests")
        assert "is mutating" in str(exc_test.value)


def test_fs_read_slice_goto():
    test_file = Path("/Users/rus/ai-tools/tools/tests/slice_test_file.txt")
    test_file.write_text(
        "\n".join([f"Line {i}" for i in range(1, 150)]), encoding="utf-8"
    )

    try:
        with patch.dict(os.environ, {"AGY_MODE": "patch"}):
            # Читаем сначала
            run_coro(fs_read_slice(str(test_file), start_line=1, num_lines=10))

            # Переходим на строку 50
            res = run_coro(goto(50))
            assert "slice_test_file.txt" in res
            assert "Lines 50-59 of 149" in res
            assert "50: Line 50" in res

    finally:
        if test_file.exists():
            test_file.unlink()


def test_fs_read_skeleton_success():
    test_file = Path("/Users/rus/ai-tools/tools/tests/skeleton_test_file.py")
    test_file.write_text(
        """import os
from pathlib import Path

class A(object):
    def method_one(self, x: int) -> str:
        return "one"

def hello_world(name: str = "world"):
    print("hello")
""",
        encoding="utf-8",
    )

    try:
        with patch.dict(os.environ, {"AGY_MODE": "patch"}):
            res = run_coro(fs_read_skeleton(str(test_file)))
            assert "class A(object):" in res
            assert "method_one" in res
            assert "hello_world" in res
            assert "import os" in res
            assert "from pathlib import Path" in res
            assert "return" not in res  # тело должно быть вырезано

    finally:
        if test_file.exists():
            test_file.unlink()


def test_checkpoint_create_and_restore():
    test_file = Path("/Users/rus/ai-tools/tools/tests/checkpoint_test_file.txt")
    test_file.write_text("Original Content", encoding="utf-8")

    try:
        # Накладываем патч (это должно создать бэкап)
        patch_text = "<<<<<<< SEARCH\nOriginal Content\n=======\nModified Content\n>>>>>>> REPLACE"

        with patch.dict(os.environ, {"AGY_MODE": "patch"}):
            import asyncio

            res_patch = asyncio.run(apply_patch(str(test_file), patch_text))
            assert "SUCCESS" in res_patch
            assert test_file.read_text(encoding="utf-8") == "Modified Content"

            # Восстанавливаем из бэкапа
            res_restore = asyncio.run(restore_checkpoint(str(test_file)))
            assert "SUCCESS" in res_restore
            assert test_file.read_text(encoding="utf-8") == "Original Content"

    finally:
        if test_file.exists():
            test_file.unlink()
        import hashlib

        path_hash = hashlib.sha256(
            str(test_file.resolve()).encode("utf-8")
        ).hexdigest()[:8]
        backup_path = (
            Path("/Users/rus/ai-tools/scratch/checkpoints")
            / f"{test_file.name}_{path_hash}.bak"
        )
        if backup_path.exists():
            backup_path.unlink()
