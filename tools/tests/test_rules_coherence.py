import os
import re
from pathlib import Path

import pytest

try:
    from tools.config import get_workspace_root
except ImportError:
    from config import get_workspace_root

workspace_root = get_workspace_root()
home = Path.home()

# Список путей к файлам правил на хосте
RULES_FILES = {
    "GEMINI_ANTIGRAVITY.md": str(home / "GEMINI_ANTIGRAVITY.md"),
    "STUDENT_GUIDE.md": str(home / "STUDENT_GUIDE.md"),
    "CLAUDE.md": str(workspace_root / "CLAUDE.md"),
    "AGENTS.md": str(workspace_root / "AGENTS.md"),
    "gem_bot_prompt_architect.md": str(
        home / "Desktop" / "gem_bot_prompt_architect.md"
    ),
    "gemini_bot_knowledge_base.md": str(
        home / "Desktop" / "gemini_bot_knowledge_base.md"
    ),
}


def load_file_content(path: str) -> str:
    """Безопасно считывает контент файла, если он существует."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


def test_no_subagent_contradictions():
    """
    Тест проверяет, что в правилах нет противоречивых утверждений,
    разрешающих использование субагентов. Должен быть только полный Solo Loop.
    """
    found_any = False
    for name, path in RULES_FILES.items():
        content = load_file_content(path)
        if not content:
            continue
        found_any = True

        # Проверяем, что в правилах нет фраз, утверждающих совместную работу с субагентами
        # (например, "Исполнители-субагенты" или "субагенты пишут код")
        assert not re.search(
            r"(субагенты.*исполнители|субагенты.*пишут.*код|архитектор.*и.*исполнители)",
            content,
            re.IGNORECASE,
        ), (
            f"В файле {name} найдено противоречивое упоминание субагентов как исполнителей"
        )

    if not found_any:
        pytest.skip("Файлы правил недоступны в текущем окружении (например, в CI)")


def test_no_home_workdir_paths():
    """
    Тест проверяет, что в правилах в качестве рабочего окружения агента
    не прописан путь /home/workdir (разрешен только /Users/rus/ на macOS).
    """
    found_any = False
    for name, path in RULES_FILES.items():
        content = load_file_content(path)
        if not content:
            continue
        found_any = True

        # Разрешено упоминать /home/workdir только в контексте запрета (например, "/home/workdir/ строго запрещено")
        # Но нельзя писать "рабочая папка /home/workdir" или использовать его как дефолтный путь.
        # Ищем случаи, где /home/workdir предлагается использовать как рабочий путь.
        matches = re.findall(
            r"([^.\n]*\/home\/workdir\/?[^.\n]*)", content, re.IGNORECASE
        )
        for match in matches:
            assert any(
                keyword in match.lower()
                for keyword in [
                    "запрещено",
                    "запрещены",
                    "запрещен",
                    "forbidden",
                    "нельзя",
                    "исключить",
                    "соотносится с",
                    "исключено",
                ]
            ), (
                f"В файле {name} найден неразрешенный контекст использования /home/workdir: '{match}'"
            )

    if not found_any:
        pytest.skip("Файлы правил недоступны в текущем окружении")


def test_katex_in_kpi_formulas():
    """
    Тест проверяет, что в правилах математические KPI (T_video, U_jaccard, T_saved)
    оформлены в разметке KaTeX.
    """
    found_any = False
    for name, path in RULES_FILES.items():
        content = load_file_content(path)
        if not content:
            continue
        found_any = True

        # Ищем некорректное использование KPI без знаков доллара $
        # Например, T_video > 90 или U_jaccard > 60%
        # В KaTeX должно быть: $T_{video} > 90$ или $U_{jaccard}$
        bad_patterns = [
            r"\bT_video\b",
            r"\bU_jaccard\b",
            r"\bt_ui\b",
            r"\bT_saved\b",
        ]
        for pattern in bad_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                start = max(0, match.start() - 10)
                end = min(len(content), match.end() + 10)
                context = content[start:end]
                # Проверяем, окружен ли найденный паттерн знаками $
                assert "$" in context, (
                    f"В файле {name} KPI формула '{match.group(0)}' оформлена без KaTeX: '{context}'"
                )

    if not found_any:
        pytest.skip("Файлы правил недоступны в текущем окружении")
