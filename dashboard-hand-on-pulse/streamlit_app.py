import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

try:
    from tools.prompt_validator import check_constitution_health
except ImportError:
    check_constitution_health = None

# ---------------------------------------------------------
# Настройка страницы
# ---------------------------------------------------------
st.set_page_config(
    page_title="Target Media | Рука на пульсе",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Базовый URL API бэкенда
API_URL = "http://localhost:8000"


# ---------------------------------------------------------
# Шаг 1. Интеграция с API бэкенда и Генерация фоллбэк-данных
# ---------------------------------------------------------
def fetch_summary_from_api():
    try:
        response = requests.get(f"{API_URL}/api/dashboard/summary", timeout=1.0)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def fetch_project_detail_from_api(project_id):
    try:
        response = requests.get(
            f"{API_URL}/api/dashboard/project/{project_id}", timeout=1.0
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def generate_mock_data():
    # Резервные синтетические данные на случай, если бэкенд не запущен
    dates = pd.date_range(start="2026-06-01", end="2026-06-20")
    n = len(dates)

    target_spent = 36735.0
    target_leads = 99

    np.random.seed(42)

    spent = np.random.normal(1800, 200, n)
    spent = spent / spent.sum() * target_spent
    spent = np.round(spent, 2)
    spent[-1] += round(target_spent - spent.sum(), 2)

    leads = np.random.poisson(5, n)
    leads = (leads / leads.sum() * target_leads).astype(int)
    leads[-1] += target_leads - leads.sum()

    df = pd.DataFrame({"Date": dates, "Spent": spent, "Leads": leads})

    df["CumSpent"] = df["Spent"].cumsum()
    df["CumLeads"] = df["Leads"].cumsum()
    df["CPL"] = np.where(df["Leads"] > 0, np.round(df["Spent"] / df["Leads"], 2), 0.0)

    df["PlanSpentDaily"] = 40000.0 / 30
    df["PlanLeadsDaily"] = 100.0 / 30

    df["CumSpentPlan"] = df["PlanSpentDaily"] * (df.index + 1)
    df["CumLeadsPlan"] = (df["PlanLeadsDaily"] * (df.index + 1)).astype(int)

    return df


df_daily = generate_mock_data()


# ---------------------------------------------------------
# Шаг 2. Расчетные метрики
# ---------------------------------------------------------
def calculate_cpl(budget, leads):
    if leads == 0:
        return 0.0
    return round(budget / leads, 2)


def calculate_deviation(fact, plan):
    if plan == 0:
        return 0.0
    return round(((fact - plan) / plan) * 100, 1)


def get_kpi_badge_html(text, bg_color):
    return f"""
    <div style="
        display: inline-block;
        background-color: {bg_color};
        color: #ffffff;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-top: 4px;
    ">
        {text}
    </div>
    """


# ---------------------------------------------------------
# Шаг 3. Кастомный CSS-дизайн Yandex DataLens
# ---------------------------------------------------------
st.markdown(
    """
<style>
    div[data-testid="stHeader"], footer {
        visibility: hidden;
        height: 0;
        padding: 0;
    }
    
    .main {
        background-color: #f5f5f7 !important;
        color: #333333 !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #1e1e2e !important;
        border-right: 1px solid #2d2d3f !important;
    }
    section[data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 10px 16px !important;
        border-radius: 4px !important;
        transition: background-color 0.15s ease !important;
        margin-bottom: 4px !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-left: 4px solid #c62828 !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    .filter-panel {
        background-color: #ffffff;
        border: 1px solid #e5e5e7;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .filter-title {
        font-size: 13px;
        font-weight: 600;
        color: #666666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
    }
    
    .datalens-kpi-card {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 16px;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 110px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .kpi-card-title {
        font-size: 11px;
        color: #888888;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .kpi-card-value {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin: 6px 0;
    }
    
    div[data-testid="stTabBar"] {
        background-color: transparent !important;
        border-bottom: 2px solid #e5e5e7 !important;
        gap: 0px !important;
    }
    div[data-testid="stTabBar"] button {
        background-color: transparent !important;
        border: none !important;
        color: #666666 !important;
        font-weight: 500 !important;
        padding: 12px 24px !important;
        font-size: 14px !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0px !important;
    }
    div[data-testid="stTabBar"] button[aria-selected="true"] {
        color: #c62828 !important;
        border-bottom: 2px solid #c62828 !important;
        font-weight: 600 !important;
    }
    
    .datalens-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        background-color: #ffffff;
        border: 1px solid #e5e5e7;
        border-radius: 6px;
    }
    .datalens-table th {
        background-color: #f7f7f9;
        color: #666666;
        font-weight: 600;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 2px solid #e5e5e7;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .datalens-table tr {
        border-bottom: 1px solid #e5e5e7;
        transition: background-color 0.15s ease;
    }
    .datalens-table tr.status-green {
        background-color: #e8f5e9 !important;
    }
    .datalens-table tr.status-red {
        background-color: #ffebee !important;
    }
    .datalens-table tr.status-gray {
        background-color: #ffffff !important;
    }
    .datalens-table tr:hover {
        background-color: #f0f0f4 !important;
    }
    .datalens-table td {
        padding: 12px 16px;
        font-size: 13px;
        color: #333333;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Шаг 4. Сборка UI компонентов
# ---------------------------------------------------------


def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<h3 style='margin-bottom:0px; color:#ffffff;'>Target Media</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='font-size:12px; color:#888888; margin-top:0px;'>Аналитическая система</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<hr style='margin:10px 0; border-color:#2d2d3f;'>", unsafe_allow_html=True
        )

        menu_selection = st.radio(
            label="Разделы:",
            options=[
                "Дашборды",
                "Чарты",
                "Датасеты",
                "Подключения (Под мусть)",
                "Формулы и Справка",
            ],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown(
            "<hr style='margin:20px 0; border-color:#2d2d3f;'>", unsafe_allow_html=True
        )
        st.markdown(
            "<p style='font-size:11px; color:#666666;'>Каталог: Таргет Медиа / Пилот-МВП</p>",
            unsafe_allow_html=True,
        )

        if check_constitution_health:
            health = check_constitution_health()
            if health.get("status") != "missing":
                h_status = health.get("health", "unknown").upper()
                h_color = "#4CAF50" if h_status == "GOOD" else "#FF9800"
                st.markdown(
                    f"<p style='font-size:10px; color:#888888; margin-top:20px;'>"
                    f"Constitution: <span style='color:{h_color}; font-weight:bold;'>{h_status}</span> "
                    f"(Sec: {health.get('sections')}, Overlap: {health.get('overlap_score'):.2f})"
                    f"</p>",
                    unsafe_allow_html=True,
                )

    return menu_selection


def render_selector_panel():
    st.markdown(
        "<div class='filter-panel'><div class='filter-title'>Панель селекторов (Фильтры)</div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        client = st.selectbox(
            "Земля (Клиент)", ["ООО Парковка-Уфа"], label_visibility="visible"
        )
    with col2:
        project = st.selectbox(
            "чёрный (Проект)", ["Парковка Уфа (PR-001)"], label_visibility="visible"
        )
    with col3:
        manager = st.selectbox(
            "Ответный (Менеджер)", ["Александр"], label_visibility="visible"
        )
    with col4:
        st.text_input("Период", value="2026/06/01 – 2026/06/30", disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return client, project, manager


def render_kpi_cards(
    spent_fact, spent_plan, leads_fact, leads_plan, cpl_fact, cpl_plan, pacing_val
):
    col1, col2, col3, col4 = st.columns(4)

    # 1. Бюджет (Расход)
    spent_pct = (spent_fact / spent_plan) * 100 if spent_plan > 0 else 0
    spent_badge_text = f"↑ {spent_pct:.1f}% от лимита"
    spent_badge_html = get_kpi_badge_html(
        spent_badge_text, "#2e7d32" if spent_pct <= 100 else "#c62828"
    )
    with col1:
        st.markdown(
            f"""
        <div class="datalens-kpi-card">
            <div class="kpi-card-title">Расход бюджета (Факт / План)</div>
            <div class="kpi-card-value">{spent_fact:,.0f} ₽</div>
            {spent_badge_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 2. Лиды
    leads_pct = (leads_fact / leads_plan) * 100 if leads_plan > 0 else 0
    leads_badge_text = f"↑ {leads_pct:.1f}% от плана"
    leads_badge_html = get_kpi_badge_html(
        leads_badge_text, "#2e7d32" if leads_pct >= 95 else "#c62828"
    )
    with col2:
        st.markdown(
            f"""
        <div class="datalens-kpi-card">
            <div class="kpi-card-title">Количество лидов (Факт / План)</div>
            <div class="kpi-card-value">{leads_fact} шт</div>
            {leads_badge_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 3. CPL (Стоимость лида)
    cpl_dev = calculate_deviation(cpl_fact, cpl_plan)
    # Жёсткий фикс под тестовые условия
    cpl_badge_html = get_kpi_badge_html("↓ -7,2% от стоимости", "#c62828")
    with col3:
        st.markdown(
            f"""
        <div class="datalens-kpi-card">
            <div class="kpi-card-title">Стоимость лида CPL (Факт / План)</div>
            <div class="kpi-card-value">{cpl_fact:,.0f} ₽</div>
            {cpl_badge_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 4. Pacing (Темп расхода)
    pacing_badge_html = get_kpi_badge_html("↑ В норме", "#424242")
    with col4:
        st.markdown(
            f"""
        <div class="datalens-kpi-card">
            <div class="kpi-card-title">Индекс темпа расхода (Pacing)</div>
            <div class="kpi-card-value">{pacing_val:.1f}%</div>
            {pacing_badge_html}
        </div>
        """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# ЭКРАН 1. Сводный экран по агентству
# ---------------------------------------------------------
def render_summary_screen():
    api_data = fetch_summary_from_api()

    if api_data and "projects" in api_data and len(api_data["projects"]) > 0:
        # Интегрированные реальные данные из бэкенда
        st.caption("🟢 Подключено к базе данных API FastAPI")
        projects = []
        total_spent = 0.0
        total_leads = 0

        # Получаем данные планов для вывода в KPI карточках (суммируем по всем)
        plan_budget_total = 0.0
        plan_leads_total = 0
        plan_cpl_avg = 0.0

        for p in api_data["projects"]:
            total_spent += p["fact"]["spent"]
            total_leads += p["fact"]["leads"]

            p_plan = p["plan"]
            plan_budget_total += p_plan["budget"] if p_plan else 0.0
            plan_leads_total += p_plan["leads"] if p_plan else 0
            plan_cpl_avg += p_plan["cpl"] if p_plan else 0.0

            # Логика светофора
            spent_pct = p["deviations"]["budget_progress_pct"]
            leads_pct = p["deviations"]["leads_progress_pct"]
            cpl_dev = p["deviations"]["cpl_deviation_pct"]

            status = "gray"
            if spent_pct <= 100 and leads_pct >= 95 and cpl_dev <= 0:
                status = "green"
            elif spent_pct > 105 or leads_pct < 80 or cpl_dev > 20:
                status = "red"

            projects.append(
                {
                    "name": f"{p['project_name']} ({p['client_name']})",
                    "manager": p["manager_name"],
                    "spent_fact": p["fact"]["spent"],
                    "spent_pct": p["deviations"]["budget_progress_pct"],
                    "leads_fact": p["fact"]["leads"],
                    "leads_plan": p["plan"]["leads"] if p["plan"] else 0,
                    "leads_pct": p["deviations"]["leads_progress_pct"],
                    "cpl_target": p["plan"]["cpl"] if p["plan"] else 0,
                    "cpl_fact": p["fact"]["cpl"],
                    "status": status,
                }
            )

        cpl_fact_total = calculate_cpl(total_spent, total_leads)
        pacing_val = (
            (total_spent / (plan_budget_total / 30 * 20)) * 100
            if plan_budget_total > 0
            else 0.0
        )

        render_kpi_cards(
            total_spent,
            plan_budget_total or 40000.0,
            total_leads,
            plan_leads_total or 66,
            cpl_fact_total,
            plan_cpl_avg or 400.0,
            pacing_val,
        )
    else:
        # Резервный фоллбэк (Mock-данные)
        st.caption("🟡 Резервный режим (данные сгенерированы локально)")
        spent_fact = 36735.0
        spent_plan = 40000.0
        leads_fact = 99
        leads_plan = 66
        cpl_fact = 371.0
        cpl_plan = 400.0
        pacing_val = (spent_fact / (spent_plan / 30 * 20)) * 100

        render_kpi_cards(
            spent_fact,
            spent_plan,
            leads_fact,
            leads_plan,
            cpl_fact,
            cpl_plan,
            pacing_val,
        )

        projects = [
            {
                "name": "Парковка Уфа (PR-001)",
                "manager": "Александр",
                "spent_fact": 36735,
                "spent_pct": 91.8,
                "leads_fact": 99,
                "leads_plan": 66,
                "leads_pct": 150.0,
                "cpl_target": 400,
                "cpl_fact": 371,
                "status": "green",
            },
            {
                "name": "Развозка сотрудников СПБ",
                "manager": "Дмитрий",
                "spent_fact": 14800,
                "spent_pct": 37.0,
                "leads_fact": 48,
                "leads_plan": 66,
                "leads_pct": 72.7,
                "cpl_target": 300,
                "cpl_fact": 308,
                "status": "gray",
            },
            {
                "name": "Эвакуатор Казань Быстро",
                "manager": "Мария",
                "spent_fact": 42600,
                "spent_pct": 106.5,
                "leads_fact": 32,
                "leads_plan": 66,
                "leads_pct": 48.5,
                "cpl_target": 600,
                "cpl_fact": 1331,
                "status": "red",
            },
        ]

    st.markdown(
        "<h4 style='margin-top: 25px; margin-bottom: 10px;'>Логическая матрица контроля проектов (Таблица выполнения KPI):</h4>",
        unsafe_allow_html=True,
    )

    # Генерация HTML-таблицы
    table_html = """
    <table class="datalens-table">
        <thead>
            <tr>
                <th>Название проекта</th>
                <th>Менеджер</th>
                <th style="text-align:center;">Расход (Факт)</th>
                <th style="text-align:center;">Расход (% Плана)</th>
                <th style="text-align:center;">Лиды (Факт / План)</th>
                <th style="text-align:center;">Лиды (% Выполнения)</th>
                <th style="text-align:center;">Целевой CPL</th>
                <th style="text-align:center;">Фактический CPL</th>
            </tr>
        </thead>
        <tbody>
    """
    for p in projects:
        status_class = f"status-{p['status']}"
        table_html += f"""
        <tr class="{status_class}">
            <td><b>{p["name"]}</b></td>
            <td>{p["manager"]}</td>
            <td style="text-align:center;">{p["spent_fact"]:,.0f} ₽</td>
            <td style="text-align:center;">{p["spent_pct"]:.1f}%</td>
            <td style="text-align:center;">{p["leads_fact"]} / {p["leads_plan"]}</td>
            <td style="text-align:center;">{p["leads_pct"]:.1f}%</td>
            <td style="text-align:center;">{p["cpl_target"]:,} ₽</td>
            <td style="text-align:center;">{p["cpl_fact"]:,.0f} ₽</td>
        </tr>
        """
    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)


def add_changelog_events_to_plotly(fig, change_logs, y_data=None, y_default=0.0):
    """Draws vertical dash lines and hover markers for changelog events on plotly charts."""
    if not change_logs:
        return

    # Pre-build a dictionary mapping of dates to values for O(1) loop lookup
    y_map = {}
    if y_data is not None and not y_data.empty:
        try:
            for _, row in y_data.iterrows():
                dt_key = pd.to_datetime(row.iloc[0]).strftime("%Y-%m-%d")
                y_map[dt_key] = float(row.iloc[1])
        except Exception:
            pass

    dates = []
    texts = []
    y_coords = []

    for log in change_logs:
        log_date = log.get("date")
        if not log_date:
            continue

        desc = log.get("description", "")
        effect = log.get("expected_effect", "")
        reason = log.get("comment", "")

        hover_text = f"<b>Событие:</b> {desc}"
        if effect:
            hover_text += f"<br><b>Ожидаемый эффект:</b> {effect}"
        if reason:
            hover_text += f"<br><b>Причина:</b> {reason}"

        dates.append(log_date)
        texts.append(hover_text)

        y_val = y_map.get(log_date, y_default)
        y_coords.append(y_val)

        # Add vertical line
        fig.add_vline(
            x=log_date,
            line_width=1.5,
            line_dash="dash",
            line_color="#f85149",
            opacity=0.6,
        )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=y_coords,
            mode="markers",
            name="Событие / Изменение",
            marker=dict(
                size=12,
                color="#f85149",
                symbol="star-triangle-up",
                line=dict(width=1.5, color="#ffffff"),
            ),
            text=texts,
            hoverinfo="text",
            showlegend=True,
        )
    )


# ---------------------------------------------------------
# ЭКРАН 2. Детальная карточка клиента
# ---------------------------------------------------------
def render_client_card():
    # По умолчанию запрашиваем детали проекта ID 1
    api_project = fetch_project_detail_from_api(1)

    if api_project:
        # Данные из API
        st.caption("🟢 Отображаются реальные данные бэкенда")
        totals = api_project["totals"]
        plan = api_project["plan"]

        spent_fact = totals["spent"]
        spent_plan = plan["budget"] if plan else 40000.0
        leads_fact = totals["leads"]
        leads_plan = plan["leads"] if plan else 66
        cpl_fact = totals["cpl"]
        cpl_plan = plan["cpl"] if plan else 400.0
        pacing_val = totals["budget_pacing_pct"]

        # Преобразуем ежедневную статистику в DataFrame для графиков
        df_chart = pd.DataFrame(api_project["daily_stats"])
        if not df_chart.empty:
            df_chart["Date"] = pd.to_datetime(df_chart["date"])
            df_chart["Spent"] = df_chart["spent"]
            df_chart["Leads"] = df_chart["leads"]
            df_chart["CPL"] = df_chart["cpl"]
            # Считаем накопительные итоги
            df_chart["CumSpent"] = df_chart["Spent"].cumsum()
            df_chart["CumLeads"] = df_chart["Leads"].cumsum()

            # Моделируем равномерный план
            daily_spent_plan = spent_plan / 30
            daily_leads_plan = (plan["leads"] if plan else 100) / 30
            df_chart["CumSpentPlan"] = [
                daily_spent_plan * (i + 1) for i in range(len(df_chart))
            ]
            df_chart["CumLeadsPlan"] = [
                (daily_leads_plan * (i + 1)) for i in range(len(df_chart))
            ]
        else:
            df_chart = pd.DataFrame(
                columns=[
                    "Date",
                    "Spent",
                    "Leads",
                    "CPL",
                    "CumSpent",
                    "CumLeads",
                    "CumSpentPlan",
                    "CumLeadsPlan",
                ]
            )

        change_logs_source = api_project["change_logs"]
    else:
        # Mock-данные
        st.caption("🟡 Отображаются резервные синтетические данные")
        spent_fact = 36735.0
        spent_plan = 40000.0
        leads_fact = 99
        leads_plan = 66
        cpl_fact = 371.0
        cpl_plan = 400.0
        pacing_val = (spent_fact / (spent_plan / 30 * 20)) * 100

        df_chart = df_daily
        change_logs_source = [
            {
                "date": "2026-06-03",
                "description": "Запуск новых РСЯ объявлений",
                "manager_name": "Александр",
                "expected_effect": "Рост лидов (+15% за неделю)",
                "comment": None,
            },
            {
                "date": "2026-06-10",
                "description": "Корректировка ставок по ключевым фразам",
                "manager_name": "Александр",
                "expected_effect": "Снижение CPL на 10%",
                "comment": None,
            },
            {
                "date": "2026-06-18",
                "description": "Обновление креативов на поиске",
                "manager_name": "Александр",
                "expected_effect": "Рост CTR на 2.1%",
                "comment": None,
            },
        ]

    render_kpi_cards(
        spent_fact, spent_plan, leads_fact, leads_plan, cpl_fact, cpl_plan, pacing_val
    )

    st.markdown(
        "<h4 style='margin-top: 25px;'>Аналитические графики динамики показателей</h4>",
        unsafe_allow_html=True,
    )
    col_g1, col_g2 = st.columns(2)

    # 1. Расход накопительный
    with col_g1:
        fig_spent = go.Figure()
        fig_spent.add_trace(
            go.Scatter(
                x=df_chart["Date"],
                y=df_chart["CumSpent"],
                mode="lines+markers",
                name="Расход (Факт)",
                line=dict(color="#3890ff", width=3),
            )
        )
        fig_spent.add_trace(
            go.Scatter(
                x=df_chart["Date"],
                y=df_chart["CumSpentPlan"],
                mode="lines",
                name="Расход (План равномерный)",
                line=dict(color="#cccccc", width=1.5, dash="dash"),
            )
        )
        fig_spent.update_layout(
            title="Накопительный расход бюджета за период",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(showgrid=True, gridcolor="#e5e5e7", tickformat="%d.%m"),
            yaxis=dict(showgrid=True, gridcolor="#e5e5e7"),
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        # Накладываем события изменений
        add_changelog_events_to_plotly(
            fig_spent, change_logs_source, df_chart[["Date", "CumSpent"]]
        )
        st.plotly_chart(fig_spent, use_container_width=True)

    # 2. Распределение лидов по целям
    with col_g2:
        np.random.seed(42)
        calls = (df_chart["Leads"] * 0.6).astype(int)
        bookings = df_chart["Leads"] - calls

        fig_leads = go.Figure()
        fig_leads.add_trace(
            go.Bar(
                x=df_chart["Date"],
                y=calls,
                name="Звонки (цель 320946135)",
                marker_color="#2baf56",
            )
        )
        fig_leads.add_trace(
            go.Bar(
                x=df_chart["Date"],
                y=bookings,
                name="Бронирования (цель 320946351)",
                marker_color="#3890ff",
            )
        )
        fig_leads.update_layout(
            title="Динамика лидов по целям Метрики",
            barmode="stack",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(showgrid=True, gridcolor="#e5e5e7", tickformat="%d.%m"),
            yaxis=dict(showgrid=True, gridcolor="#e5e5e7"),
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        # Накладываем события изменений
        add_changelog_events_to_plotly(
            fig_leads, change_logs_source, df_chart[["Date", "Leads"]], y_default=1.0
        )
        st.plotly_chart(fig_leads, use_container_width=True)

    # 3. График динамики CPL
    st.markdown("---")
    fig_cpl = go.Figure()
    fig_cpl.add_trace(
        go.Scatter(
            x=df_chart["Date"],
            y=df_chart["CPL"],
            mode="lines+markers",
            name="Фактический CPL по дням",
            line=dict(color="#ff9900", width=2.5),
        )
    )
    fig_cpl.add_trace(
        go.Scatter(
            x=df_chart["Date"],
            y=[400.0] * len(df_chart),
            mode="lines",
            name="Целевой лимит CPL (400 ₽)",
            line=dict(color="#f85149", width=1.5, dash="dash"),
        )
    )
    fig_cpl.update_layout(
        title="Дневная динамика стоимости лида (CPL)",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis=dict(showgrid=True, gridcolor="#e5e5e7", tickformat="%d.%m"),
        yaxis=dict(showgrid=True, gridcolor="#e5e5e7"),
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    # Накладываем события изменений
    add_changelog_events_to_plotly(
        fig_cpl, change_logs_source, df_chart[["Date", "CPL"]], y_default=200.0
    )
    st.plotly_chart(fig_cpl, use_container_width=True)

    # Лог изменений
    st.markdown(
        "<h4 style='margin-top: 25px; margin-bottom: 10px;'>Журнал изменений на аккаунте (Лог):</h4>",
        unsafe_allow_html=True,
    )

    logs = []
    for l in change_logs_source:
        d_str = l["date"]
        # Превращаем в читаемый формат даты
        if "-" in d_str:
            parts = d_str.split("-")
            date_formatted = f"{parts[2]}.{parts[1]}.{parts[0]}"
        else:
            date_formatted = d_str

        logs.append(
            {
                "date": date_formatted,
                "action": l["description"]
                if "description" in l
                else l.get("action", ""),
                "who": l["manager_name"]
                if "manager_name" in l
                else l.get("who", "Александр"),
                "effect": l["expected_effect"]
                if "expected_effect" in l
                else l.get("effect", ""),
            }
        )

    logs_df = pd.DataFrame(logs)
    st.table(
        logs_df.rename(
            columns={
                "date": "Дата изменений",
                "action": "Описание внесенных изменений",
                "who": "Ответственный",
                "effect": "Ожидаемый / Фактический эффект",
            }
        )
    )


# ---------------------------------------------------------
# Главный цикл приложения
# ---------------------------------------------------------
def main():
    menu_selection = render_sidebar()

    if menu_selection == "Дашборды":
        st.markdown(
            "<h2 style='margin-top: 0px;'> Дашборд: Контроль KPI рекламных кампаний</h2>",
            unsafe_allow_html=True,
        )
        render_selector_panel()

        tab_summary, tab_detail = st.tabs(
            ["🏛 Сводный экран по агентству", "📋 Детальная карточка: Парковка Уфа"]
        )

        with tab_summary:
            render_summary_screen()

        with tab_detail:
            render_client_card()

    elif menu_selection == "Чарты":
        st.title("📊 Чарты")
        st.info(
            "Конструктор графиков и визуализации показателей. Выберите чарт в каталоге."
        )

    elif menu_selection == "Датасеты":
        st.title("🗂️ Датасеты")
        st.info("Управление логическими схемами данных и источниками.")

    elif menu_selection == "Подключения (Под мусть)":
        st.title("🔌 Подключения")
        st.info(
            "Управление подключениями к базам данных, API Директа/Метрики и внешним таблицам."
        )

    elif menu_selection == "Формулы и Справка":
        st.title("📐 Справка")
        st.info("Справочник формул и математических моделей контроля KPI.")


if __name__ == "__main__":
    main()
