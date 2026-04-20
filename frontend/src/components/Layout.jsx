/**
 * Layout — Enterprise MES shell with top header + sidebar.
 */
import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../hooks/useToast';
import { Dot } from './ui';

const menuGroups = [
  { label: 'Core', items: [
    {to: '/',          label: 'Dashboard',   icon: '📊'},
    {to: '/items',     label: 'Items',       icon: '📦'},
    {to: '/bom',       label: 'BOM',         icon: '🧬'},
    {to: '/process',   label: 'Process',     icon: '⚙️'},
    {to: '/equipment', label: 'Equipment',   icon: '🏭'},
  ]},
  { label: 'Production', items: [
    {to: '/plans',        label: 'Plans',       icon: '📋'},
    {to: '/work-orders',  label: 'Work Order',  icon: '📝'},
    {to: '/inventory',    label: 'Inventory',   icon: '📦'},
  ]},
  { label: 'Quality', items: [
    {to: '/quality',      label: 'Quality',      icon: '✅'},
    {to: '/spc',          label: 'SPC 관리도',   icon: '📈'},
    {to: '/capa',         label: 'CAPA',         icon: '🔄'},
    {to: '/ncr',          label: 'NCR',          icon: '⚠️'},
    {to: '/disposition',  label: '출하판정',     icon: '📝'},
    {to: '/kpi',          label: 'KPI',          icon: '🎯'},
  ]},
  { label: 'AI / Analytics', items: [
    {to: '/ai-center',    label: 'AI Center',    icon: '🤖'},
    {to: '/reports',      label: 'Reports',      icon: '📑'},
    {to: '/oee',          label: 'OEE',          icon: '📊'},
  ]},
  { label: 'Operations', items: [
    {to: '/cmms',         label: 'CMMS 보전',    icon: '🔩'},
    {to: '/recipe',       label: '레시피',       icon: '📖'},
    {to: '/sensor',       label: '센서',         icon: '📡'},
    {to: '/barcode',      label: '바코드/QR',    icon: '📱'},
    {to: '/ewi',          label: '전자작업지시', icon: '📝'},
    {to: '/lot-trace',    label: 'LOT 추적',     icon: '🔍'},
  ]},
  { label: 'Advanced', items: [
    {to: '/msa',          label: 'MSA/Gage R&R', icon: '📐'},
    {to: '/fmea',         label: 'FMEA',         icon: '📋'},
    {to: '/energy',       label: '에너지',       icon: '⚡'},
    {to: '/calibration',  label: '교정',         icon: '🔬'},
    {to: '/sqm',          label: '공급업체',     icon: '🤝'},
    {to: '/dispatch',     label: '디스패칭',     icon: '🚀'},
    {to: '/setup-matrix', label: '셋업시간',     icon: '⏱️'},
    {to: '/costing',      label: '원가추적',     icon: '💰'},
  ]},
  { label: 'Enterprise', items: [
    {to: '/dms',              label: '문서',         icon: '📄'},
    {to: '/labor',            label: '스킬',         icon: '👷'},
    {to: '/erp',              label: 'ERP',          icon: '🔄'},
    {to: '/opcua',            label: 'OPC-UA',       icon: '🔌'},
    {to: '/batch',            label: '배치',         icon: '🧪'},
    {to: '/ecm',              label: '설계변경',     icon: '📐'},
    {to: '/complex-routing',  label: '복합라우팅',   icon: '🔀'},
    {to: '/multisite',        label: '멀티사이트',   icon: '🌐'},
  ]},
  { label: 'System', items: [
    {to: '/notification',  label: '알림',           icon: '🔔'},
    {to: '/audit',         label: '감사추적',       icon: '📜'},
    {to: '/resource',      label: '리소스',         icon: '🗂️'},
    {to: '/dash-builder',  label: '대시보드빌더',   icon: '🎨'},
    {to: '/rpt-builder',   label: '리포트빌더',     icon: '📊'},
    {to: '/network',       label: 'Network',        icon: '🌐'},
    {to: '/infra',         label: 'Infra',          icon: '🖥️'},
  ]},
];

const navLinkClass = ({isActive}) =>
  `group relative flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] font-medium transition-all
   ${isActive
      ? 'bg-gradient-to-r from-blue-600/30 to-transparent text-white border-l-2 border-blue-400'
      : 'text-slate-400 hover:text-white hover:bg-slate-800/40 border-l-2 border-transparent'}`;

const breadcrumbFromPath = (pathname) => {
  if (pathname === '/' || pathname === '') return ['Dashboard'];
  const item = menuGroups.flatMap(g => g.items).find(m => m.to === pathname);
  return item ? [item.label] : [pathname.replace('/', '')];
};

const Layout = ({children}) => {
  const {user, logout} = useAuth();
  const loc = useLocation();
  const [sideOpen, setSideOpen] = useState(false);
  const crumbs = breadcrumbFromPath(loc.pathname);

  return (
    <div className="flex h-screen bg-[#0b1120] text-slate-300 overflow-hidden">
      {/* Mobile toggle */}
      <button onClick={() => setSideOpen(!sideOpen)}
        className="md:hidden fixed top-3 left-3 z-50 bg-slate-800 text-white w-10 h-10 rounded-lg text-lg">
        {sideOpen ? '✕' : '☰'}
      </button>
      {sideOpen && <div className="md:hidden fixed inset-0 bg-black/60 z-30" onClick={() => setSideOpen(false)} />}

      {/* Sidebar */}
      <aside className={`${sideOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0
        fixed md:static z-40 w-60 bg-[#0a1226] border-r border-slate-800/70
        flex flex-col h-screen transition-transform`}>
        {/* Logo */}
        <NavLink to="/" onClick={() => setSideOpen(false)}
          className="px-5 pt-5 pb-4 border-b border-slate-800/70 flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-black text-sm shadow-lg shadow-blue-500/30">
            DX
          </div>
          <div>
            <div className="text-white font-black text-[14px] tracking-tight leading-tight">DEXWEAVER</div>
            <div className="text-[9px] uppercase text-slate-500 tracking-[0.2em] leading-tight">MES · v6.0</div>
          </div>
        </NavLink>

        {/* Menu */}
        <nav className="flex-1 overflow-y-auto py-3 px-2.5 space-y-3
          [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:bg-slate-700">
          {menuGroups.map(g => (
            <div key={g.label}>
              <div className="px-2 py-1.5 text-[9px] font-bold uppercase tracking-[0.2em] text-slate-600">
                {g.label}
              </div>
              <div className="space-y-0.5">
                {g.items.map(m => (
                  <NavLink key={m.to} to={m.to} end={m.to === '/'} onClick={() => setSideOpen(false)} className={navLinkClass}>
                    <span className="text-[13px] w-4 inline-flex justify-center">{m.icon}</span>
                    <span className="truncate">{m.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* User */}
        <div className="px-4 py-3 border-t border-slate-800/70 flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold text-xs">
            {(user?.name || 'U').slice(0, 1)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-white text-[12px] font-bold truncate">{user?.name || 'User'}</div>
            <div className="text-slate-500 text-[10px] flex items-center gap-1">
              <Dot color="emerald"/> {user?.role || 'worker'}
            </div>
          </div>
          <button onClick={logout} className="text-slate-500 hover:text-rose-400 text-xs px-2 py-1 rounded cursor-pointer" title="Logout">
            ⏻
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header */}
        <header className="h-14 bg-[#0a1226]/80 backdrop-blur border-b border-slate-800/70 flex items-center justify-between px-6">
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-500">DEXWEAVER MES</span>
            <span className="text-slate-700">/</span>
            <span className="text-white font-semibold">{crumbs[0]}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-[10px] px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <Dot color="emerald"/> All systems operational
            </div>
            <button className="relative text-slate-400 hover:text-white text-lg">
              🔔
              <span className="absolute -top-1 -right-1 bg-rose-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">3</span>
            </button>
            <div className="text-xs text-slate-500 hidden md:block">
              {new Date().toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' })}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6 bg-gradient-to-br from-[#0b1120] via-[#0b1120] to-[#0a1226]">
          {children}
        </main>
      </div>

      <Toast />
    </div>
  );
};

export default Layout;
