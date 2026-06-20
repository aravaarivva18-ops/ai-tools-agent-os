import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta

# Настройка страницы
st.set_page_config(
    page_title="Рука на пульсе | Target Media Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стилизация под темную тему Yandex DataLens BI
st.markdown("""
<style>
    .reportview-container {
        background-color: #0b0f17;
    }
    .main {
        background-color: #0b0f17;
        color: #f1f5f9;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
        color: #ffffff;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-card {
        background-color: #141923;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. ГЕНЕРАЦИЯ MOCK-ДАННЫХ (ПАРКОВКА УФА - ИЮНЬ 2026)
# ---------------------------------------------------------

@st.cache_data
def generate_mock_data():
    # Период: Июнь 2026
    start_date = date(2026, 6, 1)
    end_date = date(2026, 6, 30)
    days_count = 30
    
    # Генерация дат
    dates = [start_date + timedelta(days=i) for i in range(days_count)]
    
    # Сид для воспроизводимости
    np.random.seed(42)
    
    # Плановые KPI (Июнь 2026)
    budget_plan = 40000.0
    leads_plan = 100
    cpl_plan = 400.0
    
    daily_budget_plan = budget_plan / days_count
    daily_leads_plan = leads_plan / days_count
    
    # Фактические показатели по дням
    spent_raw = np.random.normal(1200, 200, days_count)  # Средний расход ~1200 руб/день
    spent_raw = np.clip(spent_raw, 800, 2000)
    
    # Лиды (Звонок + Бронь)
    leads_raw = np.random.poisson(3.5, days_count)      # Среднее число лидов ~3.5 в день
    leads_raw = np.clip(leads_raw, 0, 10)
    
    # В выходные трафик и расход чуть снижаются
    for i, d in enumerate(dates):
        if d.weekday() in (5, 6): # Суббота, Воскресенье
            spent_raw[i] *= 0.7
            leads_raw[i] = max(0, leads_raw[i] - 1)
            
    # Приводим к красивым округленным значениям
    spent = np.round(spent_raw, 2)
    leads = leads_raw.astype(int)
    
    # Накапливаемые (cumulative) показатели
    cum_spent = np.cumsum(spent)
    cum_leads = np.cumsum(leads)
    
    # Накапливаемый линейный план
    cum_spent_plan = [daily_budget_plan * (i + 1) for i in range(days_count)]
    cum_leads_plan = [daily_leads_plan * (i + 1) for i in range(days_count)]
    
    # Клики и Показы для детальности
    ctr = np.random.uniform(5.5, 8.2, days_count)
    clicks = (spent / np.random.uniform(15, 22, days_count)).astype(int)
    clicks = np.clip(clicks, 30, 150)
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
    
    # Вычисляем дневной CPL
    df["CPL"] = np.where(df["Leads"] > 0, np.round(df["Spent"] / df["Leads"], 2), 0.0)
    
    return df, budget_plan, leads_plan, cpl_plan

# Загружаем данные
df, budget_plan, leads_plan, cpl_plan = generate_mock_data()

# Данные Change Log (Журнал изменений)
change_logs = pd.DataFrame([
    {"Date": "2026-06-03", "Changes": "Запуск новых РСЯ объявлений", "Expected": "Рост лидов", "Comment": "Добавили 4 новых креатива"},
    {"Date": "2026-06-10", "Changes": "Корректировка ставок по ключевым фразам", "Expected": "Снижение CPL", "Comment": "Понизили ставки на неконверсионные фразы"},
    {"Date": "2026-06-18", "Changes": "Обновление баннеров на поиске", "Expected": "Рост CTR", "Comment": "Заменили старые статичные баннеры"},
    {"Date": "2026-06-25", "Changes": "Добавление минус-слов", "Expected": "Очистка мусорного трафика", "Comment": "Исключили нецелевые запросы из отчета"}
])
change_logs["Date"] = pd.to_datetime(change_logs["Date"])

# ---------------------------------------------------------
# 2. БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ
# ---------------------------------------------------------

st.sidebar.image("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/chart-line.svg", width=50)
st.sidebar.title("Навигация и Фильтры")

# Выбор экрана
view_mode = st.sidebar.radio(
    "Выберите режим отображения:",
    ["Сводный экран агентства", "Карточка клиента: Парковка Уфа", "Методология и формулы"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Глобальные фильтры")

# Фильтры в соответствии с ТЗ
client_filter = st.sidebar.selectbox("Клиент:", ["Все клиенты", "ООО Парковка-Уфа"])
project_filter = st.sidebar.selectbox("Проект:", ["Все проекты", "Парковка Уфа (PR-001)"])
manager_filter = st.sidebar.selectbox("Аккаунт-менеджер:", ["Все менеджеры", "Александр"])

# Фильтр дат
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input(
    "Диапазон дат:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Валидация диапазона дат
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_filter, end_filter = date_range
else:
    start_filter, end_filter = min_date, max_date

# Фильтруем данные для расчетов
filtered_df = df[(df["Date"].dt.date >= start_filter) & (df["Date"].dt.date <= end_filter)].copy()

# Расчет количества прошедших дней в выбранном периоде для Pacing
total_days_in_month = 30
elapsed_days = len(filtered_df)

# ---------------------------------------------------------
# 3. ЭКРАН 1: СВОДНЫЙ ЭКРАН АГЕНТСТВА
# ---------------------------------------------------------

if view_mode == "Сводный экран агентства":
    st.title("📊 Сводный отчет по проектам")
    st.subheader(f"Контроль выполнения KPI за период {start_filter.strftime('%d.%m.%Y')} — {end_filter.strftime('%d.%m.%Y')}")
    
    # Агрегированные метрики агентства
    total_spent_fact = filtered_df["Spent"].sum()
    total_leads_fact = filtered_df["Leads"].sum()
    avg_cpl_fact = total_spent_fact / total_leads_fact if total_leads_fact > 0 else 0.0
    
    # Пропорциональный план для выбранного диапазона дат
    prop_budget_plan = (budget_plan / total_days_in_month) * elapsed_days
    prop_leads_plan = int((leads_plan / total_days_in_month) * elapsed_days)
    
    # Расчет Pacing (темп расхода)
    # Pacing = (Факт расход за прошедшие дни / Прошедшие дни) / (План расход на месяц / Всего дней в месяце)
    daily_spent_fact = total_spent_fact / elapsed_days if elapsed_days > 0 else 0.0
    daily_spent_plan = budget_plan / total_days_in_month
    budget_pacing = (daily_spent_fact / daily_spent_plan) * 100 if daily_spent_plan > 0 else 0.0
    
    # Отображение KPI-блоков верхнего уровня
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        spent_pct = (total_spent_fact / prop_budget_plan * 100) if prop_budget_plan > 0 else 0.0
        st.metric(
            label="Общий Расход (Факт / План)",
            value=f"{total_spent_fact:,.0f} ₽",
            delta=f"{spent_pct:.1f}% от плана периода",
            delta_color="off"
        )
        
    with col2:
        leads_pct = (total_leads_fact / prop_leads_plan * 100) if prop_leads_plan > 0 else 0.0
        st.metric(
            label="Всего Лидов (Факт / План)",
            value=f"{total_leads_fact} шт",
            delta=f"{leads_pct:.1f}% от плана периода",
            delta_color="normal"
        )
        
    with col3:
        cpl_deviation = ((avg_cpl_fact - cpl_plan) / cpl_plan * 100) if cpl_plan > 0 else 0.0
        st.metric(
            label="Средний CPL (Факт / План)",
            value=f"{avg_cpl_fact:,.1f} ₽",
            delta=f"{cpl_deviation:+.1f}% отклонение",
            delta_color="inverse"
        )
        
    with col4:
        # Цвет статуса pacing
        if budget_pacing > 110:
            pacing_status = "🔴 Перерасход"
        elif budget_pacing >= 90:
            pacing_status = "🟢 В норме"
        else:
            pacing_status = "🟡 Недорасход"
            
        st.metric(
            label="Темп расхода (Pacing)",
            value=f"{budget_pacing:.1f}%",
            delta=pacing_status,
            delta_color="off"
        )
        
    st.markdown("---")
    st.subheader("Кросс-проектная матрица выполнения планов")
    
    # Формируем таблицу проектов (для MVP у нас один проект, покажем его выполнение и добавим виртуальные для демонстрации)
    project_rows = [
        {
            "Проект": "Парковка Уфа (PR-001)",
            "Менеджер": "Александр",
            "Расход (Факт)": f"{total_spent_fact:,.2f} ₽",
            "Расход (% Плана)": f"{spent_pct:.1f}%",
            "Лиды (Факт)": f"{total_leads_fact} / {prop_leads_plan}",
            "Лиды (% Выполнения)": f"{leads_pct:.1f}%",
            "План CPL": f"{cpl_plan:,.0f} ₽",
            "Факт CPL": f"{avg_cpl_fact:,.2f} ₽",
            "Pacing (Расход)": f"{budget_pacing:.1f}%",
            "Статус CPL": "В норме" if avg_cpl_fact <= cpl_plan else "Превышение",
            "_raw_cpl_dev": cpl_deviation,
            "_raw_pacing": budget_pacing
        },
        {
            "Проект": "Виртуальный Проект Б",
            "Менеджер": "Дмитрий",
            "Расход (Факт)": "32,500.00 ₽",
            "Расход (% Плана)": "108.3%",
            "Лиды (Факт)": "62 / 70",
            "Лиды (% Выполнения)": "88.6%",
            "План CPL": "500 ₽",
            "Факт CPL": "524.19 ₽",
            "Pacing (Расход)": "115.4%",
            "Статус CPL": "Превышение",
            "_raw_cpl_dev": 4.8,
            "_raw_pacing": 115.4
        },
        {
            "Проект": "Виртуальный Проект В",
            "Менеджер": "Александр",
            "Расход (Факт)": "12,100.00 ₽",
            "Расход (% Плана)": "60.5%",
            "Лиды (Факт)": "45 / 40",
            "Лиды (% Выполнения)": "112.5%",
            "План CPL": "300 ₽",
            "Факт CPL": "268.89 ₽",
            "Pacing (Расход)": "62.1%",
            "Статус CPL": "В норме",
            "_raw_cpl_dev": -10.37,
            "_raw_pacing": 62.1
        }
    ]
    
    matrix_df = pd.DataFrame(project_rows)
    
    # Применяем условное форматирование к датафрейму
    def highlight_deviation(row):
        color = 'background-color: transparent'
        # Если перерасход pacing > 15% (т.е. pacing > 115%) или превышение CPL > 10%
        if row['_raw_pacing'] > 115.0 or row['_raw_cpl_dev'] > 10.0:
            color = 'background-color: rgba(239, 68, 68, 0.2); color: #f87171;'  # Светло-красный
        elif 90.0 <= row['_raw_pacing'] <= 110.0 and row['_raw_cpl_dev'] <= 0:
            color = 'background-color: rgba(16, 185, 129, 0.2); color: #34d399;' # Светло-зеленый
        return [color] * len(row)

    styled_df = matrix_df.style.apply(highlight_deviation, axis=1).hide(columns=["_raw_cpl_dev", "_raw_pacing"])
    
    st.dataframe(styled_df, use_container_width=True)
    
    st.info("💡 **Цветовая индикация:** Строки проектов подсвечиваются **красным** цветом, если Pacing расхода превышает 115% или CPL превышает плановый лимит более чем на 10%. **Зеленым** подсвечиваются проекты с отличной окупаемостью (CPL ниже плана и нормальный темп расхода).")

# ---------------------------------------------------------
# 4. ЭКРАН 2: ДЕТАЛЬНАЯ КАРТОЧКА КЛИЕНТА (ПАРКОВКА УФА)
# ---------------------------------------------------------

elif view_mode == "Карточка клиента: Парковка Уфа":
    st.title("📇 Детальная аналитика: Парковка Уфа")
    
    # Метаданные в шапке
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.markdown("**Клиент:** ООО Парковка-Уфа (CL-001)")
    with col_meta2:
        st.markdown("**Проект:** Парковка Уфа (PR-001)")
    with col_meta3:
        st.markdown("**Ответственный:** Александр")
    with col_meta4:
        st.markdown("**Статус проекта:** 🟢 Активен")
        
    st.markdown("---")
    
    # 4.1. Графики Pacing (Cumulative Spend & Cumulative Leads)
    st.subheader("📈 Контроль выгорания бюджета и темпа лидов (Pacing)")
    
    # Накопительные значения
    cumulative_dates = filtered_df["Date"]
    cum_spent_fact = filtered_df["CumSpent"]
    cum_spent_plan_vals = filtered_df["CumSpentPlan"]
    
    cum_leads_fact = filtered_df["CumLeads"]
    cum_leads_plan_vals = filtered_df["CumLeadsPlan"]
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # График накопительного расхода
        fig_spent = go.Figure()
        fig_spent.add_trace(go.Scatter(
            x=cumulative_dates, y=cum_spent_fact,
            mode='lines+markers', name='Факт накопленный',
            line=dict(color='#06b6d4', width=3),
            marker=dict(size=6)
        ))
        fig_spent.add_trace(go.Scatter(
            x=cumulative_dates, y=cum_spent_plan_vals,
            mode='lines', name='Линейный план',
            line=dict(color='rgba(255,255,255,0.4)', width=2, dash='dash')
        ))
        fig_spent.update_layout(
            title="Выгорание бюджета (Кумулятивно)",
            xaxis_title="Дата",
            yaxis_title="Затраты (руб.)",
            template="plotly_dark",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_spent, use_container_width=True)
        
    with col_chart2:
        # График накопительных лидов
        fig_leads = go.Figure()
        fig_leads.add_trace(go.Scatter(
            x=cumulative_dates, y=cum_leads_fact,
            mode='lines+markers', name='Факт накопленный',
            line=dict(color='#10b981', width=3),
            marker=dict(size=6)
        ))
        fig_leads.add_trace(go.Scatter(
            x=cumulative_dates, y=cum_leads_plan_vals,
            mode='lines', name='Линейный план',
            line=dict(color='rgba(255,255,255,0.4)', width=2, dash='dash')
        ))
        fig_leads.update_layout(
            title="Выполнение плана по лидам (Кумулятивно)",
            xaxis_title="Дата",
            yaxis_title="Лиды (шт)",
            template="plotly_dark",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_leads, use_container_width=True)
        
    st.markdown("---")
    
    # 4.2. Дневная динамика Лидов и CPL
    st.subheader("📊 Дневная динамика показателей")
    
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        # Столбчатый график дневных лидов
        fig_daily_leads = px.bar(
            filtered_df, x="Date", y="Leads",
            title="Количество лидов по дням",
            labels={"Leads": "Лиды (шт)", "Date": "Дата"},
            color_discrete_sequence=["#3b82f6"]
        )
        fig_daily_leads.update_layout(
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_daily_leads, use_container_width=True)
        
    with col_chart4:
        # Линейный график дневной стоимости лида
        fig_daily_cpl = px.line(
            filtered_df, x="Date", y="CPL",
            title="Дневной CPL (Стоимость лида)",
            labels={"CPL": "CPL (руб.)", "Date": "Дата"},
            color_discrete_sequence=["#8b5cf6"],
            markers=True
        )
        # Добавляем плановый ориентир
        fig_daily_cpl.add_hline(
            y=cpl_plan, line_dash="dash", line_color="#ef4444",
            annotation_text=f"Цель CPL: {cpl_plan} ₽", annotation_position="top left"
        )
        fig_daily_cpl.update_layout(
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_daily_cpl, use_container_width=True)
        
    st.markdown("---")
    
    # 4.3. Операционный таймлайн (Change Log)
    st.subheader("📋 Журнал изменений рекламных кампаний")
    
    # Фильтруем логи по выбранному диапазону дат
    filtered_logs = change_logs[
        (change_logs["Date"].dt.date >= start_filter) & 
        (change_logs["Date"].dt.date <= end_filter)
    ].sort_values("Date", ascending=False)
    
    if len(filtered_logs) > 0:
        # Вывод в красивом табличном виде
        display_logs = filtered_logs.copy()
        display_logs["Date"] = display_logs["Date"].dt.strftime("%d.%m.%Y")
        st.table(display_logs.rename(columns={
            "Date": "Дата изменений",
            "Changes": "Описание изменений на аккаунте",
            "Expected": "Ожидаемый эффект",
            "Comment": "Комментарии менеджера"
        }))
    else:
        st.info("Нет зафиксированных изменений на аккаунте за выбранный период дат.")

# ---------------------------------------------------------
# 5. ЭКРАН 3: МЕТОДОЛОГИЯ И ФОРМУЛЫ (LaTeX)
# ---------------------------------------------------------

else:
    st.title("📐 Реестр метрик и математических моделей")
    st.write("Все расчеты в дашборде «Рука на пульсе» строго соответствуют BI-требованиям архитектуры и описаны ниже с помощью LaTeX-нотации.")
    
    st.markdown("### 1. Расчет стоимости лида (CPL)")
    st.markdown("Для избежания критических ошибок деления на ноль при отсутствии конверсий за день или выбранный период применяется математическое ветвление:")
    st.latex(r"""
    \text{Fact CPL} = \begin{cases} 
    \frac{\text{Fact Spend}}{\text{Fact Leads}}, & \text{if Fact Leads} > 0 \\
    0.0, & \text{if Fact Leads} = 0 
    \end{cases}
    """)
    
    st.markdown("### 2. Темп выгорания бюджета (Budget Pacing)")
    st.markdown("Определяет текущую скорость расхода бюджета относительно идеальной равномерной скорости для освоения планового лимита к концу месяца:")
    st.latex(r"""
    \text{Budget Pacing (\%)} = \frac{\text{Fact Spend}_{\text{daily\_avg}}}{\text{Plan Spend}_{\text{daily\_avg}}} \times 100\% = \frac{\text{Cumulative Fact Spend} / D_{\text{elapsed}}}{\text{Total Monthly Budget Plan} / D_{\text{total}}} \times 100\%
    """)
    st.markdown("""
    *где:*
    * $D_{\text{elapsed}}$ — количество прошедших (или выбранных в фильтре) дней месяца.
    * $D_{\text{total}}$ — общее количество календарных дней в расчетном месяце (для Июня — 30).
    """)
    
    st.markdown("### 3. Выполнение планового объема лидов (Lead Pacing)")
    st.markdown("Рассчитывает процент выполнения плана по лидам на текущий день с учетом равномерно распределенной линейной цели:")
    st.latex(r"""
    \text{Lead Pacing (\%)} = \frac{\text{Cumulative Fact Leads}}{\text{Expected Cumulative Plan Leads for Current Day}} \times 100\%
    """)
    st.latex(r"""
    \text{Expected Cumulative Plan Leads for Current Day} = \frac{\text{Total Monthly Leads Plan}}{D_{\text{total}}} \times D_{\text{elapsed}}
    """)
    
    st.markdown("### 4. Очистка расходов от НДС (VAT Excluder)")
    st.markdown("В зависимости от настроек проекта в личном кабинете дашборда расход Директа приводится к единому базису (планы зафиксированы с учетом НДС 20%):")
    st.latex(r"""
    \text{Fact Spend}_{\text{ex\_vat}} = \frac{\text{Fact Spend}_{\text{with\_vat}}}{1 + \text{VAT Rate}} = \frac{\text{Fact Spend}_{\text{with\_vat}}}{1.20}
    """)
