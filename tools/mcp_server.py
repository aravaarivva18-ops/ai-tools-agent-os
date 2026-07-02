#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

try:
    from tools.tool_registry import ToolRegistry
except ImportError:
    from tool_registry import ToolRegistry

registry = ToolRegistry()

# Инициализируем FastMCP сервер
mcp = FastMCP("ai-tools")

# Определяем пути к скриптам
TOOLS_DIR = Path(__file__).resolve().parent


@mcp.tool()
async def apply_patch(target_file: str, patch_text: str) -> str:
    """
    Применяет SEARCH/REPLACE патч к указанному файлу.

    Args:
        target_file: Абсолютный путь к целевому файлу.
        patch_text: Текст SEARCH/REPLACE патча.
    """
    try:
        registry.enforce_tool_policy("apply_patch")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not is_safe_path(target_file):
        return f"ERROR: Access denied: path {target_file} is outside jail."

    # Создаем бэкап перед изменением
    _create_checkpoint(target_file)

    script_path = TOOLS_DIR / "diff_applier.py"
    if not script_path.exists():
        return "Error: diff_applier.py not found."

    # Запускаем асинхронно
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script_path),
        target_file,
        patch_text,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        return f"SUCCESS:\n{stdout.decode('utf-8')}"
    else:
        return f"ERROR (exit code {proc.returncode}):\n{stderr.decode('utf-8') or stdout.decode('utf-8')}"


@mcp.tool()
async def run_tests(
    test_file: str, target_file: str = None, patch_text: str = None, timeout: int = 10
) -> str:
    """
    Запускает юнит-тесты через test_healer.py (с автоматическим исправлением стиля Ruff перед прогоном).
    Если указаны target_file и patch_text, сначала накладывает патч (делая бэкап), а в случае падения тестов откатывает его.

    Args:
        test_file: Путь к файлу тестов.
        target_file: Необязательный путь к целевому файлу для наложения патча.
        patch_text: Необязательный текст патча.
        timeout: Таймаут выполнения тестов в секундах (по умолчанию 10).
    """
    try:
        registry.enforce_tool_policy("run_tests")
    except PermissionError as e:
        return f"ERROR: {e}"

    script_path = TOOLS_DIR / "test_healer.py"
    if not script_path.exists():
        return "Error: test_healer.py not found."

    cmd = [sys.executable, str(script_path), test_file, f"--timeout={timeout}"]
    if target_file and patch_text:
        cmd += ["--target", target_file, "--patch", patch_text]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    output = stdout.decode("utf-8") + "\n" + stderr.decode("utf-8")
    if proc.returncode == 0:
        return f"TESTS PASSED:\n{output}"
    else:
        return f"TESTS FAILED (exit code {proc.returncode}):\n{output}"


@mcp.tool()
async def obsidian_log(handoff_path: str, conv_id: str) -> str:
    """
    Записывает результаты сессии (handoff) в Daily Note в Obsidian и переиндексирует базу знаний.

    Args:
        handoff_path: Абсолютный путь к файлу HANDOFF.md.
        conv_id: Уникальный ID текущей сессии (conversation ID).
    """
    try:
        registry.enforce_tool_policy("obsidian_log")
    except PermissionError as e:
        return f"ERROR: {e}"

    # Вызываем сборщик хандоффов
    collect_script = TOOLS_DIR / "collect_handoffs.py"
    if collect_script.exists():
        await asyncio.create_subprocess_exec(
            sys.executable,
            str(collect_script),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

    # Вызываем логгер сессий
    logger_script = TOOLS_DIR / "obsidian" / "session_logger.py"
    if not logger_script.exists():
        return "Error: session_logger.py not found."

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(logger_script),
        handoff_path,
        "--conv-id",
        conv_id,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        return f"LOGGED SUCCESS:\n{stdout.decode('utf-8')}"
    else:
        return f"ERROR LOGGING:\n{stderr.decode('utf-8') or stdout.decode('utf-8')}"


@mcp.tool()
async def obsidian_search(query: str) -> str:
    """
    Выполняет локальный семантический поиск по хэндоффам и базе знаний Obsidian.

    Args:
        query: Поисковый запрос на естественном языке.
    """
    try:
        registry.enforce_tool_policy("obsidian_search")
    except PermissionError as e:
        return f"ERROR: {e}"

    script_path = TOOLS_DIR / "obsidian" / "semantic_search.py"
    if not script_path.exists():
        return "Error: semantic_search.py not found."

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script_path),
        query,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        return stdout.decode("utf-8")
    else:
        return f"SEARCH ERROR:\n{stderr.decode('utf-8')}"


_current_file: str | None = None
_current_line: int = 1
_num_lines: int = 100


def is_safe_path(filepath: str) -> bool:
    try:
        abs_path = os.path.abspath(filepath)
        jail_dir = "/Users/rus/ai-tools"
        return abs_path == jail_dir or abs_path.startswith(jail_dir + os.sep)
    except Exception:
        return False


def _create_checkpoint(file_path: str) -> bool:
    import hashlib
    import shutil

    try:
        path = Path(file_path).resolve()
        if not path.exists() or not path.is_file():
            return False
        checkpoint_dir = Path("/Users/rus/ai-tools/scratch/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        path_hash = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:8]
        backup_name = f"{path.name}_{path_hash}.bak"
        backup_path = checkpoint_dir / backup_name

        shutil.copy2(path, backup_path)
        return True
    except Exception:
        return False


@mcp.tool()
async def fs_read_slice(
    file_path: str, start_line: int = 1, num_lines: int = 100
) -> str:
    """
    Возвращает слайс строк из указанного файла в пределах контекстного бюджета (макс 100 строк).
    Сохраняет состояние для последующей навигации через scroll_up/scroll_down.

    Args:
        file_path: Абсолютный путь к файлу.
        start_line: Индекс начальной строки (1-indexed).
        num_lines: Количество строк для чтения (максимум 100).
    """
    global _current_file, _current_line, _num_lines
    try:
        registry.enforce_tool_policy("fs_read_slice")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not is_safe_path(file_path):
        return f"ERROR: Access denied: path {file_path} is outside jail."

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return f"ERROR: File {file_path} not found."

    # Ограничение размера
    actual_num_lines = min(max(1, num_lines), 100)

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        total_lines = len(lines)

        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + actual_num_lines)

        slice_lines = lines[start_idx:end_idx]

        # Обновляем состояние
        _current_file = file_path
        _current_line = start_idx + 1
        _num_lines = actual_num_lines

        formatted = []
        for idx, line in enumerate(slice_lines, start=_current_line):
            formatted.append(f"{idx}: {line}")

        header = f"=== File: {file_path} (Lines {start_idx + 1}-{end_idx} of {total_lines}) ===\n"
        return header + "\n".join(formatted)
    except Exception as e:
        return f"ERROR reading file: {e}"


@mcp.tool()
async def fs_read_skeleton(file_path: str) -> str:
    """
    Возвращает структуру (скелет) файла: импорты, классы, сигнатуры функций.
    Для не-Python файлов возвращает первые 30 строк.

    Args:
        file_path: Абсолютный путь к файлу.
    """
    import ast

    try:
        registry.enforce_tool_policy("fs_read_skeleton")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not is_safe_path(file_path):
        return f"ERROR: Access denied: path {file_path} is outside jail."

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return f"ERROR: File {file_path} not found."

    try:
        if file_path.endswith(".py"):
            source_code = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return f"ERROR: Syntax error in python file: {e}"

            output = []

            def get_func_sig(node) -> str:
                try:
                    sig = ast.unparse(node.args)
                    is_async = (
                        "async " if isinstance(node, ast.AsyncFunctionDef) else ""
                    )
                    return f"{is_async}def {node.name}({sig}):"
                except Exception:
                    args = [a.arg for a in node.args.args]
                    is_async = (
                        "async " if isinstance(node, ast.AsyncFunctionDef) else ""
                    )
                    return f"{is_async}def {node.name}({', '.join(args)}):"

            for item in tree.body:
                if isinstance(item, (ast.Import, ast.ImportFrom)):
                    try:
                        output.append(ast.unparse(item))
                    except Exception:
                        pass
                elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    output.append(get_func_sig(item) + "\n    ...")
                elif isinstance(item, ast.ClassDef):
                    bases = ""
                    if item.bases:
                        try:
                            bases = f"({', '.join(ast.unparse(b) for b in item.bases)})"
                        except Exception:
                            pass
                    class_header = f"class {item.name}{bases}:"
                    output.append(class_header)
                    class_body_found = False
                    for subitem in item.body:
                        if isinstance(subitem, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            output.append(
                                "    " + get_func_sig(subitem) + "\n        ..."
                            )
                            class_body_found = True
                    if not class_body_found:
                        output.append("    ...")

            header = f"=== Python File Structure: {file_path} ===\n"
            return header + "\n\n".join(output)
        else:
            # Для не-Python файлов возвращаем первые 30 строк
            lines = path.read_text(encoding="utf-8").splitlines()
            total_lines = len(lines)
            slice_lines = lines[:30]
            header = (
                f"=== File Preview (First 30 lines of {total_lines}): {file_path} ===\n"
            )
            footer = "\n... [truncated]" if total_lines > 30 else ""
            return header + "\n".join(slice_lines) + footer
    except Exception as e:
        return f"ERROR reading file: {e}"


@mcp.tool()
async def restore_checkpoint(target_file: str) -> str:
    """
    Восстанавливает файл из последней контрольной точки (undo последнего изменения).

    Args:
        target_file: Абсолютный путь к целевому файлу.
    """
    import hashlib

    try:
        registry.enforce_tool_policy("restore_checkpoint")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not is_safe_path(target_file):
        return f"ERROR: Access denied: path {target_file} is outside jail."

    try:
        path = Path(target_file).resolve()
        checkpoint_dir = Path("/Users/rus/ai-tools/scratch/checkpoints")
        path_hash = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:8]
        backup_name = f"{path.name}_{path_hash}.bak"
        backup_path = checkpoint_dir / backup_name

        if not backup_path.exists():
            return f"ERROR: No checkpoint found for file {target_file}."

        import shutil

        shutil.copy2(backup_path, path)
        return f"SUCCESS: Restored {target_file} from checkpoint {backup_name}."
    except Exception as e:
        return f"ERROR restoring checkpoint: {e}"


@mcp.tool()
async def scroll_up() -> str:
    """Прокручивает текущий открытый файл вверх на сохраненное количество строк."""
    global _current_file, _current_line, _num_lines
    try:
        registry.enforce_tool_policy("scroll_up")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not _current_file:
        return "ERROR: No active file stream. Call fs_read_slice first."

    new_start = max(1, _current_line - _num_lines)
    return await fs_read_slice(
        _current_file, start_line=new_start, num_lines=_num_lines
    )


@mcp.tool()
async def scroll_down() -> str:
    """Прокручивает текущий открытый файл вниз на сохраненное количество строк."""
    global _current_file, _current_line, _num_lines
    try:
        registry.enforce_tool_policy("scroll_down")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not _current_file:
        return "ERROR: No active file stream. Call fs_read_slice first."

    new_start = _current_line + _num_lines
    return await fs_read_slice(
        _current_file, start_line=new_start, num_lines=_num_lines
    )


@mcp.tool()
async def goto(line: int) -> str:
    """
    Перемещает указатель чтения текущего открытого файла на заданную строку.

    Args:
        line: Номер строки для перехода (1-indexed).
    """
    global _current_file, _current_line, _num_lines
    try:
        registry.enforce_tool_policy("goto")
    except PermissionError as e:
        return f"ERROR: {e}"

    if not _current_file:
        return "ERROR: No active file stream. Call fs_read_slice first."

    return await fs_read_slice(_current_file, start_line=line, num_lines=_num_lines)


if __name__ == "__main__":
    # Запускаем MCP stdio сервер
    mcp.run()
