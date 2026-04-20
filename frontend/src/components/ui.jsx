/**
 * Shared UI components — enterprise MES design system.
 */
import React from 'react';

/* ─────────── KPI cards with gradient + icon + trend ─────────── */
export const KpiCard = ({title, value, unit = '', icon, trend, color = 'blue'}) => {
  const grad = {
    blue:    'from-blue-500/20 to-blue-500/0   border-blue-500/30   text-blue-400',
    emerald: 'from-emerald-500/20 to-emerald-500/0 border-emerald-500/30 text-emerald-400',
    amber:   'from-amber-500/20 to-amber-500/0 border-amber-500/30 text-amber-400',
    rose:    'from-rose-500/20 to-rose-500/0   border-rose-500/30   text-rose-400',
    violet:  'from-violet-500/20 to-violet-500/0 border-violet-500/30 text-violet-400',
  }[color];
  return (
    <div className={`relative rounded-2xl border bg-gradient-to-br ${grad} p-5 overflow-hidden group hover:scale-[1.02] transition-transform`}>
      <div className="absolute -right-4 -top-4 text-6xl opacity-10">{icon}</div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">{title}</span>
        {trend != null && (
          <span className={`text-[10px] font-bold ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {trend >= 0 ? '▲' : '▼'} {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-black text-white tabular-nums">{value}</span>
        {unit && <span className="text-sm text-slate-400 font-semibold">{unit}</span>}
      </div>
    </div>
  );
};

export const Card = ({title, value, color = 'text-blue-400', className = ''}) => (
  <div className={`bg-slate-900/40 backdrop-blur p-5 rounded-2xl border border-slate-800 ${className}`}>
    <span className="text-slate-500 font-bold uppercase text-[10px] tracking-wider">{title}</span>
    <p className={`text-3xl font-black mt-1 ${color} tabular-nums`}>{value}</p>
  </div>
);

/* ─────────── Inline SVG charts ─────────── */
export const BarChart = ({data, height = 160, color = '#3b82f6'}) => {
  if (!data || data.length === 0) return <EmptyState message="No data" icon="📈" />;
  const max = Math.max(...data.map(d => d.value || 0), 1);
  const barW = 100 / data.length;
  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full" preserveAspectRatio="none" style={{height}}>
      <defs>
        <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.9"/>
          <stop offset="100%" stopColor={color} stopOpacity="0.3"/>
        </linearGradient>
      </defs>
      {data.map((d, i) => {
        const h = ((d.value || 0) / max) * (height - 24);
        return (
          <g key={i}>
            <rect x={i * barW + barW * 0.2} y={height - h - 16} width={barW * 0.6} height={h}
                  fill="url(#barGrad)" rx="1"/>
            <text x={i * barW + barW * 0.5} y={height - 2} textAnchor="middle"
                  fontSize="4" fill="#64748b">{d.label}</text>
          </g>
        );
      })}
    </svg>
  );
};

export const DonutChart = ({pct = 0, size = 140, stroke = 14, color = '#10b981', label}) => {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c - (pct / 100) * c;
  return (
    <div className="relative inline-flex items-center justify-center" style={{width: size, height: size}}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={stroke}/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={stroke}
                strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
                style={{transition: 'stroke-dashoffset .8s'}}/>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-white tabular-nums">{pct.toFixed(1)}%</span>
        {label && <span className="text-[10px] uppercase text-slate-500 mt-0.5 tracking-wider">{label}</span>}
      </div>
    </div>
  );
};

/* ─────────── Table ─────────── */
export const Table = ({cols, rows, renderRow}) => (
  <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden">
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead className="bg-slate-800/60 text-slate-400 uppercase text-[10px] tracking-wider">
          <tr>{cols.map(c => <th key={c} className="p-4 font-semibold">{c}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-800">{rows.map(renderRow)}</tbody>
      </table>
    </div>
  </div>
);

export const Badge = ({v}) => {
  const pal = {
    RUNNING: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    WORKING: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    DONE: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    PASS: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    NORMAL: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    DOWN: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    FAIL: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    OUT: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    LOW: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    WAIT: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
    STOP: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    HIGH: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    MID: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  };
  const c = pal[v] || 'bg-slate-500/15 text-slate-300 border-slate-500/30';
  return <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${c} inline-flex items-center gap-1`}>{v}</span>;
};

/* ─────────── Inputs / Buttons ─────────── */
export const Input = React.forwardRef((props, ref) => (
  <input ref={ref} {...props}
    className={`bg-slate-900 border border-slate-700 focus:border-blue-500 outline-none px-3 py-2 rounded-lg text-white text-sm transition-colors ${props.className||''}`} />
));

export const Btn = ({children, ...p}) => (
  <button {...p}
    className={`bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold text-xs transition-colors shadow-sm shadow-blue-500/30 ${p.className||''}`}>
    {children}
  </button>
);

export const BtnSuccess = ({children, ...p}) => (
  <button {...p}
    className={`bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-semibold text-xs cursor-pointer transition-colors shadow-sm shadow-emerald-500/30 ${p.className||''}`}>
    {children}
  </button>
);

export const BtnDanger = ({children, ...p}) => (
  <button {...p}
    className={`bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 rounded-lg font-semibold text-xs cursor-pointer transition-colors shadow-sm shadow-rose-500/30 ${p.className||''}`}>
    {children}
  </button>
);

/* ─────────── Filter bar ─────────── */
export const FilterBar = ({children}) => (
  <div className="flex items-center gap-3 mb-4 flex-wrap bg-slate-900/40 px-4 py-3 rounded-2xl border border-slate-800">
    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mr-1">Filter</span>
    {children}
  </div>
);

export const FilterSelect = ({label, value, onChange, options}) => (
  <div className="flex items-center gap-1.5">
    <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
    <select value={value} onChange={e => onChange(e.target.value)}
      className="bg-slate-900 border border-slate-700 px-2.5 py-1.5 rounded-lg text-white text-[11px] focus:border-blue-500 outline-none">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
);

export const FilterSearch = ({value, onChange, placeholder = 'Search...'}) => (
  <div className="relative ml-auto">
    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">🔎</span>
    <input placeholder={placeholder} value={value} onChange={e => onChange(e.target.value)}
      className="bg-slate-900 border border-slate-700 focus:border-blue-500 outline-none pl-8 pr-3 py-1.5 rounded-lg text-white text-[11px] w-56" />
  </div>
);

export const FilterCount = ({total, filtered}) => (
  <span className="text-[10px] text-slate-600">
    {filtered < total ? <>{filtered} / {total}</> : total} rows
  </span>
);

/* ─────────── Modal ─────────── */
export const Modal = ({open, onClose, title, children}) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-2xl"
        onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-white font-bold">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-2xl leading-none cursor-pointer">&times;</button>
        </div>
        {children}
      </div>
    </div>
  );
};

export const Select = ({value, onChange, options, className = '', ...rest}) => (
  <select value={value} onChange={e => onChange(e.target.value)} {...rest}
    className={`bg-slate-900 border border-slate-700 focus:border-blue-500 outline-none p-2 rounded-lg text-white text-sm ${className}`}>
    {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
);

export const FormRow = ({label, children}) => (
  <div className="mb-3">
    <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1 tracking-wider">{label}</label>
    {children}
  </div>
);

export const PageHeader = ({title, subtitle, actions}) => (
  <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
    <div>
      <h2 className="text-white font-black text-2xl tracking-tight">{title}</h2>
      {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
    </div>
    <div className="flex gap-2">{actions}</div>
  </div>
);

export const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
  </div>
);

export const EmptyState = ({message = 'No data available', icon = '📭', cta}) => (
  <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
    <div className="text-6xl mb-4 opacity-50">{icon}</div>
    <p className="text-slate-400 text-sm font-semibold mb-1">{message}</p>
    <p className="text-slate-600 text-xs mb-4">데이터가 쌓이면 자동으로 표시됩니다</p>
    {cta}
  </div>
);

/* ─────────── Section container ─────────── */
export const Section = ({title, subtitle, children, actions, className = ''}) => (
  <div className={`bg-slate-900/40 backdrop-blur border border-slate-800 rounded-2xl p-5 ${className}`}>
    {(title || actions) && (
      <div className="flex justify-between items-center mb-4">
        <div>
          {title && <h3 className="text-white font-bold text-sm">{title}</h3>}
          {subtitle && <p className="text-slate-500 text-[10px] mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex gap-2">{actions}</div>
      </div>
    )}
    {children}
  </div>
);

/* ─────────── Status dot ─────────── */
export const Dot = ({color = 'emerald'}) => {
  const c = {emerald: 'bg-emerald-400', rose: 'bg-rose-400', amber: 'bg-amber-400', slate: 'bg-slate-400', blue: 'bg-blue-400'}[color];
  return <span className={`inline-block w-2 h-2 rounded-full ${c} shadow-[0_0_8px] shadow-current`}/>;
};
