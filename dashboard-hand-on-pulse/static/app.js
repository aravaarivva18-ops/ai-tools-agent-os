// Базовый URL API (пустой для работы на одном хосте)
const API_BASE = "";

// Состояние приложения
let state = {
    token: localStorage.getItem("token") || null,
    user: JSON.parse(localStorage.getItem("user")) || null,
    currentProject: null,
    chart: null,
    activeChartTab: "spent" // spent, leads, cpl
};

// --- УТИЛИТЫ ДЛЯ HTTP ЗАПРОСОВ ---

function getHeaders() {
    const headers = {
        "Content-Type": "application/json"
    };
    if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
    }
    return headers;
}

async function request(url, options = {}) {
    options.headers = { ...getHeaders(), ...options.headers };
    
    try {
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            // Токен устарел или невалиден
            logout();
            throw new Error("Необходима повторная авторизация");
        }
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Ошибка запроса (код ${response.status})`);
        }
        
        // Для редиректов
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        
        return await response.json();
    } catch (error) {
        console.error("HTTP Error:", error);
        throw error;
    }
}

// --- УПРАВЛЕНИЕ АВТОРИЗАЦИЕЙ ---

function showScreen(screenId) {
    const loginScreen = document.getElementById("login-screen");
    const appContainer = document.getElementById("app-container");
    
    const screens = [loginScreen, appContainer];
    screens.forEach(s => {
        if (s.id === screenId) {
            s.classList.remove("hidden");
            // Даем один кадр для применения анимации перехода
            requestAnimationFrame(() => {
                s.classList.remove("screen-hidden");
            });
        } else {
            s.classList.add("screen-hidden");
            setTimeout(() => {
                if (s.classList.contains("screen-hidden")) {
                    s.classList.add("hidden");
                }
            }, 350);
        }
    });
}

function checkAuth() {
    if (!state.token) {
        showScreen("login-screen");
        return false;
    }
    
    // Обновляем шапку
    document.getElementById("user-email").textContent = state.user?.email || "user@targetmedia.ru";
    document.getElementById("user-role").textContent = state.user?.role === "admin" ? "Администратор" : "Менеджер";
    
    showScreen("app-container");
    return true;
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    showScreen("login-screen");
    window.location.hash = "#/";
}

// --- РОУТИНГ (ROUTING) ---

function showView(viewId) {
    const summaryView = document.getElementById("summary-view");
    const detailView = document.getElementById("project-detail-view");
    const securityView = document.getElementById("security-view");
    
    const views = [summaryView, detailView, securityView];
    views.forEach(v => {
        if (v.id === viewId) {
            v.classList.remove("hidden");
            requestAnimationFrame(() => {
                v.classList.remove("screen-hidden");
            });
        } else {
            v.classList.add("screen-hidden");
            setTimeout(() => {
                if (v.classList.contains("screen-hidden")) {
                    v.classList.add("hidden");
                }
            }, 350);
        }
    });
}

async function handleRoute() {
    if (!checkAuth()) return;
    
    const hash = window.location.hash || "#/";
    
    if (hash === "#/" || hash === "#") {
        const startInput = document.getElementById("filter-start-date");
        const endInput = document.getElementById("filter-end-date");
        if (startInput) startInput.value = "";
        if (endInput) endInput.value = "";

        showView("summary-view");
        await loadSummary();
    } else if (hash.startsWith("#/project/")) {
        const parts = hash.split("/");
        const projectId = parseInt(parts[2]);
        if (projectId) {
            const startInput = document.getElementById("filter-start-date");
            const endInput = document.getElementById("filter-end-date");
            if (startInput) startInput.value = "";
            if (endInput) endInput.value = "";

            showView("project-detail-view");
            await loadProjectDetail(projectId);
        }
    } else if (hash === "#/security") {
        showView("security-view");
        initSecurityView();
    }
}

// --- СВОДНЫЙ ЭКРАН (SUMMARY) ---

async function loadSummary() {
    const tableBody = document.getElementById("projects-table-body");
    tableBody.innerHTML = Array.from({ length: 3 }).map(() => `
        <tr class="animate-pulse">
            <td class="py-4 px-6"><div class="h-6 w-32 skeleton"></div><div class="h-4 w-20 skeleton mt-2"></div></td>
            <td class="py-4 px-6"><div class="h-5 w-24 skeleton"></div></td>
            <td class="py-4 px-6"><div class="h-8 w-24 skeleton mx-auto"></div></td>
            <td class="py-4 px-6"><div class="h-8 w-24 skeleton mx-auto"></div></td>
            <td class="py-4 px-6"><div class="h-8 w-24 skeleton mx-auto"></div></td>
            <td class="py-4 px-6"><div class="h-8 w-24 skeleton mx-auto"></div></td>
            <td class="py-4 px-6"><div class="h-8 w-24 skeleton mx-auto"></div></td>
            <td class="py-4 px-6"><div class="h-7 w-20 skeleton mx-auto"></div></td>
        </tr>
    `).join("");
    
    try {
        const data = await request(`${API_BASE}/api/dashboard/summary`);
        
        // Обновляем месяц на бэйдже
        const monthParts = data.month.split('-');
        const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
        const formattedMonth = `${monthNames[parseInt(monthParts[1]) - 1]} ${monthParts[0]}`;
        document.getElementById("current-month-badge").textContent = formattedMonth;
        
        if (!data.projects || data.projects.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-slate-500">Нет активных проектов. Нажмите кнопку "Создать тест-проект", чтобы наполнить базу.</td></tr>`;
            updateSummaryCards(0, 0, 0);
            return;
        }
        
        let totalSpent = 0;
        let totalLeads = 0;
        tableBody.innerHTML = "";
        
        data.projects.forEach(p => {
            totalSpent += p.fact.spent;
            totalLeads += p.fact.leads;
            
            // Вычисляем стили светофора
            let budgetClass = "text-slate-300";
            let leadsClass = "text-slate-300";
            let qualLeadsClass = "text-slate-300";
            let cplClass = "text-slate-300";
            let pacingClass = "text-slate-300";
            
            if (p.plan) {
                // Бюджет (расход)
                const spentPct = p.deviations.budget_progress_pct;
                if (spentPct > 100) {
                    budgetClass = "bg-red-500/10 text-red-400 border border-red-500/20";
                } else if (spentPct >= 90) {
                    budgetClass = "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20";
                } else {
                    budgetClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                }
                
                // Лиды
                const leadsPct = p.deviations.leads_progress_pct;
                if (leadsPct >= 90) {
                    leadsClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                } else if (leadsPct >= 75) {
                    leadsClass = "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20";
                } else {
                    leadsClass = "bg-red-500/10 text-red-400 border border-red-500/20";
                }

                // Квал-лиды
                const qualLeadsPct = p.deviations.qual_leads_progress_pct;
                if (qualLeadsPct >= 90) {
                    qualLeadsClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                } else if (qualLeadsPct >= 75) {
                    qualLeadsClass = "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20";
                } else {
                    qualLeadsClass = "bg-red-500/10 text-red-400 border border-red-500/20";
                }
                
                // CPL
                const cplPct = p.deviations.cpl_deviation_pct;
                if (cplPct <= 0) {
                    cplClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                } else if (cplPct <= 15) {
                    cplClass = "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20";
                } else {
                    cplClass = "bg-red-500/10 text-red-400 border border-red-500/20";
                }

                // Pacing
                const pacingPct = p.deviations.budget_pacing_pct;
                if (pacingPct > 110) {
                    pacingClass = "bg-red-500/10 text-red-400 border border-red-500/20";
                } else if (pacingPct >= 90) {
                    pacingClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                } else {
                    pacingClass = "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20";
                }
            }
            
            const tr = document.createElement("tr");
            tr.className = "table-row-interactive hover:bg-slate-900/30 border-b border-slate-800/50";
            tr.innerHTML = `
                <td class="py-4 px-6">
                    <a href="#/project/${p.id}" class="font-semibold text-white hover:text-sky-400 transition block text-base">${p.project_name}</a>
                    <span class="text-xs text-slate-500">${p.client_name}</span>
                </td>
                <td class="py-4 px-6 text-slate-300">${p.manager_name}</td>
                <td class="py-4 px-6 text-center">
                    <div class="font-medium text-white">${formatCurrency(p.fact.spent)}</div>
                    ${p.plan ? `<div class="text-xs text-slate-500 mt-0.5">План: ${formatCurrency(p.plan.budget)}</div><span class="inline-block mt-1.5 px-2 py-0.5 text-2xs rounded-full font-medium ${budgetClass}">${p.deviations.budget_progress_pct}%</span>` : `<span class="text-xs text-slate-600">—</span>`}
                </td>
                <td class="py-4 px-6 text-center">
                    <div class="font-medium text-white">${p.fact.leads}</div>
                    ${p.plan ? `<div class="text-xs text-slate-500 mt-0.5">План: ${p.plan.leads}</div><span class="inline-block mt-1.5 px-2 py-0.5 text-2xs rounded-full font-medium ${leadsClass}">${p.deviations.leads_progress_pct}%</span>` : `<span class="text-xs text-slate-600">—</span>`}
                </td>
                <td class="py-4 px-6 text-center">
                    <div class="font-medium text-white">${p.fact.qualified_leads}</div>
                    ${p.plan ? `<div class="text-xs text-slate-500 mt-0.5">План: ${p.plan.qualified_leads}</div><span class="inline-block mt-1.5 px-2 py-0.5 text-2xs rounded-full font-medium ${qualLeadsClass}">${p.deviations.qual_leads_progress_pct}%</span>` : `<span class="text-xs text-slate-600">—</span>`}
                </td>
                <td class="py-4 px-6 text-center">
                    <div class="font-medium text-white">${formatCurrency(p.fact.cpl)}</div>
                    ${p.plan ? `<div class="text-xs text-slate-500 mt-0.5">План: ${formatCurrency(p.plan.cpl)}</div><span class="inline-block mt-1.5 px-2 py-0.5 text-2xs rounded-full font-medium ${cplClass}">${p.deviations.cpl_deviation_pct > 0 ? '+' : ''}${p.deviations.cpl_deviation_pct}%</span>` : `<span class="text-xs text-slate-600">—</span>`}
                </td>
                <td class="py-4 px-6 text-center">
                    <div class="font-medium text-white">${p.deviations.budget_pacing_pct}%</div>
                    ${p.plan ? `<span class="inline-block mt-1.5 px-2 py-0.5 text-2xs rounded-full font-medium ${pacingClass}">${p.deviations.budget_pacing_pct > 110 ? 'Перерасход' : (p.deviations.budget_pacing_pct >= 90 ? 'Норма' : 'Недорасход')}</span>` : `<span class="text-xs text-slate-600">—</span>`}
                </td>
                <td class="py-4 px-6 text-center">
                    <a href="#/project/${p.id}" class="py-1.5 px-3 rounded-lg bg-slate-850 hover:bg-slate-800 text-slate-200 hover:text-white font-medium text-xs transition btn-spring inline-flex items-center gap-1 border border-slate-800">
                        <i class="fa-solid fa-chart-line text-sky-400"></i> Анализ
                    </a>
                </td>
            `;
            tableBody.appendChild(tr);
        });
        
        updateSummaryCards(data.projects.length, totalSpent, totalLeads);
        
    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-red-400"><i class="fa-solid fa-triangle-exclamation mr-2"></i>Ошибка загрузки: ${error.message}</td></tr>`;
    }
}

function updateSummaryCards(count, spent, leads) {
    document.getElementById("summary-total-projects").textContent = count;
    document.getElementById("summary-total-spent").textContent = `${formatCurrency(spent)}`;
    document.getElementById("summary-total-leads").textContent = leads;
}

// --- ДЕТАЛЬНЫЙ ЭКРАН ПРОЕКТА (PROJECT DETAIL) ---

async function loadProjectDetail(projectId) {
    try {
        // Проверяем инпуты дат
        const startDateInput = document.getElementById("filter-start-date");
        const endDateInput = document.getElementById("filter-end-date");
        
        let url = `${API_BASE}/api/dashboard/project/${projectId}`;
        const params = [];
        if (startDateInput && startDateInput.value) {
            params.push(`start_date=${startDateInput.value}`);
        }
        if (endDateInput && endDateInput.value) {
            params.push(`end_date=${endDateInput.value}`);
        }
        if (params.length > 0) {
            url += `?${params.join("&")}`;
        }

        // Показываем пружинные скелетоны на время загрузки
        document.getElementById("detail-spent").innerHTML = `<div class="h-7 w-24 skeleton mx-auto md:mx-0"></div>`;
        document.getElementById("detail-leads").innerHTML = `<div class="h-7 w-12 skeleton mx-auto md:mx-0"></div>`;
        document.getElementById("detail-qual-leads").innerHTML = `<div class="h-7 w-12 skeleton mx-auto md:mx-0"></div>`;
        document.getElementById("detail-cpl").innerHTML = `<div class="h-7 w-20 skeleton mx-auto md:mx-0"></div>`;
        document.getElementById("detail-cpl-qual").innerHTML = `<div class="h-7 w-20 skeleton mx-auto md:mx-0"></div>`;
        document.getElementById("detail-pacing").innerHTML = `<div class="h-7 w-16 skeleton mx-auto md:mx-0"></div>`;

        const data = await request(url);
        state.currentProject = data;
        
        // Устанавливаем даты в инпуты, если они пришли от бэкенда и пустые в инпутах
        if (startDateInput && !startDateInput.value) {
            startDateInput.value = data.period.start_date;
        }
        if (endDateInput && !endDateInput.value) {
            endDateInput.value = data.period.end_date;
        }
        
        // Заполняем текстовые поля
        document.getElementById("project-detail-title").textContent = data.project.name;
        document.getElementById("project-detail-client").textContent = `Клиент: ${data.project.client_name}`;
        
        // Статус Яндекс.Токена
        const statusBadge = document.getElementById("project-yandex-status");
        if (data.project.has_yandex_token) {
            statusBadge.textContent = "API Яндекс.Директ подключен";
            statusBadge.className = "px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        } else {
            statusBadge.textContent = "API Яндекс.Директ отключен";
            statusBadge.className = "px-2.5 py-0.5 text-xs font-semibold rounded-full bg-red-500/10 text-red-400 border border-red-500/20";
        }
        
        // Заполняем карточки итогов
        document.getElementById("detail-spent").textContent = `${formatCurrency(data.totals.spent)} ₽`;
        document.getElementById("detail-spent-progress").textContent = data.plan ? `План: ${formatCurrency(data.plan.budget)} ₽` : "План: не установлен";
        
        document.getElementById("detail-leads").textContent = data.totals.leads;
        document.getElementById("detail-leads-progress").textContent = data.plan ? `План: ${data.plan.leads}` : "План: не установлен";
        
        document.getElementById("detail-qual-leads").textContent = data.totals.qualified_leads;
        document.getElementById("detail-qual-leads-progress").textContent = data.plan ? `План: ${data.plan.qualified_leads}` : "План: не установлен";
        
        document.getElementById("detail-cpl").textContent = `${formatCurrency(data.totals.cpl)} ₽`;
        document.getElementById("detail-cpl-progress").textContent = data.plan ? `План: ${formatCurrency(data.plan.cpl)} ₽` : "План: не установлен";
        
        document.getElementById("detail-cpl-qual").textContent = `${formatCurrency(data.totals.cpl_qualified)} ₽`;
        document.getElementById("detail-cpl-qual-progress").textContent = data.plan ? `План: ${formatCurrency(data.plan.cpl_qualified)} ₽` : "План: не установлен";
        
        document.getElementById("detail-pacing").textContent = `${data.totals.budget_pacing_pct}%`;
        
        // Цвета карточки pacing
        const pacingProgress = document.getElementById("detail-pacing-progress");
        const pacingVal = data.totals.budget_pacing_pct;
        if (data.plan) {
            if (pacingVal > 110) {
                pacingProgress.textContent = "Превышение нормы!";
                pacingProgress.className = "text-xs mt-2 pt-2 border-t border-slate-800 text-red-450 font-semibold";
            } else if (pacingVal >= 90) {
                pacingProgress.textContent = "В рамках нормы";
                pacingProgress.className = "text-xs mt-2 pt-2 border-t border-slate-800 text-emerald-400 font-semibold";
            } else {
                pacingProgress.textContent = "Недорасход бюджета";
                pacingProgress.className = "text-xs mt-2 pt-2 border-t border-slate-800 text-yellow-450 font-semibold";
            }
        } else {
            pacingProgress.textContent = "Норма: 100%";
            pacingProgress.className = "text-xs mt-2 pt-2 border-t border-slate-800 text-slate-500";
        }
        
        // Рендерим логи изменений
        renderChangeLogs(data.change_logs);
        
        // Рендерим графики
        renderChart();
        
    } catch (error) {
        alert(`Ошибка при загрузке деталей проекта: ${error.message}`);
        window.location.hash = "#/";
    }
}

function renderChangeLogs(logs) {
    const container = document.getElementById("change-logs-list");
    if (!logs || logs.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-slate-500 text-sm">В этом месяце изменений в журнале не зафиксировано</div>`;
        return;
    }
    
    container.innerHTML = "";
    logs.forEach(log => {
        const item = document.createElement("div");
        item.className = "p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex flex-col gap-1.5 text-xs";
        
        // Форматируем дату
        const dateParts = log.date.split('-');
        const formattedDate = `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`;
        
        item.innerHTML = `
            <div class="flex justify-between items-center">
                <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold text-2xs">${formattedDate}</span>
                ${log.expected_effect ? `<span class="text-sky-400 font-medium"><i class="fa-solid fa-arrow-trend-up mr-1"></i>${log.expected_effect}</span>` : ""}
            </div>
            <div class="text-slate-200 font-medium text-sm mt-1">${log.description}</div>
            ${log.comment ? `<div class="text-slate-400 mt-1 pl-2 border-l-2 border-slate-700 italic">${log.comment}</div>` : ""}
        `;
        container.appendChild(item);
    });
}

function renderChart() {
    const ctx = document.getElementById("project-chart").getContext("2d");
    const data = state.currentProject;
    
    if (!data || !data.daily_stats || data.daily_stats.length === 0) {
        if (state.chart) state.chart.destroy();
        return;
    }
    
    // Подготовка данных
    const labels = data.daily_stats.map(s => {
        const parts = s.date.split('-');
        return `${parts[2]}.${parts[1]}`;
    });
    
    let chartData = [];
    let label = "";
    let borderColor = "#0ea5e9";
    let backgroundColor = "rgba(14, 165, 233, 0.15)";
    
    if (state.activeChartTab === "spent") {
        chartData = data.daily_stats.map(s => s.spent);
        label = "Расход бюджета (₽)";
        borderColor = "#38bdf8";
        backgroundColor = "rgba(56, 189, 248, 0.1)";
    } else if (state.activeChartTab === "leads") {
        chartData = data.daily_stats.map(s => s.leads);
        label = "Лиды (шт)";
        borderColor = "#10b981";
        backgroundColor = "rgba(16, 185, 129, 0.1)";
    } else if (state.activeChartTab === "qual_leads") {
        chartData = data.daily_stats.map(s => s.qualified_leads);
        label = "Квалифицированные лиды (шт)";
        borderColor = "#059669";
        backgroundColor = "rgba(5, 150, 105, 0.1)";
    } else if (state.activeChartTab === "cpl") {
        chartData = data.daily_stats.map(s => s.cpl);
        label = "Стоимость лида CPL (₽)";
        borderColor = "#8b5cf6";
        backgroundColor = "rgba(139, 92, 246, 0.1)";
    } else if (state.activeChartTab === "cpl_qualified") {
        chartData = data.daily_stats.map(s => s.cpl_qualified);
        label = "CPL квалифицированного лида (₽)";
        borderColor = "#d946ef";
        backgroundColor = "rgba(217, 70, 239, 0.1)";
    }
    
    if (state.chart) {
        state.chart.destroy();
    }
    
    state.chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: chartData,
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                borderWidth: 2,
                fill: true,
                tension: 0.38,
                pointRadius: 2,
                pointHoverRadius: 6,
                pointBackgroundColor: borderColor,
                pointHoverBackgroundColor: "#ffffff",
                pointHoverBorderColor: borderColor,
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.9)",
                    titleFont: { family: "Outfit", size: 12, weight: "bold" },
                    bodyFont: { family: "Inter", size: 12 },
                    padding: 10,
                    borderColor: "rgba(255, 255, 255, 0.08)",
                    borderWidth: 1,
                    borderRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: "#8a94a6",
                        font: {
                            family: "Inter",
                            size: 10
                        }
                    }
                },
                y: {
                    grid: {
                        color: "rgba(255, 255, 255, 0.04)",
                        drawBorder: false
                    },
                    ticks: {
                        color: "#8a94a6",
                        font: {
                            family: "Inter",
                            size: 10
                        }
                    }
                }
            }
        }
    });
}

// --- УТИЛИТЫ ДЛЯ СЛУШАТЕЛЕЙ (LISTENERS) ---

function formatCurrency(value) {
    if (value === undefined || value === null) return "0";
    return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(value);
}

// --- НАСТРОЙКА ОБРАБОТЧИКОВ И ИНИЦИАЛИЗАЦИЯ ---

document.addEventListener("DOMContentLoaded", () => {
    // 1. Слушатель роутинга
    window.addEventListener("hashchange", handleRoute);
    
    // 2. Логин
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        const errorBlock = document.getElementById("login-error");
        
        errorBlock.classList.add("hidden");
        
        try {
            const data = await request(`${API_BASE}/api/auth/login`, {
                method: "POST",
                body: JSON.stringify({ email, password })
            });
            
            state.token = data.access_token;
            state.user = data.user;
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            
            showScreen("app-container");
            await handleRoute();
        } catch (err) {
            errorBlock.classList.remove("hidden");
            document.getElementById("login-error-msg").textContent = err.message;
        }
    });
    
    // 3. Выход
    document.getElementById("logout-btn").addEventListener("click", logout);
    
    // 4. Кнопка автонастройки тестовой структуры
    document.getElementById("setup-test-btn").addEventListener("click", async () => {
        const btn = document.getElementById("setup-test-btn");
        const originalContent = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Создаем...`;
        btn.disabled = true;
        
        try {
            await request(`${API_BASE}/api/test/setup`, { method: "POST" });
            // Сразу после создания тестовой структуры, запустим ее синхронизацию
            await request(`${API_BASE}/api/dashboard/project/1/sync`, { method: "POST" });
            // И импорт Excel данных
            alert("Тестовый проект 'Парковка Уфа' успешно создан, статистика сгенерирована, планы KPI импортированы из Excel!");
            await loadSummary();
        } catch (err) {
            alert(`Ошибка при настройке: ${err.message}`);
        } finally {
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
    });
    
    // 5. Синхронизация проекта
    document.getElementById("project-sync-btn").addEventListener("click", async () => {
        if (!state.currentProject) return;
        const projectId = state.currentProject.project.id;
        const btn = document.getElementById("project-sync-btn");
        const originalContent = btn.innerHTML;
        
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Синхронизация...`;
        btn.disabled = true;
        
        try {
            await request(`${API_BASE}/api/dashboard/project/${projectId}/sync`, { method: "POST" });
            alert("Данные успешно синхронизированы!");
            await loadProjectDetail(projectId);
        } catch (err) {
            alert(`Ошибка синхронизации: ${err.message}`);
        } finally {
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
    });
    
    // 6. Подключение Яндекс OAuth
    document.getElementById("yandex-auth-btn").addEventListener("click", async () => {
        if (!state.currentProject) return;
        const projectId = state.currentProject.project.id;
        
        try {
            const data = await request(`${API_BASE}/api/auth/yandex/login?project_id=${projectId}`);
            if (data && data.auth_url) {
                // Перенаправляем на Яндекс OAuth
                window.location.href = data.auth_url;
            }
        } catch (err) {
            alert(`Не удалось запустить авторизацию: ${err.message}`);
        }
    });
    
    // 7. Переключение вкладок графика
    const tabButtons = document.querySelectorAll(".chart-tab-btn");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            tabButtons.forEach(b => {
                b.classList.remove("bg-sky-600", "text-white");
                b.classList.add("bg-slate-800", "text-slate-400");
            });
            btn.classList.remove("bg-slate-800", "text-slate-400");
            btn.classList.add("bg-sky-600", "text-white");
            
            state.activeChartTab = btn.getAttribute("data-chart");
            renderChart();
        });
    });
    
    // 8. Кнопка применить фильтр дат
    document.getElementById("apply-filter-btn").addEventListener("click", async () => {
        if (!state.currentProject) return;
        const projectId = state.currentProject.project.id;
        await loadProjectDetail(projectId);
    });

    // Запускаем роутинг при старте
    handleRoute();
});

// --- РАЗДЕЛ БЕЗОПАСНОСТИ ---

function initSecurityView() {
    const scanBtn = document.getElementById("run-scan-btn");
    if (scanBtn) {
        scanBtn.onclick = runSecurityScan;
    }
}

async function runSecurityScan() {
    const scanBtn = document.getElementById("run-scan-btn");
    const statusText = document.getElementById("scan-status-text");
    const totalSecrets = document.getElementById("scan-total-secrets");
    const totalSast = document.getElementById("scan-total-sast");
    const secretsContainer = document.getElementById("secrets-scan-results");
    const sastContainer = document.getElementById("sast-scan-results");
    
    if (!scanBtn) return;
    
    // Блокируем кнопку
    scanBtn.disabled = true;
    scanBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Сканирование...`;
    statusText.textContent = "Выполняется сканирование...";
    
    secretsContainer.innerHTML = `<div class="text-center py-12"><i class="fa-solid fa-spinner fa-spin text-xl text-sky-400"></i><p class="text-xs text-slate-400 mt-2">Поиск секретов...</p></div>`;
    sastContainer.innerHTML = `<div class="text-center py-12"><i class="fa-solid fa-spinner fa-spin text-xl text-sky-400"></i><p class="text-xs text-slate-400 mt-2">Анализ кода Bandit...</p></div>`;
    
    try {
        const data = await request(`${API_BASE}/api/security/scan`, { method: "POST" });
        
        statusText.textContent = "Сканирование завершено";
        totalSecrets.textContent = data.secrets.summary.total;
        totalSast.textContent = data.bandit.summary.total;
        
        // 1. Отображаем секреты
        if (data.secrets.findings.length === 0) {
            secretsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12 text-emerald-400">
                    <i class="fa-regular fa-circle-check text-4xl mb-3"></i>
                    <p class="font-semibold text-sm">Секреты не найдены</p>
                    <p class="text-xs text-slate-500 mt-1">Все файлы чисты от токенов и паролей</p>
                </div>`;
        } else {
            secretsContainer.innerHTML = data.secrets.findings.map(f => {
                if (f.error) {
                    return `
                        <div class="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                            Ошибка: ${f.error}
                        </div>`;
                }
                const shortFile = f.file.replace("/Users/rus/ai-tools/", "");
                return `
                    <div class="p-4 rounded-lg bg-red-500/5 border border-red-500/20 text-xs hover:border-red-500/40 transition">
                        <div class="flex justify-between items-start gap-2 mb-2">
                            <span class="font-bold text-red-400 flex items-center gap-1.5">
                                <i class="fa-solid fa-triangle-exclamation"></i> ${f.type}
                            </span>
                            <span class="text-[10px] text-slate-500 font-mono">${shortFile}:${f.line}</span>
                        </div>
                        <div class="bg-slate-950 p-2.5 rounded font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre"><code>${escapeHtml(f.context)}</code></div>
                    </div>`;
            }).join("");
        }
        
        // 2. Отображаем уязвимости Bandit SAST
        if (data.bandit.issues.length === 0) {
            sastContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12 text-emerald-400">
                    <i class="fa-regular fa-circle-check text-4xl mb-3"></i>
                    <p class="font-semibold text-sm">Уязвимости не найдены</p>
                    <p class="text-xs text-slate-500 mt-1">Bandit SAST не обнаружил проблем безопасности</p>
                </div>`;
        } else {
            sastContainer.innerHTML = data.bandit.issues.map(issue => {
                const shortFile = issue.filename.replace("/Users/rus/ai-tools/", "");
                const severity = issue.issue_severity || "LOW";
                
                let severityBadge = "";
                if (severity === "HIGH") {
                    severityBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30">HIGH</span>`;
                } else if (severity === "MEDIUM") {
                    severityBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">MEDIUM</span>`;
                } else {
                    severityBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">LOW</span>`;
                }
                
                return `
                    <div class="p-4 rounded-lg bg-slate-900/40 border border-slate-800 text-xs hover:border-slate-700 transition">
                        <div class="flex justify-between items-start gap-2 mb-2">
                            <span class="font-semibold text-white flex items-center gap-1.5">
                                ${severityBadge} <span class="text-slate-200">${issue.test_name}</span>
                            </span>
                            <span class="text-[10px] text-slate-500 font-mono">${shortFile}:${issue.line_number}</span>
                        </div>
                        <p class="text-slate-400 mb-2 font-medium">${escapeHtml(issue.issue_text)}</p>
                        <div class="bg-slate-950 p-2.5 rounded font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre"><code>${escapeHtml(issue.code)}</code></div>
                    </div>`;
            }).join("");
        }
        
    } catch (err) {
        statusText.textContent = "Ошибка при сканировании";
        secretsContainer.innerHTML = `<div class="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs">Не удалось выполнить сканирование: ${err.message}</div>`;
        sastContainer.innerHTML = `<div class="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs">Не удалось выполнить сканирование: ${err.message}</div>`;
    } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = `<i class="fa-solid fa-play"></i> Запустить сканирование`;
    }
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

