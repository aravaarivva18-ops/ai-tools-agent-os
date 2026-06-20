import os
import sys

# Добавляем корневую директорию проекта в path, чтобы корректно импортировать модули
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard_mvp.db import Base, SessionLocal, engine
from dashboard_mvp.models import Source, User
from dashboard_mvp.security_utils import get_password_hash


def init_database():
    print("Инициализация базы данных...")
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("Таблицы базы данных успешно созданы.")

    db = SessionLocal()
    try:
        # Проверяем, есть ли уже пользователи в базе
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            print("Создаем дефолтного администратора...")
            default_admin = User(
                email="admin@targetmedia.ru",
                password_hash=get_password_hash("admin12345"),
                role="admin"
            )
            db.add(default_admin)
            db.commit()
            print("Администратор создан: admin@targetmedia.ru / admin12345")
        else:
            print("Администратор уже существует.")

        # Автоматическое создание дефолтных источников
        yandex_source = db.query(Source).filter(Source.name == "yandex").first()
        if not yandex_source:
            print("Создаем дефолтный источник 'yandex'...")
            yandex_source = Source(name="yandex")
            db.add(yandex_source)
            db.commit()
            print("Источник 'yandex' создан.")
        else:
            print("Источник 'yandex' уже существует.")
    except Exception as e:
        print(f"Ошибка при инициализации данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
