import asyncio
import os
import sys
from datetime import date

# Добавляем корневую директорию проекта в path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard_mvp.config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SPREADSHEET_ID
from dashboard_mvp.db import SessionLocal
from dashboard_mvp.sync import sync_google_sheets_data, sync_yandex_data


async def main():
    db = SessionLocal()
    today = date.today()
    # Возьмем данные с 1 июня 2026 года по сегодняшний день
    start_date = "2026-06-01"
    end_date = today.strftime("%Y-%m-%d")

    print("Импорт планов и логов из Google Sheets...")
    sync_google_sheets_data(db, GOOGLE_SPREADSHEET_ID, GOOGLE_CREDENTIALS_PATH)

    print(
        f"Запуск ручной синхронизации для проекта ID 1 с {start_date} по {end_date}..."
    )
    success = await sync_yandex_data(db, 1, start_date, end_date)
    if success:
        print("Синхронизация успешно завершена!")
    else:
        print("Синхронизация завершилась с ошибкой.")
    db.close()


if __name__ == "__main__":
    asyncio.run(main())
