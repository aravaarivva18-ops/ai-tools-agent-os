import os
import sqlite3
import tempfile
import threading
import time


def test_hermes_concurrency_with_safe_pragmas():
    """
    Позитивный тест: проверка параллельного чтения и записи в базу SQLite
    при отключенном mmap и включенном режиме WAL.
    Показывает отсутствие взаимных блокировок (locks) и стабильность потоков.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "hermes_test.db")

        # Инициализация базы данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, val TEXT);"
        )
        # Настройка безопасных для macOS прагм
        cursor.execute("PRAGMA mmap_size = 0;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA temp_store = MEMORY;")
        conn.commit()
        conn.close()

        # Флаг для координации потоков
        stop_event = threading.Event()
        errors = []

        # Функция для записи
        def writer_thread():
            try:
                conn_writer = sqlite3.connect(db_path)
                cursor_writer = conn_writer.cursor()
                cursor_writer.execute("PRAGMA mmap_size = 0;")
                cursor_writer.execute("PRAGMA journal_mode = WAL;")

                counter = 0
                while not stop_event.is_set():
                    cursor_writer.execute(
                        "INSERT INTO data (val) VALUES (?)", (f"value_{counter}",)
                    )
                    conn_writer.commit()
                    counter += 1
                    time.sleep(0.01)
                conn_writer.close()
            except Exception as e:
                errors.append(f"Writer error: {e}")

        # Функция для чтения
        def reader_thread():
            try:
                conn_reader = sqlite3.connect(db_path)
                cursor_reader = conn_reader.cursor()
                cursor_reader.execute("PRAGMA mmap_size = 0;")
                cursor_reader.execute("PRAGMA journal_mode = WAL;")

                while not stop_event.is_set():
                    cursor_reader.execute("SELECT COUNT(*) FROM data")
                    _ = cursor_reader.fetchone()
                    time.sleep(0.01)
                conn_reader.close()
            except Exception as e:
                errors.append(f"Reader error: {e}")

        # Запускаем 1 пишущий и 3 читающих потока
        threads = [
            threading.Thread(target=writer_thread),
            threading.Thread(target=reader_thread),
            threading.Thread(target=reader_thread),
            threading.Thread(target=reader_thread),
        ]

        for t in threads:
            t.start()

        # Симулируем 0.5 секунды интенсивной конкурентной нагрузки
        time.sleep(0.5)

        stop_event.set()
        for t in threads:
            t.join()

        # Убеждаемся, что не возникло никаких ошибок взаимных блокировок или SIGBUS
        assert len(errors) == 0, f"Ошибки конкурентного доступа: {errors}"

        # Проверяем, что данные успешно записаны
        conn_check = sqlite3.connect(db_path)
        c = conn_check.cursor()
        c.execute("SELECT COUNT(*) FROM data")
        count = c.fetchone()[0]
        conn_check.close()
        assert count > 0


def test_hermes_mmap_disabled_negative_check():
    """
    Проверка отключения mmap: гарантируем, что прагма mmap_size
    действительно возвращает 0 (mmap выключен),
    чтобы исключить маппинг в виртуальную память и риск SIGBUS.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "hermes_test_negative.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Задаем размер mmap = 0 (отключен)
        cursor.execute("PRAGMA mmap_size = 0;")
        # Запрашиваем текущее значение
        cursor.execute("PRAGMA mmap_size;")
        mmap_size = cursor.fetchone()[0]

        conn.close()

        # Убеждаемся, что mmap полностью выключен
        assert mmap_size == 0
