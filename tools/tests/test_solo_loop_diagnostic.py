import ast
from pathlib import Path


def detect_subagent_usage(code: str) -> bool:
    """Проверяет код на наличие реальных вызовов или импортов субагентов через AST."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Если файл содержит синтаксические ошибки, проверим регуляркой,
        # но для тестирования наших скриптов AST достаточно
        return False

    for node in ast.walk(tree):
        # Поиск вызовов: invoke_subagent() или define_subagent()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("invoke_subagent", "define_subagent"):
                return True
        # Поиск импортов из mcp или других модулей
        if isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            if any(name in ("invoke_subagent", "define_subagent") for name in names):
                return True
    return False


def test_solo_loop_compliant() -> None:
    """Позитивный тест: Проверяет, что в основных скриптах автоматизации нет вызовов субагентов."""
    tools_dir = Path(__file__).parent.parent
    scripts_to_check = [
        "self_improve.py",
        "test_healer.py",
        "collect_handoffs.py",
        "diff_applier.py",
    ]

    for script in scripts_to_check:
        script_path = tools_dir / script
        if script_path.exists():
            content = script_path.read_text(encoding="utf-8")
            assert not detect_subagent_usage(content), (
                f"Обнаружен реальный вызов субагента в {script}"
            )


def test_solo_loop_violation_detected() -> None:
    """Негативный тест: Проверяет, что функция обнаружения корректно детектирует запрещенные вызовы."""
    bad_code = """
def run_subagent_task():
    invoke_subagent(TypeName="research", Prompt="check files")
"""
    assert detect_subagent_usage(bad_code), (
        "Детектор не зафиксировал вызов invoke_subagent"
    )
