/**
 * Shared UI components — extracted from App.jsx for reuse across pages.
 */
import React from 'react';

export const Card = ({title, value, color = 'text-blue-500', className = ''}) => (
  <div className={`bg-[#1e293b]/30 p-6 rounded-2xl border border-slate-800 text-center ${className}`}>
    <span className="text-slate-500 font-bold uppercase text-[10px]">{title}</span>
    <p className={`text-4xl font-black mt-1 ${color}`}>{value}</p>
  </div>
);

export const Table = ({cols, rows, renderRow}) => (
  <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
    <table className="w-full text-left">
      <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
        <tr>{cols.map(c => <th key={c} className="p-3">{c}</th>)}</tr>
      </thead>
      <tbody className="divide-y divide-slate-800">{rows.map(renderRow)}</tbody>
    </table>
  </div>
);

export const Badge = ({v}) => {
  const c = v==='RUNNING'||v==='DONE'||v==='PASS'||v==='NORMAL' ? 'bg-emerald-500/20 text-emerald-400'
    : v==='DOWN'||v==='FAIL'||v==='OUT'||v==='LOW' ? 'bg-red-500/20 text-red-400'
    : 'bg-amber-500/20 text-amber-400';
  return <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${c}`}>{v}</span>;
};

export const Input = React.forwardRef((props, ref) => (
  <input ref={ref} {...props}
    className={`bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs ${props.className||''}`} />
));

export const Btn = ({children, ...p}) => (
  <button {...p}
    className={`bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-xs ${p.className||''}`}>
    {children}
  </button>
);

export const BtnSuccess = ({children, ...p}) => (
  <button {...p}
    className={`bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-bold text-xs cursor-pointer ${p.className||''}`}>
    {children}
  </button>
);

export const BtnDanger = ({children, ...p}) => (
  <button {...p}
    className={`bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-bold text-xs cursor-pointer ${p.className||''}`}>
    {children}
  </button>
);

export const FilterBar = ({children}) => (
  <div className="flex items-center gap-3 mb-3 flex-wrap bg-[#0f172a]/60 px-3 py-2 rounded-xl border border-slate-800/50">
    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mr-1">Filter</span>
    {children}
  </div>
);

export const FilterSelect = ({label, value, onChange, options}) => (
  <div className="flex items-center gap-1.5">
    <span className="text-[10px] text-slate-500">{label}</span>
    <select value={value} onChange={e => onChange(e.target.value)}
      className="bg-[#0f172a] border border-slate-700 px-2 py-1 rounded text-white text-[11px]">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
);

export const FilterSearch = ({value, onChange, placeholder = 'Search...'}) => (
  <input placeholder={placeholder} value={value} onChange={e => onChange(e.target.value)}
    className="bg-[#0f172a] border border-slate-700 px-3 py-1 rounded text-white text-[11px] w-48 ml-auto" />
);

export const FilterCount = ({total, filtered}) => (
  <span className="text-[10px] text-slate-600 ml-2">
    {filtered < total ? <>{filtered} / {total}</> : total} rows
  </span>
);

export const Modal = ({open, onClose, title, children}) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[#1e293b] rounded-2xl border border-slate-700 p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-white font-bold text-sm">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-lg cursor-pointer">&times;</button>
        </div>
        {children}
      </div>
    </div>
  );
};

export const Select = ({value, onChange, options, className = '', ...rest}) => (
  <select value={value} onChange={e => onChange(e.target.value)} {...rest}
    className={`bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs ${className}`}>
    {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
);

export const FormRow = ({label, children}) => (
  <div className="mb-3">
    <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1">{label}</label>
    {children}
  </div>
);

export const PageHeader = ({title, actions}) => (
  <div className="flex justify-between items-center mb-4">
    <h2 className="text-white font-black text-lg">{title}</h2>
    <div className="flex gap-2">{actions}</div>
  </div>
);

export const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
  </div>
);

export const EmptyState = ({message = 'No data available'}) => (
  <div className="text-center py-12 text-slate-500 text-xs">{message}</div>
);
