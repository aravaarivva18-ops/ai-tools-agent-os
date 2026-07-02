"""
Модуль для безопасной работы с JSON.
Использует ленивый импорт json_repair для исправления ошибок форматирования LLM.
"""

import json
from typing import Any


def safe_load_json(text: str) -> Any:
    """Пытается распарсить JSON. В случае ошибки использует json_repair для авто-исправления."""
    if not text:
        return None

    clean_text = text.strip()

    # Быстрая попытка через стандартный json.loads
    try:
        return json.loads(clean_text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Если не вышло, применяем json_repair
    try:
        import json_repair

        repaired = json_repair.repair_json(clean_text, return_objects=True)
        # Если результат - строка, но вход не был строкой в кавычках, значит ремонт не удался
        if isinstance(repaired, str) and not (clean_text.startswith('"') or clean_text.startswith("'")):
            return json.loads(clean_text)
        return repaired
    except Exception:
        # Фолбэк на оригинальное исключение json.loads для сохранения поведения
        return json.loads(clean_text)
