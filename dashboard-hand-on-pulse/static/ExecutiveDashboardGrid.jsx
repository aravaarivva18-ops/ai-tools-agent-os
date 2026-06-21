import React, { useState, useMemo } from 'react';

/**
 * ExecutiveDashboardGrid - Модульный UI-компонент таблицы контроля KPI.
 * Разработан по правилам White Label для руководства агентства Target Media.
 */
export default function ExecutiveDashboardGrid({ projectsData, onFilterChange }) {
  // Локальные состояния фильтров
  const [selectedClient, setSelectedClient] = useState('All');
  const [startDate, setStartDate] = useState('2026-06-01');
  const [endDate, setEndDate] = useState('2026-06-30');

  // Уникальный список клиентов для селектора
  const clientsList = useMemo(() => {
    const clients = new Set(projectsData.map(p => p.client_name));
    return ['All', ...Array.from(clients)];
  }, [projectsData]);

  // Фильтрация данных на клиенте
  const filteredProjects = useMemo(() => {
    return projectsData.filter(project => {
      const matchClient = selectedClient === 'All' || project.client_name === selectedClient;
      return matchClient;
    });
  }, [projectsData, selectedClient]);

  // Вспомогательные функции для расчета условий предупреждений (светофор/soft-red)
  const isCplOverrun = (factCpl, planCpl) => {
    return planCpl > 0 && factCpl > planCpl;
  };

  const isLeadsDeficit = (factLeads, planLeads) => {
    return planLeads > 0 && factLeads < planLeads * 0.9; // Предупреждение при выполнении менее 90%
  };

  const isOverpacing = (pacingPct) => {
    return pacingPct > 105.0; // Предупреждение при перерасходе бюджета (темп выше 105%)
  };

  return (
    <div className="w-full bg-slate-950 text-slate-100 p-6 rounded-2xl border border-slate-800 font-sans shadow-xl">
      {/* 1. ПАНЕЛЬ ФИЛЬТРОВ И КОНТРОЛЕЙ (White Label / Минимализм) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-white">Контроль эффективности проектов</h2>
          <p className="text-xs text-slate-400 mt-1">Target Media / Панель мониторинга руководителей</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Селектор клиентов */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Клиент</label>
            <select
              value={selectedClient}
              onChange={(e) => {
                setSelectedClient(e.target.value);
                onFilterChange?.({ client: e.target.value, startDate, endDate });
              }}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-sky-500 transition-colors"
            >
              {clientsList.map(client => (
                <option key={client} value={client}>{client}</option>
              ))}
            </select>
          </div>

          {/* Фильтр по датам */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Начало</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                onFilterChange?.({ client: selectedClient, startDate: e.target.value, endDate });
              }}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Конец</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                onFilterChange?.({ client: selectedClient, startDate, endDate: e.target.value });
              }}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* 2. ИНТЕРАКТИВНАЯ ТАБЛИЦА (EXECUTIVE GRID VIEW) */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <th className="py-4 px-3">Название проекта</th>
              <th className="py-4 px-3 text-right">Расход (Факт)</th>
              <th className="py-4 px-3 text-right">Отклонение бюджета</th>
              <th className="py-4 px-3 text-right">Лиды (Факт)</th>
              <th className="py-4 px-3 text-right">Отклонение лидов</th>
              <th className="py-4 px-3 text-right">Текущий CPL</th>
              <th className="py-4 px-3 text-right">Отклонение CPL</th>
              <th className="py-4 px-3 text-right">Pacing (Темп трат)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850 text-sm text-slate-200">
            {filteredProjects.map((project) => {
              const plan = project.plan || {};
              const fact = project.fact || {};
              const dev = project.deviations || {};

              const isCplAlert = isCplOverrun(fact.cpl, plan.cpl);
              const isLeadsAlert = isLeadsDeficit(fact.leads, plan.leads);
              const isPacingAlert = isOverpacing(dev.budget_pacing_pct);

              return (
                <tr key={project.id} className="hover:bg-slate-900/40 transition-colors duration-150">
                  {/* Имя клиента / Проект */}
                  <td className="py-4 px-3 font-medium text-white">
                    <div>{project.project_name}</div>
                    <div className="text-xs text-slate-400 font-normal">{project.client_name}</div>
                  </td>
                  
                  {/* Расход (Факт) */}
                  <td className="py-4 px-3 text-right tabular-nums">
                    {fact.spent?.toLocaleString('ru-RU')} ₽
                  </td>
                  
                  {/* Отклонение бюджета % */}
                  <td className="py-4 px-3 text-right tabular-nums">
                    <span className={dev.budget_progress_pct > 100 ? 'text-amber-400' : 'text-slate-400'}>
                      {dev.budget_progress_pct?.toFixed(1)}%
                    </span>
                  </td>
                  
                  {/* Лиды (Факт) */}
                  <td className={`py-4 px-3 text-right tabular-nums ${isLeadsAlert ? 'bg-red-500/10 text-red-400 font-semibold rounded-lg' : ''}`}>
                    {fact.leads} / <span className="text-slate-500 text-xs">{plan.leads}</span>
                  </td>
                  
                  {/* Отклонение лидов % */}
                  <td className="py-4 px-3 text-right tabular-nums">
                    <span className={dev.leads_progress_pct >= 100 ? 'text-emerald-400' : 'text-rose-400'}>
                      {dev.leads_progress_pct?.toFixed(1)}%
                    </span>
                  </td>
                  
                  {/* Текущий CPL */}
                  <td className={`py-4 px-3 text-right tabular-nums ${isCplAlert ? 'bg-red-500/10 text-red-400 font-semibold rounded-lg' : ''}`}>
                    {fact.cpl?.toLocaleString('ru-RU')} ₽
                  </td>
                  
                  {/* Отклонение CPL % */}
                  <td className="py-4 px-3 text-right tabular-nums">
                    <span className={dev.cpl_deviation_pct <= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                      {dev.cpl_deviation_pct > 0 ? '+' : ''}{dev.cpl_deviation_pct?.toFixed(1)}%
                    </span>
                  </td>
                  
                  {/* Pacing (Темп расхода) */}
                  <td className={`py-4 px-3 text-right tabular-nums ${isPacingAlert ? 'bg-red-500/10 text-red-400 font-semibold rounded-lg' : ''}`}>
                    {dev.budget_pacing_pct?.toFixed(1)}%
                  </td>
                </tr>
              );
            })}
            
            {filteredProjects.length === 0 && (
              <tr>
                <td colSpan="8" className="py-8 text-center text-slate-500">
                  Нет активных проектов, соответствующих выбранным критериям.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
