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

  /* ── Hubble network state ─────────────────────────── */
  const [hubbleFlows, setHubbleFlows] = useState([]);
  const [serviceMap, setServiceMap] = useState({ services:[], connections:[] });
  const [hubbleFilter, setHubbleFilter] = useState({ verdict:'ALL', protocol:'ALL', namespace:'ALL', search:'' });
  const [hubbleView, setHubbleView] = useState('map');
  const [selectedSvc, setSelectedSvc] = useState(null);
  const [flowPanelOpen, setFlowPanelOpen] = useState(true);

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
        if (menu==='NETWORK_FLOW') {
          const [hf, sm] = await Promise.all([
            axios.get('/api/network/hubble-flows?last=100'),
            axios.get('/api/network/service-map')
          ]);
          setHubbleFlows(hf.data.flows||[]);
          setServiceMap({ services:sm.data.services||[], connections:sm.data.connections||[] });
        }
      } catch(e) { console.error(e); }
    };
    load();
  }, [menu]);

  /* ── Hubble auto-refresh (every 5s when on Network page) */
  useEffect(() => {
    if (menu !== 'NETWORK_FLOW') return;
    const t = setInterval(async () => {
      try {
        const [hf, sm] = await Promise.all([
          axios.get('/api/network/hubble-flows?last=100'),
          axios.get('/api/network/service-map')
        ]);
        setHubbleFlows(hf.data.flows||[]);
        setServiceMap({ services:sm.data.services||[], connections:sm.data.connections||[] });
      } catch(e) {}
    }, 5000);
    return () => clearInterval(t);
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

        {/* ── NETWORK FLOW — Hubble-style UI ─────────────── */}
        {menu==='NETWORK_FLOW' && (() => {
          const allNamespaces = [...new Set(serviceMap.services.map(s=>s.namespace))];
          const filteredFlows = hubbleFlows.filter(f => {
            if (hubbleFilter.verdict!=='ALL' && f.verdict!==hubbleFilter.verdict) return false;
            if (hubbleFilter.protocol!=='ALL' && f.l4?.protocol!==hubbleFilter.protocol) return false;
            if (hubbleFilter.namespace!=='ALL') {
              if (f.source?.namespace!==hubbleFilter.namespace && f.destination?.namespace!==hubbleFilter.namespace) return false;
            }
            if (hubbleFilter.search) {
              const s = hubbleFilter.search.toLowerCase();
              const hay = `${f.source?.pod_name||''} ${f.destination?.pod_name||''} ${f.l7?.type||''} ${f.l4?.protocol||''}`.toLowerCase();
              if (!hay.includes(s)) return false;
            }
            return true;
          });
          const filteredSvcs = serviceMap.services.filter(s => hubbleFilter.namespace==='ALL' || s.namespace===hubbleFilter.namespace);
          const filteredConns = serviceMap.connections.filter(c => {
            const ss = serviceMap.services.find(s=>s.id===c.source);
            const ds = serviceMap.services.find(s=>s.id===c.target);
            if (hubbleFilter.namespace!=='ALL') {
              if (ss?.namespace!==hubbleFilter.namespace && ds?.namespace!==hubbleFilter.namespace) return false;
            }
            return true;
          });

          /* service map layout — force-directed-like positions */
          const svcPositions = {};
          const W=880, H=380, CX=W/2, CY=H/2;
          const nsByNs = {};
          filteredSvcs.forEach(s => { if(!nsByNs[s.namespace]) nsByNs[s.namespace]=[]; nsByNs[s.namespace].push(s); });
          const nsKeys = Object.keys(nsByNs);
          nsKeys.forEach((ns, ni) => {
            const nsAngle = nsKeys.length===1 ? 0 : (ni/nsKeys.length)*Math.PI*2 - Math.PI/2;
            const nsOffX = nsKeys.length===1 ? 0 : Math.cos(nsAngle)*100;
            const nsOffY = nsKeys.length===1 ? 0 : Math.sin(nsAngle)*60;
            const svcs = nsByNs[ns];
            svcs.forEach((s, si) => {
              const a = (si/svcs.length)*Math.PI*2 - Math.PI/2;
              const r = Math.min(120, 60+svcs.length*15);
              svcPositions[s.id] = {
                x: CX + nsOffX + r*Math.cos(a),
                y: CY + nsOffY + r*Math.sin(a),
              };
            });
          });

          const verdictColor = v => v==='FORWARDED' ? '#22c55e' : v==='DROPPED' ? '#ef4444' : '#f59e0b';
          const protoColor = p => p==='HTTP' ? '#3b82f6' : p==='TCP' ? '#06b6d4' : p==='UDP' ? '#a855f7' : p==='gRPC' ? '#f97316' : '#64748b';

          return (
            <div className="flex flex-col" style={{height:'calc(100vh - 120px)'}}>
              {/* ── Hubble Toolbar ── */}
              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Namespace</span>
                  <select value={hubbleFilter.namespace} onChange={e=>setHubbleFilter(p=>({...p,namespace:e.target.value}))}
                    className="bg-[#0f172a] border border-slate-700 px-2 py-1 rounded text-white text-[11px]">
                    <option value="ALL">All Namespaces</option>
                    {allNamespaces.map(n=><option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Verdict</span>
                  {['ALL','FORWARDED','DROPPED'].map(v=>(
                    <button key={v} onClick={()=>setHubbleFilter(p=>({...p,verdict:v}))}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all
                        ${hubbleFilter.verdict===v
                          ? v==='FORWARDED' ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                            : v==='DROPPED' ? 'bg-red-500/20 border-red-500 text-red-400'
                            : 'bg-blue-500/20 border-blue-500 text-blue-400'
                          : 'border-slate-700 text-slate-500 hover:border-slate-500'}`}>
                      {v==='ALL' ? 'All' : v.charAt(0)+v.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Protocol</span>
                  {['ALL','HTTP','TCP','UDP','gRPC'].map(p=>(
                    <button key={p} onClick={()=>setHubbleFilter(prev=>({...prev,protocol:p}))}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all
                        ${hubbleFilter.protocol===p ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400' : 'border-slate-700 text-slate-500 hover:border-slate-500'}`}>
                      {p==='ALL' ? 'All' : p}
                    </button>
                  ))}
                </div>
                <input placeholder="Search pods, endpoints..."
                  value={hubbleFilter.search} onChange={e=>setHubbleFilter(p=>({...p,search:e.target.value}))}
                  className="bg-[#0f172a] border border-slate-700 px-3 py-1 rounded text-white text-[11px] w-48 ml-auto" />
                <div className="flex items-center gap-1 border border-slate-700 rounded overflow-hidden">
                  <button onClick={()=>setHubbleView('map')}
                    className={`px-3 py-1 text-[10px] font-bold ${hubbleView==='map' ? 'bg-blue-600 text-white' : 'text-slate-500'}`}>
                    Service Map</button>
                  <button onClick={()=>setHubbleView('table')}
                    className={`px-3 py-1 text-[10px] font-bold ${hubbleView==='table' ? 'bg-blue-600 text-white' : 'text-slate-500'}`}>
                    Flows Only</button>
                </div>
                {/* live indicator */}
                <div className="flex items-center gap-1.5">
                  <span className="relative flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span></span>
                  <span className="text-[10px] text-emerald-400 font-bold">LIVE</span>
                </div>
              </div>

              {/* ── Stats bar ── */}
              <div className="flex items-center gap-4 mb-3 px-1">
                <span className="text-[10px] text-slate-500">Services: <span className="text-white font-bold">{filteredSvcs.length}</span></span>
                <span className="text-[10px] text-slate-500">Connections: <span className="text-white font-bold">{filteredConns.length}</span></span>
                <span className="text-[10px] text-slate-500">Flows: <span className="text-white font-bold">{filteredFlows.length}</span></span>
                <span className="text-[10px] text-emerald-400">Forwarded: <span className="font-bold">{filteredFlows.filter(f=>f.verdict==='FORWARDED').length}</span></span>
                <span className="text-[10px] text-red-400">Dropped: <span className="font-bold">{filteredFlows.filter(f=>f.verdict==='DROPPED').length}</span></span>
              </div>

              {/* ── Service Map ── */}
              {hubbleView==='map' && (
                <div className="flex-1 min-h-0 bg-[#0a0f1e] rounded-xl border border-slate-800 overflow-hidden relative mb-3" style={{minHeight:'340px'}}>
                  {filteredSvcs.length===0 ? (
                    <div className="flex items-center justify-center h-full text-slate-600">Loading service map...</div>
                  ) : (
                    <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} className="select-none">
                      <defs>
                        <marker id="arrow-fwd" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                          <polygon points="0 0, 10 3.5, 0 7" fill="#22c55e" opacity="0.7"/>
                        </marker>
                        <marker id="arrow-drop" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                          <polygon points="0 0, 10 3.5, 0 7" fill="#ef4444" opacity="0.7"/>
                        </marker>
                        <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                      </defs>

                      {/* namespace backgrounds */}
                      {nsKeys.map((ns, ni) => {
                        const svcs = nsByNs[ns];
                        const positions = svcs.map(s=>svcPositions[s.id]).filter(Boolean);
                        if(!positions.length) return null;
                        const minX = Math.min(...positions.map(p=>p.x))-50;
                        const minY = Math.min(...positions.map(p=>p.y))-40;
                        const maxX = Math.max(...positions.map(p=>p.x))+50;
                        const maxY = Math.max(...positions.map(p=>p.y))+40;
                        return (
                          <g key={ns}>
                            <rect x={minX} y={minY} width={maxX-minX} height={maxY-minY} rx="12"
                              fill={ni===0 ? 'rgba(59,130,246,0.04)' : 'rgba(168,85,247,0.04)'}
                              stroke={ni===0 ? 'rgba(59,130,246,0.15)' : 'rgba(168,85,247,0.15)'} strokeWidth="1" strokeDasharray="4 2"/>
                            <text x={minX+8} y={minY+14} fill={ni===0 ? '#3b82f6' : '#a855f7'} fontSize="9" fontWeight="700" opacity="0.6">{ns}</text>
                          </g>
                        );
                      })}

                      {/* connections */}
                      {filteredConns.map((c, i) => {
                        const sp = svcPositions[c.source]; const tp = svcPositions[c.target];
                        if(!sp||!tp) return null;
                        const hasDropped = c.dropped_count > 0;
                        const strokeW = Math.min(4, 1 + Math.log1p(c.total_count)*0.8);
                        const dx=tp.x-sp.x, dy=tp.y-sp.y;
                        const len=Math.sqrt(dx*dx+dy*dy)||1;
                        const nx=dx/len, ny=dy/len;
                        const sx2=sp.x+nx*28, sy2=sp.y+ny*28;
                        const tx2=tp.x-nx*28, ty2=tp.y-ny*28;
                        const mx=(sx2+tx2)/2+ny*20, my=(sy2+ty2)/2-nx*20;
                        return (
                          <g key={i}>
                            <path d={`M${sx2},${sy2} Q${mx},${my} ${tx2},${ty2}`}
                              fill="none" stroke={hasDropped ? '#ef4444' : '#22c55e'}
                              strokeWidth={strokeW} opacity="0.5"
                              markerEnd={hasDropped ? 'url(#arrow-drop)' : 'url(#arrow-fwd)'}
                              strokeDasharray={hasDropped ? '4 3' : 'none'}>
                              <animate attributeName="stroke-dashoffset" values="14;0" dur="1s" repeatCount="indefinite"/>
                            </path>
                            <text x={mx} y={my-6} fill="#64748b" fontSize="8" textAnchor="middle" fontWeight="600">
                              {c.protocol}:{c.port}
                            </text>
                            <text x={mx} y={my+5} fill={hasDropped ? '#f87171' : '#4ade80'} fontSize="7" textAnchor="middle">
                              {c.total_count} flows
                            </text>
                          </g>
                        );
                      })}

                      {/* service nodes */}
                      {filteredSvcs.map(s => {
                        const pos = svcPositions[s.id]; if(!pos) return null;
                        const isSelected = selectedSvc===s.id;
                        const hasDropped = s.dropped > 0;
                        const nodeColor = hasDropped ? '#ef4444' : s.namespace==='kube-system' ? '#a855f7' : '#3b82f6';
                        return (
                          <g key={s.id} onClick={()=>setSelectedSvc(isSelected?null:s.id)} style={{cursor:'pointer'}}>
                            {/* outer ring pulse */}
                            <circle cx={pos.x} cy={pos.y} r={isSelected?30:26} fill="none"
                              stroke={nodeColor} strokeWidth={isSelected?2:1} opacity={isSelected?0.8:0.2}>
                              <animate attributeName="r" values={isSelected?"28;34;28":"24;28;24"} dur="2s" repeatCount="indefinite"/>
                              <animate attributeName="opacity" values={isSelected?"0.8;0.3;0.8":"0.2;0.1;0.2"} dur="2s" repeatCount="indefinite"/>
                            </circle>
                            {/* main circle */}
                            <circle cx={pos.x} cy={pos.y} r={22} fill={`${nodeColor}20`}
                              stroke={nodeColor} strokeWidth={isSelected?2.5:1.5}
                              filter={isSelected?"url(#glow)":"none"}/>
                            {/* icon */}
                            <text x={pos.x} y={pos.y-4} fill={nodeColor} fontSize="14" textAnchor="middle" dominantBaseline="central">
                              {s.type==='StatefulSet' ? '◆' : s.type==='DaemonSet' ? '◈' : '●'}
                            </text>
                            {/* name */}
                            <text x={pos.x} y={pos.y+10} fill="#e2e8f0" fontSize="8" fontWeight="700" textAnchor="middle">{s.name.length>14?s.name.slice(0,12)+'..':s.name}</text>
                            {/* traffic badges */}
                            <text x={pos.x} y={pos.y+34} fill="#64748b" fontSize="7" textAnchor="middle">
                              ↓{s.traffic_in} ↑{s.traffic_out}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  )}

                  {/* selected service detail panel */}
                  {selectedSvc && (() => {
                    const s = serviceMap.services.find(sv=>sv.id===selectedSvc);
                    if(!s) return null;
                    const relatedConns = serviceMap.connections.filter(c=>c.source===s.id||c.target===s.id);
                    return (
                      <div className="absolute top-3 right-3 w-56 bg-[#0f172a]/95 border border-slate-700 rounded-xl p-3 backdrop-blur-sm">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="text-white font-bold text-xs">{s.name}</div>
                            <div className="text-slate-500 text-[9px]">{s.namespace} / {s.type}</div>
                          </div>
                          <button onClick={()=>setSelectedSvc(null)} className="text-slate-500 hover:text-white text-xs">✕</button>
                        </div>
                        <div className="space-y-1 text-[10px]">
                          <div className="flex justify-between"><span className="text-slate-500">IP</span><span className="text-blue-400 font-mono">{s.ip}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Protocol</span><span style={{color:protoColor(s.protocol)}}>{s.protocol}:{s.port}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Traffic In</span><span className="text-emerald-400">{s.traffic_in}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Traffic Out</span><span className="text-blue-400">{s.traffic_out}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Forwarded</span><span className="text-emerald-400">{s.forwarded}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Dropped</span><span className="text-red-400">{s.dropped}</span></div>
                        </div>
                        {relatedConns.length>0 && (
                          <div className="mt-2 pt-2 border-t border-slate-800">
                            <div className="text-[9px] text-slate-500 uppercase font-bold mb-1">Connections</div>
                            {relatedConns.slice(0,5).map((c,i)=>(
                              <div key={i} className="flex items-center gap-1 text-[9px] mb-0.5">
                                <span className="text-blue-400">{c.source}</span>
                                <span className="text-slate-600">→</span>
                                <span className="text-purple-400">{c.target}</span>
                                <span className="ml-auto" style={{color: c.dropped_count>0?'#ef4444':'#22c55e'}}>{c.total_count}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* ── Flow Events Table ── */}
              <div className={`${hubbleView==='map' ? '' : 'flex-1'} min-h-0 bg-[#0f172a] rounded-xl border border-slate-800 flex flex-col`}
                style={hubbleView==='map' ? {height: flowPanelOpen ? '280px' : '36px'} : {minHeight:'400px'}}>
                <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 cursor-pointer select-none"
                  onClick={()=>hubbleView==='map' && setFlowPanelOpen(!flowPanelOpen)}>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Flow Events</span>
                    <span className="text-[10px] text-slate-600">{filteredFlows.length} flows</span>
                  </div>
                  {hubbleView==='map' && <span className="text-slate-600 text-xs">{flowPanelOpen ? '▼' : '▲'}</span>}
                </div>
                {(flowPanelOpen || hubbleView==='table') && (
                  <div className="flex-1 overflow-auto">
                    <table className="w-full text-left text-[10px]">
                      <thead className="bg-[#1e293b] text-slate-500 uppercase sticky top-0 z-10">
                        <tr>
                          <th className="p-2 w-[130px]">Timestamp</th>
                          <th className="p-2">Source</th>
                          <th className="p-2 w-8"></th>
                          <th className="p-2">Destination</th>
                          <th className="p-2 w-[80px]">Verdict</th>
                          <th className="p-2 w-[60px]">Protocol</th>
                          <th className="p-2 w-[50px]">Port</th>
                          <th className="p-2">L7 Info</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/50">
                        {filteredFlows.map((f, k) => (
                          <tr key={f.flow_id||k} className="hover:bg-slate-800/30 transition-colors">
                            <td className="p-2 text-slate-500 font-mono text-[9px]">
                              {f.time ? new Date(f.time).toLocaleTimeString('en-GB', {hour12:false, hour:'2-digit', minute:'2-digit', second:'2-digit', fractionalSecondDigits:3}) : '-'}
                            </td>
                            <td className="p-2">
                              <div className="flex items-center gap-1">
                                <span className="text-slate-600 text-[8px]">{f.source?.namespace||''}</span>
                                <span className="text-blue-400 font-mono font-bold">{f.source?.pod_name||'external'}</span>
                              </div>
                              <div className="text-[8px] text-slate-600 font-mono">{f.IP?.source||''}:{f.l4?.source_port||''}</div>
                            </td>
                            <td className="p-2 text-center">
                              <span style={{color: verdictColor(f.verdict)}} className="text-sm">{f.verdict==='FORWARDED' ? '→' : '⊘'}</span>
                            </td>
                            <td className="p-2">
                              <div className="flex items-center gap-1">
                                <span className="text-slate-600 text-[8px]">{f.destination?.namespace||''}</span>
                                <span className="text-purple-400 font-mono font-bold">{f.destination?.pod_name||'external'}</span>
                              </div>
                              <div className="text-[8px] text-slate-600 font-mono">{f.IP?.destination||''}:{f.l4?.destination_port||''}</div>
                            </td>
                            <td className="p-2">
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold
                                ${f.verdict==='FORWARDED' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                                {f.verdict==='FORWARDED' ? '✓ FWD' : '✕ DROP'}
                              </span>
                            </td>
                            <td className="p-2">
                              <span className="font-bold" style={{color:protoColor(f.l4?.protocol)}}>{f.l4?.protocol||'-'}</span>
                            </td>
                            <td className="p-2 text-slate-400 font-mono">{f.l4?.destination_port||'-'}</td>
                            <td className="p-2 text-slate-500 truncate max-w-[200px]" title={f.l7?.type||''}>
                              {f.l7?.type||'-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          );
        })()}

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
