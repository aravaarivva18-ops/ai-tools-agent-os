#!/usr/bin/env python3
import os
import pathlib
import sys
import zipfile

try:
    from tools import config
except ImportError:
    import config


def run_rules_check() -> bool:
    """Запускает проверку правил перед сборкой."""
    root = config.get_workspace_root()
    validator_path = root / "tools" / "rules_validator.py"
    if not validator_path.exists():
        return True

    print("⏳ Запуск проверки правил перед сборкой (rules_validator.py)...")
    import subprocess  # nosec B404

    try:
        res = subprocess.run(
            [sys.executable, str(validator_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )  # nosec B603
        if res.returncode == 0:
            print("✅ Все проверки правил успешно пройдены.")
            return True
        else:
            print("❌ Ошибка валидации правил перед сборкой!")
            print(res.stdout)
            print(res.stderr, file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ Исключение при проверке правил: {e}", file=sys.stderr)
        return False


def should_exclude(path: pathlib.Path, root: pathlib.Path) -> bool:
    """Определяет, должен ли быть исключен файл или папка из сборки релиза."""
    # Получаем относительный путь и разбиваем на части
    rel_path = path.relative_to(root)
    parts = rel_path.parts

    # Исключаемые директории на любом уровне вложенности
    exclude_dirs = {
        ".git",
        ".gemini",
        "vault",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "dist",
        "scratch",
    }

    # Если любая из частей пути входит в список исключаемых папок
    for part in parts[:-1]:
        if part in exclude_dirs:
            return True

    # Если сам путь является исключаемой директорией
    if path.is_dir() and path.name in exclude_dirs:
        return True

    # Исключаемые конкретные имена файлов
    exclude_files = {"dashboard.db", "sales.db", ".DS_Store", "ziIlyoYE"}
    if path.name in exclude_files:
        return True

    # Исключение временных архивов настроек
    if path.name.startswith("backup_settings_") and path.name.endswith(".zip"):
        return True

    # Исключение скомпилированных файлов Python
    if path.suffix in (".pyc", ".pyo", ".pyd"):
        return True

    return False


def build_zip_release(out_path: pathlib.Path | None = None) -> pathlib.Path | None:
    """Упаковывает чистый релиз проекта в .zip архив."""
    root = config.get_workspace_root()
    config_data = config.load_config()
    version = config_data.get("version", "1.0.0")

    # Определяем имя и путь к архиву
    dist_dir = root / "dist"
    dist_dir.mkdir(exist_ok=True)

    archive_name = f"ai-tools-v{version}.zip"
    archive_path = out_path if out_path else dist_dir / archive_name

    # Перед сборкой запускаем проверку правил
    if not run_rules_check():
        print("❌ Сборка отменена из-за ошибок валидации правил.")
        return None

    print(f"📦 Сборка чистого релиза v{version}...")
    print(f"Корень проекта: {root}")
    print(f"Путь к архиву: {archive_path}")

    files_added = 0
    try:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for current_dir, dirs, files in os.walk(root):
                # Фильтруем папки на месте для оптимизации os.walk
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_exclude(pathlib.Path(current_dir) / d, root)
                ]

                for file in files:
                    file_path = pathlib.Path(current_dir) / file
                    if not should_exclude(file_path, root):
                        rel_file_path = file_path.relative_to(root)
                        zip_file.write(file_path, rel_file_path)
                        files_added += 1

        size_mb = archive_path.stat().st_size / (1024 * 1024)
        print("✅ Релиз успешно собран!")
        print(f"Добавлено файлов: {files_added}")
        print(f"Размер архива: {size_mb:.2f} MB")

        # Логируем изменения в dashboard.db
        try:
            from tools import dashboard_logger

            dashboard_logger.log_change(
                "System",
                f"Built release v{version} ({files_added} files, {size_mb:.2f} MB)",
            )
        except Exception:
            pass

        return archive_path
    except Exception as e:
        print(f"❌ Ошибка сборки архива: {e}", file=sys.stderr)
        if archive_path.exists():
            archive_path.unlink()
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Автоматический сборщик чистых релизов."
    )
    parser.add_argument(
        "--out", "-o", type=str, help="Путь для сохранения собранного архива"
    )
    args = parser.parse_args()

    out_path = pathlib.Path(args.out) if args.out else None
    build_zip_release(out_path)
