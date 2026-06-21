import os
from datetime import date

import pytest
from dashboard_mvp.db import Base, get_db
from dashboard_mvp.main import app
from dashboard_mvp.models import (
    Integration,
    MarketingFact,
    MarketingPlan,
    Source,
    User,
)
from dashboard_mvp.security_utils import get_password_hash
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Использование временного файла для тестов решает проблему стирания SQLite :memory: базы
TEST_DB_FILE = "./test_temp.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Переопределяем зависимость get_db в приложении
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def run_around_tests():
    # Удаляем старый файл бд перед тестом, если остался
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass

    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    # Добавляем тестового администратора и дефолтный источник yandex
    db = TestingSessionLocal()
    admin = User(
        email="test_admin@targetmedia.ru",
        password_hash=get_password_hash("test_password123"),
        role="admin",
    )
    db.add(admin)

    yandex_source = Source(name="yandex")
    db.add(yandex_source)

    db.commit()
    db.close()

    yield

    # Закрываем все соединения и удаляем файл БД
    engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass


# Пересоздаем клиент для тестов
client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text


def test_login_success():
    payload = {"email": "test_admin@targetmedia.ru", "password": "test_password123"}
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_admin@targetmedia.ru"


def test_login_invalid_password():
    payload = {"email": "test_admin@targetmedia.ru", "password": "wrong_password"}
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"


def test_setup_test_project():
    response = client.post("/api/test/setup")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "project_id" in data


def test_yandex_login_url():
    response = client.get("/api/auth/yandex/login?project_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data


def test_get_dashboard_summary():
    # Сначала создадим тестовые данные
    client.post("/api/test/setup")

    # Делаем запрос к сводному дашборду
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "month" in data
    assert "projects" in data
    assert len(data["projects"]) == 1

    proj = data["projects"][0]
    assert proj["project_name"] == "Парковка Уфа"
    assert "plan" in proj
    assert "fact" in proj
    assert "deviations" in proj


def test_get_project_detail():
    # Создаем данные
    client.post("/api/test/setup")

    # Добавим одну запись статистики напрямую в бд для теста
    db = TestingSessionLocal()
    yandex_source = db.query(Source).filter(Source.name == "yandex").first()
    stat = MarketingFact(
        project_id=1,
        source_id=yandex_source.id,
        date=date.today(),
        impressions=1000,
        clicks=50,
        spend=1000.0,
        leads_primary=5,
        ctr=5.0,
        cpc=20.0,
        cpl=200.0,
    )
    db.add(stat)

    # Добавим план
    current_month = date.today().strftime("%Y-%m")
    plan = MarketingPlan(
        month=current_month,
        project_id=1,
        budget_plan=40000,
        leads_plan=100,
        cpl_plan=400,
    )
    db.add(plan)

    db.commit()
    db.close()

    # Делаем запрос детальной страницы
    response = client.get("/api/dashboard/project/1")
    assert response.status_code == 200
    data = response.json()
    assert data["project"]["name"] == "Парковка Уфа"
    assert data["totals"]["spent"] == 1000.0
    assert data["totals"]["leads"] == 5
    assert len(data["daily_stats"]) == 1
    assert data["daily_stats"][0]["clicks"] == 50


def test_trigger_sync_success():
    # Создаем структуру
    client.post("/api/test/setup")

    # Добавляем mock integration токен
    db = TestingSessionLocal()
    integration = Integration(project_id=1, type="yandex", access_token="mock_token")
    db.add(integration)
    db.commit()
    db.close()

    # Запускаем ручную синхронизацию
    response = client.post("/api/dashboard/project/1/sync")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Синхронизация успешно завершена",
    }


def test_cron_sync_all():
    # Создаем структуру
    client.post("/api/test/setup")

    # Запускаем cron синхронизацию
    response = client.get("/api/cron/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "Парковка Уфа" in data["results"]
