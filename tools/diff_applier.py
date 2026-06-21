import difflib
import os
import re


def parse_blocks(patch_text):
    """
    Парсит SEARCH/REPLACE блоки.
    Возвращает список словарей: [{'search': '...', 'replace': '...'}]
    """
    pattern = r"<<<<<<< SEARCH\n([\s\S]*?)\n=======\n([\s\S]*?)\n>>>>>>> REPLACE"
    matches = re.findall(pattern, patch_text)

    blocks = []
    for search_content, replace_content in matches:
        blocks.append({"search": search_content, "replace": replace_content})
    return blocks


def match_fuzzy(content, search_block, threshold=0.8):
    """
    Выполняет нечеткий поиск подстроки search_block в content.
    Возвращает (start_idx, end_idx, confidence) или (None, None, 0.0)
    """
    search_lines = search_block.splitlines()
    content_lines = content.splitlines()

    if not search_lines or not content_lines:
        return None, None, 0.0

    best_ratio = 0.0
    best_range: tuple[int | None, int | None] = (None, None)

    n_search = len(search_lines)
    n_content = len(content_lines)

    # Нормализуем строки для сравнения (удаляем лишние пробелы)
    def clean(s):
        return re.sub(r"\s+", " ", s.strip())

    clean_search = "\n".join(clean(l) for l in search_lines)

    # Скользящее окно по строкам файла
    for i in range(n_content - n_search + 1):
        window_lines = content_lines[i : i + n_search]
        clean_window = "\n".join(clean(l) for l in window_lines)

        ratio = difflib.SequenceMatcher(None, clean_search, clean_window).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_range = (i, i + n_search)

    if best_ratio >= threshold:
        # Реконструируем символьные индексы для найденного диапазона строк
        start_line, end_line = best_range

        # Находим символьные позиции в исходном тексте
        lines_before_start = content_lines[:start_line]
        lines_before_end = content_lines[:end_line]

        start_char = len("\n".join(lines_before_start)) + (
            1 if lines_before_start else 0
        )
        end_char = len("\n".join(lines_before_end))

        return start_char, end_char, best_ratio

    return None, None, 0.0


def apply_blocks(content, blocks, fuzzy_threshold=0.8):
    """
    Применяет список блоков изменений к контенту.
    Возвращает (success, new_content, error_message)
    """
    current_content = content

    for i, block in enumerate(blocks):
        search_str = block["search"]
        replace_str = block["replace"]

        # 1. Попытка точного совпадения
        if search_str in current_content:
            current_content = current_content.replace(search_str, replace_str, 1)
            continue

        # 2. Попытка нечеткого совпадения
        start_idx, end_idx, _confidence = match_fuzzy(
            current_content, search_str, fuzzy_threshold
        )
        if start_idx is not None:
            # Вырезаем совпавший блок и заменяем
            prefix = current_content[:start_idx]
            suffix = current_content[end_idx:]

            # Пытаемся адаптировать отступы REPLACE под контекст
            # Извлекаем отступ первой строки найденного оригинального блока
            matched_text = current_content[start_idx:end_idx]
            orig_lines = matched_text.splitlines()
            if orig_lines:
                orig_indent = len(orig_lines[0]) - len(orig_lines[0].lstrip())
                replace_lines = replace_str.splitlines()
                if replace_lines:
                    first_rep_indent = len(replace_lines[0]) - len(
                        replace_lines[0].lstrip()
                    )
                    indent_diff = orig_indent - first_rep_indent

                    if indent_diff != 0:
                        new_rep_lines = []
                        for line in replace_lines:
                            if line.strip():
                                if indent_diff > 0:
                                    new_rep_lines.append(" " * indent_diff + line)
                                else:
                                    new_rep_lines.append(line[-indent_diff:])
                            else:
                                new_rep_lines.append(line)
                        replace_str = "\n".join(new_rep_lines)

            current_content = prefix + replace_str + suffix
        else:
            return False, content, f"Could not match block #{i + 1}:\n{search_str}"

    return True, current_content, None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 diff_applier.py <target_file> <patch_file_or_text>")
        sys.exit(1)

    target_path = sys.argv[1]
    patch_source = sys.argv[2]

    # Читаем целевой файл
    if not os.path.exists(target_path):
        print(f"Error: Target file {target_path} not found.")
        sys.exit(1)

    with open(target_path, encoding="utf-8") as f:
        target_content = f.read()

    # Читаем патч (из файла или как прямую строку)
    if os.path.exists(patch_source):
        with open(patch_source, encoding="utf-8") as f:
            patch_text = f.read()
    else:
        patch_text = patch_source

    blocks = parse_blocks(patch_text)
    if not blocks:
        print("Error: No SEARCH/REPLACE blocks parsed from input.")
        sys.exit(1)

    success, new_content, err_msg = apply_blocks(target_content, blocks)

    if not success:
        print(f"Error applying patch: {err_msg}")
        sys.exit(1)

    backup_path = target_path + ".bak"

    # Проверяем на anti-clutter перед записью
    try:
        try:
            from tools.prompt_validator import enforce_anti_clutter
        except ImportError:
            from prompt_validator import enforce_anti_clutter
        if enforce_anti_clutter:
            enforce_anti_clutter(target_path)
            enforce_anti_clutter(backup_path)
    except Exception as e:
        print(f"Anti-Clutter error: {e}")
        sys.exit(1)

    # Делаем резервную копию перед записью
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(target_content)

    # Записываем изменения
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Проверка синтаксиса для Python файлов через AST (без компиляции в .pyc файлы)
    if target_path.endswith(".py"):
        try:
            import ast

            with open(target_path, encoding="utf-8") as f:
                ast.parse(f.read())
            print(f"Success: Patch applied cleanly to {target_path} and AST verified.")
            if os.path.exists(backup_path):
                os.remove(backup_path)  # Удаляем бэкап при успехе
        except Exception as e:
            print(f"Error: AST syntax check failed after patch: {e}")
            # Восстанавливаем из бэкапа
            os.replace(backup_path, target_path)
            sys.exit(1)
    else:
        print(f"Success: Patch applied cleanly to {target_path}.")
        if os.path.exists(backup_path):
            os.remove(backup_path)
