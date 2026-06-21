import os
from datetime import datetime

import pytest
from dashboard_mvp.db import Base
from dashboard_mvp.models import (
    Changelog,
    Client,
    Integration,
    MarketingFact,
    MarketingPlan,
    Project,
    Source,
    SourceMapping,
)
from dashboard_mvp.sync import sync_excel_data, sync_yandex_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_FILE = "./test_sync_temp.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def run_around_tests():
    # Очистка
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass

    Base.metadata.create_all(bind=engine)

    # Инициализация тестовой структуры
    db = TestingSessionLocal()

    # Создаем дефолтный источник yandex
    yandex_source = Source(id=1, name="yandex")
    db.add(yandex_source)

    client = Client(id=1, name="Парковка Уфа", status="active")
    db.add(client)

    project = Project(id=1, client_id=1, name="Парковка Уфа")
    db.add(project)

    mapping = SourceMapping(
        id=1,
        project_id=1,
        direct_login="e-17390364",
        metrika_counter_id="96109777",
        lead_goals_ids="320946135,320946351",
    )
    db.add(mapping)

    # Добавляем интеграцию с mock_token
    integration = Integration(project_id=1, type="yandex", access_token="mock_token")
    db.add(integration)

    db.commit()
    db.close()

    yield

    engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass


@pytest.mark.anyio
async def test_sync_yandex_mock_data():
    db = TestingSessionLocal()
    # Запускаем синхронизацию за 10 дней июня 2026
    result = await sync_yandex_data(
        db, project_id=1, start_date_str="2026-06-01", end_date_str="2026-06-10"
    )
    assert result is True

    # Проверяем, что в БД записались данные
    stats = db.query(MarketingFact).filter(MarketingFact.project_id == 1).all()
    assert len(stats) == 10

    # Проверим конкретный день
    first_day = (
        db.query(MarketingFact)
        .filter(
            MarketingFact.project_id == 1,
            MarketingFact.date == datetime.strptime("2026-06-01", "%Y-%m-%d").date(),
        )
        .first()
    )

    assert first_day is not None
    assert first_day.impressions > 0
    assert first_day.clicks > 0
    assert first_day.spend > 0
    assert first_day.ctr > 0
    assert first_day.cpc > 0
    db.close()


def test_sync_excel_data():
    db = TestingSessionLocal()
    excel_path = "/Users/rus/Downloads/dashboard_input_pack_mvp_filled_parking_ufa.xlsx"

    # Проверяем импорт Excel
    result = sync_excel_data(db, excel_path)
    assert result is True

    # Проверяем импортированные планы KPI
    plans = db.query(MarketingPlan).filter(MarketingPlan.project_id == 1).all()
    assert len(plans) > 0
    plan_june = (
        db.query(MarketingPlan)
        .filter(MarketingPlan.project_id == 1, MarketingPlan.month == "2026-06")
        .first()
    )
    assert plan_june is not None
    assert plan_june.budget_plan == 40000.0
    assert plan_june.leads_plan == 100
    assert plan_june.cpl_plan == 400.0

    # Проверяем импортированные логи изменений
    logs = db.query(Changelog).filter(Changelog.project_id == 1).all()
    assert len(logs) > 0
    db.close()
