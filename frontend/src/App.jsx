import React, { useState, useEffect } from 'react';
import axios from 'axios';

axios.defaults.baseURL = import.meta.env.VITE_API_URL || '';

const App = () => {
  const [menu, setMenu] = useState('DASHBOARD');
  const [db, setDb] = useState({ items: [], bom: [], plans: [], flows: [], pods: [], logs: '', infra: {} });
  const [newPlan, setNewPlan] = useState({ item_code: '', plan_qty: 0, plan_date: '' });
  const [selPod, setSelPod] = useState('');
  const [showPodOnly, setShowPodOnly] = useState(true);
  const [topology, setTopology] = useState({ nodes: [], edges: [] });
  const [topologyView, setTopologyView] = useState('list'); // 'list' or 'graph'

  const fetchData = async () => {
    try {
      const [m, f, n, p] = await Promise.all([
        axios.get('/api/mes/data'), axios.get('/api/network/flows'),
        axios.get('/api/infra/status'), axios.get('/api/k8s/pods')
      ]);

      // Normalize flows data: backend may return either { flows: [...] } or an array
      let flowsData = [];
      if (f && f.data) {
        if (Array.isArray(f.data)) {
          flowsData = f.data;
        } else if (Array.isArray(f.data.flows)) {
          flowsData = f.data.flows;
        }
      }

      setDb(prev => ({ ...prev, ...m.data, flows: flowsData, infra: n.data, pods: p.data }));

      // fetch topology for graph view (non-blocking)
      axios.get('/api/network/topology').then(res => {
        if (res && res.data && res.data.status === 'success') {
          setTopology({ nodes: res.data.nodes || [], edges: res.data.edges || [] });
        }
      }).catch(() => {});

      if (selPod) {
        const l = await axios.get(`/api/k8s/logs/${selPod}`);
        setDb(prev => ({ ...prev, logs: l.data }));
      }
    } catch (e) {
      console.error('Sync Error', e);
    }
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 4000); return () => clearInterval(t); }, [selPod]);

  const addPlan = async (e) => {
    e.preventDefault();
    await axios.post('/api/mes/plans', newPlan);
    alert("생산계획 등록 성공!");
    fetchData();
  };

  return (
    <div className="flex min-h-screen bg-[#020617] text-slate-400 font-sans text-[11px]">
      <aside className="w-60 bg-[#0f172a] border-r border-slate-800 p-6 space-y-1">
        <h1 className="text-xl font-black text-blue-500 mb-10 tracking-tighter italic">KNU MES v5.0</h1>
        {['DASHBOARD', 'MASTER_INFO', 'BOM_STRUCTURE', 'PRODUCTION_PLAN', 'NETWORK_FLOW', 'INFRA_MONITOR', 'K8S_MANAGER'].map(m => (
          <button key={m} onClick={() => setMenu(m)} className={`w-full text-left px-4 py-2 rounded-lg transition-all ${menu === m ? 'bg-blue-600 text-white font-bold' : 'hover:bg-slate-800'}`}>
            {m.replace('_', ' ')}
          </button>
        ))}
      </aside>

      <main className="flex-1 p-10 overflow-y-auto">
        <h2 className="text-2xl font-bold text-white mb-8 border-b border-slate-800 pb-4">{menu}</h2>
        
        {menu === 'DASHBOARD' && (
          <div className="grid grid-cols-3 gap-6">
            <div className="bg-[#1e293b]/30 p-8 rounded-3xl border border-slate-800 text-center"><span className="text-slate-500 font-bold uppercase">Items</span><p className="text-5xl font-black text-blue-500 mt-2">{db.items.length}</p></div>
            <div className="bg-[#1e293b]/30 p-8 rounded-3xl border border-slate-800 text-center"><span className="text-slate-500 font-bold uppercase">CPU LOAD</span><p className="text-5xl font-black text-slate-200 mt-2">{db.infra.cpu || '0%'}</p></div>
            <div className="bg-[#1e293b]/30 p-8 rounded-3xl border border-slate-800 text-center"><span className="text-slate-500 font-bold uppercase">Live Pods</span><p className="text-5xl font-black text-emerald-500 mt-2">{db.pods.length}</p></div>
          </div>
        )}

        {menu === 'MASTER_INFO' && (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-left"><thead className="bg-[#1e293b] text-slate-500 uppercase"><tr><th className="p-4">Code</th><th className="p-4">Name</th><th className="p-4">Unit</th></tr></thead>
              <tbody className="divide-y divide-slate-800">{db.items.map((i, k) => <tr key={k}><td className="p-4 font-mono text-blue-400">{i.item_code}</td><td className="p-4 text-white font-bold">{i.name}</td><td className="p-4">{i.unit}</td></tr>)}</tbody>
            </table>
          </div>
        )}

        {menu === 'BOM_STRUCTURE' && (
          <div className="grid gap-4">{db.bom.map((b, k) => (<div key={k} className="bg-[#1e293b]/20 p-4 rounded-2xl border border-slate-800 flex justify-between items-center"><span className="text-blue-400 font-bold">{b.parent_item}</span><span className="text-slate-700">── {b.qty_per_unit} EA ──▶</span><span className="text-purple-400 font-bold">{b.child_item}</span></div>))}</div>
        )}

        {menu === 'PRODUCTION_PLAN' && (
          <div className="space-y-8">
            <form onSubmit={addPlan} className="bg-[#1e293b]/30 p-6 rounded-3xl border border-slate-800 flex gap-4 items-end">
              <select className="flex-1 bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white" onChange={e => setNewPlan({...newPlan, item_code: e.target.value})}><option>Select Item</option>{db.items.map(i => <option key={i.item_code} value={i.item_code}>{i.name}</option>)}</select>
              <input type="number" placeholder="QTY" className="w-24 bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white" onChange={e => setNewPlan({...newPlan, plan_qty: e.target.value})} />
              <input type="date" className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white" onChange={e => setNewPlan({...newPlan, plan_date: e.target.value})} />
              <button className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold">ADD PLAN</button>
            </form>
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-hidden"><table className="w-full text-left">
                <thead className="bg-[#1e293b] text-slate-500 uppercase"><tr><th className="p-4">Date</th><th className="p-4">Item</th><th className="p-4">Qty</th><th className="p-4">Status</th></tr></thead>
                <tbody className="divide-y divide-slate-800">{db.plans.map((p, k) => <tr key={k}><td className="p-4">{p.plan_date}</td><td className="p-4 text-white">{p.item_name}</td><td className="p-4 text-blue-400">{p.plan_qty}</td><td className="p-4 text-emerald-500 font-bold">{p.status}</td></tr>)}</tbody>
            </table></div>
          </div>
        )}

        {menu === 'NETWORK_FLOW' && (
          <div className="space-y-4">
            <div className="flex items-center gap-4 mb-4">
              <label className="text-sm text-slate-400 flex items-center gap-2">
                <input type="checkbox" checked={showPodOnly} onChange={() => setShowPodOnly(v => !v)} />
                <span>Pod-to-Pod flows only</span>
              </label>
              <div className="ml-auto">
                <label className="text-sm text-slate-400 mr-3">Visualization</label>
                <select value={topologyView} onChange={e => setTopologyView(e.target.value)} className="bg-[#0f172a] border border-slate-700 px-3 py-1 rounded-lg text-white hover:border-slate-600 focus:outline-none focus:border-blue-500">
                  <option value="graph">🌐 Topology Graph</option>
                  <option value="list">📋 Flow List</option>
                </select>
              </div>
            </div>

            {(() => {
              const flows = db.flows || [];
              const podNames = new Set((db.pods || []).map(p => p.name));
              const filtered = flows.filter(f => {
                const src = f.source?.pod_name;
                const dst = f.destination?.pod_name;
                if (showPodOnly) return src && dst && podNames.has(src) && podNames.has(dst);
                return true;
              });
              const nodes = topology.nodes || [];
              const edges = topology.edges || [];

              if (topologyView === 'graph') {
                // Topology graph view
                if (nodes.length === 0) {
                  return (
                    <div className="p-8 bg-[#1e293b]/20 rounded-2xl border border-slate-800 text-center min-h-96 flex flex-col items-center justify-center">
                      <div className="text-4xl mb-4">🔄</div>
                      <h3 className="text-slate-300 font-bold text-lg mb-2">Network Topology</h3>
                      <p className="text-slate-500 max-w-md">Topology data will appear when Cilium/Hubble collects network flows. This shows pod-to-pod communication patterns as a graph.</p>
                      <p className="text-slate-600 text-sm mt-4 italic">Waiting for flow events...</p>
                    </div>
                  );
                }
                const w = 900; const h = 400; const cx = w/2; const cy = h/2; const r = Math.min(w,h)/2 - 60;
                const angle = (i, total) => (i/total) * Math.PI * 2 - Math.PI/2;
                return (
                  <div className="p-6 bg-[#1e293b]/30 rounded-2xl border border-slate-800 overflow-auto">
                    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ minHeight: '400px' }}>
                      <defs>
                        <marker id="arrowblue" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
                          <path d="M0,0 L8,3 L0,6 z" fill="#60a5fa"/>
                        </marker>
                        <filter id="glow"><feGaussianBlur stdDeviation="3" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                      </defs>
                      {edges.map((e, i) => {
                        const si = nodes.findIndex(n => n.id === e.source);
                        const ti = nodes.findIndex(n => n.id === e.target);
                        if (si === -1 || ti === -1) return null;
                        const sa = angle(si, nodes.length); 
                        const ta = angle(ti, nodes.length);
                        const sx = cx + r * Math.cos(sa); 
                        const sy = cy + r * Math.sin(sa);
                        const tx = cx + r * Math.cos(ta); 
                        const ty = cy + r * Math.sin(ta);
                        const strokeW = Math.min(3, 1 + Math.log1p(e.count));
                        return (
                          <g key={`edge-${i}`} opacity="0.85">
                            <line x1={sx} y1={sy} x2={tx} y2={ty} stroke="#0ea5e9" strokeWidth={strokeW} markerEnd="url(#arrowblue)" strokeLinecap="round"/>
                            <text x={(sx+tx)/2} y={(sy+ty)/2-5} fontSize="10" fill="#60a5fa" textAnchor="middle" opacity="0.7">{e.count}</text>
                          </g>
                        );
                      })}
                      {nodes.map((n, i) => {
                        const a = angle(i, nodes.length);
                        const x = cx + r * Math.cos(a); 
                        const y = cy + r * Math.sin(a);
                        const label = n.label.length > 12 ? n.label.slice(0,10)+'..' : n.label;
                        return (
                          <g key={`node-${n.id}`} filter="url(#glow)">
                            <circle cx={x} cy={y} r={22} fill="#06b6d4" opacity="0.9"/>
                            <circle cx={x} cy={y} r={22} fill="none" stroke="#0891b2" strokeWidth="2" opacity="0.4"/>
                            <text x={x} y={y+5} fontSize="9" fontWeight="700" fill="#020617" textAnchor="middle" pointerEvents="none">{label}</text>
                          </g>
                        );
                      })}
                      <text x="10" y="25" fontSize="12" fill="#94a3b8" opacity="0.7">Pod-to-Pod Traffic ({nodes.length} pods, {edges.length} connections)</text>
                    </svg>
                  </div>
                );
              }

              // List view
              if (filtered.length === 0) {
                return (
                  <div className="p-8 bg-[#1e293b]/20 rounded-2xl border border-slate-800 text-center">
                    <p className="text-slate-500">No network flows detected.</p>
                    <p className="text-slate-600 text-sm mt-2">Enable Cilium traffic monitoring to see flow data here.</p>
                  </div>
                );
              }

              return filtered.map((f, k) => {
                const src = f.source?.pod_name || f.source?.labels || 'external';
                const dst = f.destination?.pod_name || f.destination?.labels || 'external';
                const proto = f.IP?.protocol || f.l4?.protocol || 'TCP';
                const verdict = f.verdict || f.summary || '✓';
                const ts = f.time || f.timestamp || '';
                return (
                  <div key={k} className="flex items-center justify-between p-4 bg-[#1e293b]/30 hover:bg-[#1e293b]/50 rounded-xl border border-slate-700 hover:border-slate-600 transition-colors font-mono text-xs">
                    <div className="flex-1 text-blue-400 truncate font-semibold">{src}</div>
                    <div className="text-slate-600 px-3 flex-shrink-0">{proto}</div>
                    <div className="text-slate-400 px-1">{'->'}</div>
                    <div className="flex-1 text-purple-400 truncate font-semibold text-right">{dst}</div>
                    <div className="ml-4 text-emerald-500 font-bold flex-shrink-0">{verdict}</div>
                    <div className="ml-4 text-slate-500 flex-shrink-0">{ts}</div>
                  </div>
                );
              });
            })()}
          </div>
        )}

        {menu === 'INFRA_MONITOR' && (
          <div className="bg-[#1e293b]/20 p-8 rounded-3xl border border-slate-800 space-y-8">
            <div className="flex justify-between items-center text-white"><span>API Engine Status</span><span className="text-emerald-500 font-black animate-pulse">● ONLINE</span></div>
            <div><div className="flex justify-between text-xs mb-2"><span>CPU USAGE</span><span>{db.infra.cpu}</span></div><div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-blue-500" style={{width: db.infra.cpu}}></div></div></div>
            <div><div className="flex justify-between text-xs mb-2"><span>MEM ALLOCATION</span><span>{db.infra.mem}</span></div><div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-purple-500" style={{width: db.infra.mem}}></div></div></div>
          </div>
        )}

        {menu === 'K8S_MANAGER' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[500px]">
            <div className="bg-[#1e293b]/20 p-6 rounded-2xl border border-slate-800 overflow-auto space-y-2">
              <h3 className="text-white font-bold mb-4 italic">📦 Pod Status</h3>
              {db.pods.map(p => (<div key={p.name} onClick={() => setSelPod(p.name)} className={`p-3 rounded-xl border cursor-pointer ${selPod === p.name ? 'border-blue-500 bg-blue-500/10' : 'border-slate-800'}`}><div className="flex justify-between"><span>{p.name}</span><span className="text-emerald-400">{p.status}</span></div></div>))}
            </div>
            <div className="bg-black/80 p-6 rounded-2xl border border-slate-800 flex flex-col">
              <h3 className="text-blue-400 font-bold mb-4 font-mono"># {selPod} console output:</h3>
              <pre className="text-emerald-500 font-mono text-[9px] flex-1 overflow-auto whitespace-pre-wrap leading-tight">{db.logs}</pre>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
export default App;
