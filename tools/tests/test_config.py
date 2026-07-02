import json
import os
import tempfile
from pathlib import Path

from tools.config import (
    DEFAULT_CONFIG,
    get_global_config_dir,
    get_workspace_root,
    load_config,
)


def test_get_workspace_root_by_marker():
    """Позитивный тест: находит корень по маркеру (.agentic-dev.json)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sub_dir = tmp_path / "subdir" / "nested"
        sub_dir.mkdir(parents=True)

        # Создаем маркер в корне
        (tmp_path / ".agentic-dev.json").write_text("{}", encoding="utf-8")

        # Меняем текущую директорию во время теста
        old_cwd = os.getcwd()
        os.chdir(sub_dir)
        try:
            root = get_workspace_root()
            # Должен подняться до tmp_path
            assert root.resolve() == tmp_path.resolve()
        finally:
            os.chdir(old_cwd)


def test_get_workspace_root_fallback():
    """Тест фолбэка: если маркеров нет, возвращает текущую директорию."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            root = get_workspace_root()
            assert root.resolve() == tmp_path.resolve()
        finally:
            os.chdir(old_cwd)


def test_get_global_config_dir():
    """Тест получения глобальной директории (не должна быть пустой)."""
    global_dir = get_global_config_dir()
    assert isinstance(global_dir, Path)
    assert global_dir.name == "agentic-dev"


def test_load_config_merging():
    """Позитивный тест: загрузка и слияние конфигурации."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Создаем пользовательский .agentic-dev.json
        user_config = {
            "version": "2.0.0",
            "vault": {"findings_file": "custom_vault/findings.md"},
        }
        (tmp_path / ".agentic-dev.json").write_text(
            json.dumps(user_config), encoding="utf-8"
        )

        # Меняем cwd на tmpdir, чтобы get_workspace_root нашел наш конфиг
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            config = load_config()
            # Проверяем, что версия обновилась
            assert config["version"] == "2.0.0"
            # Проверяем, что findings_file изменился
            assert config["vault"]["findings_file"] == "custom_vault/findings.md"
            # Проверяем, что handoffs_dir остался дефолтным (слияние словарей)
            assert (
                config["vault"]["handoffs_dir"]
                == DEFAULT_CONFIG["vault"]["handoffs_dir"]
            )
        finally:
            os.chdir(old_cwd)
