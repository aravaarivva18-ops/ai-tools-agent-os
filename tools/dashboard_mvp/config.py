import os

from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настройки базы данных
# Для локального тестирования по умолчанию используем SQLite, если DATABASE_URL не задана
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dashboard.db")

# Превращаем postgres:// в postgresql:// для SQLAlchemy (если используется Heroku/Render)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Безопасность и JWT
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-it-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 часа

# Настройки Яндекс OAuth
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET", "")
YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI", "http://localhost:3000/auth/yandex/callback")

# Настройки Google Sheets API
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")

