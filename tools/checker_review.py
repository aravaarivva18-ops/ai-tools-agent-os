import os
import re
from pathlib import Path

# Список запрещенных ИИ-маркеров (Stop-Slop)
FORBIDDEN_MARKERS_EN = {
    "delve",
    "tapestry",
    "beacon",
    "dynamic landscape",
    "underscore",
    "robust",
    "key takeaways",
    "look no further",
    "in conclusion",
    "furthermore",
    "moreover",
    "crucial",
    "paramount",
    "elevate",
    "game-changer",
    "revolutionary",
    "seamless",
    "leverage",
    "hybrid",
    "ecosystem",
    "pivot",
    "synergy",
    "agile",
    "align",
}

FORBIDDEN_MARKERS_RU = {
    "углубляться",
    "погружаться",
    "гобелен",
    "динамичный ландшафт",
    "подчеркивать",
    "робастный",
    "ключевые выводы",
    "не ищите дальше",
    "в заключение",
    "выводить на новый уровень",
    "гейм-чейнджер",
    "революционный",
    "бесшовный",
    "использовать рычаг",
    "экосистема",
    "пивот",
    "синергия",
    "синхронизироваться",
    "выравниваться",
}


class CheckerReview:
    """
    Валидатор Maker/Checker Split.
    Анализирует предлагаемые изменения (патчи) и файлы на соответствие
    правилам YAGNI, безопасности, форматирования ссылок и Stop-Slop.
    """

    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = workspace_root

    def review_patch(
        self, target_file_path: str, patch_text: str
    ) -> tuple[bool, str | None]:
        """
        Проверяет SEARCH/REPLACE патч перед его применением.
        Возвращает (success, error_message).
        """
        # 1. Проверяем наличие ИИ-мусора (Stop-Slop) в блоке REPLACE
        # Извлекаем все строки замены (между ======= и >>>>>>> REPLACE)
        replace_blocks = []
        lines = patch_text.splitlines()
        in_replace = False
        curr_block = []

        for line in lines:
            if "=======" in line:
                in_replace = True
                curr_block = []
                continue
            if ">>>>>>> REPLACE" in line:
                in_replace = False
                replace_blocks.append("\n".join(curr_block))
                continue
            if in_replace:
                curr_block.append(line)

        for block in replace_blocks:
            # Проверяем Stop-Slop
            block_lower = block.lower()

            # Проверяем английские маркеры
            for marker in FORBIDDEN_MARKERS_EN:
                if marker in block_lower:
                    return (
                        False,
                        f"Stop-Slop: обнаружен запрещенный маркер '{marker}' в заменяемом коде/комментарии.",
                    )

            # Проверяем русские маркеры
            for marker in FORBIDDEN_MARKERS_RU:
                if marker in block_lower:
                    return (
                        False,
                        f"Stop-Slop: обнаружен запрещенный маркер '{marker}' в заменяемом коде/комментарии.",
                    )

            # 2. Проверка форматирования ссылок (бэктики вокруг ссылок вида [`name`](file://...))
            # Ищем паттерн: [`текст`](file://...) или [`текст`](http...)
            link_pattern = re.compile(r"\[`[^`]+`\]\((file|http)s?://[^\)]+\)")
            if link_pattern.search(block):
                return (
                    False,
                    "Link Formatting: обнаружены запрещенные бэктики вокруг названия ссылки в формате [`name`](url). Используйте [name](url).",
                )

            # 3. YAGNI аудит (ограничение размера вносимых изменений)
            # Если блок REPLACE содержит более 150 строк, требуем декомпозиции
            if len(block.splitlines()) > 150:
                return (
                    False,
                    "YAGNI Bloat: размер вносимого изменения превышает 150 строк. Пожалуйста, разбейте патч на более мелкие шаги.",
                )

        return True, None

    def review_file(self, file_path: str) -> tuple[bool, list[str]]:
        """
        Проводит полный аудит файла на соответствие стандартам качества.
        Возвращает (success, list_of_warnings).
        """
        warnings = []
        path_obj = Path(file_path)
        if not path_obj.exists():
            return True, [f"Файл {file_path} не существует."]

        try:
            content = path_obj.read_text(encoding="utf-8")
        except Exception as e:
            return False, [f"Не удалось прочитать файл: {e}"]

        content_lower = content.lower()

        # 1. Stop-Slop аудит
        for marker in FORBIDDEN_MARKERS_EN:
            if marker in content_lower:
                warnings.append(f"Stop-Slop: в файле обнаружен маркер '{marker}'.")

        for marker in FORBIDDEN_MARKERS_RU:
            if marker in content_lower:
                warnings.append(f"Stop-Slop: в файле обнаружен маркер '{marker}'.")

        # 2. Link formatting
        link_pattern = re.compile(r"\[`[^`]+`\]\((file|http)s?://[^\)]+\)")
        if link_pattern.search(content):
            warnings.append(
                "Link Formatting: в файле обнаружены бэктики в ссылках [`name`](url)."
            )

        # 3. YAGNI LoC limit
        # Максимальная длина файла не должна превышать 800 строк
        loc = len(content.splitlines())
        if loc > 800:
            warnings.append(
                f"YAGNI Bloat: длина файла составляет {loc} строк, что превышает лимит в 800 строк."
            )

        return len(warnings) == 0, warnings
