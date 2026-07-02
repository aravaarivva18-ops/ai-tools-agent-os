import argparse
import os
import shutil
import sys
import time
import unittest
from pathlib import Path

import pytest

# Добавляем пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import cmd_clean


class TestDeepClean(unittest.TestCase):
    def setUp(self):
        # Создаем временную структуру воркспейса для тестов
        self.test_dir = Path("test_clean_workspace").resolve()
        self.test_dir.mkdir(exist_ok=True)

        # Мокаем config.get_workspace_root() в cli.py
        import cli

        self.orig_get_root = cli.config.get_workspace_root
        cli.config.get_workspace_root = lambda: self.test_dir

        # Создаем мусорные файлы
        self.bak_file = self.test_dir / "script.py.bak"
        self.bak_file.write_text("backup")

        # Активный lock-файл (создан только что)
        self.active_lock = self.test_dir / "active.py.lock"
        self.active_lock.write_text("111")

        # Старый lock-файл (устарел)
        self.stale_lock = self.test_dir / "stale.py.lock"
        self.stale_lock.write_text("222")

        # Кэш папка
        self.pycache_dir = self.test_dir / "__pycache__"
        self.pycache_dir.mkdir(exist_ok=True)
        (self.pycache_dir / "cached.pyc").write_text("compiled")

    def tearDown(self):
        # Восстанавливаем оригинальный метод
        import cli

        cli.config.get_workspace_root = self.orig_get_root

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_deep_clean_removes_correct_items(self):
        """Проверяет рекурсивное удаление кэшей, бэкапов и старых блокировок."""
        # Меняем mtime старого lock-файла на 20 секунд назад
        past_time = time.time() - 20.0
        os.utime(self.stale_lock, (past_time, past_time))

        # Проверяем, что файлы созданы
        assert self.bak_file.exists()
        assert self.active_lock.exists()
        assert self.stale_lock.exists()
        assert self.pycache_dir.exists()

        # Запускаем cmd_clean с перехватом sys.exit
        args = argparse.Namespace(keep=None)
        with pytest.raises(SystemExit) as cm:
            cmd_clean(args)

        assert cm.value.code == 0

        # Проверяем результаты
        assert not (self.bak_file.exists())  # Удален .bak
        assert not (self.stale_lock.exists())  # Удален старый .lock
        assert not (self.pycache_dir.exists())  # Удален __pycache__
        assert self.active_lock.exists()  # Активный .lock ДОЛЖЕН остаться!


if __name__ == "__main__":
    unittest.main()
