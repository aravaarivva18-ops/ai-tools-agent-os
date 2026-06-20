# Аналитический дашборд «Рука на пульсе» | Target Media MVP

Аналитическая система сквозной аналитики и контроля плановых KPI по рекламным кампаниям клиентов маркетингового агентства.

MVP-версия объединяет данные из API Яндекс.Директа, API Яндекс.Метрики и Google Таблиц (через Excel-выгрузки) в едином интерактивном окне.

---

## 🛠️ Стек технологий

* **Backend:** FastAPI (Python) + SQLAlchemy ORM.
* **Database:** PostgreSQL (на проде) / SQLite (для локальных тестов).
* **Frontend:** HTML5 + Vanilla JS + Tailwind CSS (Glassmorphism) + Chart.js (интерактивные графики).
* **Библиотеки API:** direct-api / metrika-api клиентские модули.
* **Деплой:** Готов к моментальному развертыванию на **Vercel** (Serverless) и **VPS** (Docker/PostgreSQL).

---

## 🚀 Быстрый старт (Локально)

### 1. Подготовка окружения
Перейдите в папку проекта и активируйте виртуальное окружение:
```bash
cd /Users/rus/ai-tools/tools/dashboard_mvp
# Если виртуальное окружение не создано:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Конфигурация (.env)
Создайте файл `.env` в корне папки `dashboard_mvp/` с настройками:
```env
# База данных (для SQLite оставьте пустым или укажите sqlite:///./dashboard.db)
DATABASE_URL=postgresql://user:password@localhost:5432/dashboard

# Секрет для генерации JWT-токенов сотрудников
JWT_SECRET=super-secret-key-change-it-in-production

# Настройки Яндекс OAuth приложения (создается в Яндекс ID)
YANDEX_CLIENT_ID=ваш_client_id
YANDEX_CLIENT_SECRET=ваш_client_secret
YANDEX_REDIRECT_URI=http://localhost:8000/auth/yandex/callback
```

### 3. Инициализация БД и создание администратора
Скрипт создаст таблицы в базе данных и добавит первого пользователя-администратора:
```bash
PYTHONPATH=../ python init_db.py
```
*Дефолтный логин администратора:* `admin@targetmedia.ru` / `admin12345`

### 4. Запуск локального сервера
```bash
PYTHONPATH=../ uvicorn main:app --reload --port 8000
```
После запуска откройте в браузере: `http://localhost:8000`

---

## 🧪 Запуск тестов (TDD)

Проект полностью покрыт автоматическими тестами. Запуск тестов из корня `ai-tools/`:
```bash
PYTHONPATH=./tools .venv/bin/pytest tools/dashboard_mvp/
```

---

## 🌐 Деплой на Vercel (Serverless)

Проект полностью оптимизирован под serverless-архитектуру Vercel. 
1. База данных должна быть внешней (используйте бесплатные PostgreSQL на **Neon.tech** или **Supabase**).
2. Зарегистрируйте проект в CLI Vercel:
   ```bash
   vercel
   ```
3. Пропишите переменные окружения (`DATABASE_URL`, `JWT_SECRET`, `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`, `YANDEX_REDIRECT_URI`) в панели Vercel Dashboard.
4. Планировщик в файле [vercel.json](vercel.json) будет автоматически раз в 4 часа вызывать эндпоинт `/api/cron/sync` для обновления статистики по API Яндекса.

---

## 🖥️ Деплой на VPS (Docker-compose)

Для постоянного размещения на сервере агентства подготовлена докер-сборка.
Пример `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: dashboard_db
    restart: always
    environment:
      POSTGRES_USER: dashboard_user
      POSTGRES_PASSWORD: secret_password
      POSTGRES_DB: dashboard_kpi
    volumes:
      - pgdata:/var/lib/postgresql/data

  web:
    build: .
    container_name: dashboard_app
    restart: always
    ports:
      - "80:8000"
    environment:
      DATABASE_URL: postgresql://dashboard_user:secret_password@db:5432/dashboard_kpi
      JWT_SECRET: production_jwt_secret_key
      YANDEX_CLIENT_ID: your_yandex_client_id
      YANDEX_CLIENT_SECRET: your_yandex_client_secret
      YANDEX_REDIRECT_URI: http://your-vps-ip/auth/yandex/callback
    depends_on:
      - db

volumes:
  pgdata:
```
Развертывание на VPS в одну команду: `docker-compose up -d --build`.

---

## 📊 Демонстрация работы (MVP Кейс)

В интерфейсе добавлена кнопка **«Создать тест-проект»**:
При клике на нее:
1. В БД автоматически создается структура под тестовый проект **«Парковка Уфа»**.
2. Из присланного шаблона Excel-файла [dashboard_input_pack_mvp_filled_parking_ufa.xlsx](file:///Users/rus/Downloads/dashboard_input_pack_mvp_filled_parking_ufa.xlsx) автоматически вычитываются планы KPI на месяц (бюджет `40 000 ₽`, лидов `100`, CPL `400 ₽`) и загружаются логи изменений.
3. Генерируется реалистичная статистика расходов, кликов и лидов по дням.
4. Сводная таблица и карточка проекта наполняются интерактивными графиками и светофором отклонений.
