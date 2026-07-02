#!/usr/bin/env python3
"""
Helper utilities for Antigravity self-improvement loop.
Contains query generators, prompt optimizers, and friction points detectors.
"""


def generate_research_queries(category: str, issue_content: str) -> list:
    """Генерирует целевые поисковые запросы для GitHub/arXiv/Web на основе описания проблемы."""
    clean_text = "".join(
        c if c.isalnum() or c.isspace() else " " for c in issue_content
    ).strip()
    words = [w for w in clean_text.split() if len(w) > 3][:6]
    keywords = " ".join(words)

    queries = [
        f"site:github.com {category} {keywords}",
        f"site:arxiv.org {category} {keywords}",
        f"best practices {category} {keywords}",
    ]
    return queries


def detect_tool_conflicts(logs: list) -> list:
    """Анализирует логи трения на наличие конфликтов инструментов."""
    conflicts = []
    for log in logs:
        for pt in log.get("friction_points", []):
            content = pt.get("content", "").lower()
            if any(
                k in content
                for k in [
                    "subagent",
                    "субагент",
                    "sub-agent",
                    "invoke_subagent",
                    "define_subagent",
                ]
            ):
                conflicts.append(
                    f"Session {log.get('session_id')}: Найдено упоминание субагентов или вызовов invoke_subagent/define_subagent. Убедитесь, что используется Solo Loop по умолчанию."
                )
    return list(set(conflicts))


def optimize_prompt_for_speed(category: str, issue_content: str) -> str:
    """Создает оптимизированный сжатый промпт для устранения указанной проблемы."""
    lines = [line.strip() for line in issue_content.splitlines() if line.strip()]
    first_line = lines[0] if lines else ""

    clean_line = "".join(
        c if c.isalnum() or c.isspace() else " " for c in first_line
    ).strip()
    summary = " ".join(clean_line.split()[:10])

    return f"Исправь {category}: {summary}. Используй TDD, YAGNI (max 3 levels) и Solo Loop."


def suggest_tool_combinations(category: str) -> str:
    """Рекомендует эффективные комбинации инструментов для решения проблемы."""
    cat_lower = category.lower()
    if "oom" in cat_lower or "memory" in cat_lower or "памят" in cat_lower:
        return "`view_file` (ограничение чтения строк) + `run_command` (очистка памяти/проверка логов)"
    if (
        "тест" in cat_lower
        or "ошибк" in cat_lower
        or "fail" in cat_lower
        or "error" in cat_lower
    ):
        return "`replace_file_content` (точечные правки) + `run_command` (запуск тестов) + `tools/test_healer.py` (автоисправление)"
    return "`search_web` (сбор фактов) + `replace_file_content` (правка) + `make check-rules` (валидация)"


def analyze_self_healing_needs(issue_content: str) -> str:
    """Определяет, нужен ли запуск test_healer.py для самовосстановления."""
    content_lower = issue_content.lower()
    if any(
        k in content_lower
        for k in ["failed", "assert", "traceback", "syntaxerror", "import"]
    ):
        return "⚠️ Рекомендуется запуск `tools/test_healer.py` для автоматического исправления тестов/импортов."
    return (
        "💡 Проблема решается стандартным редактированием через `replace_file_content`."
    )
