import os
from pathlib import Path

# Список разрешенных инструментов по режимам
# (соответствует именам функций-инструментов в mcp_server.py и CLI командам)
MODE_SHORTLISTS = {
    "inspect": {
        "obsidian_search",
        "doctor",
        "search",
        "fs_read_slice",
        "fs_read_skeleton",
        "scroll_up",
        "scroll_down",
        "goto",
        "restore_checkpoint",
    },
    "patch": {
        "obsidian_search",
        "doctor",
        "search",
        "apply_patch",
        "improve",
        "fs_read_slice",
        "fs_read_skeleton",
        "scroll_up",
        "scroll_down",
        "goto",
        "restore_checkpoint",
    },
    "verify": {
        "obsidian_search",
        "doctor",
        "search",
        "run_tests",
        "validate",
        "test",
        "fs_read_slice",
        "fs_read_skeleton",
        "scroll_up",
        "scroll_down",
        "goto",
        "restore_checkpoint",
    },
    "git": {
        "obsidian_search",
        "doctor",
        "search",
        "log",
        "clean",
        "build",
        "fs_read_slice",
        "fs_read_skeleton",
        "scroll_up",
        "scroll_down",
        "goto",
        "restore_checkpoint",
    },
    "mcp": {
        "obsidian_search",
        "doctor",
        "search",
        "obsidian_log",
        "mcp",
        "fs_read_slice",
        "fs_read_skeleton",
        "scroll_up",
        "scroll_down",
        "goto",
        "restore_checkpoint",
    },
}


class ToolRegistry:
    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = workspace_root

    def get_current_mode(self) -> str:
        """
        Определяет текущий режим работы.
        Сначала проверяется переменная окружения AGY_MODE.
        Затем анализируется implementation_plan.md на предмет активного шага.
        """
        env_mode = os.environ.get("AGY_MODE")
        if env_mode in MODE_SHORTLISTS:
            return env_mode

        plan_path = self.workspace_root / "implementation_plan.md"
        if not plan_path.exists():
            plan_path = Path.home() / ".gemini" / "antigravity-cli" / "brain"
            # Попробуем найти первый попавшийся implementation_plan.md
            plans = list(plan_path.glob("**/implementation_plan.md"))
            if plans:
                plan_path = plans[0]

        if plan_path.exists():
            try:
                with open(plan_path, encoding="utf-8") as f:
                    content = f.read()

                # Ищем первый невыполненный шаг (вида "- [ ]")
                for line in content.splitlines():
                    if "- [ ]" in line:
                        line_lower = line.lower()
                        if any(
                            kw in line_lower
                            for kw in ("тест", "проверить", "test", "verify", "валид")
                        ):
                            return "verify"
                        if any(
                            kw in line_lower
                            for kw in (
                                "внедрить",
                                "добавить",
                                "написать",
                                "реализовать",
                                "создать",
                                "add",
                                "implement",
                                "write",
                            )
                        ):
                            return "patch"
                        if any(
                            kw in line_lower
                            for kw in (
                                "исследовать",
                                "изучить",
                                "найти",
                                "search",
                                "explore",
                                "read",
                            )
                        ):
                            return "inspect"
            except Exception:
                pass

        # Дефолтный режим
        return "inspect"

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Проверяет, разрешен ли вызов инструмента в текущем режиме."""
        current_mode = self.get_current_mode()
        allowed_tools = MODE_SHORTLISTS.get(current_mode, set())
        return tool_name in allowed_tools

    def enforce_tool_policy(self, tool_name: str) -> None:
        """Вызывает PermissionError, если инструмент не разрешен."""
        # 1. Проверяем Viewer/Editor Split
        role = os.environ.get("AGY_ROLE", "editor").lower()
        if role == "viewer":
            # Мутирующие инструменты запрещены для Viewer роли
            mutating_tools = {
                "apply_patch",
                "run_tests",
                "obsidian_log",
                "restore_checkpoint",
            }
            if tool_name in mutating_tools:
                raise PermissionError(
                    f"Access Denied: Tool '{tool_name}' is mutating and cannot be called under role '{role}'."
                )

        # 2. Стандартная проверка по режиму
        if not self.is_tool_allowed(tool_name):
            current_mode = self.get_current_mode()
            raise PermissionError(
                f"Access Denied: Tool '{tool_name}' is not allowed in current mode '{current_mode}'."
            )
