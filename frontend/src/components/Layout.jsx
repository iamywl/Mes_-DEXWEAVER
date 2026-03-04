/**
 * Layout — Sidebar navigation + main content area.
 */
import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../hooks/useToast';

const menuGroups = [
  {
    label: 'Core',
    items: [
      {to: '/', label: 'Dashboard', icon: '📊'},
      {to: '/items', label: 'Items', icon: '📦'},
      {to: '/bom', label: 'BOM', icon: '🔗'},
      {to: '/process', label: 'Process', icon: '⚙️'},
      {to: '/equipment', label: 'Equipment', icon: '🏭'},
    ],
  },
  {
    label: 'Production',
    items: [
      {to: '/plans', label: 'Plans', icon: '📋'},
      {to: '/work-orders', label: 'Work Order', icon: '🔧'},
      {to: '/inventory', label: 'Inventory', icon: '📦'},
    ],
  },
  {
    label: 'Quality',
    items: [
      {to: '/quality', label: 'Quality', icon: '✅'},
      {to: '/spc', label: 'SPC 관리도', icon: '📈'},
      {to: '/capa', label: 'CAPA', icon: '🔄'},
      {to: '/ncr', label: 'NCR', icon: '⚠️'},
      {to: '/disposition', label: '출하판정', icon: '📝'},
      {to: '/kpi', label: 'KPI', icon: '🎯'},
    ],
  },
  {
    label: 'AI / Analytics',
    items: [
      {to: '/ai-center', label: 'AI Center', icon: '🤖'},
      {to: '/reports', label: 'Reports', icon: '📑'},
      {to: '/oee', label: 'OEE', icon: '📊'},
    ],
  },
  {
    label: 'Operations',
    items: [
      {to: '/cmms', label: 'CMMS 보전', icon: '🔩'},
      {to: '/recipe', label: '레시피', icon: '📖'},
      {to: '/sensor', label: '센서', icon: '📡'},
      {to: '/barcode', label: '바코드/QR', icon: '📱'},
      {to: '/ewi', label: '전자작업지시서', icon: '📝'},
      {to: '/lot-trace', label: 'LOT 추적', icon: '🔍'},
    ],
  },
  {
    label: 'Advanced',
    items: [
      {to: '/msa', label: 'MSA/Gage R&R', icon: '📐'},
      {to: '/fmea', label: 'FMEA', icon: '📋'},
      {to: '/energy', label: '에너지', icon: '⚡'},
      {to: '/calibration', label: '교정', icon: '🔬'},
      {to: '/sqm', label: '공급업체', icon: '🤝'},
      {to: '/dispatch', label: '디스패칭', icon: '🚀'},
      {to: '/setup-matrix', label: '셋업시간', icon: '⏱️'},
      {to: '/costing', label: '원가추적', icon: '💰'},
    ],
  },
  {
    label: 'Enterprise',
    items: [
      {to: '/dms', label: '문서', icon: '📄'},
      {to: '/labor', label: '스킬', icon: '👷'},
      {to: '/erp', label: 'ERP', icon: '🔄'},
      {to: '/opcua', label: 'OPC-UA', icon: '🔌'},
      {to: '/batch', label: '배치', icon: '🧪'},
      {to: '/ecm', label: '설계변경', icon: '📐'},
      {to: '/complex-routing', label: '복합라우팅', icon: '🔀'},
      {to: '/multisite', label: '멀티사이트', icon: '🌐'},
    ],
  },
  {
    label: 'System',
    items: [
      {to: '/notification', label: '알림', icon: '🔔'},
      {to: '/audit', label: '감사추적', icon: '📜'},
      {to: '/resource', label: '리소스', icon: '🗂️'},
      {to: '/dash-builder', label: '대시보드빌더', icon: '🎨'},
      {to: '/rpt-builder', label: '리포트빌더', icon: '📊'},
      {to: '/network', label: 'Network', icon: '🌐'},
      {to: '/infra', label: 'Infra', icon: '🖥️'},
    ],
  },
];

const navLinkClass = ({isActive}) =>
  `flex items-center gap-2 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all ${
    isActive
      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
  }`;

const Layout = () => {
  const {user, logout} = useAuth();
  const [sideOpen, setSideOpen] = useState(false);
  const [collapsed, setCollapsed] = useState({});

  const toggle = (label) => setCollapsed(p => ({...p, [label]: !p[label]}));

  return (
    <div className="flex h-screen bg-[#020617] text-slate-300 text-xs overflow-hidden">
      {/* Mobile toggle */}
      <button onClick={() => setSideOpen(!sideOpen)}
        className="md:hidden fixed top-3 left-3 z-50 bg-slate-800 text-white px-2 py-1 rounded-lg text-sm cursor-pointer">
        {sideOpen ? '\u2715' : '\u2630'}
      </button>

      {/* Mobile overlay */}
      {sideOpen && <div className="md:hidden fixed inset-0 bg-black/50 z-30" onClick={() => setSideOpen(false)} />}

      {/* Sidebar */}
      <aside className={`${sideOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 fixed md:static z-40 w-52 bg-[#0f172a] border-r border-slate-800 p-3 overflow-y-auto flex flex-col h-screen transition-transform`}>
        {/* Logo */}
        <NavLink to="/" onClick={() => setSideOpen(false)} className="text-left mb-4 group block">
          <h1 className="text-blue-500 font-black text-sm tracking-tighter italic group-hover:text-blue-400">
            DEXWEAVER MES
          </h1>
          <span className="text-[9px] text-slate-600">v6.0</span>
        </NavLink>

        {/* Menu groups */}
        <nav className="flex-1 space-y-2">
          {menuGroups.map(g => (
            <div key={g.label}>
              <button onClick={() => toggle(g.label)}
                className="w-full text-left text-[9px] text-slate-600 uppercase font-bold tracking-wider px-2 py-1 hover:text-slate-400 cursor-pointer">
                {collapsed[g.label] ? '▸' : '▾'} {g.label}
              </button>
              {!collapsed[g.label] && (
                <div className="space-y-0.5 ml-1">
                  {g.items.map(m => (
                    <NavLink key={m.to} to={m.to} onClick={() => setSideOpen(false)} className={navLinkClass}>
                      <span className="text-[10px]">{m.icon}</span>
                      <span className="truncate">{m.label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* User info */}
        <div className="mt-auto pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between px-2">
            <div>
              <p className="text-white text-[11px] font-bold">{user?.name || 'User'}</p>
              <p className="text-slate-500 text-[9px]">{user?.role || 'worker'}</p>
            </div>
            <button onClick={logout}
              className="text-slate-500 hover:text-red-400 text-[10px] cursor-pointer">
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>

      {/* Global toast */}
      <Toast />
    </div>
  );
};

export default Layout;
