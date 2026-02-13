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

          /* ── Hierarchical left-to-right layout (like Hubble UI) ── */
          const W=960, H=400;
          const tierMap = { 'world':0, 'mes-frontend':1, 'mes-api-service':2, 'postgres':3, 'kube-dns':3, 'hubble-relay':3, 'cilium-agent':3 };
          const tierLabels = ['External','Ingress','Application','Backend / Infra'];
          const tierColors = ['#f59e0b','#3b82f6','#06b6d4','#a855f7'];
          const tierX = [80, 290, 510, 760];

          /* group services into tiers */
          const tiers = [{},{},{},{}];
          filteredSvcs.forEach(s => {
            const t = tierMap[s.id] ?? 3;
            if (!tiers[t][s.id]) tiers[t][s.id] = s;
          });

          /* position nodes: evenly spaced vertically within each tier column */
          const svcPositions = {};
          const nodeW = 140, nodeH = 52;
          tiers.forEach((tier, ti) => {
            const svcs = Object.values(tier);
            const totalH = svcs.length * (nodeH + 20) - 20;
            const startY = (H - totalH) / 2;
            svcs.forEach((s, si) => {
              svcPositions[s.id] = {
                x: tierX[ti],
                y: startY + si * (nodeH + 20) + nodeH / 2,
                tier: ti,
              };
            });
          });

          const verdictColor = v => v==='FORWARDED' ? '#22c55e' : v==='DROPPED' ? '#ef4444' : '#f59e0b';
          const protoColor = p => p==='HTTP' ? '#3b82f6' : p==='TCP' ? '#06b6d4' : p==='UDP' ? '#a855f7' : p==='gRPC' ? '#f97316' : '#64748b';
          const typeIcon = t => t==='StatefulSet' ? 'DB' : t==='DaemonSet' ? 'DS' : t==='Pod' ? 'EXT' : 'SVC';

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

              {/* ── Service Map (hierarchical left→right) ── */}
              {hubbleView==='map' && (
                <div className="flex-1 min-h-0 bg-[#060a14] rounded-xl border border-slate-800 overflow-hidden relative mb-3" style={{minHeight:'360px'}}>
                  {filteredSvcs.length===0 ? (
                    <div className="flex items-center justify-center h-full text-slate-600">Loading service map...</div>
                  ) : (
                    <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} className="select-none">
                      <defs>
                        <marker id="arrow-fwd" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                          <polygon points="0 0, 8 3, 0 6" fill="#22c55e" opacity="0.8"/>
                        </marker>
                        <marker id="arrow-drop" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                          <polygon points="0 0, 8 3, 0 6" fill="#ef4444" opacity="0.8"/>
                        </marker>
                        <filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                        <filter id="shadow"><feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.4"/></filter>
                      </defs>

                      {/* subtle grid */}
                      {Array.from({length:20},(_,i)=><line key={`gx${i}`} x1={i*50} y1="0" x2={i*50} y2={H} stroke="#1e293b" strokeWidth="0.3" opacity="0.3"/>)}
                      {Array.from({length:10},(_,i)=><line key={`gy${i}`} x1="0" y1={i*50} x2={W} y2={i*50} stroke="#1e293b" strokeWidth="0.3" opacity="0.3"/>)}

                      {/* tier column headers */}
                      {tierLabels.map((label, i) => (
                        <g key={`tier-${i}`}>
                          <rect x={tierX[i]-10} y={8} width={nodeW+20} height={18} rx="4"
                            fill={`${tierColors[i]}10`} stroke={`${tierColors[i]}30`} strokeWidth="0.5"/>
                          <text x={tierX[i]+nodeW/2} y={20} fill={tierColors[i]} fontSize="8" fontWeight="700"
                            textAnchor="middle" opacity="0.8">{label}</text>
                        </g>
                      ))}

                      {/* tier column lines */}
                      {tierX.map((x, i) => (
                        <line key={`tl-${i}`} x1={x+nodeW/2} y1={30} x2={x+nodeW/2} y2={H-10}
                          stroke={tierColors[i]} strokeWidth="0.5" opacity="0.06" strokeDasharray="4 4"/>
                      ))}

                      {/* connections (smooth horizontal bezier curves) */}
                      {filteredConns.map((c, i) => {
                        const sp = svcPositions[c.source]; const tp = svcPositions[c.target];
                        if(!sp||!tp) return null;
                        const hasDropped = c.dropped_count > 0;
                        const strokeW = Math.min(3.5, 1 + Math.log1p(c.total_count)*0.6);
                        const clr = hasDropped ? '#ef4444' : '#22c55e';
                        /* horizontal bezier: source right edge → target left edge */
                        const sx = sp.x + nodeW + 2, sy = sp.y;
                        const tx = tp.x - 2, ty = tp.y;
                        const cpOffset = Math.abs(tx-sx)*0.4;
                        const path = `M${sx},${sy} C${sx+cpOffset},${sy} ${tx-cpOffset},${ty} ${tx},${ty}`;
                        const midX = (sx+tx)/2, midY = (sy+ty)/2;
                        return (
                          <g key={`conn-${i}`}>
                            {/* glow underline */}
                            <path d={path} fill="none" stroke={clr} strokeWidth={strokeW+3} opacity="0.06"/>
                            {/* main line */}
                            <path d={path} fill="none" stroke={clr} strokeWidth={strokeW} opacity="0.6"
                              markerEnd={hasDropped ? 'url(#arrow-drop)' : 'url(#arrow-fwd)'}
                              strokeDasharray={hasDropped ? '6 4' : 'none'}>
                              {!hasDropped && <animate attributeName="stroke-dashoffset" values="20;0" dur="1.5s" repeatCount="indefinite"/>}
                            </path>
                            {/* label pill */}
                            <rect x={midX-28} y={midY-8} width="56" height="16" rx="8"
                              fill="#0f172a" stroke={`${clr}40`} strokeWidth="0.5" opacity="0.9"/>
                            <text x={midX} y={midY+3} fill={clr} fontSize="7" fontWeight="600" textAnchor="middle" opacity="0.9">
                              {c.protocol}:{c.port} ({c.total_count})
                            </text>
                          </g>
                        );
                      })}

                      {/* service nodes (rounded rectangles) */}
                      {filteredSvcs.map(s => {
                        const pos = svcPositions[s.id]; if(!pos) return null;
                        const isSelected = selectedSvc===s.id;
                        const hasDropped = s.dropped > 0;
                        const tc = tierColors[pos.tier] || '#64748b';
                        const nodeColor = hasDropped ? '#ef4444' : tc;
                        const nx = pos.x, ny = pos.y - nodeH/2;
                        return (
                          <g key={s.id} onClick={()=>setSelectedSvc(isSelected?null:s.id)} style={{cursor:'pointer'}}>
                            {/* selection highlight */}
                            {isSelected && (
                              <rect x={nx-4} y={ny-4} width={nodeW+8} height={nodeH+8} rx="14"
                                fill="none" stroke={nodeColor} strokeWidth="2" opacity="0.4">
                                <animate attributeName="opacity" values="0.4;0.15;0.4" dur="2s" repeatCount="indefinite"/>
                              </rect>
                            )}
                            {/* card shadow */}
                            <rect x={nx} y={ny} width={nodeW} height={nodeH} rx="10"
                              fill="#0c1222" filter="url(#shadow)"/>
                            {/* card body */}
                            <rect x={nx} y={ny} width={nodeW} height={nodeH} rx="10"
                              fill={isSelected ? `${nodeColor}15` : '#0f172a'}
                              stroke={isSelected ? nodeColor : '#1e293b'} strokeWidth={isSelected ? 1.5 : 1}/>
                            {/* left color bar */}
                            <rect x={nx} y={ny} width="4" height={nodeH} rx="2"
                              fill={nodeColor} opacity={isSelected ? 1 : 0.6}/>
                            {/* type badge */}
                            <rect x={nx+12} y={ny+8} width="26" height="14" rx="4"
                              fill={`${nodeColor}20`} stroke={`${nodeColor}40`} strokeWidth="0.5"/>
                            <text x={nx+25} y={ny+18} fill={nodeColor} fontSize="7" fontWeight="800" textAnchor="middle">
                              {typeIcon(s.type)}
                            </text>
                            {/* service name */}
                            <text x={nx+44} y={ny+18} fill="#e2e8f0" fontSize="9" fontWeight="700">
                              {s.name.length > 16 ? s.name.slice(0,14)+'..' : s.name}
                            </text>
                            {/* namespace + protocol */}
                            <text x={nx+12} y={ny+33} fill="#475569" fontSize="7">
                              {s.namespace}
                            </text>
                            <text x={nx+12} y={ny+43} fill="#64748b" fontSize="7">
                              {s.protocol}:{s.port}
                            </text>
                            {/* traffic counters on right side */}
                            <text x={nx+nodeW-8} y={ny+18} fill="#4ade80" fontSize="7" fontWeight="600" textAnchor="end">
                              {s.forwarded > 0 ? `${s.forwarded}` : ''}
                            </text>
                            {s.dropped > 0 && (
                              <text x={nx+nodeW-8} y={ny+29} fill="#f87171" fontSize="7" fontWeight="600" textAnchor="end">
                                {s.dropped}
                              </text>
                            )}
                            <text x={nx+nodeW-8} y={ny+43} fill="#334155" fontSize="6" textAnchor="end">
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
                      <div className="absolute top-3 right-3 w-60 bg-[#0c1222]/95 border border-slate-700/50 rounded-xl p-4 backdrop-blur-md shadow-2xl">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <div className="text-white font-bold text-xs">{s.name}</div>
                            <div className="text-slate-500 text-[9px] mt-0.5">{s.namespace} / {s.type}</div>
                          </div>
                          <button onClick={()=>setSelectedSvc(null)} className="text-slate-600 hover:text-white text-xs w-5 h-5 flex items-center justify-center rounded hover:bg-slate-800">✕</button>
                        </div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[10px]">
                          <span className="text-slate-500">IP</span><span className="text-blue-400 font-mono text-right">{s.ip}</span>
                          <span className="text-slate-500">Protocol</span><span className="text-right" style={{color:protoColor(s.protocol)}}>{s.protocol}:{s.port}</span>
                          <span className="text-slate-500">Traffic In</span><span className="text-emerald-400 text-right font-bold">{s.traffic_in}</span>
                          <span className="text-slate-500">Traffic Out</span><span className="text-blue-400 text-right font-bold">{s.traffic_out}</span>
                          <span className="text-slate-500">Forwarded</span><span className="text-emerald-400 text-right">{s.forwarded}</span>
                          <span className="text-slate-500">Dropped</span><span className="text-red-400 text-right">{s.dropped}</span>
                        </div>
                        {relatedConns.length>0 && (
                          <div className="mt-3 pt-3 border-t border-slate-800/50">
                            <div className="text-[9px] text-slate-500 uppercase font-bold mb-1.5">Connections</div>
                            {relatedConns.slice(0,6).map((c,i)=>(
                              <div key={i} className="flex items-center gap-1 text-[9px] mb-1 py-0.5">
                                <span className="text-blue-400 truncate max-w-[70px]">{c.source}</span>
                                <span className="text-slate-700 flex-shrink-0">→</span>
                                <span className="text-purple-400 truncate max-w-[70px]">{c.target}</span>
                                <span className="ml-auto flex-shrink-0 font-bold" style={{color: c.dropped_count>0?'#ef4444':'#22c55e'}}>{c.total_count}</span>
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
