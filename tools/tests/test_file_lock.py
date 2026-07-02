import os
import sys
import time
import unittest

import pytest

# Добавляем пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diff_applier import FileLock


class TestFileLock(unittest.TestCase):
    def setUp(self):
        self.test_file = os.path.abspath("test_lock_target.txt")
        self.lock_file = self.test_file + ".lock"
        # Создаем пустой целевой файл
        with open(self.test_file, "w") as f:
            f.write("target content")

    def tearDown(self):
        for f in (self.test_file, self.lock_file):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_lock_lifecycle(self):
        """Проверяет создание и удаление lock-файла."""
        assert not (os.path.exists(self.lock_file))

        with FileLock(self.test_file) as lock:
            assert lock.has_lock
            assert os.path.exists(self.lock_file)

        assert not (os.path.exists(self.lock_file))

    def test_lock_timeout(self):
        """Проверяет выброс TimeoutError при двойной блокировке."""
        with FileLock(self.test_file):
            # Вторая блокировка должна упасть по таймауту
            with pytest.raises(TimeoutError):
                with FileLock(self.test_file, timeout=0.2, delay=0.05):
                    pass

    def test_stale_lock_cleanup(self):
        """Проверяет авто-очистку устаревших блокировок."""
        # Создаем искусственную блокировку, которая считается устаревшей
        with open(self.lock_file, "w") as f:
            f.write("99999")

        # Меняем mtime на 20 секунд назад
        past_time = time.time() - 20.0
        os.utime(self.lock_file, (past_time, past_time))

        # Новая блокировка должна успешно удалить старую и захватить файл
        with FileLock(self.test_file, timeout=1.0) as lock:
            assert lock.has_lock
            with open(self.lock_file) as f:
                pid = f.read()
            assert pid == str(os.getpid())


if __name__ == "__main__":
    unittest.main()
