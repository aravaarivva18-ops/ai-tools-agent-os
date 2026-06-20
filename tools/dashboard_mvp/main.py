import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timedelta

from dashboard_mvp.db import Base, engine, get_db
from dashboard_mvp.models import (
    ChangeLog,
    Client,
    DailyStat,
    Integration,
    KPIPlan,
    Project,
    SourceMapping,
    User,
)
from dashboard_mvp.security_utils import create_access_token, verify_password
from dashboard_mvp.sync import sync_yandex_data
from dashboard_mvp.yandex_oauth import exchange_code_for_tokens, get_yandex_auth_url
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

app = FastAPI(title="Аналитический дашборд «Рука на пульсе» API")

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)

# API роуты монтируются ниже, корень обслуживается статикой static/index.html

# --- РАЗДЕЛ АВТОРИЗАЦИИ СОТРУДНИКОВ ---

@app.post("/api/auth/login")
def login(payload: dict, db: Session = Depends(get_db)):
    """Авторизация сотрудника по email и паролю. Возвращает JWT токен."""
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Необходимы email и password")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    # Генерируем JWT токен
    token_data = {
        "sub": user.email,
        "role": user.role,
        "user_id": user.id,
        "client_id": user.client_id
    }
    access_token = create_access_token(token_data, expires_delta=timedelta(minutes=1440))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "role": user.role,
            "client_id": user.client_id
        }
    }

# --- РАЗДЕЛ ЯНДЕКС OAUTH АВТОРИЗАЦИИ ---

@app.get("/api/auth/yandex/login")
def yandex_login(project_id: int):
    """Инициирует процесс авторизации в Яндекс. Возвращает ссылку на авторизацию."""
    auth_url = get_yandex_auth_url(project_id)
    return {"auth_url": auth_url}

@app.get("/auth/yandex/callback")
async def yandex_callback(
    code: str = Query(None),
    state: str = Query(None), # Здесь передается project_id
    error: str = Query(None),
    db: Session = Depends(get_db)
):
    """Обработчик ответа (callback) от Яндекса после авторизации пользователя."""
    if error:
        raise HTTPException(status_code=400, detail=f"Ошибка авторизации Яндекс: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Отсутствует code или state")

    try:
        project_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный ID проекта в state")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Проект с ID {project_id} не найден")

    try:
        tokens = await exchange_code_for_tokens(code)

        integration = db.query(Integration).filter(
            Integration.project_id == project_id,
            Integration.type == "yandex"
        ).first()

        if integration:
            integration.access_token = tokens["access_token"]
            integration.refresh_token = tokens["refresh_token"]
            integration.expires_at = tokens["expires_at"]
        else:
            integration = Integration(
                project_id=project_id,
                type="yandex",
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=tokens["expires_at"]
            )
            db.add(integration)

        db.commit()

        # Перенаправляем пользователя обратно на фронтенд
        return RedirectResponse(url=f"http://localhost:3000/#/project/{project_id}?auth=success")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить токены: {e!s}")

# --- РАЗДЕЛ ДАШБОРДА И АНАЛИТИКИ ---

@app.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Возвращает сводный отчет по всем проектам для главного экрана (светофор)."""
    # Будем выводить данные за текущий месяц
    today = date.today()
    current_month_str = today.strftime("%Y-%m")

    # Расчет интервала дат текущего месяца
    start_of_month = date(today.year, today.month, 1)
    # Находим последний день текущего месяца
    if today.month == 12:
        end_of_month = date(today.year, 12, 31)
    else:
        end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

    projects = db.query(Project).all()
    summary_data = []

    for project in projects:
        # 1. Получаем план на текущий месяц
        plan = db.query(KPIPlan).filter(
            KPIPlan.project_id == project.id,
            KPIPlan.month == current_month_str
        ).first()

        # 2. Получаем сумму факта по daily_stats за этот месяц
        stats = db.query(
            DailyStat.impressions,
            DailyStat.clicks,
            DailyStat.spent,
            DailyStat.leads,
            DailyStat.qualified_leads
        ).filter(
            DailyStat.project_id == project.id,
            DailyStat.date >= start_of_month,
            DailyStat.date <= end_of_month
        ).all()

        fact_impressions = sum(s.impressions for s in stats)
        fact_clicks = sum(s.clicks for s in stats)
        fact_spent = sum(s.spent for s in stats)
        fact_leads = sum(s.leads for s in stats)
        fact_qualified_leads = sum(s.qualified_leads for s in stats)

        fact_cpl = (fact_spent / fact_leads) if fact_leads > 0 else 0.0
        fact_cpl_qualified = (fact_spent / fact_qualified_leads) if fact_qualified_leads > 0 else 0.0
        fact_ctr = (fact_clicks / fact_impressions * 100) if fact_impressions > 0 else 0.0
        fact_cpc = (fact_spent / fact_clicks) if fact_clicks > 0 else 0.0

        # 3. Вычисляем отклонения для светофора
        budget_dev = 0.0
        leads_dev = 0.0
        cpl_dev = 0.0
        qual_leads_dev = 0.0
        cpl_qual_dev = 0.0
        pacing_pct = 0.0

        if plan:
            # Отклонение по расходу (бюджету)
            if plan.budget_plan > 0:
                budget_dev = round((fact_spent / plan.budget_plan) * 100, 1)
            # Выполнение плана по лидам
            if plan.leads_plan > 0:
                leads_dev = round((fact_leads / plan.leads_plan) * 100, 1)
            # Отклонение по стоимости лида (CPL)
            if plan.cpl_plan > 0:
                cpl_dev = round(((fact_cpl - plan.cpl_plan) / plan.cpl_plan) * 100, 1)
            # Выполнение плана по квал-лидам
            if plan.qualified_leads_plan > 0:
                qual_leads_dev = round((fact_qualified_leads / plan.qualified_leads_plan) * 100, 1)
            # Отклонение по стоимости квал-лида
            if plan.cpl_qualified_plan > 0:
                cpl_qual_dev = round(((fact_cpl_qualified - plan.cpl_qualified_plan) / plan.cpl_qualified_plan) * 100, 1)
                
            # Расчет Pacing
            elapsed_days = today.day
            total_days = end_of_month.day
            daily_spent_plan = plan.budget_plan / total_days if plan.budget_plan > 0 else 0.0
            daily_spent_fact = fact_spent / elapsed_days if elapsed_days > 0 else 0.0
            pacing_pct = round((daily_spent_fact / daily_spent_plan) * 100, 1) if daily_spent_plan > 0 else 0.0

        # Название ответственного менеджера
        manager_name = project.manager.email.split('@')[0] if project.manager else "Не назначен"

        summary_data.append({
            "id": project.id,
            "client_name": project.client.name,
            "project_name": project.name,
            "manager_name": manager_name,
            "plan": {
                "budget": plan.budget_plan if plan else 0.0,
                "leads": plan.leads_plan if plan else 0,
                "cpl": plan.cpl_plan if plan else 0.0,
                "qualified_leads": plan.qualified_leads_plan if plan else 0,
                "cpl_qualified": plan.cpl_qualified_plan if plan else 0.0
            } if plan else None,
            "fact": {
                "impressions": fact_impressions,
                "clicks": fact_clicks,
                "spent": round(fact_spent, 2),
                "leads": fact_leads,
                "qualified_leads": fact_qualified_leads,
                "cpl": round(fact_cpl, 2),
                "cpl_qualified": round(fact_cpl_qualified, 2),
                "ctr": round(fact_ctr, 2),
                "cpc": round(fact_cpc, 2)
            },
            "deviations": {
                "budget_progress_pct": budget_dev, # % расхода от плана
                "leads_progress_pct": leads_dev,   # % выполнения плана по лидам
                "cpl_deviation_pct": cpl_dev,       # % превышения стоимости лида от плана
                "qual_leads_progress_pct": qual_leads_dev,
                "cpl_qual_deviation_pct": cpl_qual_dev,
                "budget_pacing_pct": pacing_pct
            }
        })

    return {
        "month": current_month_str,
        "projects": summary_data
    }

@app.get("/api/dashboard/project/{project_id}")
def get_project_detail(
    project_id: int,
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """Возвращает детальные данные проекта за выбранный период (графики, лог изменений)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # Разрешаем пустые даты - берем текущий месяц по умолчанию
    today = date.today()
    if not start_date:
        start_date_val = date(today.year, today.month, 1)
    else:
        start_date_val = datetime.strptime(start_date, "%Y-%m-%d").date()

    if not end_date:
        end_date_val = today
    else:
        end_date_val = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 1. Получаем планы за этот период
    month_str = start_date_val.strftime("%Y-%m")
    plan = db.query(KPIPlan).filter(
        KPIPlan.project_id == project_id,
        KPIPlan.month == month_str
    ).first()

    # 2. Получаем ежедневную статистику
    stats_query = db.query(DailyStat).filter(
        DailyStat.project_id == project_id,
        DailyStat.date >= start_date_val,
        DailyStat.date <= end_date_val
    ).order_by(DailyStat.date.asc()).all()

    stats_list = []
    total_impressions = 0
    total_clicks = 0
    total_spent = 0.0
    total_leads = 0
    total_qualified_leads = 0

    for s in stats_query:
        total_impressions += s.impressions
        total_clicks += s.clicks
        total_spent += s.spent
        total_leads += s.leads
        total_qualified_leads += s.qualified_leads

        stats_list.append({
            "date": s.date.strftime("%Y-%m-%d"),
            "impressions": s.impressions,
            "clicks": s.clicks,
            "spent": round(s.spent, 2),
            "leads": s.leads,
            "qualified_leads": s.qualified_leads,
            "ctr": s.ctr,
            "cpc": s.cpc,
            "cpl": s.cpl,
            "cpl_qualified": s.cpl_qualified
        })

    total_cpl = (total_spent / total_leads) if total_leads > 0 else 0.0
    total_cpl_qualified = (total_spent / total_qualified_leads) if total_qualified_leads > 0 else 0.0
    total_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
    total_cpc = (total_spent / total_clicks) if total_clicks > 0 else 0.0

    # Расчет Pacing для выбранного периода
    pacing_pct = 0.0
    if plan and plan.budget_plan > 0:
        total_period_days = (end_date_val - start_date_val).days + 1
        if start_date_val > today:
            elapsed_period_days = 0
        elif end_date_val < today:
            elapsed_period_days = total_period_days
        else:
            elapsed_period_days = (today - start_date_val).days + 1
            
        daily_spent_plan = plan.budget_plan / total_period_days
        daily_spent_fact = total_spent / elapsed_period_days if elapsed_period_days > 0 else 0.0
        pacing_pct = round((daily_spent_fact / daily_spent_plan) * 100, 1)

    # 3. Получаем логи изменений
    logs_query = db.query(ChangeLog).filter(
        ChangeLog.project_id == project_id,
        ChangeLog.date >= start_date_val,
        ChangeLog.date <= end_date_val
    ).order_by(ChangeLog.date.desc()).all()

    logs_list = [{
        "date": log.date.strftime("%Y-%m-%d"),
        "description": log.changes_description,
        "comment": log.comment,
        "expected_effect": log.expected_effect
    } for log in logs_query]

    # Идентификатор токена Яндекс (для отображения статуса подключения)
    yandex_integration = db.query(Integration).filter(
        Integration.project_id == project_id,
        Integration.type == "yandex"
    ).first()
    has_token = yandex_integration is not None

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "client_name": project.client.name,
            "has_yandex_token": has_token,
            "vat_type": project.vat_type,
            "vat_rate": project.vat_rate
        },
        "period": {
            "start_date": start_date_val.strftime("%Y-%m-%d"),
            "end_date": end_date_val.strftime("%Y-%m-%d")
        },
        "plan": {
            "budget": plan.budget_plan if plan else 0.0,
            "leads": plan.leads_plan if plan else 0,
            "cpl": plan.cpl_plan if plan else 0.0,
            "qualified_leads": plan.qualified_leads_plan if plan else 0,
            "cpl_qualified": plan.cpl_qualified_plan if plan else 0.0
        } if plan else None,
        "totals": {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "spent": round(total_spent, 2),
            "leads": total_leads,
            "qualified_leads": total_qualified_leads,
            "cpl": round(total_cpl, 2),
            "cpl_qualified": round(total_cpl_qualified, 2),
            "ctr": round(total_ctr, 2),
            "cpc": round(total_cpc, 2),
            "budget_pacing_pct": pacing_pct
        },
        "daily_stats": stats_list,
        "change_logs": logs_list
    }

@app.post("/api/dashboard/project/{project_id}/sync")
async def trigger_sync(project_id: int, db: Session = Depends(get_db)):
    """Запускает ручную синхронизацию данных проекта за текущий месяц."""
    today = date.today()
    start_of_month = date(today.year, today.month, 1).strftime("%Y-%m-%d")
    end_of_today = today.strftime("%Y-%m-%d")

    success = await sync_yandex_data(db, project_id, start_of_month, end_of_today)
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка при синхронизации данных")

    return {"status": "success", "message": "Синхронизация успешно завершена"}

@app.get("/api/cron/sync")
async def cron_sync_all(db: Session = Depends(get_db)):
    """Автоматическая фоновая синхронизация всех проектов (вызывается Vercel Cron)."""
    projects = db.query(Project).all()
    today = date.today()
    start_of_month = date(today.year, today.month, 1).strftime("%Y-%m-%d")
    end_of_today = today.strftime("%Y-%m-%d")

    results = {}
    for proj in projects:
        success = await sync_yandex_data(db, proj.id, start_of_month, end_of_today)
        results[proj.name] = "success" if success else "failed"

    return {"status": "completed", "results": results}

# --- УТИЛИТНЫЙ ЭНДПОИНТ ДЛЯ ТЕСТОВОЙ СТРУКТУРЫ ---

@app.post("/api/test/setup")
def setup_test_project(db: Session = Depends(get_db)):
    """Создает тестового клиента 'Парковка Уфа' и проект для отладки, если они еще не созданы."""
    client = db.query(Client).filter(Client.name == "Парковка Уфа").first()
    if not client:
        client = Client(name="Парковка Уфа", status="active")
        db.add(client)
        db.commit()
        db.refresh(client)

    manager = db.query(User).filter(User.role == "admin").first()
    manager_id = manager.id if manager else None

    project = db.query(Project).filter(Project.name == "Парковка Уфа").first()
    if not project:
        project = Project(
            client_id=client.id,
            name="Парковка Уфа",
            manager_id=manager_id,
            vat_type="with_vat",
            vat_rate=0.20
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    else:
        project.vat_type = "with_vat"
        project.vat_rate = 0.20
        db.commit()

    mapping = db.query(SourceMapping).filter(SourceMapping.project_id == project.id).first()
    if not mapping:
        mapping = SourceMapping(
            project_id=project.id,
            direct_login="e-17390364",
            metrika_counter_id="96109777",
            lead_goals_ids="320946135",
            qual_goals_ids="320946351"
        )
        db.add(mapping)
        db.commit()
    else:
        mapping.lead_goals_ids = "320946135"
        mapping.qual_goals_ids = "320946351"
        db.commit()

    # Автоматически импортируем планы KPI и логи изменений из Excel
    excel_path = "/Users/rus/Downloads/dashboard_input_pack_mvp_filled_parking_ufa.xlsx"
    if os.path.exists(excel_path):
        from dashboard_mvp.sync import sync_excel_data
        sync_excel_data(db, excel_path)
    else:
        print(f"[SETUP TEST] Файл Excel по пути {excel_path} не найден. Планы не импортированы.")

    return {
        "status": "success",
        "client_id": client.id,
        "project_id": project.id,
        "message": "Тестовая структура создана (Парковка Уфа) и планы KPI импортированы из Excel"
    }

# Раздача статических файлов (фронтенда)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
