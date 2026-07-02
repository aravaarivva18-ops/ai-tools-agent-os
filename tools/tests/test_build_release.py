#!/usr/bin/env python3
import pathlib
import tempfile
import zipfile
from unittest import mock

try:
    from tools import build_release
except ImportError:
    import build_release


def test_should_exclude():
    """Тест правил исключения файлов и папок."""
    root = pathlib.Path("/workspace")

    # Разрешенные файлы
    assert build_release.should_exclude(root / "tools" / "cli.py", root) is False
    assert build_release.should_exclude(root / "README.md", root) is False
    assert build_release.should_exclude(root / "AGENTS.md", root) is False

    # Исключаемые папки на верхнем уровне
    assert build_release.should_exclude(root / ".git" / "config", root) is True
    assert build_release.should_exclude(root / ".venv" / "bin" / "python", root) is True
    assert (
        build_release.should_exclude(
            root / "scratch" / "MediaCrawler" / "test.py", root
        )
        is True
    )
    assert build_release.should_exclude(root / "dist" / "release.zip", root) is True

    # Исключаемые папки внутри других папок
    assert (
        build_release.should_exclude(
            root / "tools" / "__pycache__" / "cli.cpython-310.pyc", root
        )
        is True
    )

    # Исключаемые конкретные файлы
    assert build_release.should_exclude(root / "dashboard.db", root) is True
    assert build_release.should_exclude(root / "sales.db", root) is True
    assert build_release.should_exclude(root / ".DS_Store", root) is True
    assert build_release.should_exclude(root / "ziIlyoYE", root) is True
    assert (
        build_release.should_exclude(root / "backup_settings_2026-06-28.zip", root)
        is True
    )


def test_build_zip_release_success():
    """Тест успешного создания zip-архива с правильным составом файлов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        # Создаем фейковую структуру проекта
        (tmp_path / "tools").mkdir()
        (tmp_path / ".venv").mkdir()
        (tmp_path / "scratch").mkdir()

        # Записываем файлы
        (tmp_path / ".agentic-dev.json").write_text(
            '{"version": "1.2.3"}', encoding="utf-8"
        )
        (tmp_path / "README.md").write_text("Hello README", encoding="utf-8")
        (tmp_path / "tools" / "cli.py").write_text("print('cli')", encoding="utf-8")
        (tmp_path / "tools" / "rules_validator.py").write_text(
            "print('validator')", encoding="utf-8"
        )

        # Файлы, которые должны быть исключены
        (tmp_path / ".venv" / "pip").write_text("pip", encoding="utf-8")
        (tmp_path / "dashboard.db").write_text("sqlite data", encoding="utf-8")
        (tmp_path / "scratch" / "temp.txt").write_text("temp", encoding="utf-8")

        # Мокаем get_workspace_root и проверку правил (чтобы не запускать реальный rules_validator)
        with mock.patch(
            "tools.build_release.config.get_workspace_root", return_value=tmp_path
        ):
            with mock.patch("tools.build_release.run_rules_check", return_value=True):
                # Также подменим load_config, чтобы он читал версию 1.2.3
                with mock.patch(
                    "tools.build_release.config.load_config",
                    return_value={"version": "1.2.3"},
                ):
                    archive_path = build_release.build_zip_release()

                    assert archive_path is not None
                    assert archive_path.exists()
                    assert archive_path.name == "ai-tools-v1.2.3.zip"

                    # Проверяем содержимое zip-архива
                    with zipfile.ZipFile(archive_path, "r") as zip_file:
                        namelist = zip_file.namelist()

                        # Разрешенные файлы должны быть в архиве
                        assert ".agentic-dev.json" in namelist
                        assert "README.md" in namelist
                        assert "tools/cli.py" in namelist
                        assert "tools/rules_validator.py" in namelist

                        # Исключенные файлы НЕ должны быть в архиве
                        assert "dashboard.db" not in namelist
                        assert ".venv/pip" not in namelist
                        assert "scratch/temp.txt" not in namelist
                        assert (
                            any(name.startswith(".venv") for name in namelist) is False
                        )
                        assert (
                            any(name.startswith("scratch") for name in namelist)
                            is False
                        )
                        assert (
                            any(name.startswith("dist") for name in namelist) is False
                        )
