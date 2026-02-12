import React, { useState, useEffect } from 'react';
import axios from 'axios';

axios.defaults.baseURL = `http://192.168.64.5:30461`;

const App = () => {
  const [menu, setMenu] = useState('DASHBOARD');
  const [db, setDb] = useState({ items: [], bom: [], plans: [], flows: [], pods: [], logs: '', infra: {} });
  const [newPlan, setNewPlan] = useState({ item_code: '', plan_qty: 0, plan_date: '' });
  const [selPod, setSelPod] = useState('');
  const [showPodOnly, setShowPodOnly] = useState(true);

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
            <div className="flex items-center gap-4 mb-2">
              <label className="text-sm text-slate-400">Show only pod-to-pod flows</label>
              <input type="checkbox" checked={showPodOnly} onChange={() => setShowPodOnly(v => !v)} />
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

              if (filtered.length === 0) return <div className="text-slate-500">No network flows found.</div>;

              return filtered.map((f, k) => {
                const src = f.source?.pod_name || f.source?.labels || 'external';
                const dst = f.destination?.pod_name || f.destination?.labels || 'external';
                const proto = f.IP?.protocol || f.l4?.protocol || 'TCP';
                const verdict = f.verdict || f.summary || 'N/A';
                const ts = f.time || f.timestamp || '';
                return (
                  <div key={k} className="flex justify-between items-center p-4 bg-[#1e293b]/20 rounded-2xl border border-slate-800 font-mono">
                    <div className="flex-1 text-blue-400 truncate">{src}</div>
                    <div className="text-slate-700 px-4">── {proto} ──▶</div>
                    <div className="flex-1 text-purple-400 truncate text-right">{dst}</div>
                    <div className="ml-4 text-emerald-500 font-bold">{verdict}</div>
                    <div className="ml-4 text-slate-500 text-xs">{ts}</div>
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
