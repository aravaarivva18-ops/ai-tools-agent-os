import pathlib
from functools import lru_cache

PROMPT_DIR = pathlib.Path(__file__).resolve().parent / "prompts"


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Лениво считывает и кэширует шаблон промпта из папки prompts."""
    # Нормализуем имя (убираем расширение, если передано)
    clean_name = name
    if name.endswith(".md"):
        clean_name = name[:-3]
    elif name.endswith(".txt"):
        clean_name = name[:-4]

    prompt_path = PROMPT_DIR / f"{clean_name}.md"
    if not prompt_path.exists():
        # Попробуем с расширением .txt на случай фолбэка
        prompt_path = PROMPT_DIR / f"{clean_name}.txt"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Шаблон промпта '{name}' не найден по пути {PROMPT_DIR}")

    return prompt_path.read_text(encoding="utf-8")


def render_prompt(name: str, **vars) -> str:
    """Лениво загружает шаблон и подставляет в него переменные."""
    template = load_prompt(name)
    try:
        return template.format(**vars)
    except KeyError as e:
        # Для безопасности, если шаблон содержит фигурные скобки, не являющиеся переменными,
        # или отсутствуют ожидаемые переменные.
        # В случае ошибки format() мы можем сделать простой replace или вернуть исходный шаблон.
        raise KeyError(
            f"Ошибка форматирования промпта '{name}': отсутствует переменная {e}"
        ) from e
