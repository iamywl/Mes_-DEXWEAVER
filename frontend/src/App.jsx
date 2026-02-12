import React, { useState, useEffect } from 'react';
import axios from 'axios';

axios.defaults.baseURL = import.meta.env.VITE_API_URL || '';

/* ── helper components ─────────────────────────────────── */
const Card = ({title, value, color='text-blue-500'}) => (
  <div className="bg-[#1e293b]/30 p-6 rounded-2xl border border-slate-800 text-center">
    <span className="text-slate-500 font-bold uppercase text-[10px]">{title}</span>
    <p className={`text-4xl font-black mt-1 ${color}`}>{value}</p>
  </div>
);
const Table = ({cols, rows, renderRow}) => (
  <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
    <table className="w-full text-left">
      <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
        <tr>{cols.map(c => <th key={c} className="p-3">{c}</th>)}</tr>
      </thead>
      <tbody className="divide-y divide-slate-800">{rows.map(renderRow)}</tbody>
    </table>
  </div>
);
const Badge = ({v}) => {
  const c = v==='RUNNING'||v==='DONE'||v==='PASS'||v==='NORMAL' ? 'bg-emerald-500/20 text-emerald-400'
    : v==='DOWN'||v==='FAIL'||v==='OUT'||v==='LOW' ? 'bg-red-500/20 text-red-400'
    : 'bg-amber-500/20 text-amber-400';
  return <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${c}`}>{v}</span>;
};
const Input = (props) => <input {...props} className={`bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs ${props.className||''}`} />;
const Btn = ({children,...p}) => <button {...p} className={`bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-xs ${p.className||''}`}>{children}</button>;

/* ── main app ──────────────────────────────────────────── */
const App = () => {
  const [menu, setMenu] = useState('DASHBOARD');
  const [db, setDb] = useState({ items:[], bom:[], plans:[], flows:[], pods:[], logs:'', infra:{} });
  const [extra, setExtra] = useState({});
  const [selPod, setSelPod] = useState('');
  const [topology, setTopology] = useState({ nodes:[], edges:[] });
  const [topologyView, setTopologyView] = useState('list');

  /* ── data fetching ─────────────────────────────────── */
  const fetchCore = async () => {
    try {
      const [m, f, n, p] = await Promise.all([
        axios.get('/api/mes/data'), axios.get('/api/network/flows'),
        axios.get('/api/infra/status'), axios.get('/api/k8s/pods')
      ]);
      let flowsData = [];
      if (f?.data) { flowsData = Array.isArray(f.data) ? f.data : (f.data.flows||[]); }
      setDb(prev => ({ ...prev, ...m.data, flows: flowsData, infra: n.data, pods: Array.isArray(p.data)?p.data:[] }));
      axios.get('/api/network/topology').then(r => {
        if (r?.data?.status==='success') setTopology({ nodes:r.data.nodes||[], edges:r.data.edges||[] });
      }).catch(()=>{});
      if (selPod) { const l = await axios.get(`/api/k8s/logs/${selPod}`); setDb(prev=>({...prev,logs:l.data})); }
    } catch(e) { console.error('Sync Error',e); }
  };

  useEffect(() => { fetchCore(); const t=setInterval(fetchCore,5000); return ()=>clearInterval(t); }, [selPod]);

  /* ── load page-specific data on menu change ────────── */
  useEffect(() => {
    const load = async () => {
      try {
        if (menu==='ITEMS') {
          const r = await axios.get('/api/items?size=100');
          setExtra(prev=>({...prev, itemList: r.data.items||[]}));
        }
        if (menu==='BOM') {
          const r = await axios.get('/api/items?size=100');
          setExtra(prev=>({...prev, itemList: r.data.items||[], bomTree:null}));
        }
        if (menu==='PROCESS') {
          const r = await axios.get('/api/items?size=100');
          setExtra(prev=>({...prev, itemList: r.data.items||[], routingData:null}));
        }
        if (menu==='EQUIPMENT') {
          const r = await axios.get('/api/equipments');
          setExtra(prev=>({...prev, equips: r.data.equipments||[]}));
        }
        if (menu==='PLANS') {
          const r = await axios.get('/api/plans');
          setExtra(prev=>({...prev, planList: r.data.plans||[]}));
        }
        if (menu==='WORK_ORDER') {
          const r = await axios.get('/api/work-orders');
          setExtra(prev=>({...prev, woList: r.data.orders||[]}));
        }
        if (menu==='QUALITY') {
          const r = await axios.get('/api/quality/defects');
          setExtra(prev=>({...prev, defects: r.data}));
        }
        if (menu==='INVENTORY') {
          const r = await axios.get('/api/inventory');
          setExtra(prev=>({...prev, invItems: r.data.items||[]}));
        }
        if (menu==='AI_CENTER') {
          setExtra(prev=>({...prev, aiDemand:null, aiDefect:null, aiFailure:null}));
        }
        if (menu==='REPORTS') {
          const [pr, qr] = await Promise.all([
            axios.get('/api/reports/production'),
            axios.get('/api/reports/quality')
          ]);
          setExtra(prev=>({...prev, prodReport:pr.data, qualReport:qr.data}));
        }
      } catch(e) { console.error(e); }
    };
    load();
  }, [menu]);

  /* ── sidebar menu ──────────────────────────────────── */
  const menus = [
    {id:'DASHBOARD',    label:'Dashboard'},
    {id:'ITEMS',        label:'Items'},
    {id:'BOM',          label:'BOM'},
    {id:'PROCESS',      label:'Process'},
    {id:'EQUIPMENT',    label:'Equipment'},
    {id:'PLANS',        label:'Plans'},
    {id:'WORK_ORDER',   label:'Work Order'},
    {id:'QUALITY',      label:'Quality'},
    {id:'INVENTORY',    label:'Inventory'},
    {id:'AI_CENTER',    label:'AI Center'},
    {id:'REPORTS',      label:'Reports'},
    {id:'NETWORK_FLOW', label:'Network'},
    {id:'INFRA_MONITOR',label:'Infra'},
    {id:'K8S_MANAGER',  label:'K8s'},
  ];

  return (
    <div className="flex min-h-screen bg-[#020617] text-slate-400 font-sans text-[11px]">
      {/* sidebar */}
      <aside className="w-52 bg-[#0f172a] border-r border-slate-800 p-4 space-y-0.5 overflow-y-auto">
        <h1 className="text-lg font-black text-blue-500 mb-6 tracking-tighter italic">KNU MES v5.0</h1>
        {menus.map(m=>(
          <button key={m.id} onClick={()=>setMenu(m.id)}
            className={`w-full text-left px-3 py-1.5 rounded-lg transition-all text-xs
              ${menu===m.id ? 'bg-blue-600 text-white font-bold':'hover:bg-slate-800'}`}>
            {m.label}
          </button>
        ))}
      </aside>

      {/* main content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <h2 className="text-xl font-bold text-white mb-6 border-b border-slate-800 pb-3">
          {menus.find(m=>m.id===menu)?.label || menu}
        </h2>

        {/* ── DASHBOARD ────────────────────────────────── */}
        {menu==='DASHBOARD' && (
          <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
              <Card title="Items" value={db.items?.length||0} />
              <Card title="CPU" value={db.infra.cpu||'0%'} color="text-slate-200" />
              <Card title="Memory" value={db.infra.mem||'0%'} color="text-purple-400" />
              <Card title="Pods" value={db.pods?.length||0} color="text-emerald-500" />
            </div>
          </div>
        )}

        {/* ── ITEMS (FN-004~007) ───────────────────────── */}
        {menu==='ITEMS' && (
          <div className="space-y-4">
            <Table cols={['Code','Name','Category','Unit','Spec','Stock','Safety','Status']}
              rows={extra.itemList||[]}
              renderRow={(i,k)=>(
                <tr key={k}>
                  <td className="p-3 font-mono text-blue-400">{i.item_code}</td>
                  <td className="p-3 text-white font-bold">{i.name}</td>
                  <td className="p-3"><Badge v={i.category}/></td>
                  <td className="p-3">{i.unit}</td>
                  <td className="p-3 text-slate-500">{i.spec}</td>
                  <td className="p-3 text-blue-400 font-bold">{i.stock}</td>
                  <td className="p-3">{i.safety_stock}</td>
                  <td className="p-3"><Badge v={i.stock<=0?'OUT':i.stock<i.safety_stock?'LOW':'NORMAL'}/></td>
                </tr>
              )} />
          </div>
        )}

        {/* ── BOM (FN-008~009) ─────────────────────────── */}
        {menu==='BOM' && (
          <div className="space-y-4">
            <div className="flex gap-2 items-center">
              <select className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs"
                onChange={async e => {
                  if(!e.target.value) return;
                  const r = await axios.get(`/api/bom/explode/${e.target.value}`);
                  setExtra(prev=>({...prev, bomTree:r.data}));
                }}>
                <option value="">Select item to explode BOM</option>
                {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
              </select>
            </div>
            {extra.bomTree && (
              <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800 space-y-2">
                <h3 className="text-white font-bold mb-2">BOM Tree: {extra.bomTree.item_code}</h3>
                {(function renderTree(nodes, depth=0) {
                  return nodes.map((n,i)=>(
                    <div key={i}>
                      <div className="flex items-center gap-2" style={{paddingLeft:depth*24}}>
                        <span className="text-slate-600">{'└─'}</span>
                        <span className="text-blue-400 font-mono">{n.item_code}</span>
                        <span className="text-white">{n.item_name}</span>
                        <span className="text-amber-400">x{n.required_qty}</span>
                        <span className="text-slate-600 text-[9px]">loss:{n.loss_rate}%</span>
                      </div>
                      {n.children && renderTree(n.children, depth+1)}
                    </div>
                  ));
                })(extra.bomTree.tree||[])}
              </div>
            )}
          </div>
        )}

        {/* ── PROCESS / ROUTING (FN-010~012) ───────────── */}
        {menu==='PROCESS' && (
          <div className="space-y-4">
            <div className="flex gap-2 items-center">
              <select className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs"
                onChange={async e => {
                  if(!e.target.value) return;
                  const r = await axios.get(`/api/routings/${e.target.value}`);
                  setExtra(prev=>({...prev, routingData:r.data}));
                }}>
                <option value="">Select item for routing</option>
                {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
              </select>
            </div>
            {extra.routingData && (
              <div className="space-y-3">
                <div className="text-white font-bold">Routing: {extra.routingData.item_code} (Total: {extra.routingData.total_time} min)</div>
                <div className="flex gap-2 items-center flex-wrap">
                  {(extra.routingData.routes||[]).map((r,i)=>(
                    <React.Fragment key={i}>
                      <div className="bg-[#1e293b] p-3 rounded-xl border border-slate-700 text-center min-w-[120px]">
                        <div className="text-blue-400 font-bold">{r.process_name}</div>
                        <div className="text-[10px] text-slate-500">{r.process_code}</div>
                        <div className="text-amber-400 mt-1">{r.cycle_time} min</div>
                        <div className="text-[9px] text-slate-600">{r.equip_name}</div>
                      </div>
                      {i < extra.routingData.routes.length-1 && <span className="text-slate-600 text-lg">→</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── EQUIPMENT (FN-013~014, 032~034) ──────────── */}
        {menu==='EQUIPMENT' && (
          <div className="space-y-4">
            <div className="grid grid-cols-5 gap-3">
              {(extra.equips||[]).map(e=>(
                <div key={e.equip_code} className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-white font-bold text-xs">{e.name}</span>
                    <Badge v={e.status}/>
                  </div>
                  <div className="text-[10px] text-slate-500 space-y-0.5">
                    <div>Code: {e.equip_code}</div>
                    <div>Process: {e.process_code}</div>
                    <div>Capacity: {e.capacity_per_hour}/hr</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── PLANS (FN-015~017) ───────────────────────── */}
        {menu==='PLANS' && (
          <div className="space-y-4">
            <Table cols={['ID','Item','Qty','Due Date','Priority','Status','Progress']}
              rows={extra.planList||[]}
              renderRow={(p,k)=>(
                <tr key={k}>
                  <td className="p-3 text-blue-400 font-mono">{p.plan_id}</td>
                  <td className="p-3 text-white">{p.item_name}</td>
                  <td className="p-3">{p.qty}</td>
                  <td className="p-3">{p.due_date}</td>
                  <td className="p-3"><Badge v={p.priority}/></td>
                  <td className="p-3"><Badge v={p.status}/></td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{width:`${p.progress}%`}}/>
                      </div>
                      <span className="text-[10px] text-blue-400">{p.progress}%</span>
                    </div>
                  </td>
                </tr>
              )} />
          </div>
        )}

        {/* ── WORK ORDER (FN-020~024) ──────────────────── */}
        {menu==='WORK_ORDER' && (
          <div className="space-y-4">
            <Table cols={['WO ID','Item','Qty','Date','Equipment','Status']}
              rows={extra.woList||[]}
              renderRow={(w,k)=>(
                <tr key={k}>
                  <td className="p-3 font-mono text-blue-400">{w.wo_id}</td>
                  <td className="p-3 text-white">{w.item_name}</td>
                  <td className="p-3">{w.plan_qty}</td>
                  <td className="p-3">{w.work_date}</td>
                  <td className="p-3 text-purple-400">{w.equip_code}</td>
                  <td className="p-3"><Badge v={w.status}/></td>
                </tr>
              )} />
          </div>
        )}

        {/* ── QUALITY (FN-025~028) ─────────────────────── */}
        {menu==='QUALITY' && (
          <div className="space-y-6">
            <h3 className="text-white font-bold">Defect Summary</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Table cols={['Defect Type','Count','Rate']}
                  rows={extra.defects?.summary||[]}
                  renderRow={(d,k)=>(
                    <tr key={k}>
                      <td className="p-3 text-red-400 font-bold">{d.defect_type}</td>
                      <td className="p-3 text-white">{d.count}</td>
                      <td className="p-3">{(d.rate*100).toFixed(1)}%</td>
                    </tr>
                  )} />
              </div>
              <div>
                <h4 className="text-slate-400 mb-2 font-bold">Defect Trend</h4>
                <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800 space-y-2">
                  {(extra.defects?.trend||[]).map((t,i)=>(
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs w-24">{t.date}</span>
                      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full" style={{width:`${Math.min(t.rate*1000,100)}%`}}/>
                      </div>
                      <span className="text-red-400 text-[10px] w-12 text-right">{(t.rate*100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── INVENTORY (FN-029~031) ───────────────────── */}
        {menu==='INVENTORY' && (
          <Table cols={['Code','Name','Stock','Available','Safety','Status']}
            rows={extra.invItems||[]}
            renderRow={(i,k)=>(
              <tr key={k}>
                <td className="p-3 font-mono text-blue-400">{i.item_code}</td>
                <td className="p-3 text-white">{i.name}</td>
                <td className="p-3 text-blue-400 font-bold">{i.stock}</td>
                <td className="p-3">{i.available}</td>
                <td className="p-3 text-amber-400">{i.safety}</td>
                <td className="p-3"><Badge v={i.status}/></td>
              </tr>
            )} />
        )}

        {/* ── AI CENTER (FN-018,028,034) ───────────────── */}
        {menu==='AI_CENTER' && (
          <div className="grid grid-cols-3 gap-4">
            {/* Demand Forecast */}
            <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="text-white font-bold">Demand Forecast</h3>
              <Input placeholder="Item code (e.g. ITEM003)" id="ai-demand-item" className="w-full" />
              <Btn onClick={async()=>{
                const code = document.getElementById('ai-demand-item').value;
                if(!code) return;
                const r = await axios.get(`/api/ai/demand-prediction/${code}`);
                setExtra(prev=>({...prev, aiDemand:r.data}));
              }}>Predict</Btn>
              {extra.aiDemand && (
                <div className="text-xs space-y-1">
                  <div className="text-slate-400">Data points: {extra.aiDemand.data_points_used}</div>
                  {(extra.aiDemand.predictions||[]).map((p,i)=>(
                    <div key={i} className="flex justify-between">
                      <span>Month +{p.month_offset}</span>
                      <span className="text-blue-400 font-bold">{p.predicted_qty} EA</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Defect Prediction */}
            <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="text-white font-bold">Defect Prediction</h3>
              <Input placeholder="Temp" id="ai-def-temp" className="w-full" type="number" />
              <Input placeholder="Pressure" id="ai-def-pres" className="w-full" type="number" />
              <Input placeholder="Speed" id="ai-def-speed" className="w-full" type="number" />
              <Input placeholder="Humidity" id="ai-def-hum" className="w-full" type="number" />
              <Btn onClick={async()=>{
                const r = await axios.post('/api/ai/defect-prediction', {
                  temperature: +document.getElementById('ai-def-temp').value,
                  pressure: +document.getElementById('ai-def-pres').value,
                  speed: +document.getElementById('ai-def-speed').value,
                  humidity: +document.getElementById('ai-def-hum').value,
                });
                setExtra(prev=>({...prev, aiDefect:r.data}));
              }}>Predict</Btn>
              {extra.aiDefect && (
                <div className="text-xs space-y-1">
                  <div className="text-2xl font-black" style={{color: extra.aiDefect.defect_probability > 50 ? '#ef4444':'#22c55e'}}>
                    {extra.aiDefect.defect_probability}%
                  </div>
                  {(extra.aiDefect.main_causes||[]).map((c,i)=><div key={i} className="text-slate-400">{c}</div>)}
                  <div className="text-amber-400">{extra.aiDefect.recommended_action}</div>
                </div>
              )}
            </div>

            {/* Failure Prediction */}
            <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="text-white font-bold">Failure Prediction</h3>
              <Input placeholder="Equip code (e.g. EQP-003)" id="ai-fail-eq" className="w-full" />
              <Input placeholder="Vibration" id="ai-fail-vib" className="w-full" type="number" />
              <Input placeholder="Temperature" id="ai-fail-temp" className="w-full" type="number" />
              <Input placeholder="Current (A)" id="ai-fail-cur" className="w-full" type="number" />
              <Btn onClick={async()=>{
                const r = await axios.post('/api/ai/failure-predict', {
                  equip_code: document.getElementById('ai-fail-eq').value,
                  sensor: {
                    vibration: +document.getElementById('ai-fail-vib').value,
                    temperature: +document.getElementById('ai-fail-temp').value,
                    current: +document.getElementById('ai-fail-cur').value,
                  }
                });
                setExtra(prev=>({...prev, aiFailure:r.data}));
              }}>Predict</Btn>
              {extra.aiFailure && (
                <div className="text-xs space-y-1">
                  <div className="text-2xl font-black" style={{color: extra.aiFailure.failure_prob > 50 ? '#ef4444':'#22c55e'}}>
                    {extra.aiFailure.failure_prob}%
                  </div>
                  <div className="text-slate-400">Remaining: {extra.aiFailure.remaining_life_hours}h</div>
                  <div className="text-amber-400">{extra.aiFailure.recommendation}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── REPORTS (FN-035~037) ─────────────────────── */}
        {menu==='REPORTS' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              {/* Production Report */}
              <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
                <h3 className="text-white font-bold">Production Report</h3>
                <div className="flex gap-4">
                  <Card title="Total Qty" value={extra.prodReport?.summary?.total_qty||0} />
                  <Card title="Achieve Rate" value={`${((extra.prodReport?.summary?.achieve_rate||0)*100).toFixed(0)}%`} color="text-emerald-400" />
                </div>
                <h4 className="text-slate-500 text-[10px] uppercase mt-2">By Item</h4>
                {(extra.prodReport?.by_item||[]).map((b,i)=>(
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-white text-xs w-24">{b.item}</span>
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{width:`${b.rate*100}%`}}/>
                    </div>
                    <span className="text-blue-400 text-[10px]">{b.qty} ({(b.rate*100).toFixed(0)}%)</span>
                  </div>
                ))}
              </div>

              {/* Quality Report */}
              <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
                <h3 className="text-white font-bold">Quality Report</h3>
                <div className="flex gap-4">
                  <Card title="Defect Rate" value={`${((extra.qualReport?.defect_rate||0)*100).toFixed(1)}%`} color="text-red-400" />
                  <Card title="Cpk" value={extra.qualReport?.cpk||'-'} color="text-emerald-400" />
                </div>
                <h4 className="text-slate-500 text-[10px] uppercase mt-2">Trend</h4>
                {(extra.qualReport?.trend||[]).map((t,i)=>(
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-xs w-24">{t.date}</span>
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-red-500 rounded-full" style={{width:`${t.rate*1000}%`}}/>
                    </div>
                    <span className="text-red-400 text-[10px]">{(t.rate*100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Insights */}
            <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-3">
                <h3 className="text-white font-bold">AI Insights</h3>
                <Btn onClick={async()=>{
                  const r = await axios.post('/api/ai/insights',{focus_area:'production'});
                  setExtra(prev=>({...prev, insights:r.data}));
                }}>Generate</Btn>
              </div>
              {extra.insights && (
                <div className="space-y-2">
                  <div className="text-white text-xs">{extra.insights.summary}</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <h4 className="text-red-400 font-bold text-[10px] uppercase mb-1">Issues</h4>
                      {(extra.insights.issues||[]).map((is,i)=>(
                        <div key={i} className="text-xs text-slate-400 mb-1">
                          <Badge v={is.area}/> {is.desc}
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4 className="text-emerald-400 font-bold text-[10px] uppercase mb-1">Recommendations</h4>
                      {(extra.insights.recommendations||[]).map((r,i)=>(
                        <div key={i} className="text-xs text-slate-400 mb-1">
                          {r.action} <span className="text-emerald-500">({r.expected_impact})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── NETWORK FLOW (existing) ──────────────────── */}
        {menu==='NETWORK_FLOW' && (
          <div className="space-y-4">
            <div className="flex items-center gap-4 mb-4">
              <select value={topologyView} onChange={e=>setTopologyView(e.target.value)} className="bg-[#0f172a] border border-slate-700 px-3 py-1 rounded-lg text-white text-xs">
                <option value="graph">Topology Graph</option>
                <option value="list">Flow List</option>
              </select>
            </div>
            {topologyView==='graph' ? (
              topology.nodes.length===0 ? <div className="p-8 text-center text-slate-500">Waiting for flow events...</div> : (
                <div className="p-4 bg-[#1e293b]/30 rounded-2xl border border-slate-800 overflow-auto">
                  <svg width="100%" viewBox="0 0 900 400" style={{minHeight:'400px'}}>
                    <defs><marker id="ab" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="#60a5fa"/></marker></defs>
                    {topology.edges.map((e,i)=>{
                      const ns=topology.nodes; const si=ns.findIndex(n=>n.id===e.source); const ti=ns.findIndex(n=>n.id===e.target);
                      if(si===-1||ti===-1)return null;
                      const a=(j,t)=>(j/t)*Math.PI*2-Math.PI/2; const cx=450,cy=200,r=140;
                      const sx=cx+r*Math.cos(a(si,ns.length)),sy=cy+r*Math.sin(a(si,ns.length));
                      const tx=cx+r*Math.cos(a(ti,ns.length)),ty=cy+r*Math.sin(a(ti,ns.length));
                      return <line key={i} x1={sx} y1={sy} x2={tx} y2={ty} stroke="#0ea5e9" strokeWidth={Math.min(3,1+Math.log1p(e.count))} markerEnd="url(#ab)"/>;
                    })}
                    {topology.nodes.map((n,i)=>{
                      const a=(i/topology.nodes.length)*Math.PI*2-Math.PI/2; const x=450+140*Math.cos(a),y=200+140*Math.sin(a);
                      return <g key={n.id}><circle cx={x} cy={y} r={20} fill="#06b6d4" opacity="0.9"/><text x={x} y={y+4} fontSize="8" fontWeight="700" fill="#020617" textAnchor="middle">{n.label.slice(0,10)}</text></g>;
                    })}
                  </svg>
                </div>
              )
            ) : (
              (db.flows||[]).length===0 ? <div className="p-8 text-center text-slate-500">No flows detected.</div> :
              (db.flows||[]).map((f,k)=>(
                <div key={k} className="flex items-center justify-between p-3 bg-[#1e293b]/30 rounded-xl border border-slate-700 font-mono text-xs">
                  <span className="text-blue-400">{f.source?.pod_name||'ext'}</span>
                  <span className="text-slate-600">→</span>
                  <span className="text-purple-400">{f.destination?.pod_name||'ext'}</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* ── INFRA MONITOR (existing) ─────────────────── */}
        {menu==='INFRA_MONITOR' && (
          <div className="bg-[#1e293b]/20 p-8 rounded-3xl border border-slate-800 space-y-8">
            <div className="flex justify-between items-center text-white"><span>API Engine</span><span className="text-emerald-500 font-black animate-pulse">ONLINE</span></div>
            <div><div className="flex justify-between text-xs mb-2"><span>CPU</span><span>{db.infra.cpu}</span></div><div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-blue-500" style={{width:db.infra.cpu}}/></div></div>
            <div><div className="flex justify-between text-xs mb-2"><span>MEM</span><span>{db.infra.mem}</span></div><div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-purple-500" style={{width:db.infra.mem}}/></div></div>
          </div>
        )}

        {/* ── K8S MANAGER (existing) ───────────────────── */}
        {menu==='K8S_MANAGER' && (
          <div className="grid grid-cols-2 gap-6 h-[500px]">
            <div className="bg-[#1e293b]/20 p-4 rounded-2xl border border-slate-800 overflow-auto space-y-2">
              <h3 className="text-white font-bold mb-3">Pod Status</h3>
              {(db.pods||[]).map(p=>(
                <div key={p.name} onClick={()=>setSelPod(p.name)} className={`p-2 rounded-xl border cursor-pointer text-xs ${selPod===p.name?'border-blue-500 bg-blue-500/10':'border-slate-800'}`}>
                  <div className="flex justify-between"><span>{p.name}</span><Badge v={p.status}/></div>
                </div>
              ))}
            </div>
            <div className="bg-black/80 p-4 rounded-2xl border border-slate-800 flex flex-col">
              <h3 className="text-blue-400 font-bold mb-2 font-mono text-xs"># {selPod||'select a pod'}</h3>
              <pre className="text-emerald-500 font-mono text-[9px] flex-1 overflow-auto whitespace-pre-wrap leading-tight">{db.logs}</pre>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};
export default App;
