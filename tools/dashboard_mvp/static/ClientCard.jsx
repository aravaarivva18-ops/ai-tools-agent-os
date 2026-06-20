import React, { useState, useMemo } from 'react';
import {
  LineChart, Line, BarChart, Bar, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ResponsiveContainer
} from 'recharts';

/**
 * ClientCard — детальная карточка аналитики по проекту.
 * White Label / Минималистичная тема агентства Target Media.
 *
 * Props:
 * - project     { id, name, client_name }
 * - plan        { budget, leads, cpl }
 * - fact        { spent, leads, cpl, ctr, cpc }
 * - deviations  { budget_progress_pct, leads_progress_pct, cpl_deviation_pct, budget_pacing_pct }
 * - dailyStats  [{ date, spent, cumSpent, leads, cpl, source }]
 * - changelog   [{ date, description, reason, expected_effect }]
 * - sources     [{ id, name }]
 */
export default function ClientCard({
  project, plan, fact, deviations, dailyStats, changelog, sources
}) {
  const [granularity, setGranularity] = useState('day');   // day | week | month
  const [activeSource, setActiveSource] = useState('all');

  // ─── Фильтрация данных по источнику ─────────────────────────────────────
  const filteredStats = useMemo(() => {
    if (activeSource === 'all') return dailyStats;
    return dailyStats.filter(d => d.source === activeSource);
  }, [dailyStats, activeSource]);

  // ─── Агрегация по гранулярности ────────────────────────────────────────
  const aggregatedStats = useMemo(() => {
    if (granularity === 'day') return filteredStats;

    const buckets = {};
    filteredStats.forEach(d => {
      const date = new Date(d.date);
      let key;
      if (granularity === 'week') {
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay() + 1);
        key = weekStart.toISOString().slice(0, 10);
      } else {
        key = d.date.slice(0, 7);
      }
      if (!buckets[key]) buckets[key] = { date: key, spent: 0, leads: 0, cplSum: 0, count: 0 };
      buckets[key].spent  += d.spent;
      buckets[key].leads  += d.leads;
      buckets[key].cplSum += d.cpl;
      buckets[key].count  += 1;
    });

    return Object.values(buckets).map(b => ({
      ...b,
      cpl: b.leads > 0 ? +(b.spent / b.leads).toFixed(2) : 0,
    }));
  }, [filteredStats, granularity]);

  // ─── Вспомогательные функции ────────────────────────────────────────────
  const fmt = (n) => n?.toLocaleString('ru-RU') ?? '—';
  const pct = (n) => (n != null ? `${n > 0 ? '+' : ''}${n.toFixed(1)}%` : '—');
  const deviation = deviations || {};

  const scoreCardClass = (val, reverse = false) => {
    if (val == null) return 'text-slate-400';
    const bad = reverse ? val > 0 : val < 0;
    return bad ? 'text-rose-400' : 'text-emerald-400';
  };

  const dailyLeadTarget = plan?.leads ? +(plan.leads / 30).toFixed(1) : 0;

  // ─── Темы и стили графиков ──────────────────────────────────────────────
  const chartStyle = {
    backgroundColor: 'transparent',
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: 11,
  };
  const axisStyle = { fill: '#64748b', fontSize: 11 };
  const gridStyle = { stroke: '#1e293b', strokeDasharray: '3 3' };
  const tooltipStyle = {
    backgroundColor: '#0f172a',
    border: '1px solid #1e293b',
    borderRadius: '8px',
    color: '#cbd5e1',
    fontSize: '12px',
  };

  // ─── РЕНДЕР ─────────────────────────────────────────────────────────────
  return (
    <div className="w-full space-y-6 font-sans text-slate-200">

      {/* ── 1. ШАПКА КАРТОЧКИ ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">{project?.name}</h2>
          <p className="text-sm text-slate-400">{project?.client_name}</p>
        </div>
        {/* Контролы гранулярности */}
        <div className="flex items-center gap-2">
          {['day', 'week', 'month'].map(g => (
            <button
              key={g}
              onClick={() => setGranularity(g)}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
                granularity === g
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
              }`}
            >
              {g === 'day' ? 'День' : g === 'week' ? 'Неделя' : 'Месяц'}
            </button>
          ))}
          <div className="w-px h-6 bg-slate-700 mx-1" />
          {/* Селектор источника */}
          <select
            value={activeSource}
            onChange={e => setActiveSource(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="all">Все источники</option>
            {sources?.map(s => (
              <option key={s.id} value={s.name}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* ── 2. KPI-СКОРКАРТЫ (ПЛАН vs ФАКТ) ─────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: 'Бюджет (Расход)',
            plan: `${fmt(plan?.budget)} ₽`,
            fact: `${fmt(fact?.spent)} ₽`,
            devLabel: 'от плана',
            dev: deviation.budget_progress_pct,
            reverse: false,
          },
          {
            label: 'Лиды',
            plan: `${plan?.leads ?? '—'} шт.`,
            fact: `${fact?.leads ?? '—'} шт.`,
            devLabel: 'от плана',
            dev: deviation.leads_progress_pct,
            reverse: false,
          },
          {
            label: 'CPL',
            plan: `${fmt(plan?.cpl)} ₽`,
            fact: `${fmt(fact?.cpl)} ₽`,
            devLabel: 'отклонение',
            dev: deviation.cpl_deviation_pct,
            reverse: true,  // Для CPL рост — плохо
          },
          {
            label: 'Pacing (Темп)',
            plan: '100%',
            fact: `${deviation.budget_pacing_pct?.toFixed(1) ?? '—'}%`,
            devLabel: 'от нормы',
            dev: deviation.budget_pacing_pct != null ? deviation.budget_pacing_pct - 100 : null,
            reverse: true,
          },
        ].map(card => (
          <div key={card.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="text-xs uppercase font-bold tracking-wider text-slate-500">{card.label}</div>
            <div className="text-xl font-bold text-white">{card.fact}</div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">План: {card.plan}</span>
              <span className={`text-xs font-semibold ${scoreCardClass(card.dev, card.reverse)}`}>
                {pct(card.dev)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* ── 3. ГРАФИКИ ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Chart 1: Расход (Bar) + Накопительный лимит бюджета (Line) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs uppercase font-bold tracking-wider text-slate-500 mb-4">
            Расход vs Бюджетный лимит
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={aggregatedStats} style={chartStyle}>
              <CartesianGrid {...gridStyle} />
              <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false}
                tickFormatter={v => v.slice(5)} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false}
                tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v, n) => [`${v?.toLocaleString('ru-RU')} ₽`, n]} />
              <Bar dataKey="spent" name="Расход (день)" fill="#0ea5e9" opacity={0.8} radius={[3,3,0,0]} />
              <Line dataKey="cumSpent" name="Накопительный расход" stroke="#6366f1"
                strokeWidth={2} dot={false} type="monotone" />
              {plan?.budget && (
                <ReferenceLine y={plan.budget} stroke="#f43f5e" strokeDasharray="4 4"
                  label={{ value: 'Лимит', fill: '#f43f5e', fontSize: 10 }} />
              )}
              <Legend wrapperStyle={{ fontSize: '11px', color: '#64748b' }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 2: Лиды (Bar) + Базовая цель (Line) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs uppercase font-bold tracking-wider text-slate-500 mb-4">
            Лиды vs Дневной целевой показатель
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={aggregatedStats} style={chartStyle}>
              <CartesianGrid {...gridStyle} />
              <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false}
                tickFormatter={v => v.slice(5)} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v, n) => [n === 'Цель' ? `${v} шт.` : `${v} шт.`, n]} />
              <Bar dataKey="leads" name="Лиды (факт)" fill="#22c55e" opacity={0.85} radius={[3,3,0,0]} />
              {dailyLeadTarget > 0 && (
                <ReferenceLine y={dailyLeadTarget} stroke="#f59e0b" strokeDasharray="4 4"
                  label={{ value: 'Цель/день', fill: '#f59e0b', fontSize: 10 }} />
              )}
              <Legend wrapperStyle={{ fontSize: '11px', color: '#64748b' }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 3: Тренд CPL */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs uppercase font-bold tracking-wider text-slate-500 mb-4">
            Динамика CPL
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={aggregatedStats} style={chartStyle}>
              <CartesianGrid {...gridStyle} />
              <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false}
                tickFormatter={v => v.slice(5)} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false}
                tickFormatter={v => `${v} ₽`} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={v => [`${v?.toLocaleString('ru-RU')} ₽`, 'CPL']} />
              <Line dataKey="cpl" name="Факт CPL" stroke="#e879f9"
                strokeWidth={2.5} dot={false} type="monotone" />
              {plan?.cpl && (
                <ReferenceLine y={plan.cpl} stroke="#f43f5e" strokeDasharray="4 4"
                  label={{ value: 'Цель', fill: '#f43f5e', fontSize: 10 }} />
              )}
              <Legend wrapperStyle={{ fontSize: '11px', color: '#64748b' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── 4. ОПЕРАЦИОННЫЙ ЛОГ ИЗМЕНЕНИЙ (READ-ONLY) ───────────────── */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="text-xs uppercase font-bold tracking-wider text-slate-500 mb-4">
          Лог операционных изменений
        </div>
        {changelog?.length > 0 ? (
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                <th className="py-2 px-3 w-28">Дата</th>
                <th className="py-2 px-3">Описание изменения</th>
                <th className="py-2 px-3">Причина</th>
                <th className="py-2 px-3">Ожидаемый эффект</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {changelog.map((log, i) => (
                <tr key={i} className="text-slate-300 text-xs">
                  <td className="py-3 px-3 text-slate-500 font-mono whitespace-nowrap">{log.date}</td>
                  <td className="py-3 px-3">{log.description}</td>
                  <td className="py-3 px-3 text-slate-400">{log.reason ?? '—'}</td>
                  <td className="py-3 px-3 text-slate-400">{log.expected_effect ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-slate-500 text-sm py-4 text-center">
            Записи об изменениях для данного проекта отсутствуют.
          </p>
        )}
      </div>
    </div>
  );
}
