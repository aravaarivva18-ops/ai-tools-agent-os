import ast
import re
from pathlib import Path


def analyze_abstraction_levels(content: str) -> int:
    """Анализирует контент на количество уровней абстракции.
    Считает количество классов с паттернами: Interface/ABC -> Implementation -> Factory -> Wrapper/Adapter/Decorator.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return 0

    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    levels = 0
    has_interface = any(re.search(r'(interface|abc|base)', c, re.IGNORECASE) for c in classes)
    has_impl = any(not re.search(r'(interface|abc|base|factory|wrapper|adapter|decorator)', c, re.IGNORECASE) for c in classes) and len(classes) > 0
    has_factory = any(re.search(r'factory', c, re.IGNORECASE) for c in classes)
    has_wrapper = any(re.search(r'(wrapper|adapter|decorator)', c, re.IGNORECASE) for c in classes)

    if has_interface:
        levels += 1
    if has_impl:
        levels += 1
    if has_factory:
        levels += 1
    if has_wrapper:
        levels += 1

    return levels

def detect_subagent_usage(code: str) -> bool:
    """Проверяет код на попытку вызова или определения субагентов."""
    # Поиск использования инструментов define_subagent или invoke_subagent в коде или промптах
    pattern = re.compile(r'(define_subagent|invoke_subagent)', re.IGNORECASE)
    return bool(pattern.search(code))

def test_gemini_antigravity_version_positive():
    """Позитивный тест: Проверяет, что GEMINI_ANTIGRAVITY.md содержит Max Power Protocol v3.0."""
    path = Path("/Users/rus/GEMINI_ANTIGRAVITY.md")
    assert path.exists(), "GEMINI_ANTIGRAVITY.md не найден"
    content = path.read_text(encoding="utf-8")
    assert "Max Power & Self-* Protocol v3.0" in content, "Отсутствует актуальная версия протокола Max Power v3.0"

def test_yagni_levels_negative():
    """Негативный тест: Симулирует нарушение YAGNI (глубокие абстракции) и убеждается, что анализатор фиксирует >= 3 уровня."""
    bad_code = """
class BaseUserRepositoryInterface:
    def get_user(self, user_id: int):
        pass

class SqlUserRepository(BaseUserRepositoryInterface):
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "Test"}

class UserRepositoryFactory:
    @staticmethod
    def create():
        return SqlUserRepository()

class UserRepositoryLoggingWrapper:
    def __init__(self, repo):
        self._repo = repo
    def get_user(self, user_id: int):
        print("Logging...")
        return self._repo.get_user(user_id)
"""
    levels = analyze_abstraction_levels(bad_code)
    assert levels >= 3, f"Ожидалось нарушение YAGNI (уровни >= 3), но получено: {levels}"

def test_solo_loop_enforced_positive():
    """Позитивный тест: Проверяет наличие требований строгого Solo Loop и блокировки субагентов в базах знаний."""
    kb_path = Path("/Users/rus/Desktop/gemini_bot_knowledge_base.md")
    antigravity_path = Path("/Users/rus/GEMINI_ANTIGRAVITY.md")

    assert kb_path.exists(), "gemini_bot_knowledge_base.md не найден"
    assert antigravity_path.exists(), "GEMINI_ANTIGRAVITY.md не найден"

    kb_content = kb_path.read_text(encoding="utf-8")
    ag_content = antigravity_path.read_text(encoding="utf-8")

    assert "strictly disabled and blocked" in kb_content, "В System Prompt не зафиксирована блокировка субагентов"
    assert "категорически запрещено" in ag_content, "В конституции не прописан запрет субагентов"

def test_subagent_invocation_attempt_negative():
    """Негативный тест: Симулирует попытку вызова субагента в промпте/коде и проверяет, что детектор блокирует это."""
    bad_prompt_or_code = """
    We need to spawn a research subagent to do this task.
    Call invoke_subagent(TypeName="research", Prompt="check files")
    """
    is_blocked = detect_subagent_usage(bad_prompt_or_code)
    assert is_blocked, "Попытка вызова субагента не была заблокирована/детектирована"
