import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta

# Настройка страницы в стиле Yandex Cloud
st.set_page_config(
    page_title="Yandex DataLens | Рука на пульсе",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Подробная стилизация интерфейса под Yandex DataLens
st.markdown("""
<style>
    /* Базовые цвета Yandex DataLens */
    :root {
        --dl-bg-main: #0c0f14;
        --dl-bg-panel: #161b22;
        --dl-border: #21262d;
        --dl-blue: #3890ff;
        --dl-blue-hover: #5ca3ff;
        --dl-text-main: #c9d1d9;
        --dl-text-light: #f0f6fc;
        --dl-text-muted: #8b949e;
        --dl-green: #2baf56;
        --dl-red: #f85149;
        --dl-yellow: #f1e05a;
    }

    /* Фон страницы */
    .main {
        background-color: var(--dl-bg-main);
        color: var(--dl-text-main);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Левая панель навигации (DataLens Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #0c0f14 !important;
        border-right: 1px solid var(--dl-border) !important;
        width: 220px !important;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }

    /* Стилизация панелей (дашлетов) */
    .datalens-dashlet {
        background-color: #161b22;
        border: 1px solid var(--dl-border);
        border-radius: 4px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* Карточки KPI (Селекторы/Индикаторы) */
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid var(--dl-border) !important;
        border-radius: 4px !important;
        padding: 12px 16px !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 500 !important;
        color: var(--dl-text-light) !important;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--dl-text-muted) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-weight: 600 !important;
    }

    /* Кнопки в стиле Yandex Cloud */
    .stButton>button {
        background-color: var(--dl-blue) !important;
        color: #ffffff !important;
        border: 1px solid var(--dl-blue) !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 6px 16px !important;
        transition: background-color 0.15s ease !important;
    }
    
    .stButton>button:hover {
        background-color: var(--dl-blue-hover) !important;
        border-color: var(--dl-blue-hover) !important;
    }

    /* Заголовки */
    h1, h2, h3 {
        color: var(--dl-text-light) !important;
        font-weight: 500 !important;
    }
    
    /* Таблицы */
    .dataframe {
        border: 1px solid var(--dl-border) !important;
        background-color: #161b22 !important;
    }

    /* Кастомная панель навигации в сайдбаре */
    .nav-item {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        color: var(--dl-text-main);
        text-decoration: none;
        border-radius: 4px;
        margin-bottom: 4px;
        font-size: 0.9rem;
        cursor: pointer;
    }
    .nav-item:hover {
        background-color: rgba(255,255,255,0.05);
        color: var(--dl-text-light);
    }
    .nav-item.active {
        background-color: rgba(56, 144, 255, 0.15);
        color: var(--dl-blue);
        font-weight: 500;
        border-left: 3px solid var(--dl-blue);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. ГЕНЕРАЦИЯ ДАННЫХ ДЛЯ ДАШБОРДА (ИЮНЬ 2026)
# ---------------------------------------------------------

@st.cache_data
def get_datalens_dataset():
    start_date = date(2026, 6, 1)
    days_count = 30
    dates = [start_date + timedelta(days=i) for i in range(days_count)]
    
    # KPI параметры
    budget_plan = 40000.0
    leads_plan = 100
    cpl_plan = 400.0
    
    daily_budget_plan = budget_plan / days_count
    daily_leads_plan = leads_plan / days_count
    
    np.random.seed(101)
    
    # Генерация затрат и лидов
    spent = np.random.normal(1300, 150, days_count)
    spent = np.clip(spent, 900, 1800)
    
    leads = np.random.poisson(3.6, days_count)
    leads = np.clip(leads, 0, 8)
    
    # Корректировка под выходные
    for i, d in enumerate(dates):
        if d.weekday() in (5, 6):
            spent[i] *= 0.65
            leads[i] = max(0, leads[i] - 1)
            
    spent = np.round(spent, 2)
    leads = leads.astype(int)
    
    # Накопительные итоги
    cum_spent = np.cumsum(spent)
    cum_leads = np.cumsum(leads)
    cum_spent_plan = [daily_budget_plan * (i + 1) for i in range(days_count)]
    cum_leads_plan = [daily_leads_plan * (i + 1) for i in range(days_count)]
    
    # CTR & Clicks
    ctr = np.random.uniform(6.0, 7.8, days_count)
    clicks = (spent / np.random.uniform(17, 23, days_count)).astype(int)
    clicks = np.clip(clicks, 25, 120)
    impressions = (clicks / (ctr / 100)).astype(int)
    
    df = pd.DataFrame({
        "Date": pd.to_datetime(dates),
        "Impressions": impressions,
        "Clicks": clicks,
        "Spent": spent,
        "Leads": leads,
        "CumSpent": cum_spent,
        "CumLeads": cum_leads,
        "CumSpentPlan": cum_spent_plan,
        "CumLeadsPlan": cum_leads_plan,
    })
    
    # CPL с обработкой нулевых лидов
    df["CPL"] = np.where(df["Leads"] > 0, np.round(df["Spent"] / df["Leads"], 2), 0.0)
    df["CTR"] = np.round((df["Clicks"] / df["Impressions"]) * 100, 2)
    df["CPC"] = np.where(df["Clicks"] > 0, np.round(df["Spent"] / df["Clicks"], 2), 0.0)
    
    return df, budget_plan, leads_plan, cpl_plan

df, budget_plan, leads_plan, cpl_plan = get_datalens_dataset()

# Определение журнала изменений (change_logs)
change_logs = pd.DataFrame([
    {"Date": "2026-06-03", "Changes": "Запуск новых РСЯ объявлений", "Expected": "Рост лидов", "Comment": "Добавили 4 новых креатива"},
    {"Date": "2026-06-10", "Changes": "Корректировка ставок по ключевым фразам", "Expected": "Снижение CPL", "Comment": "Понизили ставки на неконверсионные фразы"},
    {"Date": "2026-06-18", "Changes": "Обновление баннеров на поиске", "Expected": "Рост CTR", "Comment": "Заменили старые статичные баннеры"},
    {"Date": "2026-06-25", "Changes": "Добавление минус-слов", "Expected": "Очистка мусорного трафика", "Comment": "Исключили нецелевые запросы из отчета"}
])
change_logs["Date"] = pd.to_datetime(change_logs["Date"])

# ---------------------------------------------------------
# 2. ЛЕВАЯ ПАНЕЛЬ НАВИГАЦИИ (YANDEX DATALENS SIDEBAR)
# ---------------------------------------------------------

with st.sidebar:
    # Имитация брендинга Яндекс Облака / DataLens
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 25px;">
        <div style="background-color: #3890ff; width: 32px; height: 32px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.1rem;">
            DL
        </div>
        <div>
            <div style="font-weight: 500; font-size: 0.95rem; color: #f0f6fc; line-height: 1.2;">Yandex DataLens</div>
            <div style="font-size: 0.7rem; color: #8b949e;">Аналитическая система</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Пункты меню как в оригинальном DataLens
    menu_selection = st.radio(
        "Разделы:",
        ["Дашборды", "Чарты", "Датасеты", "Подключения", "Формулы и Справка"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #8b949e; padding: 10px 0;">
        <b>Текущий каталог:</b><br>
        Target Media / pilot-mvp
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. ЭКРАН: ПОДКЛЮЧЕНИЯ (CONNECTIONS)
# ---------------------------------------------------------

if menu_selection == "Подключения":
    st.title("🔌 Подключения (Connections)")
    st.subheader("Управление источниками данных рекламного агентства")
    
    st.markdown("Здесь настраиваются интеграции с рекламными кабинетами, счетчиками аналитики и ручными таблицами.")
    
    # Сетка подключений
    col_conn1, col_conn2, col_conn3 = st.columns(3)
    
    with col_conn1:
        st.markdown("""
        <div class="datalens-dashlet">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="font-size: 2rem;">🛡️</div>
                <div>
                    <h4 style="margin: 0; font-size: 1.05rem; color: #f0f6fc;">Yandex.Direct API</h4>
                    <span style="font-size: 0.75rem; color: #2baf56; font-weight: 600;">АКТИВНО (OAuth)</span>
                </div>
            </div>
            <p style="font-size: 0.8rem; color: #8b949e;">Логин кабинета: <b>e-17390364</b><br>НДС: <b>Включен (20%)</b><br>Период: Авто-обновление</p>
            <hr style="border-color: #21262d; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.75rem; color: #8b949e;">Обновлено 4 часа назад</span>
                <span style="color: #3890ff; font-size: 0.8rem; font-weight: 500; cursor: pointer;">Настроить</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_conn2:
        st.markdown("""
        <div class="datalens-dashlet">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="font-size: 2rem;">📈</div>
                <div>
                    <h4 style="margin: 0; font-size: 1.05rem; color: #f0f6fc;">Yandex.Metrika API</h4>
                    <span style="font-size: 0.75rem; color: #2baf56; font-weight: 600;">АКТИВНО</span>
                </div>
            </div>
            <p style="font-size: 0.8rem; color: #8b949e;">Счетчик: <b>96109777</b><br>Цели: <b>320946135, 320946351</b><br>Считать лидом: <b>Да</b></p>
            <hr style="border-color: #21262d; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.75rem; color: #8b949e;">Обновлено 4 часа назад</span>
                <span style="color: #3890ff; font-size: 0.8rem; font-weight: 500; cursor: pointer;">Настроить</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_conn3:
        st.markdown("""
        <div class="datalens-dashlet">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="font-size: 2rem;">📁</div>
                <div>
                    <h4 style="margin: 0; font-size: 1.05rem; color: #f0f6fc;">Google Sheets / Excel</h4>
                    <span style="font-size: 0.75rem; color: #2baf56; font-weight: 600;">ЗАГРУЖЕНО</span>
                </div>
            </div>
            <p style="font-size: 0.8rem; color: #8b949e;">Файл: <b>dashboard_input_pack_mvp...xlsx</b><br>План KPI: Лист 04 ( June 2026 )<br>Журнал изменений: Лист 05</p>
            <hr style="border-color: #21262d; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.75rem; color: #8b949e;">Обновлено вручную</span>
                <span style="color: #3890ff; font-size: 0.8rem; font-weight: 500; cursor: pointer;">Загрузить новый</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.button("+ Создать новое подключение")

# ---------------------------------------------------------
# 4. ЭКРАН: ДАТАСЕТЫ (DATASETS)
# ---------------------------------------------------------

elif menu_selection == "Датасеты":
    st.title("🗂️ Датасеты (Datasets)")
    st.subheader(" pilot_mvp_dataset.csv ")
    
    st.markdown("Результат логического объединения таблиц фактов (Директ + Метрика) и справочников по ключу `[Date, ProjectID]`. Этот датасет используется как источник данных для чартов и дашбордов.")
    
    # Поля датасета
    st.write("**Поля и типы данных логической схемы:**")
    fields_info = pd.DataFrame([
        {"Поле": "Date", "Тип": "Date (Идентификатор)", "Описание": "Календарный день сбора статистики"},
        {"Поле": "Impressions", "Тип": "Integer (Показатель)", "Описание": "Количество показов рекламы в Директе"},
        {"Поле": "Clicks", "Тип": "Integer (Показатель)", "Описание": "Количество переходов по объявлениям"},
        {"Поле": "Spent", "Тип": "Float (Показатель)", "Описание": "Затраты рекламного бюджета (с НДС)"},
        {"Поле": "Leads", "Тип": "Integer (Показатель)", "Описание": "Количество лидов (звонки + бронирования)"},
        {"Поле": "CPL", "Тип": "Float (Вычисляемое)", "Описание": "Стоимость одного лида: Spent / Leads"},
        {"Поле": "CTR", "Тип": "Float (Вычисляемое)", "Описание": "CTR объявлений: Clicks / Impressions * 100"},
        {"Поле": "CPC", "Тип": "Float (Вычисляемое)", "Описание": "Стоимость клика: Spent / Clicks"}
    ])
    st.table(fields_info)
    
    st.markdown("---")
    st.write("**Предпросмотр данных (Preview):**")
    st.dataframe(df, width="stretch")

# ---------------------------------------------------------
# 5. ЭКРАН: ЧАРТЫ (CHARTS / CHART BUILDER)
# ---------------------------------------------------------

elif menu_selection == "Чарты":
    st.title("📊 Конструктор чартов (Charts)")
    st.subheader("Визуализация показателей и построение графиков")
    
    st.info("Вы можете выбрать нужный показатель, сгруппировать его и настроить тип чарта так же, как в конструкторе Yandex DataLens.")
    
    col_ch_f1, col_ch_f2, col_ch_f3 = st.columns(3)
    with col_ch_f1:
        metric_choice = st.selectbox("Показатель (Y-axis):", ["Spent", "Leads", "CPL", "CTR", "CPC"])
    with col_ch_f2:
        chart_type = st.selectbox("Тип визуализации:", ["Линейный график (Line)", "Столбчатая диаграмма (Bar)", "Область с накоплением (Area)"])
    with col_ch_f3:
        color_choice = st.color_picker("Цвет графика:", "#3890ff")
        
    st.markdown("---")
    
    # Построение графика в зависимости от выбора
    if chart_type == "Линейный график (Line)":
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df[metric_choice],
            mode='lines+markers', name=metric_choice,
            line=dict(color=color_choice, width=2.5)
        ))
    elif chart_type == "Столбчатая диаграмма (Bar)":
        fig = px.bar(df, x="Date", y=metric_choice, color_discrete_sequence=[color_choice])
    else:
        fig = px.area(df, x="Date", y=metric_choice, color_discrete_sequence=[color_choice])
        
    fig.update_layout(
        title=f"График динамики показателя: {metric_choice}",
        xaxis_title="Дата",
        yaxis_title=metric_choice,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------
# 6. ЭКРАН: ДАШБОРДЫ (DASHBOARDS)
# ---------------------------------------------------------

elif menu_selection == "Дашборды":
    # ---------------------------------------------------------
    # СЕЛЕКТОРЫ И ФИЛЬТРЫ (В соответствии с DataLens - сверху дашборда!)
    # ---------------------------------------------------------
    st.title("🖥️ Дашборд: Контроль KPI рекламных кампаний")
    
    # Селекторы в один ряд сверху дашборда (Фирменный стиль DataLens!)
    st.markdown("""
    <div style="background-color: #161b22; border: 1px solid #21262d; border-radius: 4px; padding: 12px; margin-bottom: 20px;">
        <span style="font-size: 0.8rem; color: #8b949e; font-weight: 600; text-transform: uppercase;">Панель селекторов (Фильтры)</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
    with col_sel1:
        client_sel = st.selectbox("Клиент (Селектор):", ["ООО Парковка-Уфа"], label_visibility="collapsed")
    with col_sel2:
        project_sel = st.selectbox("Проект (Селектор):", ["Парковка Уфа (PR-001)"], label_visibility="collapsed")
    with col_sel3:
        manager_sel = st.selectbox("Ответственный (Селектор):", ["Александр"], label_visibility="collapsed")
    with col_sel4:
        # Упрощенный выбор периода дат
        date_sel = st.date_input("Период (Селектор):", value=(date(2026, 6, 1), date(2026, 6, 30)), label_visibility="collapsed")
        
    # Парсим выбранный диапазон дат
    if isinstance(date_sel, tuple) and len(date_sel) == 2:
        start_d, end_d = date_sel
    else:
        start_d, end_d = date(2026, 6, 1), date(2026, 6, 30)
        
    # Фильтруем данные дашборда
    df_filtered = df[(df["Date"].dt.date >= start_d) & (df["Date"].dt.date <= end_d)].copy()
    days_elapsed = len(df_filtered)
    
    # Вкладки внутри дашборда (Сводный экран / Карточка проекта)
    tab_summary, tab_detail = st.tabs(["🏛️ Сводный экран по агентству", "📇 Детальная карточка: Парковка Уфа"])
    
    # --- ВКЛАДКА 1: СВОДНЫЙ ЭКРАН ---
    with tab_summary:
        # Агрегация данных за выбранный период
        total_spent = df_filtered["Spent"].sum()
        total_leads = df_filtered["Leads"].sum()
        avg_cpl = total_spent / total_leads if total_leads > 0 else 0.0
        
        # Пропорциональный план для выбранных дней
        prop_budget_plan = (budget_plan / 30) * days_elapsed
        prop_leads_plan = int((leads_plan / 30) * days_elapsed)
        
        # Pacing
        daily_spent_fact = total_spent / days_elapsed if days_elapsed > 0 else 0.0
        daily_spent_plan = budget_plan / 30
        pacing_pct = (daily_spent_fact / daily_spent_plan) * 100 if daily_spent_plan > 0 else 0.0
        
        # Карточки KPI (в DataLens они называются Селекторы-Индикаторы)
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        
        with col_kpi1:
            spent_progress_pct = (total_spent / prop_budget_plan * 100) if prop_budget_plan > 0 else 0.0
            st.metric(
                label="Расход бюджета (Факт / План)",
                value=f"{total_spent:,.0f} ₽",
                delta=f"{spent_progress_pct:.1f}% от лимита"
            )
            
        with col_kpi2:
            leads_progress_pct = (total_leads / prop_leads_plan * 100) if prop_leads_plan > 0 else 0.0
            st.metric(
                label="Количество Лидов (Факт / План)",
                value=f"{total_leads} шт",
                delta=f"{leads_progress_pct:.1f}% от плана",
                delta_color="normal"
            )
            
        with col_kpi3:
            cpl_dev_pct = ((avg_cpl - cpl_plan) / cpl_plan * 100) if cpl_plan > 0 else 0.0
            st.metric(
                label="Стоимость лида CPL (Факт / План)",
                value=f"{avg_cpl:,.1f} ₽",
                delta=f"{cpl_dev_pct:+.1f}% отклонение",
                delta_color="inverse"
            )
            
        with col_kpi4:
            st.metric(
                label="Индекс темпа расхода (Pacing)",
                value=f"{pacing_pct:.1f}%",
                delta="В норме" if 90 <= pacing_pct <= 110 else ("Перерасход" if pacing_pct > 110 else "Недорасход"),
                delta_color="off"
            )
            
        st.markdown("---")
        st.write("**Логическая матрица контроля проектов (Таблица выполнения KPI):**")
        
        # Строка "Парковки Уфа" и две виртуальные строки для демонстрации вложенности и фильтрации
        rows = [
            {
                "Название проекта": "Парковка Уфа (PR-001)",
                "Менеджер": "Александр",
                "Расход (Факт)": f"{total_spent:,.0f} ₽",
                "Расход (% Плана)": f"{spent_progress_pct:.1f}%",
                "Лиды (Факт / План)": f"{total_leads} / {prop_leads_plan}",
                "Лиды (% Выполнения)": f"{leads_progress_pct:.1f}%",
                "Целевой CPL": f"{cpl_plan:,.0f} ₽",
                "Фактический CPL": f"{avg_cpl:,.0f} ₽",
                "Pacing расхода": f"{pacing_pct:.1f}%",
                "_pacing": pacing_pct,
                "_cpl_dev": cpl_dev_pct
            },
            {
                "Название проекта": "Развозка сотрудников СПБ",
                "Менеджер": "Дмитрий",
                "Расход (Fact)": "14,800 ₽",
                "Расход (% Плана)": "92.5%",
                "Лиды (Факт / План)": "48 / 50",
                "Лиды (% Выполнения)": "96.0%",
                "Целевой CPL": "300 ₽",
                "Фактический CPL": "308 ₽",
                "Pacing расхода": "93.4%",
                "_pacing": 93.4,
                "_cpl_dev": 2.6
            },
            {
                "Название проекта": "Эвакуатор Казань Быстро",
                "Менеджер": "Мария",
                "Расход (Fact)": "28,600 ₽",
                "Расход (% Плана)": "119.2%",
                "Лиды (Факт / План)": "32 / 40",
                "Лиды (% Выполнения)": "80.0%",
                "Целевой CPL": "600 ₽",
                "Фактический CPL": "893 ₽",
                "Pacing расхода": "121.5%",
                "_pacing": 121.5,
                "_cpl_dev": 48.8
            }
        ]
        
        matrix_df = pd.DataFrame(rows)
        
        # Применяем условное форматирование в стиле DataLens
        def dl_style_deviation(row):
            color = 'background-color: transparent'
            # Превышение pacing > 15% (т.е. > 115%) или критическое удорожание CPL > 10%
            if row['_pacing'] > 115.0 or row['_cpl_dev'] > 10.0:
                color = 'background-color: rgba(248, 81, 73, 0.15); color: #ff6e6e;' # Yandex Red 15% opacity
            elif 90.0 <= row['_pacing'] <= 110.0 and row['_cpl_dev'] <= 0:
                color = 'background-color: rgba(43, 175, 86, 0.15); color: #56d364;' # Yandex Green 15% opacity
            return [color] * len(row)

        styled_df = matrix_df.style.apply(dl_style_deviation, axis=1)
        columns_to_hide = ["_pacing", "_cpl_dev"]
        try:
            styled_df = styled_df.hide(axis="columns", subset=columns_to_hide)
        except Exception:
            try:
                styled_df = styled_df.hide_columns(columns_to_hide)
            except Exception:
                try:
                    styled_df = styled_df.hide(columns_to_hide)
                except Exception:
                    pass
        st.dataframe(styled_df, width="stretch")
        
        st.markdown("""
        <div style="font-size: 0.8rem; color: #8b949e; margin-top: 10px;">
            ⚠️ <b>Маркеры отклонений:</b> Подсветка строки включается автоматически при перерасходе суточного лимита бюджета на 15% или удорожании CPL на 10%.
        </div>
        """, unsafe_allow_html=True)
        
    # --- ВКЛАДКА 2: ДЕТАЛЬНАЯ КАРТОЧКА ---
    with tab_detail:
        st.subheader("Проект: Парковка Уфа (PR-001)")
        
        # 1. Линейный график накопительного Spent & Leads (Pacing)
        st.markdown("#### Накопительные графики Pacing")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            fig_spent_cum = go.Figure()
            fig_spent_cum.add_trace(go.Scatter(
                x=df_filtered["Date"], y=df_filtered["CumSpent"],
                mode="lines+markers", name="Расход (Факт)",
                line=dict(color="#3890ff", width=3)
            ))
            fig_spent_cum.add_trace(go.Scatter(
                x=df_filtered["Date"], y=df_filtered["CumSpentPlan"],
                mode="lines", name="Расход (План равномерный)",
                line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dash")
            ))
            fig_spent_cum.update_layout(
                title="Накопительный расход бюджета за период",
                xaxis_title="Дата",
                yaxis_title="Затраты (руб.)",
                template="plotly_dark",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig_spent_cum, width="stretch")
            
        with col_c2:
            fig_leads_cum = go.Figure()
            fig_leads_cum.add_trace(go.Scatter(
                x=df_filtered["Date"], y=df_filtered["CumLeads"],
                mode="lines+markers", name="Лиды (Факт)",
                line=dict(color="#2baf56", width=3)
            ))
            fig_leads_cum.add_trace(go.Scatter(
                x=df_filtered["Date"], y=df_filtered["CumLeadsPlan"],
                mode="lines", name="Лиды (План равномерный)",
                line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dash")
            ))
            fig_leads_cum.update_layout(
                title="Накопительный объем лидов за период",
                xaxis_title="Дата",
                yaxis_title="Лиды (шт)",
                template="plotly_dark",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig_leads_cum, width="stretch")
            
        st.markdown("---")
        
        # 2. Столбчатый график лидов и линейный CPL
        st.markdown("#### Дневная динамика показателей")
        col_c3, col_c4 = st.columns(2)
        
        with col_c3:
            fig_leads_daily = px.bar(
                df_filtered, x="Date", y="Leads",
                title="Лиды по дням (шт)",
                color_discrete_sequence=["#3890ff"]
            )
            fig_leads_daily.update_layout(template="plotly_dark")
            st.plotly_chart(fig_leads_daily, width="stretch")
            
        with col_c4:
            fig_cpl_daily = px.line(
                df_filtered, x="Date", y="CPL",
                title="Динамика CPL по дням (руб.)",
                color_discrete_sequence=["#ff9900"],
                markers=True
            )
            fig_cpl_daily.add_hline(
                y=cpl_plan, line_dash="dash", line_color="#f85149",
                annotation_text=f"Лимит CPL {cpl_plan} ₽", annotation_position="top left"
            )
            fig_cpl_daily.update_layout(template="plotly_dark")
            st.plotly_chart(fig_cpl_daily, width="stretch")
            
        st.markdown("---")
        
        # 3. Operational Timeline
        st.markdown("#### Операционный таймлайн ( Change Log )")
        
        # Журнал изменений из Excel
        st.table(change_logs)

# ---------------------------------------------------------
# 7. ЭКРАН: СПРАВКА И ФОРМУЛЫ (METRICS EXPLAINER)
# ---------------------------------------------------------

else:
    st.title("📐 Реестр метрик и формулы")
    st.subheader("Математические модели Yandex DataLens в дашборде")
    
    st.markdown("### Стоимость лида (Fact CPL)")
    st.latex(r"""
    \text{Fact CPL} = \begin{cases} 
    \frac{\text{Fact Spend}}{\text{Fact Leads}}, & \text{if Fact Leads} > 0 \\
    0.0, & \text{if Fact Leads} = 0 
    \end{cases}
    """)
    
    st.markdown("### Темп расхода рекламного бюджета (Budget Pacing)")
    st.latex(r"""
    \text{Pacing (\%)} = \frac{\text{Fact Spend}_{\text{daily\_avg}}}{\text{Plan Spend}_{\text{daily\_avg}}} \times 100\% = \frac{\text{Cumulative Fact Spend} / D_{\text{elapsed}}}{\text{Total Monthly Budget Plan} / D_{\text{total}}} \times 100\%
    """)
    
    st.markdown("### Выполнение планового объема лидов (Lead Pacing)")
    st.latex(r"""
    \text{Lead Pacing (\%)} = \frac{\text{Cumulative Fact Leads}}{\text{Expected Cumulative Plan Leads for Current Day}} \times 100\%
    """)
    st.latex(r"""
    \text{Expected Cumulative Plan Leads for Current Day} = \frac{\text{Total Monthly Leads Plan}}{D_{\text{total}}} \times D_{\text{elapsed}}
    """)
    
    st.markdown("### Исключение НДС из затрат")
    st.latex(r"""
    \text{Spent}_{\text{ex\_vat}} = \frac{\text{Spent}_{\text{with\_vat}}}{1 + \text{VAT Rate}} = \frac{\text{Spent}_{\text{with\_vat}}}{1.20}
    """)
