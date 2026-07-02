import ast
import os
from pathlib import Path


def is_safe_path(path_str: str, workspace_root: Path) -> bool:
    """Проверяет, находится ли путь внутри воркспейса (для предотвращения удаления системных файлов)."""
    try:
        resolved_root = workspace_root.resolve()
        # Если путь относительный, он считается безопасным (относительно корня или текущей папки)
        if not os.path.isabs(path_str):
            return True
        resolved_path = Path(path_str).resolve()
        return resolved_root in resolved_path.parents or resolved_path == resolved_root
    except Exception:
        return False


def verify_code_safety(
    file_path: str, workspace_root: Path = None
) -> tuple[bool, str | None]:
    """
    Выполняет статический анализ Python файла на наличие потенциально опасных системных вызовов
    и операций с файловой системой вне воркспейса перед запуском тестов.
    """
    if not os.path.exists(file_path):
        return True, None

    if workspace_root is None:
        # Автоопределение корня воркспейса
        workspace_root = Path(file_path).resolve().parent
        while workspace_root.parent != workspace_root:
            if (workspace_root / ".git").exists() or (
                workspace_root / "pyproject.toml"
            ).exists():
                break
            workspace_root = workspace_root.parent

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)
    except Exception as e:
        return False, f"Ошибка синтаксического анализа (AST parse error): {e}"

    for node in ast.walk(tree):
        # 1. Проверка импортов сетевых библиотек (в тестах сеть должна быть замокана)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            for name in names:
                if name in (
                    "socket",
                    "requests",
                    "httpx",
                    "urllib",
                    "aiohttp",
                ) and "test" in os.path.basename(file_path):
                    return (
                        False,
                        f"Запрещен импорт сетевой библиотеки '{name}' в тестовом файле. Сетевые вызовы должны быть замоканы.",
                    )

        # 2. Проверка вызовов функций (Call)
        elif isinstance(node, ast.Call):
            func = node.func
            func_name = ""

            # Вытаскиваем имя функции (например: os.system или shutil.rmtree)
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                # Для вызовов типа module.function
                parts = []
                curr = func
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                parts.reverse()
                func_name = ".".join(parts)

            # Блокировка опасных системных вызовов
            if func_name in (
                "os.system",
                "subprocess.call",
                "subprocess.check_call",
                "sh",
            ):
                return (
                    False,
                    f"Обнаружен запрещенный системный вызов '{func_name}'. Использование внешнего шелла в тестах небезопасно.",
                )

            # Блокировка деструктивных файловых операций вне воркспейса
            if func_name in (
                "shutil.rmtree",
                "os.remove",
                "os.unlink",
                "os.rmdir",
                "shutil.move",
            ):
                # Пытаемся проверить аргументы
                if node.args:
                    first_arg = node.args[0]
                    # Если путь передан как строковая константа (ast.Constant)
                    if isinstance(first_arg, ast.Constant) and isinstance(
                        first_arg.value, str
                    ):
                        path_val = first_arg.value
                        if not is_safe_path(path_val, workspace_root):
                            return (
                                False,
                                f"Попытка удаления/перемещения файла за пределами воркспейса: {func_name}('{path_val}')",
                            )
                    # Если путь передан как динамическое выражение, требуем ручного подтверждения безопасности
                    elif not isinstance(first_arg, ast.Constant):
                        # В тестах допускаются динамические пути, если они явно создаются внутри временных папок (например, tmp_path, tmpdir)
                        # Мы даем предупреждение, но не блокируем, если имя переменной содержит 'tmp' или 'temp'
                        arg_str = (
                            ast.unparse(first_arg) if hasattr(ast, "unparse") else ""
                        )
                        if not any(
                            t in arg_str.lower()
                            for t in ("tmp", "temp", "bak", "backup", "test")
                        ):
                            return (
                                False,
                                f"Подозрительный динамический путь в деструктивном вызове: {func_name}({arg_str})",
                            )

    return True, None
