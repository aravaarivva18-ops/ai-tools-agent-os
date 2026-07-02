import difflib
import os
import re
import time


def is_safe_path(filepath: str) -> bool:
    """
    Проверяет, лежит ли файл внутри разрешенной директории /Users/rus/ai-tools/.
    Разрешены только пути внутри этой директории.
    """
    try:
        abs_path = os.path.abspath(filepath)
        jail_dir = "/Users/rus/ai-tools"
        return abs_path == jail_dir or abs_path.startswith(jail_dir + os.sep)
    except Exception:
        return False


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


def normalize_unicode(s: str) -> str:
    """Нормализует юникод-символы кавычек, тире и неразрывных пробелов к ASCII."""
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("—", "-").replace("–", "-")
    s = s.replace("\u00a0", " ").replace("\u2002", " ").replace("\u2003", " ")
    return s


def find_sequence(lines: list[str], pattern: list[str]) -> int:
    """Ищет последовательность pattern в lines. Возвращает индекс начала или -1."""
    if not pattern:
        return -1
    n_lines = len(lines)
    n_pat = len(pattern)
    for i in range(n_lines - n_pat + 1):
        if lines[i : i + n_pat] == pattern:
            return i
    return -1


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
    Применяет список блоков изменений к контенту с использованием каскада строгости.
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

        # 2. Попытка точного совпадения после Unicode-нормализации (без изменения отступов)
        norm_content = normalize_unicode(current_content)
        norm_search = normalize_unicode(search_str)
        idx = norm_content.find(norm_search)
        if idx != -1:
            prefix = current_content[:idx]
            suffix = current_content[idx + len(search_str) :]
            current_content = prefix + replace_str + suffix
            continue

        # Подготовка строк для построчного поиска
        content_lines = current_content.split("\n")
        search_lines = search_str.split("\n")

        # 3. Построчное совпадение после Unicode-нормализации и rstrip()
        norm_lines = [normalize_unicode(line).rstrip() for line in content_lines]
        norm_search_lines = [normalize_unicode(line).rstrip() for line in search_lines]

        line_idx = find_sequence(norm_lines, norm_search_lines)
        if line_idx != -1:
            # Адаптация отступов для REPLACE
            orig_text = "\n".join(
                content_lines[line_idx : line_idx + len(search_lines)]
            )
            orig_indent = len(content_lines[line_idx]) - len(
                content_lines[line_idx].lstrip()
            )

            replace_lines = replace_str.split("\n")
            if replace_lines and search_lines:
                search_indent = len(search_lines[0]) - len(search_lines[0].lstrip())
                indent_diff = orig_indent - search_indent
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

            content_lines[line_idx : line_idx + len(search_lines)] = [replace_str]
            current_content = "\n".join(content_lines)
            continue

        # 4. Построчное совпадение после Unicode-нормализации и strip() (изменение вложенности)
        norm_lines_strip = [normalize_unicode(line).strip() for line in content_lines]
        norm_search_lines_strip = [
            normalize_unicode(line).strip() for line in search_lines
        ]

        line_idx = find_sequence(norm_lines_strip, norm_search_lines_strip)
        if line_idx != -1:
            orig_indent = len(content_lines[line_idx]) - len(
                content_lines[line_idx].lstrip()
            )
            replace_lines = replace_str.split("\n")
            if replace_lines and search_lines:
                search_indent = len(search_lines[0]) - len(search_lines[0].lstrip())
                indent_diff = orig_indent - search_indent
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

            content_lines[line_idx : line_idx + len(search_lines)] = [replace_str]
            current_content = "\n".join(content_lines)
            continue

        # 5. Резервный нечеткий поиск по SequenceMatcher
        start_idx, end_idx, _confidence = match_fuzzy(
            current_content, search_str, fuzzy_threshold
        )
        if start_idx is not None:
            prefix = current_content[:start_idx]
            suffix = current_content[end_idx:]

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


class FileLock:
    def __init__(self, filepath: str, timeout: float = 10.0, delay: float = 0.1):
        if not is_safe_path(filepath):
            raise PermissionError(
                f"Access denied: path {filepath} is outside /Users/rus/ai-tools/"
            )
        self.filepath = os.path.abspath(filepath)
        self.lock_file = self.filepath + ".lock"
        self.timeout = timeout
        self.delay = delay
        self.has_lock = False

    def __enter__(self):
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(str(os.getpid()))
                self.has_lock = True
                return self
            except FileExistsError:
                # Очистка устаревшей блокировки (старше 15 секунд)
                try:
                    mtime = os.path.getmtime(self.lock_file)
                    if time.time() - mtime > 15.0:
                        os.remove(self.lock_file)
                        continue
                except FileNotFoundError:
                    pass
                time.sleep(self.delay)
        raise TimeoutError(
            f"Не удалось получить блокировку для файла {self.lock_file} за {self.timeout} секунд."
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.has_lock:
            try:
                os.remove(self.lock_file)
            except FileNotFoundError:
                pass


def verify_no_placeholders(blocks: list[dict[str, str]]) -> tuple[bool, str | None]:
    """Проверяет REPLACE-блоки на наличие явных заглушек (TODO, FIXME, пустой pass)."""
    for i, block in enumerate(blocks):
        rep = block["replace"]
        for line in rep.splitlines():
            line_clean = line.strip()
            if line_clean.startswith("#") and any(
                kw in line_clean.upper() for kw in ("TODO", "FIXME")
            ):
                return (
                    False,
                    f"Блок #{i + 1} содержит заглушку в комментарии: '{line_clean}'",
                )
            if line_clean == "pass" and "def " in rep:
                return (
                    False,
                    f"Блок #{i + 1} содержит пустую заглушку 'pass' в новой функции.",
                )
    return True, None


def apply_patch_file(
    target_file: str, patch_file_or_text: str
) -> tuple[bool, str | None]:
    """
    Применяет SEARCH/REPLACE патч к файлу target_file с использованием файловой блокировки и каскада нечеткого поиска.
    Возвращает: (success, error_message)
    """
    if not is_safe_path(target_file):
        return False, f"Access denied: target file {target_file} is outside jail."

    is_path = False
    if "\n" not in patch_file_or_text and len(patch_file_or_text) < 1024:
        try:
            if os.path.exists(patch_file_or_text):
                is_path = True
        except Exception:
            pass

    if is_path:
        if not is_safe_path(patch_file_or_text):
            return (
                False,
                f"Access denied: patch file {patch_file_or_text} is outside jail.",
            )

    if not os.path.exists(target_file):
        return False, f"Target file {target_file} not found."

    with FileLock(target_file):
        # Читаем целевой файл
        with open(target_file, encoding="utf-8") as f:
            target_content = f.read()

        # Читаем патч
        if os.path.exists(patch_file_or_text):
            with open(patch_file_or_text, encoding="utf-8") as f:
                patch_text = f.read()
        else:
            patch_text = patch_file_or_text

        blocks = parse_blocks(patch_text)
        if not blocks:
            return False, "No SEARCH/REPLACE blocks parsed from input."

        # Валидация на заглушки
        no_placeholders, placeholder_err = verify_no_placeholders(blocks)
        if not no_placeholders:
            return False, f"Placeholder Validation Failed: {placeholder_err}"

        # Maker/Checker Split валидация перед применением патча
        try:
            from tools.checker_review import CheckerReview
        except ImportError:
            try:
                from checker_review import CheckerReview
            except ImportError:
                CheckerReview = None

        if CheckerReview is not None:
            checker = CheckerReview()
            ok, review_err = checker.review_patch(target_file, patch_text)
            if not ok:
                return False, f"Checker Review Failed: {review_err}"

        success, new_content, err_msg = apply_blocks(target_content, blocks)
        if not success:
            return False, f"Error applying patch: {err_msg}"

        backup_path = target_file + ".bak"

        # Проверка на anti-clutter перед записью
        try:
            enforce_fn = None
            try:
                import tools.rules_validator

                enforce_fn = tools.rules_validator.enforce_anti_clutter
            except ImportError:
                try:
                    import rules_validator

                    enforce_fn = rules_validator.enforce_anti_clutter
                except ImportError:
                    pass
            if enforce_fn is not None:
                enforce_fn(target_file)
                enforce_fn(backup_path)
        except Exception as e:
            return False, f"Anti-Clutter validation error: {e}"

        # Делаем резервную копию перед записью
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(target_content)

        # Записываем изменения
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Проверка синтаксиса для Python файлов через AST
        if target_file.endswith(".py"):
            try:
                import ast

                ast.parse(new_content)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return True, None
            except Exception as e:
                # Восстанавливаем из бэкапа
                os.replace(backup_path, target_file)
                return False, f"AST verification failed: {e}"
        else:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return True, None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 diff_applier.py <target_file> <patch_file_or_text>")
        sys.exit(1)

    target_path = sys.argv[1]
    patch_source = sys.argv[2]

    success, err_msg = apply_patch_file(target_path, patch_source)
    if not success:
        print(f"Error applying patch: {err_msg}")
        sys.exit(1)
    else:
        print(f"Success: Patch applied cleanly to {target_path}.")
