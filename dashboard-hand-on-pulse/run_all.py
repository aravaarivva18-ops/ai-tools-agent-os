import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Определяем пути проекта
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

# Добавляем родительскую директорию в PYTHONPATH для корректного импорта модулей
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def check_dependencies():
    """Проверяет наличие необходимых библиотек Python."""
    required = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "streamlit",
        "pandas",
        "numpy",
        "plotly",
        "requests",
    ]
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print("Внимание: Не обнаружены необходимые библиотеки:")
        for m in missing:
            print(f"  - {m}")
        print("\nПожалуйста, установите их следующей командой:")
        print(f"  {sys.executable} -m pip install " + " ".join(missing))
        sys.exit(1)


def setup_database_and_mock_data():
    """Инициализирует базу данных и загружает тестовые данные из Excel."""
    print("Инициализация базы данных и подготовка окружения...")
    try:
        from db import SessionLocal
        from init_db import init_database
        from main import setup_test_project

        # 1. Запуск инициализации схемы БД и дефолтного админа
        init_database()

        # 2. Настройка тестового клиента и импорт планов
        db = SessionLocal()
        try:
            res = setup_test_project(db)
            print(f"Статус настройки БД: {res.get('message', 'Успешно')}")
        finally:
            db.close()

    except Exception as e:
        print(f"Ошибка при настройке базы данных: {e}")
        print("Продолжаем запуск с использованием резервных данных...")


def main():
    check_dependencies()
    setup_database_and_mock_data()

    # Подготовка переменных окружения для корректной работы путей импорта
    env = os.environ.copy()
    env["PYTHONPATH"] = str(parent_dir)

    processes = []
    try:
        print("\nЗапуск FastAPI Бэкенда на http://localhost:8000...")
        backend_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--log-level",
                "warning",
            ],
            cwd=str(current_dir),
            env=env,
        )
        processes.append(backend_proc)

        # Небольшая пауза, чтобы FastAPI успел инициализироваться
        time.sleep(1.5)

        print(
            "Запуск Streamlit Дашборда (Yandex DataLens стиль) на http://localhost:8501..."
        )
        streamlit_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "streamlit_app.py",
                "--server.port",
                "8501",
                "--server.headless",
                "true",
            ],
            cwd=str(current_dir),
            env=env,
        )
        processes.append(streamlit_proc)

        time.sleep(2)
        print("\nСистема успешно запущена.")
        print("  - FastAPI API: http://localhost:8000")
        print("  - Streamlit Панель: http://localhost:8501")
        print("\nОткрываем дашборд в браузере...")

        webbrowser.open("http://localhost:8501")

        print("\nНажмите Ctrl+C для остановки обоих серверов.")

        # Ожидаем завершения процессов
        while True:
            # Проверяем, не упал ли какой-то из процессов
            for p in processes:
                if p.poll() is not None:
                    print(
                        f"\nОдин из процессов неожиданно завершился с кодом {p.returncode}"
                    )
                    return
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nПолучен сигнал остановки (Ctrl+C). Завершение процессов...")
    finally:
        # Убиваем все дочерние процессы
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("Все процессы остановлены.")


if __name__ == "__main__":
    main()
