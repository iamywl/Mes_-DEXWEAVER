import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Keycloak from 'keycloak-js';

axios.defaults.baseURL = import.meta.env.VITE_API_URL || '';

/* ── Keycloak 설정 ───────────────────────────────────────── */
const KC_URL = import.meta.env.VITE_KC_URL || `http://${window.location.hostname}:30080`;
const KC_REALM = 'mes-realm';
const KC_CLIENT = 'mes-frontend';

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
const Input = React.forwardRef((props, ref) => <input ref={ref} {...props} className={`bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs ${props.className||''}`} />);
const Btn = ({children,...p}) => <button {...p} className={`bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-xs ${p.className||''}`}>{children}</button>;
const FilterBar = ({children}) => (
  <div className="flex items-center gap-3 mb-3 flex-wrap bg-[#0f172a]/60 px-3 py-2 rounded-xl border border-slate-800/50">
    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mr-1">Filter</span>
    {children}
  </div>
);
const FilterSelect = ({label, value, onChange, options}) => (
  <div className="flex items-center gap-1.5">
    <span className="text-[10px] text-slate-500">{label}</span>
    <select value={value} onChange={e=>onChange(e.target.value)}
      className="bg-[#0f172a] border border-slate-700 px-2 py-1 rounded text-white text-[11px]">
      {options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
);
const FilterSearch = ({value, onChange, placeholder='Search...'}) => (
  <input placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}
    className="bg-[#0f172a] border border-slate-700 px-3 py-1 rounded text-white text-[11px] w-48 ml-auto" />
);
const FilterCount = ({total, filtered}) => (
  <span className="text-[10px] text-slate-600 ml-2">
    {filtered < total ? <>{filtered} / {total}</> : total} rows
  </span>
);
const Modal = ({open, onClose, title, children}) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[#1e293b] rounded-2xl border border-slate-700 p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={e=>e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-white font-bold text-sm">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-lg cursor-pointer">&times;</button>
        </div>
        {children}
      </div>
    </div>
  );
};
const Select = ({value, onChange, options, className='', ...rest}) => (
  <select value={value} onChange={e=>onChange(e.target.value)} {...rest}
    className={`bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs ${className}`}>
    {options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
);
const FormRow = ({label, children}) => (
  <div className="mb-3">
    <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1">{label}</label>
    {children}
  </div>
);
const BtnSuccess = ({children,...p}) => <button {...p} className={`bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-bold text-xs cursor-pointer ${p.className||''}`}>{children}</button>;

/* ── main app ──────────────────────────────────────────── */
const App = () => {
  /* ── 인증 상태 (자체 로그인 우선, Keycloak fallback) ───── */
  const [authReady, setAuthReady] = useState(false);
  const [authUser, setAuthUser] = useState(null);  // {id, name, role, token}
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [userPerms, setUserPerms] = useState(null); // [{menu, read, write}, ...]
  const kcRef = useRef(null);

  const [menu, setMenu] = useState('DASHBOARD');
  const [db, setDb] = useState({ items:[], bom:[], plans:[], flows:[], pods:[], logs:'', infra:{} });
  const [extra, setExtra] = useState({});
  const [selPod, setSelPod] = useState('');
  const [topology, setTopology] = useState({ nodes:[], edges:[] });
  const [topologyView, setTopologyView] = useState('list');

  /* ── table filter state ─────────────────────────────── */
  const [tf, setTf] = useState({
    items: { search:'', category:'ALL', status:'ALL' },
    bom: { search:'', parent:'ALL' },
    proc: { search:'' },
    routing: { search:'' },
    equips: { search:'', status:'ALL', process:'ALL' },
    plans: { search:'', status:'ALL', priority:'ALL' },
    wo: { search:'', status:'ALL' },
    quality: { search:'' },
    inv: { search:'', status:'ALL' },
    k8s: { search:'', status:'ALL' },
  });
  const setFilter = (table, field, val) => setTf(prev=>({...prev,[table]:{...prev[table],[field]:val}}));

  /* ── modal & toast state ────────────────────────────── */
  const [modal, setModal] = useState({ type: null, data: {} });
  const openModal = async (type, data={}) => {
    setModalRoutes([{seq:1, process_code:'', cycle_time:0}]);
    setModalChecks([{name:'', type:'NUMERIC', std:0, min:0, max:0, unit:''}]);
    setModalResults([{check_name:'', value:0}]);
    setModalSelUser(''); setModalPerms([]);
    setModalSchedule(null); setModalSelPlans([]);
    setModal({ type, data });
    try {
      const needs = { item:['items'], bom:['items'], process:['equips'], routing:['items','procs'], equipment:['procs'],
        equip_status:['equips'], plan:['items'], work_order:['plans','equips'], work_result:['wo'],
        quality_std:['items'], inspection:['items'], inv_in:['inv'], inv_out:['inv'], inv_move:['inv'],
        schedule_optimize:['plans'], permissions:['users'] };
      const n = needs[type]||[];
      if (n.includes('items') && !(extra.itemList||[]).length) { const r=await axios.get('/api/items?size=100'); setExtra(p=>({...p,itemList:r.data.items||[]})); }
      if (n.includes('procs') && !(extra.processList||[]).length) { const r=await axios.get('/api/processes'); setExtra(p=>({...p,processList:r.data.processes||[]})); }
      if (n.includes('equips') && !(extra.equips||[]).length) { const r=await axios.get('/api/equipments'); setExtra(p=>({...p,equips:r.data.equipments||[]})); }
      if (n.includes('plans') && !(extra.planList||[]).length) { const r=await axios.get('/api/plans'); setExtra(p=>({...p,planList:r.data.plans||[]})); }
      if (n.includes('wo') && !(extra.woList||[]).length) { const r=await axios.get('/api/work-orders'); setExtra(p=>({...p,woList:r.data.orders||[]})); }
      if (n.includes('inv') && !(extra.invItems||[]).length) { const r=await axios.get('/api/inventory'); setExtra(p=>({...p,invItems:r.data.items||[]})); }
      if (n.includes('users') && !(extra.userList||[]).length) { const r=await axios.get('/api/auth/users'); setExtra(p=>({...p,userList:r.data.users||[]})); }
    } catch(e) { console.error('Modal data load error',e); }
  };
  const closeModal = () => setModal({ type: null, data: {} });
  const [toast, setToast] = useState(null);
  const showToast = (msg, ok=true) => { setToast({msg,ok}); setTimeout(()=>setToast(null), 3000); };

  /* ── modal-internal form state (lifted from IIFEs) ──── */
  const [modalRoutes, setModalRoutes] = useState([{seq:1, process_code:'', cycle_time:0}]);
  const [modalChecks, setModalChecks] = useState([{name:'', type:'NUMERIC', std:0, min:0, max:0, unit:''}]);
  const [modalResults, setModalResults] = useState([{check_name:'', value:0}]);
  const [modalSelUser, setModalSelUser] = useState('');
  const [modalPerms, setModalPerms] = useState([]);
  const [modalSchedule, setModalSchedule] = useState(null);
  const [modalSelPlans, setModalSelPlans] = useState([]);

  /* ── AI Center input refs (avoid document.getElementById) ── */
  const aiDemandRef = useRef(null);
  const aiDefTempRef = useRef(null);
  const aiDefPresRef = useRef(null);
  const aiDefSpeedRef = useRef(null);
  const aiDefHumRef = useRef(null);
  const aiFailEqRef = useRef(null);
  const aiFailVibRef = useRef(null);
  const aiFailTempRef = useRef(null);
  const aiFailCurRef = useRef(null);
  const lotTraceRef = useRef(null);

  const refreshPage = async (m) => {
    try {
      if (m==='ITEMS') { const r=await axios.get('/api/items?size=100'); setExtra(p=>({...p, itemList:r.data.items||[]})); }
      if (m==='BOM') { const [i,b,s]=await Promise.all([axios.get('/api/items?size=100'),axios.get('/api/bom'),axios.get('/api/bom/summary')]); setExtra(p=>({...p, itemList:i.data.items||[], bomEntries:b.data.entries||[], bomSummary:s.data||{}})); }
      if (m==='PROCESS') { const [i,pr,rs]=await Promise.all([axios.get('/api/items?size=100'),axios.get('/api/processes'),axios.get('/api/routings')]); setExtra(p=>({...p, itemList:i.data.items||[], processList:pr.data.processes||[], routingSummary:rs.data.routings||[]})); }
      if (m==='EQUIPMENT') { const r=await axios.get('/api/equipments'); setExtra(p=>({...p, equips:r.data.equipments||[]})); }
      if (m==='PLANS') { const r=await axios.get('/api/plans'); setExtra(p=>({...p, planList:r.data.plans||[]})); }
      if (m==='WORK_ORDER') { const r=await axios.get('/api/work-orders'); setExtra(p=>({...p, woList:r.data.orders||[]})); }
      if (m==='QUALITY') { const r=await axios.get('/api/quality/defects'); setExtra(p=>({...p, defects:r.data})); }
      if (m==='INVENTORY') { const r=await axios.get('/api/inventory'); setExtra(p=>({...p, invItems:r.data.items||[]})); }
    } catch(e) { console.error(e); }
  };

  /* ── BOM/Process page sub-tab state ──────────────────── */
  const [bomTab, setBomTab] = useState('list');
  const [procTab, setProcTab] = useState('master');

  /* ── Hubble network state ─────────────────────────── */
  const [hubbleFlows, setHubbleFlows] = useState([]);
  const [serviceMap, setServiceMap] = useState({ services:[], connections:[] });
  const [hubbleFilter, setHubbleFilter] = useState({ verdict:'ALL', protocol:'ALL', namespace:'ALL', search:'' });
  const [hubbleView, setHubbleView] = useState('map');
  const [selectedSvc, setSelectedSvc] = useState(null);
  const [flowPanelOpen, setFlowPanelOpen] = useState(true);

  /* ── 인증 초기화 (자체 JWT 우선, Keycloak fallback) ─── */
  const interceptorId = useRef(null);

  // 자체 로그인 처리
  const handleLogin = async (userId, password) => {
    setAuthLoading(true); setAuthError('');
    try {
      const r = await axios.post('/api/auth/login', { user_id: userId, password });
      if (r.data.error) { setAuthError(r.data.error); setAuthLoading(false); return; }
      const user = { id: r.data.user.id, name: r.data.user.name, role: r.data.user.role, token: r.data.token };
      setAuthUser(user);
      localStorage.setItem('mes_user', JSON.stringify(user));
      // 토큰 인터셉터 설정
      if (interceptorId.current !== null) axios.interceptors.request.eject(interceptorId.current);
      interceptorId.current = axios.interceptors.request.use(config => {
        config.headers.Authorization = `Bearer ${user.token}`;
        return config;
      });
      setAuthReady(true);
      loadUserPerms(user.id);
    } catch (e) { setAuthError('Login failed. Check server connection.'); }
    setAuthLoading(false);
  };

  // 자체 회원가입 처리
  const handleRegister = async (formData) => {
    setAuthLoading(true); setAuthError('');
    try {
      const r = await axios.post('/api/auth/register', formData);
      if (r.data.error) { setAuthError(r.data.error); setAuthLoading(false); return; }
      setAuthError(''); setAuthMode('login');
      setAuthError(r.data.message || 'Registration successful! Admin approval required before login.');
    } catch (e) { setAuthError('Registration failed. Check server connection.'); }
    setAuthLoading(false);
  };

  // 로그아웃
  const handleLogout = () => {
    setAuthUser(null); setAuthReady(false); setAuthMode('login'); setAuthError('');
    localStorage.removeItem('mes_user');
    if (interceptorId.current !== null) { axios.interceptors.request.eject(interceptorId.current); interceptorId.current = null; }
    const kc = kcRef.current;
    if (kc?.authenticated) { try { kc.logout({ redirectUri: window.location.origin }); } catch {} }
  };

  // 초기화: localStorage에서 세션 복원 또는 Keycloak 시도
  useEffect(() => {
    const saved = localStorage.getItem('mes_user');
    if (saved) {
      try {
        const user = JSON.parse(saved);
        setAuthUser(user);
        if (interceptorId.current !== null) axios.interceptors.request.eject(interceptorId.current);
        interceptorId.current = axios.interceptors.request.use(config => {
          config.headers.Authorization = `Bearer ${user.token}`;
          return config;
        });
        setAuthReady(true);
        // Load permissions for restored session
        axios.get(`/api/auth/permissions/${user.id}`).then(r => setUserPerms(r.data.permissions || [])).catch(() => setUserPerms([]));
        return;
      } catch {}
    }
    // Keycloak fallback 시도
    try {
      const kc = new Keycloak({ url: KC_URL, realm: KC_REALM, clientId: KC_CLIENT });
      kcRef.current = kc;
      kc.init({ onLoad: 'check-sso', checkLoginIframe: false, pkceMethod: 'S256' })
        .then(authenticated => {
          if (authenticated) {
            const user = {
              id: kc.tokenParsed?.preferred_username || 'kc-user',
              name: kc.tokenParsed?.preferred_username || kc.tokenParsed?.name || 'User',
              role: (kc.tokenParsed?.realm_access?.roles || []).includes('admin') ? 'admin' : 'worker',
              token: kc.token,
            };
            setAuthUser(user);
            if (interceptorId.current !== null) axios.interceptors.request.eject(interceptorId.current);
            interceptorId.current = axios.interceptors.request.use(async config => {
              try { await kc.updateToken(30); } catch {}
              config.headers.Authorization = `Bearer ${kc.token}`;
              return config;
            });
            setAuthReady(true);
          }
          // Keycloak 미인증이면 자체 로그인 화면 표시 (authReady=false 유지)
        })
        .catch(() => {
          // Keycloak 서버 없음 → 자체 로그인 화면 표시
        });
    } catch {
      // Keycloak 라이브러리 에러 → 자체 로그인 화면 표시
    }
  }, []);

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
        if (menu==='DASHBOARD') {
          const r = await axios.get('/api/dashboard/production');
          setExtra(prev=>({...prev, prodDashboard: r.data}));
        }
        if (menu==='ITEMS') {
          const r = await axios.get('/api/items?size=100');
          setExtra(prev=>({...prev, itemList: r.data.items||[]}));
        }
        if (menu==='BOM') {
          const [items, bomList, bomSummary] = await Promise.all([
            axios.get('/api/items?size=100'),
            axios.get('/api/bom'),
            axios.get('/api/bom/summary'),
          ]);
          setExtra(prev=>({...prev,
            itemList: items.data.items||[],
            bomEntries: bomList.data.entries||[],
            bomSummary: bomSummary.data||{},
            bomTree: null, whereUsed: null,
          }));
        }
        if (menu==='PROCESS') {
          const [items, procs, routingSummary] = await Promise.all([
            axios.get('/api/items?size=100'),
            axios.get('/api/processes'),
            axios.get('/api/routings'),
          ]);
          setExtra(prev=>({...prev,
            itemList: items.data.items||[],
            processList: procs.data.processes||[],
            routingSummary: routingSummary.data.routings||[],
            routingData: null,
          }));
        }
        if (menu==='EQUIPMENT') {
          const [r, st] = await Promise.all([
            axios.get('/api/equipments'),
            axios.get('/api/equipments/status').catch(()=>({data:{equipments:[]}})),
          ]);
          const equips = r.data.equipments||[];
          const statusMap = Object.fromEntries((st.data.equipments||[]).map(s=>[s.equip_code, s]));
          setExtra(prev=>({...prev, equips: equips.map(e=>({...e, uptime_today: (statusMap[e.equip_code]||{}).uptime_today||0, current_job: (statusMap[e.equip_code]||{}).current_job||null}))}));
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

  /* ── permission helpers ────────────────────────────── */
  const loadUserPerms = async (userId) => {
    try {
      const r = await axios.get(`/api/auth/permissions/${userId}`);
      setUserPerms(r.data.permissions || []);
    } catch { setUserPerms([]); }
  };
  const canRead = (menuId) => {
    if (!authUser) return false;
    if (authUser.role === 'admin') return true;
    if (!userPerms) return true; // permissions not loaded yet, show all
    const p = userPerms.find(x => x.menu === menuId);
    return p ? p.read : false;
  };
  const canWrite = (menuId) => {
    if (!authUser) return false;
    if (authUser.role === 'admin') return true;
    if (!userPerms) return false;
    const p = userPerms.find(x => x.menu === menuId);
    return p ? p.write : false;
  };

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

  /* ── 로그인/회원가입 화면 (미인증 상태) ────────────── */
  if (!authReady) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#020617]">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-black text-blue-500 tracking-tighter italic">KNU MES v5.2</h1>
            <p className="text-slate-600 text-xs mt-1">Manufacturing Execution System</p>
          </div>
          <div className="bg-[#1e293b] rounded-2xl border border-slate-700 p-6">
            {/* 탭 전환 */}
            <div className="flex mb-6 border-b border-slate-700">
              <button onClick={()=>{setAuthMode('login');setAuthError('');}}
                className={`flex-1 py-2 text-xs font-bold transition-all cursor-pointer ${authMode==='login'?'text-blue-400 border-b-2 border-blue-400':'text-slate-500 hover:text-slate-300'}`}>
                Login
              </button>
              <button onClick={()=>{setAuthMode('register');setAuthError('');}}
                className={`flex-1 py-2 text-xs font-bold transition-all cursor-pointer ${authMode==='register'?'text-emerald-400 border-b-2 border-emerald-400':'text-slate-500 hover:text-slate-300'}`}>
                Register
              </button>
            </div>

            {authError && (
              <div className={`text-xs p-2 rounded-lg mb-4 ${authError.includes('successful')?'bg-emerald-900/50 text-emerald-300 border border-emerald-800':'bg-red-900/50 text-red-300 border border-red-800'}`}>
                {authError}
              </div>
            )}

            {/* 로그인 폼 */}
            {authMode==='login' && (
              <form onSubmit={e=>{e.preventDefault();const fd=new FormData(e.target);handleLogin(fd.get('user_id'),fd.get('password'));}}>
                <FormRow label="User ID"><Input name="user_id" required className="w-full" placeholder="Enter your ID" autoFocus/></FormRow>
                <FormRow label="Password"><Input name="password" type="password" required className="w-full" placeholder="Enter password"/></FormRow>
                <BtnSuccess type="submit" className="w-full mt-2" disabled={authLoading}>
                  {authLoading ? 'Logging in...' : 'Login'}
                </BtnSuccess>
              </form>
            )}

            {/* 회원가입 폼 */}
            {authMode==='register' && (
              <form onSubmit={e=>{
                e.preventDefault();const fd=new FormData(e.target);
                if(fd.get('password')!==fd.get('password_confirm')){setAuthError('Passwords do not match');return;}
                handleRegister({user_id:fd.get('user_id'),password:fd.get('password'),name:fd.get('name'),email:fd.get('email'),role:fd.get('role')});
              }}>
                <FormRow label="User ID"><Input name="user_id" required className="w-full" placeholder="Choose a user ID" autoFocus/></FormRow>
                <FormRow label="Password"><Input name="password" type="password" required className="w-full" placeholder="Choose a password"/></FormRow>
                <FormRow label="Confirm Password"><Input name="password_confirm" type="password" required className="w-full" placeholder="Confirm password"/></FormRow>
                <FormRow label="Name"><Input name="name" required className="w-full" placeholder="Full name"/></FormRow>
                <FormRow label="Email"><Input name="email" type="email" className="w-full" placeholder="email@example.com"/></FormRow>
                <FormRow label="Role">
                  <Select name="role" onChange={()=>{}} value="" options={[{value:'worker',label:'Worker'},{value:'manager',label:'Manager'},{value:'viewer',label:'Viewer'}]} className="w-full"/>
                </FormRow>
                <BtnSuccess type="submit" className="w-full mt-2" disabled={authLoading}>
                  {authLoading ? 'Registering...' : 'Register'}
                </BtnSuccess>
              </form>
            )}
          </div>
          <p className="text-center text-slate-700 text-[10px] mt-4">Keycloak SSO is also supported when available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#020617] text-slate-400 font-sans text-[11px]">
      {/* sidebar */}
      <aside className="w-52 bg-[#0f172a] border-r border-slate-800 p-4 space-y-0.5 overflow-y-auto flex flex-col">
        <button onClick={()=>setMenu('DASHBOARD')} className="text-left mb-6 group cursor-pointer">
          <h1 className="text-lg font-black text-blue-500 tracking-tighter italic group-hover:text-blue-400 transition-colors">KNU MES v5.2</h1>
          <div className="text-[9px] text-slate-600 group-hover:text-slate-500 transition-colors">Manufacturing Execution System</div>
        </button>
        {menus.filter(m => canRead(m.id)).map(m=>(
          <button key={m.id} onClick={()=>setMenu(m.id)}
            className={`w-full text-left px-3 py-1.5 rounded-lg transition-all text-xs
              ${menu===m.id ? 'bg-blue-600 text-white font-bold':'hover:bg-slate-800'}`}>
            {m.label}
          </button>
        ))}
        {/* user info + logout */}
        <div className="mt-auto pt-4 border-t border-slate-800">
          <div className="px-2 py-2 text-[10px]">
            <div className="text-white font-bold truncate">{authUser?.name || 'User'}</div>
            <div className="text-slate-500">{authUser?.role || 'user'}</div>
          </div>
          {authUser?.role==='admin' && (
            <>
              <button onClick={()=>openModal('register')}
                className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-emerald-400 hover:bg-emerald-500/10 transition-all font-bold cursor-pointer">
                + Register User
              </button>
              <button onClick={async()=>{try{const r=await axios.get('/api/auth/users');setExtra(p=>({...p,userList:r.data.users||[]}));}catch{}openModal('user_approve');}}
                className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-amber-400 hover:bg-amber-500/10 transition-all font-bold cursor-pointer">
                User Approval
              </button>
              <button onClick={async()=>{try{const r=await axios.get('/api/auth/users');setExtra(p=>({...p,userList:r.data.users||[]}));}catch{}openModal('permissions');}}
                className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-purple-400 hover:bg-purple-500/10 transition-all font-bold cursor-pointer">
                Permissions
              </button>
            </>
          )}
          <button onClick={handleLogout}
            className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-all font-bold cursor-pointer">
            Logout
          </button>
        </div>
      </aside>

      {/* main content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <h2 className="text-xl font-bold text-white mb-6 border-b border-slate-800 pb-3">
          {menus.find(m=>m.id===menu)?.label || menu}
        </h2>

        {/* ── DASHBOARD ────────────────────────────────── */}
        {menu==='DASHBOARD' && (() => {
          const prod = extra.prodDashboard||{};
          const lines = prod.lines||[];
          const hourly = prod.hourly||[];
          const totalTarget = lines.reduce((s,l)=>s+l.target,0);
          const totalActual = lines.reduce((s,l)=>s+l.actual,0);
          const overallRate = totalTarget>0 ? (totalActual/totalTarget*100).toFixed(1) : 0;
          return (
          <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
              <Card title="Items" value={db.items?.length||0} />
              <Card title="CPU" value={db.infra.cpu||'0%'} color="text-slate-200" />
              <Card title="Memory" value={db.infra.mem||'0%'} color="text-purple-400" />
              <Card title="Pods" value={db.pods?.length||0} color="text-emerald-500" />
            </div>

            {/* REQ-020: Production Status Dashboard */}
            <div className="border-t border-slate-800 pt-4">
              <h3 className="text-white font-bold mb-4">Production Status (Today)</h3>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <Card title="Total Target" value={totalTarget} color="text-blue-400"/>
                <Card title="Total Actual" value={totalActual} color="text-emerald-400"/>
                <Card title="Achievement" value={`${overallRate}%`} color={overallRate>=90?'text-emerald-400':overallRate>=70?'text-amber-400':'text-red-400'}/>
              </div>
              {lines.length>0 && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-3">Line Status</h4>
                    {lines.map((l,i)=>(
                      <div key={i} className="bg-[#0f172a] p-3 rounded-xl border border-slate-800 mb-2">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-white font-bold text-xs">{l.line_id}</span>
                          <Badge v={l.status}/>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${l.rate>=0.9?'bg-emerald-500':l.rate>=0.7?'bg-amber-500':'bg-red-500'}`} style={{width:`${Math.min(l.rate*100,100)}%`}}/>
                          </div>
                          <span className="text-xs text-slate-400">{l.actual}/{l.target}</span>
                          <span className={`text-[10px] font-bold ${l.rate>=0.9?'text-emerald-400':l.rate>=0.7?'text-amber-400':'text-red-400'}`}>{(l.rate*100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-3">Hourly Output</h4>
                    <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                      {hourly.length>0 ? hourly.map((h,i)=>(
                        <div key={i} className="flex items-center gap-3 mb-1.5">
                          <span className="text-[10px] text-slate-500 w-8">{h.hour}:00</span>
                          <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 rounded-full" style={{width:`${(h.qty/Math.max(...hourly.map(x=>x.qty),1))*100}%`}}/>
                          </div>
                          <span className="text-blue-400 text-[10px] font-bold w-10 text-right">{h.qty}</span>
                        </div>
                      )) : <span className="text-slate-600 text-xs">No hourly data</span>}
                    </div>
                  </div>
                </div>
              )}
              {lines.length===0 && <div className="text-slate-600 text-xs bg-[#0f172a] p-6 rounded-xl border border-slate-800 text-center">No production data for today</div>}
            </div>
          </div>
          );
        })()}

        {/* ── ITEMS (FN-004~007) ───────────────────────── */}
        {menu==='ITEMS' && (() => {
          const allItems = extra.itemList||[];
          const categories = [...new Set(allItems.map(i=>i.category).filter(Boolean))];
          const filtered = allItems.filter(i => {
            if (tf.items.search) {
              const s = tf.items.search.toLowerCase();
              if (!(i.item_code||'').toLowerCase().includes(s) && !(i.name||'').toLowerCase().includes(s) && !(i.spec||'').toLowerCase().includes(s)) return false;
            }
            if (tf.items.category!=='ALL' && i.category!==tf.items.category) return false;
            if (tf.items.status!=='ALL') {
              const st = i.stock<=0?'OUT':i.stock<i.safety_stock?'LOW':'NORMAL';
              if (st!==tf.items.status) return false;
            }
            return true;
          });
          return (
            <div className="space-y-4">
              {canWrite('ITEMS') && <div className="flex justify-end gap-2">
                <BtnSuccess onClick={()=>openModal('item')}>+ New Item</BtnSuccess>
              </div>}
              <FilterBar>
                <FilterSelect label="Category" value={tf.items.category} onChange={v=>setFilter('items','category',v)}
                  options={[{value:'ALL',label:'All'}, ...categories.map(c=>({value:c,label:c}))]} />
                <FilterSelect label="Status" value={tf.items.status} onChange={v=>setFilter('items','status',v)}
                  options={[{value:'ALL',label:'All'},{value:'NORMAL',label:'Normal'},{value:'LOW',label:'Low Stock'},{value:'OUT',label:'Out'}]} />
                <FilterSearch value={tf.items.search} onChange={v=>setFilter('items','search',v)} placeholder="Search code, name, spec..." />
                <FilterCount total={allItems.length} filtered={filtered.length} />
              </FilterBar>
              <Table cols={['Code','Name','Category','Unit','Spec','Stock','Safety','Status','Actions']}
                rows={filtered}
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
                    <td className="p-3">
                      <div className="flex gap-1">
                        <button onClick={()=>openModal('item_edit',{item:i})} className="text-blue-400 hover:text-blue-300 text-[10px] font-bold cursor-pointer">Edit</button>
                        <button onClick={async()=>{if(confirm(`Delete ${i.item_code}?`)){try{await axios.delete(`/api/items/${i.item_code}`);showToast(`${i.item_code} deleted`);refreshPage('ITEMS');}catch(e){showToast('Delete failed',false);}}}} className="text-red-400 hover:text-red-300 text-[10px] font-bold cursor-pointer">Del</button>
                      </div>
                    </td>
                  </tr>
                )} />
            </div>
          );
        })()}

        {/* ── BOM (FN-008~009) — Enhanced with tabs ────── */}
        {menu==='BOM' && (() => {
          const summary = extra.bomSummary||{};
          const allEntries = extra.bomEntries||[];
          const parents = [...new Set(allEntries.map(e=>e.parent_item))];
          const filteredBom = allEntries.filter(e => {
            if (tf.bom.search) {
              const s = tf.bom.search.toLowerCase();
              if (!(e.parent_item||'').toLowerCase().includes(s) && !(e.parent_name||'').toLowerCase().includes(s)
                && !(e.child_item||'').toLowerCase().includes(s) && !(e.child_name||'').toLowerCase().includes(s)) return false;
            }
            if (tf.bom.parent!=='ALL' && e.parent_item!==tf.bom.parent) return false;
            return true;
          });
          return (
          <div className="space-y-4">
            {/* Summary cards */}
            <div className="grid grid-cols-4 gap-3">
              <Card title="BOM Entries" value={summary.total_entries||0} />
              <Card title="Parent Items" value={summary.parent_count||0} color="text-purple-400" />
              <Card title="Components" value={summary.child_count||0} color="text-amber-400" />
              <Card title="Avg Depth" value={summary.parent_count ? Math.ceil((summary.total_entries||0)/(summary.parent_count||1)) : 0} color="text-emerald-400" />
            </div>

            {/* Tab bar */}
            <div className="flex items-center gap-1 border-b border-slate-800 pb-1">
              {[{id:'list',label:'BOM List'},{id:'explode',label:'BOM Explode'},{id:'where',label:'Where-Used'}].map(t=>(
                <button key={t.id} onClick={()=>setBomTab(t.id)}
                  className={`px-4 py-1.5 rounded-t-lg text-xs font-bold transition-all
                    ${bomTab===t.id ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white hover:bg-slate-800'}`}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* BOM List tab */}
            {bomTab==='list' && (
              <div className="space-y-3">
                {canWrite('BOM') && <div className="flex justify-end gap-2">
                  <BtnSuccess onClick={()=>openModal('bom')}>+ New BOM</BtnSuccess>
                </div>}
                <FilterBar>
                  <FilterSelect label="Parent" value={tf.bom.parent} onChange={v=>setFilter('bom','parent',v)}
                    options={[{value:'ALL',label:'All Parents'}, ...parents.map(p=>({value:p,label:p}))]} />
                  <FilterSearch value={tf.bom.search} onChange={v=>setFilter('bom','search',v)} placeholder="Search parent, child..." />
                  <FilterCount total={allEntries.length} filtered={filteredBom.length} />
                </FilterBar>
                <Table cols={['Parent Code','Parent Name','Child Code','Child Name','Category','Qty/Unit','Loss Rate','Actions']}
                  rows={filteredBom}
                  renderRow={(e,k)=>(
                    <tr key={k}>
                      <td className="p-3 font-mono text-purple-400">{e.parent_item}</td>
                      <td className="p-3 text-white font-bold">{e.parent_name}</td>
                      <td className="p-3 font-mono text-blue-400">{e.child_item}</td>
                      <td className="p-3 text-white">{e.child_name}</td>
                      <td className="p-3"><Badge v={e.child_category}/></td>
                      <td className="p-3 text-amber-400 font-bold">{e.qty_per_unit}</td>
                      <td className="p-3 text-slate-500">{e.loss_rate}%</td>
                      <td className="p-3">
                        <div className="flex gap-1">
                          <button onClick={()=>openModal('bom_edit',{bom:e})} className="text-blue-400 hover:text-blue-300 text-[10px] font-bold cursor-pointer">Edit</button>
                          <button onClick={async()=>{if(confirm(`Delete BOM ${e.parent_item}→${e.child_item}?`)){try{const r=await axios.delete(`/api/bom/${e.bom_id}`);if(r.data.error){showToast(r.data.error,false);}else{showToast('BOM entry deleted');refreshPage('BOM');}}catch(err){showToast('Delete failed',false);}}}} className="text-red-400 hover:text-red-300 text-[10px] font-bold cursor-pointer">Del</button>
                        </div>
                      </td>
                    </tr>
                  )} />
                {/* Top parents chart */}
                {(summary.top_parents||[]).length > 0 && (
                  <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                    <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-3">Top Parent Items by Component Count</h4>
                    {(summary.top_parents||[]).map((p,i)=>(
                      <div key={i} className="flex items-center gap-3 mb-2">
                        <span className="text-xs w-28 text-purple-400 font-mono truncate">{p.item_code}</span>
                        <span className="text-xs w-32 text-white truncate">{p.name}</span>
                        <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-purple-500 rounded-full" style={{width:`${(p.component_count/Math.max(...(summary.top_parents||[]).map(x=>x.component_count),1))*100}%`}}/>
                        </div>
                        <span className="text-purple-400 text-[10px] font-bold w-8 text-right">{p.component_count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* BOM Explode tab */}
            {bomTab==='explode' && (
              <div className="space-y-4">
                <div className="flex gap-2 items-center">
                  <select className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs"
                    onChange={async e => {
                      if(!e.target.value) { setExtra(prev=>({...prev, bomTree:null})); return; }
                      const r = await axios.get(`/api/bom/explode/${e.target.value}`);
                      setExtra(prev=>({...prev, bomTree:r.data}));
                    }}>
                    <option value="">Select item to explode BOM</option>
                    {(extra.itemList||[]).filter(i=>parents.includes(i.item_code)).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
                  </select>
                </div>
                {extra.bomTree && (
                  <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="text-white font-bold">BOM Tree: {extra.bomTree.item_code}</h3>
                      <span className="text-[10px] text-slate-500">
                        {(function countNodes(nodes) { return nodes.reduce((s,n) => s + 1 + countNodes(n.children||[]), 0); })(extra.bomTree.tree||[])} components
                      </span>
                    </div>
                    {(function renderTree(nodes, depth=0) {
                      return nodes.map((n,i)=>(
                        <div key={i}>
                          <div className="flex items-center gap-2 py-0.5 hover:bg-slate-800/30 rounded px-1" style={{paddingLeft:depth*24}}>
                            <span className="text-slate-600">{'└─'}</span>
                            <span className="text-blue-400 font-mono text-[11px]">{n.item_code}</span>
                            <span className="text-white text-xs">{n.item_name}</span>
                            <span className="text-amber-400 font-bold">x{n.required_qty}</span>
                            {n.loss_rate > 0 && <span className="text-red-400/60 text-[9px]">loss:{n.loss_rate}%</span>}
                            <span className="text-slate-700 text-[9px]">L{n.level}</span>
                          </div>
                          {n.children && renderTree(n.children, depth+1)}
                        </div>
                      ));
                    })(extra.bomTree.tree||[])}
                  </div>
                )}
              </div>
            )}

            {/* Where-Used tab */}
            {bomTab==='where' && (
              <div className="space-y-4">
                <div className="flex gap-2 items-center">
                  <select className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs"
                    onChange={async e => {
                      if(!e.target.value) { setExtra(prev=>({...prev, whereUsed:null})); return; }
                      const r = await axios.get(`/api/bom/where-used/${e.target.value}`);
                      setExtra(prev=>({...prev, whereUsed:r.data}));
                    }}>
                    <option value="">Select component to find parents</option>
                    {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
                  </select>
                </div>
                {extra.whereUsed && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <span className="text-white font-bold text-xs">Component: <span className="text-blue-400">{extra.whereUsed.item_code}</span></span>
                      <span className="text-slate-500 text-xs">Used in <span className="text-amber-400 font-bold">{extra.whereUsed.count}</span> parent items</span>
                    </div>
                    {extra.whereUsed.count > 0 ? (
                      <Table cols={['Parent Code','Parent Name','Category','Qty/Unit','Loss Rate']}
                        rows={extra.whereUsed.used_in}
                        renderRow={(p,k)=>(
                          <tr key={k}>
                            <td className="p-3 font-mono text-purple-400">{p.parent_item}</td>
                            <td className="p-3 text-white font-bold">{p.parent_name}</td>
                            <td className="p-3"><Badge v={p.parent_category}/></td>
                            <td className="p-3 text-amber-400 font-bold">{p.qty_per_unit}</td>
                            <td className="p-3 text-slate-500">{p.loss_rate}%</td>
                          </tr>
                        )} />
                    ) : (
                      <div className="bg-[#0f172a] p-6 rounded-xl border border-slate-800 text-center text-slate-500">
                        This item is not used as a component in any BOM.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
          );
        })()}

        {/* ── PROCESS / ROUTING (FN-010~012) — Enhanced ── */}
        {menu==='PROCESS' && (() => {
          const allProcs = extra.processList||[];
          const allRoutingSummary = extra.routingSummary||[];
          const filteredProcs = allProcs.filter(p => {
            if (tf.proc.search) {
              const s = tf.proc.search.toLowerCase();
              if (!(p.process_code||'').toLowerCase().includes(s) && !(p.name||'').toLowerCase().includes(s)
                && !(p.equip_name||'').toLowerCase().includes(s) && !(p.description||'').toLowerCase().includes(s)) return false;
            }
            return true;
          });
          const filteredRoutings = allRoutingSummary.filter(r => {
            if (tf.routing.search) {
              const s = tf.routing.search.toLowerCase();
              if (!(r.item_code||'').toLowerCase().includes(s) && !(r.item_name||'').toLowerCase().includes(s)) return false;
            }
            return true;
          });
          const totalStdTime = allProcs.reduce((s,p) => s + (p.std_time_min||0), 0);
          const runningEquip = allProcs.filter(p => p.equip_status==='RUNNING').length;
          return (
          <div className="space-y-4">
            {/* Summary cards */}
            <div className="grid grid-cols-4 gap-3">
              <Card title="Processes" value={allProcs.length} />
              <Card title="Routed Items" value={allRoutingSummary.length} color="text-purple-400" />
              <Card title="Avg Std Time" value={allProcs.length ? `${Math.round(totalStdTime/allProcs.length)}m` : '0m'} color="text-amber-400" />
              <Card title="Equip Online" value={`${runningEquip}/${allProcs.filter(p=>p.equip_code).length}`} color="text-emerald-400" />
            </div>

            {/* Tab bar */}
            <div className="flex items-center gap-1 border-b border-slate-800 pb-1">
              {[{id:'master',label:'Process Master'},{id:'routing',label:'Routing Viewer'},{id:'summary',label:'Routing Summary'}].map(t=>(
                <button key={t.id} onClick={()=>setProcTab(t.id)}
                  className={`px-4 py-1.5 rounded-t-lg text-xs font-bold transition-all
                    ${procTab===t.id ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white hover:bg-slate-800'}`}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Process Master tab */}
            {procTab==='master' && (
              <div className="space-y-3">
                {canWrite('PROCESS') && <div className="flex justify-end gap-2">
                  <BtnSuccess onClick={()=>openModal('process')}>+ New Process</BtnSuccess>
                </div>}
                <FilterBar>
                  <FilterSearch value={tf.proc.search} onChange={v=>setFilter('proc','search',v)} placeholder="Search code, name, equipment..." />
                  <FilterCount total={allProcs.length} filtered={filteredProcs.length} />
                </FilterBar>
                <Table cols={['Process Code','Name','Std Time','Description','Equipment','Equip Status','Actions']}
                  rows={filteredProcs}
                  renderRow={(p,k)=>(
                    <tr key={k}>
                      <td className="p-3 font-mono text-blue-400">{p.process_code}</td>
                      <td className="p-3 text-white font-bold">{p.name}</td>
                      <td className="p-3 text-amber-400 font-bold">{p.std_time_min} min</td>
                      <td className="p-3 text-slate-500 max-w-[200px] truncate">{p.description||'-'}</td>
                      <td className="p-3 text-purple-400">{p.equip_name||'-'} <span className="text-slate-600 text-[9px]">{p.equip_code||''}</span></td>
                      <td className="p-3">{p.equip_status ? <Badge v={p.equip_status}/> : <span className="text-slate-600">-</span>}</td>
                      <td className="p-3">
                        <div className="flex gap-1">
                          <button onClick={()=>openModal('process_edit',{proc:p})} className="text-blue-400 hover:text-blue-300 text-[10px] font-bold cursor-pointer">Edit</button>
                          <button onClick={async()=>{if(confirm(`Delete ${p.process_code}?`)){try{const r=await axios.delete(`/api/processes/${p.process_code}`);if(r.data.error){showToast(r.data.error,false);}else{showToast(`${p.process_code} deleted`);refreshPage('PROCESS');}}catch(err){showToast(err.response?.data?.error||'Delete failed',false);}}}} className="text-red-400 hover:text-red-300 text-[10px] font-bold cursor-pointer">Del</button>
                        </div>
                      </td>
                    </tr>
                  )} />
                {/* Process time chart */}
                <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                  <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-3">Standard Time Comparison</h4>
                  {allProcs.map((p,i)=>(
                    <div key={i} className="flex items-center gap-3 mb-2">
                      <span className="text-xs w-20 text-blue-400 font-mono">{p.process_code}</span>
                      <span className="text-xs w-32 text-white truncate">{p.name}</span>
                      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-amber-500 rounded-full" style={{width:`${(p.std_time_min/Math.max(...allProcs.map(x=>x.std_time_min),1))*100}%`}}/>
                      </div>
                      <span className="text-amber-400 text-[10px] font-bold w-12 text-right">{p.std_time_min}m</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Routing Viewer tab */}
            {procTab==='routing' && (
              <div className="space-y-4">
                <div className="flex gap-2 items-center">
                  {canWrite('PROCESS') && <BtnSuccess onClick={()=>openModal('routing')}>+ New Routing</BtnSuccess>}
                  <select className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs"
                    onChange={async e => {
                      if(!e.target.value) { setExtra(prev=>({...prev, routingData:null})); return; }
                      const r = await axios.get(`/api/routings/${e.target.value}`);
                      setExtra(prev=>({...prev, routingData:r.data}));
                    }}>
                    <option value="">Select item for routing</option>
                    {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
                  </select>
                </div>
                {extra.routingData && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <span className="text-white font-bold">Routing: {extra.routingData.item_code}</span>
                      <span className="text-slate-500 text-xs">{extra.routingData.routes?.length||0} steps</span>
                      <span className="text-amber-400 text-xs font-bold">Total: {extra.routingData.total_time} min</span>
                    </div>
                    {/* Visual flow */}
                    <div className="flex gap-2 items-center flex-wrap">
                      {(extra.routingData.routes||[]).map((r,i)=>(
                        <React.Fragment key={i}>
                          <div className="bg-[#1e293b] p-3 rounded-xl border border-slate-700 text-center min-w-[130px] hover:border-blue-500/50 transition-all">
                            <div className="text-[9px] text-slate-600 mb-1">Step {r.seq}</div>
                            <div className="text-blue-400 font-bold">{r.process_name}</div>
                            <div className="text-[10px] text-slate-500">{r.process_code}</div>
                            <div className="text-amber-400 mt-1 font-bold">{r.cycle_time} min</div>
                            <div className="text-[9px] text-purple-400 mt-0.5">{r.equip_name||'N/A'}</div>
                          </div>
                          {i < extra.routingData.routes.length-1 && <span className="text-slate-600 text-lg">→</span>}
                        </React.Fragment>
                      ))}
                    </div>
                    {/* Routing table */}
                    <Table cols={['Seq','Process Code','Process Name','Cycle Time','Equipment','% of Total']}
                      rows={extra.routingData.routes||[]}
                      renderRow={(r,k)=>(
                        <tr key={k}>
                          <td className="p-3 text-white font-bold">{r.seq}</td>
                          <td className="p-3 font-mono text-blue-400">{r.process_code}</td>
                          <td className="p-3 text-white">{r.process_name}</td>
                          <td className="p-3 text-amber-400 font-bold">{r.cycle_time} min</td>
                          <td className="p-3 text-purple-400">{r.equip_name||'-'}</td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 rounded-full" style={{width:`${extra.routingData.total_time>0 ? (r.cycle_time/extra.routingData.total_time*100) : 0}%`}}/>
                              </div>
                              <span className="text-[10px] text-blue-400 w-10 text-right">{extra.routingData.total_time>0 ? (r.cycle_time/extra.routingData.total_time*100).toFixed(0) : 0}%</span>
                            </div>
                          </td>
                        </tr>
                      )} />
                  </div>
                )}
              </div>
            )}

            {/* Routing Summary tab */}
            {procTab==='summary' && (
              <div className="space-y-3">
                <FilterBar>
                  <FilterSearch value={tf.routing.search} onChange={v=>setFilter('routing','search',v)} placeholder="Search item code, name..." />
                  <FilterCount total={allRoutingSummary.length} filtered={filteredRoutings.length} />
                </FilterBar>
                <Table cols={['Item Code','Item Name','Category','Steps','Total Time','Avg Time/Step']}
                  rows={filteredRoutings}
                  renderRow={(r,k)=>(
                    <tr key={k} className="cursor-pointer hover:bg-slate-800/30" onClick={async()=>{
                      setProcTab('routing');
                      const res = await axios.get(`/api/routings/${r.item_code}`);
                      setExtra(prev=>({...prev, routingData:res.data}));
                    }}>
                      <td className="p-3 font-mono text-blue-400">{r.item_code}</td>
                      <td className="p-3 text-white font-bold">{r.item_name}</td>
                      <td className="p-3"><Badge v={r.category}/></td>
                      <td className="p-3 text-purple-400 font-bold">{r.step_count}</td>
                      <td className="p-3 text-amber-400 font-bold">{r.total_time} min</td>
                      <td className="p-3 text-slate-400">{r.step_count>0 ? (r.total_time/r.step_count).toFixed(1) : 0} min</td>
                    </tr>
                  )} />
              </div>
            )}
          </div>
          );
        })()}

        {/* ── EQUIPMENT (FN-013~014, 032~034) ──────────── */}
        {menu==='EQUIPMENT' && (() => {
          const allEquips = extra.equips||[];
          const statuses = [...new Set(allEquips.map(e=>e.status).filter(Boolean))];
          const processes = [...new Set(allEquips.map(e=>e.process_code).filter(Boolean))];
          const filtered = allEquips.filter(e => {
            if (tf.equips.search) {
              const s = tf.equips.search.toLowerCase();
              if (!(e.name||'').toLowerCase().includes(s) && !(e.equip_code||'').toLowerCase().includes(s)) return false;
            }
            if (tf.equips.status!=='ALL' && e.status!==tf.equips.status) return false;
            if (tf.equips.process!=='ALL' && e.process_code!==tf.equips.process) return false;
            return true;
          });
          return (
            <div className="space-y-4">
              {canWrite('EQUIPMENT') && <div className="flex justify-end gap-2">
                <BtnSuccess onClick={()=>openModal('equipment')}>+ New Equipment</BtnSuccess>
                <Btn onClick={()=>openModal('equip_status')}>Change Status</Btn>
              </div>}
              <FilterBar>
                <FilterSelect label="Status" value={tf.equips.status} onChange={v=>setFilter('equips','status',v)}
                  options={[{value:'ALL',label:'All'}, ...statuses.map(s=>({value:s,label:s}))]} />
                <FilterSelect label="Process" value={tf.equips.process} onChange={v=>setFilter('equips','process',v)}
                  options={[{value:'ALL',label:'All'}, ...processes.map(p=>({value:p,label:p}))]} />
                <FilterSearch value={tf.equips.search} onChange={v=>setFilter('equips','search',v)} placeholder="Search name, code..." />
                <FilterCount total={allEquips.length} filtered={filtered.length} />
              </FilterBar>
              {/* ── Availability Summary ── */}
              {(() => {
                const running = allEquips.filter(e=>e.status==='RUNNING').length;
                const down = allEquips.filter(e=>e.status==='DOWN').length;
                const stop = allEquips.filter(e=>e.status==='STOP').length;
                const total = allEquips.length||1;
                const avgUptime = allEquips.length ? Math.round(allEquips.reduce((s,e)=>s+(e.uptime_today||0)*100,0)/allEquips.length) : 0;
                return (
                  <div className="bg-[#1e293b]/50 rounded-2xl border border-slate-800 p-4 grid grid-cols-5 gap-4">
                    <div className="text-center"><div className="text-2xl font-bold text-white">{total}</div><div className="text-[10px] text-slate-500">Total</div></div>
                    <div className="text-center"><div className="text-2xl font-bold text-emerald-400">{running}</div><div className="text-[10px] text-slate-500">Running</div></div>
                    <div className="text-center"><div className="text-2xl font-bold text-red-400">{down}</div><div className="text-[10px] text-slate-500">Down</div></div>
                    <div className="text-center"><div className="text-2xl font-bold text-amber-400">{stop}</div><div className="text-[10px] text-slate-500">Stopped</div></div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-cyan-400">{avgUptime}%</div>
                      <div className="text-[10px] text-slate-500">Avg Uptime</div>
                      <div className="mt-1 w-full bg-slate-700 rounded-full h-2">
                        <div className={`h-2 rounded-full ${avgUptime>=80?'bg-emerald-500':avgUptime>=50?'bg-amber-500':'bg-red-500'}`} style={{width:`${avgUptime}%`}}/>
                      </div>
                    </div>
                  </div>
                );
              })()}
              <div className="grid grid-cols-5 gap-3">
                {filtered.map(e=>{
                  const upt = Math.round((e.uptime_today||0)*100);
                  return (
                  <div key={e.equip_code} className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-white font-bold text-xs">{e.name}</span>
                      <Badge v={e.status}/>
                    </div>
                    <div className="text-[10px] text-slate-500 space-y-0.5">
                      <div>Code: {e.equip_code}</div>
                      <div>Process: {e.process_code}</div>
                      <div>Capacity: {e.capacity_per_hour}/hr</div>
                      {e.current_job && <div className="text-cyan-400">Job: {e.current_job}</div>}
                    </div>
                    <div className="mt-2">
                      <div className="flex justify-between text-[10px] mb-0.5">
                        <span className="text-slate-500">Uptime</span>
                        <span className={upt>=80?'text-emerald-400':upt>=50?'text-amber-400':'text-red-400'}>{upt}%</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-1.5">
                        <div className={`h-1.5 rounded-full ${upt>=80?'bg-emerald-500':upt>=50?'bg-amber-500':'bg-red-500'}`} style={{width:`${upt}%`}}/>
                      </div>
                    </div>
                  </div>
                  );
                })}
              </div>
            </div>
          );
        })()}

        {/* ── PLANS (FN-015~017) ───────────────────────── */}
        {menu==='PLANS' && (() => {
          const allPlans = extra.planList||[];
          const statuses = [...new Set(allPlans.map(p=>p.status).filter(Boolean))];
          const priorities = [...new Set(allPlans.map(p=>p.priority).filter(Boolean))];
          const filtered = allPlans.filter(p => {
            if (tf.plans.search) {
              const s = tf.plans.search.toLowerCase();
              if (!String(p.plan_id).includes(s) && !(p.item_name||'').toLowerCase().includes(s)) return false;
            }
            if (tf.plans.status!=='ALL' && p.status!==tf.plans.status) return false;
            if (tf.plans.priority!=='ALL' && p.priority!==tf.plans.priority) return false;
            return true;
          });
          return (
            <div className="space-y-4">
              {canWrite('PLANS') && <div className="flex justify-end gap-2">
                <BtnSuccess onClick={()=>openModal('plan')}>+ New Plan</BtnSuccess>
              </div>}
              <FilterBar>
                <FilterSelect label="Status" value={tf.plans.status} onChange={v=>setFilter('plans','status',v)}
                  options={[{value:'ALL',label:'All'}, ...statuses.map(s=>({value:s,label:s}))]} />
                <FilterSelect label="Priority" value={tf.plans.priority} onChange={v=>setFilter('plans','priority',v)}
                  options={[{value:'ALL',label:'All'}, ...priorities.map(p=>({value:p,label:p}))]} />
                <FilterSearch value={tf.plans.search} onChange={v=>setFilter('plans','search',v)} placeholder="Search ID, item..." />
                <FilterCount total={allPlans.length} filtered={filtered.length} />
              </FilterBar>
              <Table cols={['ID','Item','Qty','Due Date','Priority','Status','Progress']}
                rows={filtered}
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
          );
        })()}

        {/* ── WORK ORDER (FN-020~024) ──────────────────── */}
        {menu==='WORK_ORDER' && (() => {
          const allWo = extra.woList||[];
          const statuses = [...new Set(allWo.map(w=>w.status).filter(Boolean))];
          const filtered = allWo.filter(w => {
            if (tf.wo.search) {
              const s = tf.wo.search.toLowerCase();
              if (!(w.wo_id||'').toLowerCase().includes(s) && !(w.item_name||'').toLowerCase().includes(s) && !(w.equip_code||'').toLowerCase().includes(s)) return false;
            }
            if (tf.wo.status!=='ALL' && w.status!==tf.wo.status) return false;
            return true;
          });
          return (
            <div className="space-y-4">
              {canWrite('WORK_ORDER') && <div className="flex justify-end gap-2">
                <BtnSuccess onClick={()=>openModal('work_order')}>+ New Work Order</BtnSuccess>
                <Btn onClick={()=>openModal('work_result')}>Record Result</Btn>
              </div>}
              <FilterBar>
                <FilterSelect label="Status" value={tf.wo.status} onChange={v=>setFilter('wo','status',v)}
                  options={[{value:'ALL',label:'All'}, ...statuses.map(s=>({value:s,label:s}))]} />
                <FilterSearch value={tf.wo.search} onChange={v=>setFilter('wo','search',v)} placeholder="Search WO ID, item, equipment..." />
                <FilterCount total={allWo.length} filtered={filtered.length} />
              </FilterBar>
              <Table cols={['WO ID','Item','Qty','Date','Equipment','Status','Actions']}
                rows={filtered}
                renderRow={(w,k)=>{
                  const transitions = {WAIT:['WORKING'],WORKING:['DONE','HOLD'],HOLD:['WORKING'],DONE:[]};
                  const allowed = transitions[w.status]||[];
                  return (
                  <tr key={k}>
                    <td className="p-3 font-mono text-blue-400">{w.wo_id}</td>
                    <td className="p-3 text-white">{w.item_name}</td>
                    <td className="p-3">{w.plan_qty}</td>
                    <td className="p-3">{w.work_date}</td>
                    <td className="p-3 text-purple-400">{w.equip_code}</td>
                    <td className="p-3"><Badge v={w.status}/></td>
                    <td className="p-3">
                      <div className="flex gap-1 flex-wrap">
                        {allowed.map(s=>(
                          <button key={s} onClick={async()=>{try{const r=await axios.put(`/api/work-orders/${w.wo_id}/status`,{status:s});if(r.data.error){showToast(r.data.error,false);}else{showToast(`${w.wo_id} → ${s}`);refreshPage('WORK_ORDER');}}catch(err){showToast(err.response?.data?.error||'Failed',false);}}}
                            className={`px-2 py-0.5 rounded text-[9px] font-bold cursor-pointer ${s==='DONE'?'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30':s==='HOLD'?'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30':'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'}`}>
                            →{s}
                          </button>
                        ))}
                        <button onClick={async()=>{try{const r=await axios.get(`/api/work-orders/${w.wo_id}`);openModal('wo_detail',{detail:r.data});}catch{}}} className="text-slate-400 hover:text-white text-[9px] font-bold cursor-pointer">Detail</button>
                      </div>
                    </td>
                  </tr>
                  );
                }} />
            </div>
          );
        })()}

        {/* ── QUALITY (FN-025~028) ─────────────────────── */}
        {menu==='QUALITY' && (() => {
          const allDefects = extra.defects?.summary||[];
          const filtered = allDefects.filter(d => {
            if (tf.quality.search) {
              const s = tf.quality.search.toLowerCase();
              if (!(d.defect_type||'').toLowerCase().includes(s)) return false;
            }
            return true;
          });
          return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-white font-bold">Defect Summary</h3>
              {canWrite('QUALITY') && <div className="flex gap-2">
                <BtnSuccess onClick={()=>openModal('quality_std')}>+ Quality Standard</BtnSuccess>
                <Btn onClick={()=>openModal('inspection')}>+ New Inspection</Btn>
              </div>}
            </div>
            <FilterBar>
              <FilterSearch value={tf.quality.search} onChange={v=>setFilter('quality','search',v)} placeholder="Search defect type..." />
              <FilterCount total={allDefects.length} filtered={filtered.length} />
            </FilterBar>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Table cols={['Defect Type','Count','Rate']}
                  rows={filtered}
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
          );
        })()}

        {/* ── INVENTORY (FN-029~031) ───────────────────── */}
        {menu==='INVENTORY' && (() => {
          const allInv = extra.invItems||[];
          const statuses = [...new Set(allInv.map(i=>i.status).filter(Boolean))];
          const filtered = allInv.filter(i => {
            if (tf.inv.search) {
              const s = tf.inv.search.toLowerCase();
              if (!(i.item_code||'').toLowerCase().includes(s) && !(i.name||'').toLowerCase().includes(s)) return false;
            }
            if (tf.inv.status!=='ALL' && i.status!==tf.inv.status) return false;
            return true;
          });
          return (
            <div className="space-y-4">
              <div className="flex justify-end gap-2 flex-wrap">
                {canWrite('INVENTORY') && <>
                  <BtnSuccess onClick={()=>openModal('inv_in')}>+ Receive (入庫)</BtnSuccess>
                  <Btn onClick={()=>openModal('inv_out')}>Issue (出庫)</Btn>
                  <button onClick={()=>openModal('inv_move')} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold text-xs cursor-pointer">Move (移動)</button>
                </>}
                <button onClick={()=>openModal('lot_trace')} className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-bold text-xs cursor-pointer">LOT Trace (추적)</button>
              </div>
              <FilterBar>
                <FilterSelect label="Status" value={tf.inv.status} onChange={v=>setFilter('inv','status',v)}
                  options={[{value:'ALL',label:'All'}, ...statuses.map(s=>({value:s,label:s}))]} />
                <FilterSearch value={tf.inv.search} onChange={v=>setFilter('inv','search',v)} placeholder="Search code, name..." />
                <FilterCount total={allInv.length} filtered={filtered.length} />
              </FilterBar>
              <Table cols={['Code','Name','Stock','Available','Safety','Status']}
                rows={filtered}
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
            </div>
          );
        })()}

        {/* ── AI CENTER (FN-018,028,034) ───────────────── */}
        {menu==='AI_CENTER' && (
          <div className="space-y-4">
          <div className="flex justify-end">
            <BtnSuccess onClick={()=>openModal('schedule_optimize')}>AI Schedule Optimize</BtnSuccess>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {/* Demand Forecast */}
            <div className="bg-[#1e293b]/30 p-4 rounded-2xl border border-slate-800 space-y-3">
              <h3 className="text-white font-bold">Demand Forecast</h3>
              <Input placeholder="Item code (e.g. ITEM003)" ref={aiDemandRef} className="w-full" />
              <Btn onClick={async()=>{
                const code = aiDemandRef.current?.value || '';
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
              <Input placeholder="Temp" ref={aiDefTempRef} className="w-full" type="number" />
              <Input placeholder="Pressure" ref={aiDefPresRef} className="w-full" type="number" />
              <Input placeholder="Speed" ref={aiDefSpeedRef} className="w-full" type="number" />
              <Input placeholder="Humidity" ref={aiDefHumRef} className="w-full" type="number" />
              <Btn onClick={async()=>{
                const r = await axios.post('/api/ai/defect-prediction', {
                  temperature: +(aiDefTempRef.current?.value || 0),
                  pressure: +(aiDefPresRef.current?.value || 0),
                  speed: +(aiDefSpeedRef.current?.value || 0),
                  humidity: +(aiDefHumRef.current?.value || 0),
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
              <Input placeholder="Equip code (e.g. EQP-003)" ref={aiFailEqRef} className="w-full" />
              <Input placeholder="Vibration" ref={aiFailVibRef} className="w-full" type="number" />
              <Input placeholder="Temperature" ref={aiFailTempRef} className="w-full" type="number" />
              <Input placeholder="Current (A)" ref={aiFailCurRef} className="w-full" type="number" />
              <Btn onClick={async()=>{
                const r = await axios.post('/api/ai/failure-predict', {
                  equip_code: aiFailEqRef.current?.value || '',
                  sensor: {
                    vibration: +(aiFailVibRef.current?.value || 0),
                    temperature: +(aiFailTempRef.current?.value || 0),
                    current: +(aiFailCurRef.current?.value || 0),
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

          /* ── Hierarchical left-to-right layout — hand-tuned positions ── */
          const W=960, H=430;
          const tierLabels = ['External','Ingress','Application','Backend / Infra'];
          const tierColors = ['#f59e0b','#3b82f6','#06b6d4','#a855f7'];
          const tierX = [60, 270, 490, 730];
          const nodeW = 140, nodeH = 52;

          /* Fixed Y positions per service — tuned to minimize crossings:
             - world centered, frontend slightly above center
             - api-service at center so tier3 fans out symmetrically
             - tier3 ordered: postgres(top), kube-dns, hubble-relay, cilium-agent(bottom)
             - dropped connections (world→postgres, world→cilium) route top/bottom cleanly */
          const fixedY = {
            'world': 215,
            'mes-frontend': 170,
            'mes-api-service': 200,
            'postgres': 85,
            'kube-dns': 175,
            'hubble-relay': 265,
            'cilium-agent': 370,
          };
          const tierOf = { 'world':0, 'mes-frontend':1, 'mes-api-service':2, 'postgres':3, 'kube-dns':3, 'hubble-relay':3, 'cilium-agent':3 };

          const svcPositions = {};
          filteredSvcs.forEach(s => {
            const t = tierOf[s.id] ?? 3;
            svcPositions[s.id] = {
              x: tierX[t],
              y: fixedY[s.id] ?? (200 + Object.keys(svcPositions).length * 72),
              tier: t,
            };
          });

          /* ── Build per-node port lists (sorted by target/source Y) for offset distribution ── */
          const outPorts = {}, inPorts = {};
          filteredConns.forEach((c, ci) => {
            if (!outPorts[c.source]) outPorts[c.source] = [];
            if (!inPorts[c.target]) inPorts[c.target] = [];
            outPorts[c.source].push({ ci, peer: c.target });
            inPorts[c.target].push({ ci, peer: c.source });
          });
          Object.values(outPorts).forEach(arr => arr.sort((a,b) => (svcPositions[a.peer]?.y||0)-(svcPositions[b.peer]?.y||0)));
          Object.values(inPorts).forEach(arr => arr.sort((a,b) => (svcPositions[a.peer]?.y||0)-(svcPositions[b.peer]?.y||0)));

          const portOffset = (ports, ci, nodeHalf) => {
            if (!ports) return 0;
            const idx = ports.findIndex(p => p.ci === ci);
            if (idx === -1) return 0;
            const n = ports.length;
            const spacing = Math.min(10, (nodeHalf * 2 - 8) / Math.max(n, 1));
            return (idx - (n - 1) / 2) * spacing;
          };

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

                      {/* connections — smart routing to avoid crossings */}
                      {filteredConns.map((c, i) => {
                        const sp = svcPositions[c.source]; const tp = svcPositions[c.target];
                        if(!sp||!tp) return null;
                        const hasDropped = c.dropped_count > 0;
                        const strokeW = Math.min(3, 1 + Math.log1p(c.total_count)*0.5);
                        const clr = hasDropped ? '#ef4444' : '#22c55e';
                        const tierDist = Math.abs(sp.tier - tp.tier);

                        /* port offsets: distribute connection points along node edge */
                        const srcOff = portOffset(outPorts[c.source], i, nodeH/2);
                        const dstOff = portOffset(inPorts[c.target], i, nodeH/2);
                        const sx = sp.x + nodeW + 2, sy = sp.y + srcOff;
                        const tx = tp.x - 2, ty = tp.y + dstOff;

                        let path, midX, midY;
                        if (tierDist <= 1) {
                          /* adjacent tier: simple horizontal bezier */
                          const cpOff = Math.abs(tx-sx) * 0.4;
                          path = `M${sx},${sy} C${sx+cpOff},${sy} ${tx-cpOff},${ty} ${tx},${ty}`;
                          midX = (sx+tx)/2; midY = (sy+ty)/2;
                        } else {
                          /* skip-tier: route above (if target above center) or below (if below) to avoid intermediate nodes */
                          const goUp = ty < H/2;
                          const detourY = goUp ? Math.min(sy, ty) - 35 - (i % 3) * 18 : Math.max(sy, ty) + 35 + (i % 3) * 18;
                          const clampedY = Math.max(20, Math.min(H - 20, detourY));
                          /* 4-point cubic: exit → curve up/down → horizontal cruise → curve to target */
                          const q1x = sx + 50, q2x = tx - 50;
                          path = `M${sx},${sy} C${sx+35},${sy} ${q1x},${clampedY} ${(sx+tx)/2},${clampedY} S${q2x},${ty} ${tx},${ty}`;
                          midX = (sx+tx)/2; midY = clampedY;
                        }

                        return (
                          <g key={`conn-${i}`}>
                            <path d={path} fill="none" stroke={clr} strokeWidth={strokeW+2} opacity="0.04"/>
                            <path d={path} fill="none" stroke={clr} strokeWidth={strokeW} opacity="0.55"
                              markerEnd={hasDropped ? 'url(#arrow-drop)' : 'url(#arrow-fwd)'}
                              strokeDasharray={hasDropped ? '6 4' : 'none'}>
                              {!hasDropped && <animate attributeName="stroke-dashoffset" values="20;0" dur="1.5s" repeatCount="indefinite"/>}
                            </path>
                            <rect x={midX-30} y={midY-8} width="60" height="15" rx="7"
                              fill="#060a14" stroke={`${clr}30`} strokeWidth="0.5"/>
                            <text x={midX} y={midY+3} fill={clr} fontSize="6.5" fontWeight="600" textAnchor="middle" opacity="0.85">
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
        {menu==='K8S_MANAGER' && (() => {
          const allPods = db.pods||[];
          const statuses = [...new Set(allPods.map(p=>p.status).filter(Boolean))];
          const filtered = allPods.filter(p => {
            if (tf.k8s.search && !(p.name||'').toLowerCase().includes(tf.k8s.search.toLowerCase())) return false;
            if (tf.k8s.status!=='ALL' && p.status!==tf.k8s.status) return false;
            return true;
          });
          return (
          <div className="space-y-4">
            <FilterBar>
              <FilterSelect label="Status" value={tf.k8s.status} onChange={v=>setFilter('k8s','status',v)}
                options={[{value:'ALL',label:'All'}, ...statuses.map(s=>({value:s,label:s}))]} />
              <FilterSearch value={tf.k8s.search} onChange={v=>setFilter('k8s','search',v)} placeholder="Search pod name..." />
              <FilterCount total={allPods.length} filtered={filtered.length} />
            </FilterBar>
            <div className="grid grid-cols-2 gap-6 h-[500px]">
              <div className="bg-[#1e293b]/20 p-4 rounded-2xl border border-slate-800 overflow-auto space-y-2">
                <h3 className="text-white font-bold mb-3">Pod Status</h3>
                {filtered.map(p=>(
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
          </div>
          );
        })()}

      </main>

      {/* ── Toast notification ──────────────────────────── */}
      {toast && (
        <div className={`fixed top-6 right-6 z-[60] px-5 py-3 rounded-xl text-xs font-bold shadow-lg border ${toast.ok ? 'bg-emerald-900/90 border-emerald-700 text-emerald-300' : 'bg-red-900/90 border-red-700 text-red-300'}`}>
          {toast.msg}
        </div>
      )}

      {/* ── MODAL: Item Registration ─────────────────────── */}
      <Modal open={modal.type==='item'} onClose={closeModal} title="New Item Registration">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/items',{name:fd.get('name'),category:fd.get('category'),unit:fd.get('unit'),spec:fd.get('spec'),safety_stock:Number(fd.get('safety_stock')||0)});
            showToast(`Item ${r.data.item_code} created`);
            closeModal(); refreshPage('ITEMS');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item Name"><Input name="name" required className="w-full" placeholder="Enter item name"/></FormRow>
          <FormRow label="Category">
            <Select name="category" onChange={()=>{}} value="" options={[{value:'RAW',label:'RAW'},{value:'SEMI',label:'SEMI'},{value:'PRODUCT',label:'PRODUCT'}]} className="w-full"/>
          </FormRow>
          <FormRow label="Unit">
            <Select name="unit" onChange={()=>{}} value="" options={[{value:'EA',label:'EA'},{value:'KG',label:'KG'},{value:'M',label:'M'},{value:'L',label:'L'}]} className="w-full"/>
          </FormRow>
          <FormRow label="Spec"><Input name="spec" className="w-full" placeholder="Specification"/></FormRow>
          <FormRow label="Safety Stock"><Input name="safety_stock" type="number" className="w-full" defaultValue="0"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: BOM Registration ──────────────────────── */}
      <Modal open={modal.type==='bom'} onClose={closeModal} title="New BOM Registration">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            await axios.post('/api/bom',{parent_item:fd.get('parent_item'),child_item:fd.get('child_item'),qty_per_unit:Number(fd.get('qty_per_unit')||1),loss_rate:Number(fd.get('loss_rate')||0)});
            showToast('BOM entry created');
            closeModal(); refreshPage('BOM');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Parent Item (Product)">
            <select name="parent_item" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select parent item</option>
              {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Child Item (Component)">
            <select name="child_item" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select child item</option>
              {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Qty per Unit"><Input name="qty_per_unit" type="number" step="0.01" required className="w-full" defaultValue="1"/></FormRow>
          <FormRow label="Loss Rate (%)"><Input name="loss_rate" type="number" step="0.01" className="w-full" defaultValue="0"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Process Registration ──────────────────── */}
      <Modal open={modal.type==='process'} onClose={closeModal} title="New Process Registration">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/processes',{name:fd.get('name'),std_time_min:Number(fd.get('std_time_min')||0),description:fd.get('description'),equip_code:fd.get('equip_code')||null});
            showToast(`Process ${r.data.process_code} created`);
            closeModal(); refreshPage('PROCESS');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Process Name"><Input name="name" required className="w-full" placeholder="Enter process name"/></FormRow>
          <FormRow label="Standard Time (min)"><Input name="std_time_min" type="number" required className="w-full" defaultValue="0"/></FormRow>
          <FormRow label="Description"><Input name="description" className="w-full" placeholder="Process description"/></FormRow>
          <FormRow label="Equipment">
            <select name="equip_code" className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">None</option>
              {(extra.equips||[]).map(e=><option key={e.equip_code} value={e.equip_code}>{e.equip_code} - {e.name}</option>)}
            </select>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Routing Registration ──────────────────── */}
      <Modal open={modal.type==='routing'} onClose={closeModal} title="New Routing Registration">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            await axios.post('/api/routings',{item_code:fd.get('item_code'),routes:modalRoutes.filter(r=>r.process_code)});
            showToast('Routing created');
            closeModal(); refreshPage('PROCESS');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Process Steps">
            {modalRoutes.map((r,idx)=>(
              <div key={idx} className="flex gap-2 mb-2 items-center">
                <span className="text-slate-500 text-[10px] w-6">{r.seq}</span>
                <select value={r.process_code} onChange={e=>{const n=[...modalRoutes];n[idx].process_code=e.target.value;setModalRoutes(n);}}
                  className="bg-[#0f172a] border border-slate-700 p-1.5 rounded text-white text-xs flex-1">
                  <option value="">Select process</option>
                  {(extra.processList||[]).map(p=><option key={p.process_code} value={p.process_code}>{p.process_code} - {p.name}</option>)}
                </select>
                <Input type="number" value={r.cycle_time} onChange={e=>{const n=[...modalRoutes];n[idx].cycle_time=Number(e.target.value);setModalRoutes(n);}} className="w-20" placeholder="min"/>
                {modalRoutes.length>1 && <button type="button" onClick={()=>setModalRoutes(modalRoutes.filter((_,i)=>i!==idx))} className="text-red-400 hover:text-red-300 cursor-pointer">x</button>}
              </div>
            ))}
            <button type="button" onClick={()=>setModalRoutes([...modalRoutes,{seq:modalRoutes.length+1,process_code:'',cycle_time:0}])} className="text-blue-400 text-[10px] hover:text-blue-300 cursor-pointer">+ Add Step</button>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Equipment Registration ────────────────── */}
      <Modal open={modal.type==='equipment'} onClose={closeModal} title="New Equipment Registration">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/equipments',{name:fd.get('name'),process_code:fd.get('process_code')||null,capacity_per_hour:Number(fd.get('capacity_per_hour')||100),install_date:fd.get('install_date')||null});
            showToast(`Equipment ${r.data.equip_code} created`);
            closeModal(); refreshPage('EQUIPMENT');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Equipment Name"><Input name="name" required className="w-full" placeholder="Enter equipment name"/></FormRow>
          <FormRow label="Process">
            <select name="process_code" className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">None</option>
              {(extra.processList||[]).map(p=><option key={p.process_code} value={p.process_code}>{p.process_code} - {p.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Capacity per Hour"><Input name="capacity_per_hour" type="number" className="w-full" defaultValue="100"/></FormRow>
          <FormRow label="Install Date"><Input name="install_date" type="date" className="w-full"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Equipment Status Change ───────────────── */}
      <Modal open={modal.type==='equip_status'} onClose={closeModal} title="Change Equipment Status">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          const code=fd.get('equip_code');
          try {
            await axios.put(`/api/equipments/${code}/status`,{status:fd.get('status'),reason:fd.get('reason'),worker_id:fd.get('worker_id')});
            showToast(`Equipment ${code} status updated`);
            closeModal(); refreshPage('EQUIPMENT');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Equipment">
            <select name="equip_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select equipment</option>
              {(extra.equips||[]).map(e=><option key={e.equip_code} value={e.equip_code}>{e.equip_code} - {e.name} ({e.status})</option>)}
            </select>
          </FormRow>
          <FormRow label="New Status">
            <Select name="status" onChange={()=>{}} value="" options={[{value:'RUNNING',label:'RUNNING'},{value:'STOP',label:'STOP'},{value:'DOWN',label:'DOWN'}]} className="w-full"/>
          </FormRow>
          <FormRow label="Reason"><Input name="reason" className="w-full" placeholder="Reason for status change"/></FormRow>
          <FormRow label="Worker ID"><Input name="worker_id" className="w-full" placeholder="Worker ID"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Update Status</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Production Plan Registration ──────────── */}
      <Modal open={modal.type==='plan'} onClose={closeModal} title="New Production Plan">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/plans',{item_code:fd.get('item_code'),plan_qty:Number(fd.get('plan_qty')),due_date:fd.get('due_date'),priority:fd.get('priority')});
            showToast(`Plan #${r.data.plan_id} created`);
            closeModal(); refreshPage('PLANS');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Plan Quantity"><Input name="plan_qty" type="number" required className="w-full" placeholder="Quantity"/></FormRow>
          <FormRow label="Due Date"><Input name="due_date" type="date" required className="w-full"/></FormRow>
          <FormRow label="Priority">
            <Select name="priority" onChange={()=>{}} value="" options={[{value:'MID',label:'MID'},{value:'HIGH',label:'HIGH'},{value:'LOW',label:'LOW'}]} className="w-full"/>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Work Order Creation ────────────────────── */}
      <Modal open={modal.type==='work_order'} onClose={closeModal} title="New Work Order">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/work-orders',{plan_id:Number(fd.get('plan_id')),work_date:fd.get('work_date')||undefined,equip_code:fd.get('equip_code')||undefined});
            showToast(`Work Order ${r.data.work_order_id} created`);
            closeModal(); refreshPage('WORK_ORDER');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Production Plan">
            <select name="plan_id" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select plan</option>
              {(extra.planList||[]).filter(p=>p.status!=='DONE').map(p=><option key={p.plan_id} value={p.plan_id}>#{p.plan_id} - {p.item_name} (qty:{p.qty}, {p.status})</option>)}
            </select>
          </FormRow>
          <FormRow label="Work Date"><Input name="work_date" type="date" className="w-full"/></FormRow>
          <FormRow label="Equipment">
            <select name="equip_code" className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Auto assign</option>
              {(extra.equips||[]).map(e=><option key={e.equip_code} value={e.equip_code}>{e.equip_code} - {e.name}</option>)}
            </select>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Create</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Work Result Registration ──────────────── */}
      <Modal open={modal.type==='work_result'} onClose={closeModal} title="Record Work Result">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/work-results',{wo_id:fd.get('wo_id'),good_qty:Number(fd.get('good_qty')||0),defect_qty:Number(fd.get('defect_qty')||0),defect_code:fd.get('defect_code')||undefined,worker_id:fd.get('worker_id')||undefined,start_time:fd.get('start_time')||undefined,end_time:fd.get('end_time')||undefined});
            showToast(`Result recorded (Progress: ${r.data.progress_pct}%)`);
            closeModal(); refreshPage('WORK_ORDER');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Work Order">
            <select name="wo_id" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select work order</option>
              {(extra.woList||[]).filter(w=>w.status!=='DONE').map(w=><option key={w.wo_id} value={w.wo_id}>{w.wo_id} - {w.item_name} (qty:{w.plan_qty})</option>)}
            </select>
          </FormRow>
          <div className="grid grid-cols-2 gap-3">
            <FormRow label="Good Qty"><Input name="good_qty" type="number" className="w-full" defaultValue="0"/></FormRow>
            <FormRow label="Defect Qty"><Input name="defect_qty" type="number" className="w-full" defaultValue="0"/></FormRow>
          </div>
          <FormRow label="Defect Code"><Input name="defect_code" className="w-full" placeholder="e.g. DEF-001"/></FormRow>
          <FormRow label="Worker ID"><Input name="worker_id" className="w-full" placeholder="Worker ID"/></FormRow>
          <div className="grid grid-cols-2 gap-3">
            <FormRow label="Start Time"><Input name="start_time" type="datetime-local" className="w-full"/></FormRow>
            <FormRow label="End Time"><Input name="end_time" type="datetime-local" className="w-full"/></FormRow>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Record</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Quality Standard Registration ─────────── */}
      <Modal open={modal.type==='quality_std'} onClose={closeModal} title="New Quality Standard">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            await axios.post('/api/quality/standards',{item_code:fd.get('item_code'),checks:modalChecks.filter(c=>c.name)});
            showToast('Quality standard created');
            closeModal(); refreshPage('QUALITY');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Check Items">
            {modalChecks.map((c,idx)=>(
              <div key={idx} className="flex gap-1.5 mb-2 items-center flex-wrap">
                <Input value={c.name} onChange={e=>{const n=[...modalChecks];n[idx].name=e.target.value;setModalChecks(n);}} className="flex-1 min-w-[80px]" placeholder="Name"/>
                <select value={c.type} onChange={e=>{const n=[...modalChecks];n[idx].type=e.target.value;setModalChecks(n);}}
                  className="bg-[#0f172a] border border-slate-700 p-1.5 rounded text-white text-[10px]">
                  <option value="NUMERIC">Numeric</option><option value="VISUAL">Visual</option><option value="FUNCTIONAL">Functional</option>
                </select>
                <Input value={c.min} onChange={e=>{const n=[...modalChecks];n[idx].min=Number(e.target.value);setModalChecks(n);}} type="number" step="0.01" className="w-16" placeholder="Min"/>
                <Input value={c.max} onChange={e=>{const n=[...modalChecks];n[idx].max=Number(e.target.value);setModalChecks(n);}} type="number" step="0.01" className="w-16" placeholder="Max"/>
                <Input value={c.unit} onChange={e=>{const n=[...modalChecks];n[idx].unit=e.target.value;setModalChecks(n);}} className="w-14" placeholder="Unit"/>
                {modalChecks.length>1 && <button type="button" onClick={()=>setModalChecks(modalChecks.filter((_,i)=>i!==idx))} className="text-red-400 hover:text-red-300 cursor-pointer">x</button>}
              </div>
            ))}
            <button type="button" onClick={()=>setModalChecks([...modalChecks,{name:'',type:'NUMERIC',std:0,min:0,max:0,unit:''}])} className="text-blue-400 text-[10px] hover:text-blue-300 cursor-pointer">+ Add Check</button>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Quality Inspection ────────────────────── */}
      <Modal open={modal.type==='inspection'} onClose={closeModal} title="New Quality Inspection">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/quality/inspections',{type:fd.get('type'),item_code:fd.get('item_code'),lot_no:fd.get('lot_no'),inspector_id:fd.get('inspector_id'),results:modalResults.filter(r=>r.check_name)});
            showToast(`Inspection: ${r.data.judgment}${r.data.fail_items?.length ? ' (Fail: '+r.data.fail_items.join(', ')+')' : ''}`);
            closeModal(); refreshPage('QUALITY');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Inspection Type">
            <Select name="type" onChange={()=>{}} value="" options={[{value:'INCOMING',label:'INCOMING'},{value:'PROCESS',label:'PROCESS'},{value:'OUTGOING',label:'OUTGOING'}]} className="w-full"/>
          </FormRow>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Lot No"><Input name="lot_no" className="w-full" placeholder="LOT-YYYYMMDD-001"/></FormRow>
          <FormRow label="Inspector ID"><Input name="inspector_id" className="w-full" placeholder="Inspector ID"/></FormRow>
          <FormRow label="Measurement Results">
            {modalResults.map((r,idx)=>(
              <div key={idx} className="flex gap-2 mb-2 items-center">
                <Input value={r.check_name} onChange={e=>{const n=[...modalResults];n[idx].check_name=e.target.value;setModalResults(n);}} className="flex-1" placeholder="Check name"/>
                <Input value={r.value} onChange={e=>{const n=[...modalResults];n[idx].value=Number(e.target.value);setModalResults(n);}} type="number" step="0.01" className="w-24" placeholder="Value"/>
                {modalResults.length>1 && <button type="button" onClick={()=>setModalResults(modalResults.filter((_,i)=>i!==idx))} className="text-red-400 hover:text-red-300 cursor-pointer">x</button>}
              </div>
            ))}
            <button type="button" onClick={()=>setModalResults([...modalResults,{check_name:'',value:0}])} className="text-blue-400 text-[10px] hover:text-blue-300 cursor-pointer">+ Add Result</button>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Submit Inspection</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Inventory In (입고) ───────────────────── */}
      <Modal open={modal.type==='inv_in'} onClose={closeModal} title="Inventory Receive (입고)">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/inventory/in',{item_code:fd.get('item_code'),qty:Number(fd.get('qty')),supplier:fd.get('supplier'),warehouse:fd.get('warehouse')||'WH01',location:fd.get('location')});
            showToast(`Received: LOT ${r.data.lot_no}, Slip ${r.data.slip_no}`);
            closeModal(); refreshPage('INVENTORY');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.invItems||extra.itemList||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Quantity"><Input name="qty" type="number" required className="w-full" placeholder="Quantity"/></FormRow>
          <FormRow label="Supplier"><Input name="supplier" className="w-full" placeholder="Supplier name"/></FormRow>
          <FormRow label="Warehouse"><Input name="warehouse" className="w-full" defaultValue="WH01"/></FormRow>
          <FormRow label="Location"><Input name="location" className="w-full" placeholder="e.g. A-01-01"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Receive</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Inventory Out (출고) ──────────────────── */}
      <Modal open={modal.type==='inv_out'} onClose={closeModal} title="Inventory Issue (출고)">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/inventory/out',{item_code:fd.get('item_code'),qty:Number(fd.get('qty')),out_type:fd.get('out_type'),ref_id:fd.get('ref_id')});
            showToast(`Issued: Slip ${r.data.slip_no} (${r.data.lots_used?.length||0} lots used)`);
            closeModal(); refreshPage('INVENTORY');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.invItems||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name} (stock:{i.stock})</option>)}
            </select>
          </FormRow>
          <FormRow label="Quantity"><Input name="qty" type="number" required className="w-full" placeholder="Quantity"/></FormRow>
          <FormRow label="Out Type">
            <Select name="out_type" onChange={()=>{}} value="" options={[{value:'OUT',label:'OUT (출고)'},{value:'SHIP',label:'SHIP (출하)'},{value:'SCRAP',label:'SCRAP (폐기)'},{value:'RETURN',label:'RETURN (반품)'}]} className="w-full"/>
          </FormRow>
          <FormRow label="Reference ID"><Input name="ref_id" className="w-full" placeholder="e.g. WO-20240101-001"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Issue</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Item Edit (REQ-006) ───────────────────── */}
      <Modal open={modal.type==='item_edit'} onClose={closeModal} title={`Edit Item: ${modal.data?.item?.item_code||''}`}>
        {modal.data?.item && (
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          const body={};
          ['name','category','unit','spec'].forEach(f=>{if(fd.get(f))body[f]=fd.get(f);});
          if(fd.get('safety_stock'))body.safety_stock=Number(fd.get('safety_stock'));
          try {
            await axios.put(`/api/items/${modal.data.item.item_code}`,body);
            showToast(`Item ${modal.data.item.item_code} updated`);
            closeModal(); refreshPage('ITEMS');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item Name"><Input name="name" defaultValue={modal.data.item.name} required className="w-full"/></FormRow>
          <FormRow label="Category">
            <select name="category" defaultValue={modal.data.item.category} className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="RAW">RAW</option><option value="SEMI">SEMI</option><option value="PRODUCT">PRODUCT</option>
            </select>
          </FormRow>
          <FormRow label="Unit">
            <select name="unit" defaultValue={modal.data.item.unit} className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="EA">EA</option><option value="KG">KG</option><option value="M">M</option><option value="L">L</option>
            </select>
          </FormRow>
          <FormRow label="Spec"><Input name="spec" defaultValue={modal.data.item.spec||''} className="w-full"/></FormRow>
          <FormRow label="Safety Stock"><Input name="safety_stock" type="number" defaultValue={modal.data.item.safety_stock||0} className="w-full"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Update</BtnSuccess>
          </div>
        </form>
        )}
      </Modal>

      {/* ── MODAL: Inventory Move (REQ-028) ──────────────── */}
      <Modal open={modal.type==='inv_move'} onClose={closeModal} title="Inventory Movement (재고이동)">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.post('/api/inventory/move',{item_code:fd.get('item_code'),lot_no:fd.get('lot_no'),qty:Number(fd.get('qty')),from_location:fd.get('from_location'),to_location:fd.get('to_location')});
            if(r.data.error) throw {response:{data:r.data}};
            showToast(r.data.message||'Inventory moved');
            closeModal(); refreshPage('INVENTORY');
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Item">
            <select name="item_code" required className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select item</option>
              {(extra.invItems||[]).map(i=><option key={i.item_code} value={i.item_code}>{i.item_code} - {i.name}</option>)}
            </select>
          </FormRow>
          <FormRow label="Lot No"><Input name="lot_no" required className="w-full" placeholder="LOT-YYYYMMDD-001"/></FormRow>
          <FormRow label="Quantity"><Input name="qty" type="number" required className="w-full" placeholder="Quantity to move"/></FormRow>
          <FormRow label="From Location"><Input name="from_location" required className="w-full" placeholder="e.g. A-01-01"/></FormRow>
          <FormRow label="To Location"><Input name="to_location" required className="w-full" placeholder="e.g. B-02-03"/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Move</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: User Registration (REQ-002) ──────────── */}
      <Modal open={modal.type==='register'} onClose={closeModal} title="User Registration (회원가입)">
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          if(fd.get('password')!==fd.get('password_confirm')){showToast('Passwords do not match',false);return;}
          try {
            const r=await axios.post('/api/auth/register',{user_id:fd.get('user_id'),password:fd.get('password'),name:fd.get('name'),email:fd.get('email'),role:fd.get('role')});
            if(r.data.error) throw {response:{data:r.data}};
            showToast(`User ${r.data.user_id} registered`);
            closeModal();
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="User ID"><Input name="user_id" required className="w-full" placeholder="Enter user ID"/></FormRow>
          <FormRow label="Password"><Input name="password" type="password" required className="w-full" placeholder="Password"/></FormRow>
          <FormRow label="Confirm Password"><Input name="password_confirm" type="password" required className="w-full" placeholder="Confirm password"/></FormRow>
          <FormRow label="Name"><Input name="name" required className="w-full" placeholder="Full name"/></FormRow>
          <FormRow label="Email"><Input name="email" type="email" className="w-full" placeholder="email@example.com"/></FormRow>
          <FormRow label="Role">
            <Select name="role" onChange={()=>{}} value="" options={[{value:'worker',label:'Worker'},{value:'admin',label:'Admin'},{value:'viewer',label:'Viewer'}]} className="w-full"/>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Register</BtnSuccess>
          </div>
        </form>
      </Modal>

      {/* ── MODAL: Permission Management (REQ-003) ───────── */}
      <Modal open={modal.type==='permissions'} onClose={closeModal} title="Permission Management (권한관리)">
        <div>
          <FormRow label="Select User">
            <select value={modalSelUser} onChange={async e=>{
              const uid=e.target.value; setModalSelUser(uid);
              const allMenus=['DASHBOARD','ITEMS','BOM','PROCESS','EQUIPMENT','PLANS','WORK_ORDER','QUALITY','INVENTORY','AI_CENTER','REPORTS'];
              if(!uid){setModalPerms([]);return;}
              try {
                const r = await axios.get(`/api/auth/permissions/${uid}`);
                const existing = r.data.permissions||[];
                setModalPerms(allMenus.map(m=>{const found=existing.find(p=>p.menu===m); return {menu:m,read:found?found.read:false,write:found?found.write:false};}));
              } catch{ setModalPerms(allMenus.map(m=>({menu:m,read:false,write:false}))); }
            }}
              className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">Select user</option>
              {(extra.userList||[]).map(u=><option key={u.user_id} value={u.user_id}>{u.user_id} - {u.name} ({u.role})</option>)}
            </select>
          </FormRow>
          {modalSelUser && modalPerms.length>0 && (
            <div>
              <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-hidden mb-4">
                <table className="w-full text-left">
                  <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
                    <tr><th className="p-2">Menu</th><th className="p-2 text-center">Read</th><th className="p-2 text-center">Write</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {modalPerms.map((p,idx)=>(
                      <tr key={p.menu}>
                        <td className="p-2 text-white text-xs">{p.menu}</td>
                        <td className="p-2 text-center"><input type="checkbox" checked={p.read} onChange={e=>{const n=[...modalPerms];n[idx].read=e.target.checked;setModalPerms(n);}}/></td>
                        <td className="p-2 text-center"><input type="checkbox" checked={p.write} onChange={e=>{const n=[...modalPerms];n[idx].write=e.target.checked;setModalPerms(n);}}/></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={()=>{setModalPerms(modalPerms.map(p=>({...p,read:true,write:true})));}} className="text-blue-400 text-[10px] hover:text-blue-300 cursor-pointer">Select All</button>
                <button type="button" onClick={()=>{setModalPerms(modalPerms.map(p=>({...p,read:false,write:false})));}} className="text-slate-400 text-[10px] hover:text-slate-300 cursor-pointer">Clear All</button>
                <BtnSuccess onClick={async()=>{
                  try {
                    await axios.put(`/api/auth/permissions/${modalSelUser}`,{permissions:modalPerms});
                    showToast(`Permissions updated for ${modalSelUser}`);
                  } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
                }}>Save Permissions</BtnSuccess>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* ── MODAL: BOM Edit ──────────────────────────────── */}
      <Modal open={modal.type==='bom_edit'} onClose={closeModal} title={`Edit BOM: ${modal.data?.bom?.parent_item||''} → ${modal.data?.bom?.child_item||''}`}>
        {modal.data?.bom && (
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          try {
            const r=await axios.put(`/api/bom/${modal.data.bom.bom_id}`,{qty_per_unit:Number(fd.get('qty_per_unit')),loss_rate:Number(fd.get('loss_rate'))});
            if(r.data.error){showToast(r.data.error,false);}else{showToast('BOM entry updated');closeModal();refreshPage('BOM');}
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <div className="bg-[#0f172a] p-3 rounded-lg border border-slate-800 mb-4 text-xs">
            <div className="flex justify-between"><span className="text-slate-500">Parent:</span><span className="text-purple-400 font-mono">{modal.data.bom.parent_item} - {modal.data.bom.parent_name}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Child:</span><span className="text-blue-400 font-mono">{modal.data.bom.child_item} - {modal.data.bom.child_name}</span></div>
          </div>
          <FormRow label="Qty per Unit"><Input name="qty_per_unit" type="number" step="0.01" required className="w-full" defaultValue={modal.data.bom.qty_per_unit}/></FormRow>
          <FormRow label="Loss Rate (%)"><Input name="loss_rate" type="number" step="0.01" className="w-full" defaultValue={modal.data.bom.loss_rate}/></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Update</BtnSuccess>
          </div>
        </form>
        )}
      </Modal>

      {/* ── MODAL: Process Edit ────────────────────────────── */}
      <Modal open={modal.type==='process_edit'} onClose={closeModal} title={`Edit Process: ${modal.data?.proc?.process_code||''}`}>
        {modal.data?.proc && (
        <form onSubmit={async e=>{
          e.preventDefault();
          const fd=new FormData(e.target);
          const body={};
          if(fd.get('name')) body.name=fd.get('name');
          if(fd.get('std_time_min')) body.std_time_min=Number(fd.get('std_time_min'));
          if(fd.get('description')!==null) body.description=fd.get('description');
          if(fd.get('equip_code')) body.equip_code=fd.get('equip_code');
          try {
            const r=await axios.put(`/api/processes/${modal.data.proc.process_code}`,body);
            if(r.data.error){showToast(r.data.error,false);}else{showToast(`${modal.data.proc.process_code} updated`);closeModal();refreshPage('PROCESS');}
          } catch(err){ showToast(err.response?.data?.error||'Failed',false); }
        }}>
          <FormRow label="Process Name"><Input name="name" defaultValue={modal.data.proc.name} required className="w-full"/></FormRow>
          <FormRow label="Standard Time (min)"><Input name="std_time_min" type="number" defaultValue={modal.data.proc.std_time_min} required className="w-full"/></FormRow>
          <FormRow label="Description"><Input name="description" defaultValue={modal.data.proc.description||''} className="w-full"/></FormRow>
          <FormRow label="Equipment">
            <select name="equip_code" defaultValue={modal.data.proc.equip_code||''} className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs w-full">
              <option value="">None</option>
              {(extra.equips||[]).map(e=><option key={e.equip_code} value={e.equip_code}>{e.equip_code} - {e.name}</option>)}
            </select>
          </FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={closeModal} className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer">Cancel</button>
            <BtnSuccess type="submit">Update</BtnSuccess>
          </div>
        </form>
        )}
      </Modal>

      {/* ── MODAL: Work Order Detail ───────────────────────── */}
      <Modal open={modal.type==='wo_detail'} onClose={closeModal} title={`Work Order Detail: ${modal.data?.detail?.wo_id||''}`}>
        {modal.data?.detail && (() => {
          const d = modal.data.detail;
          return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><span className="text-slate-500">Item:</span> <span className="text-white font-bold">{d.item?.name}</span> <span className="text-blue-400 font-mono">({d.item?.code})</span></div>
              <div><span className="text-slate-500">Status:</span> <Badge v={d.status}/></div>
              <div><span className="text-slate-500">Plan Qty:</span> <span className="text-white">{d.qty}</span></div>
              <div><span className="text-slate-500">Progress:</span> <span className="text-emerald-400 font-bold">{d.progress_pct}%</span></div>
              <div><span className="text-slate-500">Work Date:</span> <span className="text-white">{d.work_date}</span></div>
              <div><span className="text-slate-500">Equipment:</span> <span className="text-purple-400">{d.equip_code||'-'}</span></div>
            </div>
            {/* Progress bar */}
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${d.progress_pct>=100?'bg-emerald-500':d.progress_pct>=50?'bg-blue-500':'bg-amber-500'}`} style={{width:`${Math.min(d.progress_pct,100)}%`}}/>
            </div>
            {/* Routing */}
            {(d.routing||[]).length>0 && (
              <div>
                <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-2">Routing</h4>
                <div className="flex gap-2 items-center flex-wrap">
                  {d.routing.map((r,i)=>(
                    <React.Fragment key={i}>
                      <div className="bg-[#0f172a] px-3 py-2 rounded-lg border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-600">Step {r.seq}</div>
                        <div className="text-blue-400 font-bold text-xs">{r.process}</div>
                        <div className="text-amber-400 text-[10px]">{r.cycle_time}min</div>
                      </div>
                      {i < d.routing.length-1 && <span className="text-slate-600">→</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
            {/* Results */}
            {(d.results||[]).length>0 && (
              <div>
                <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-2">Work Results</h4>
                <Table cols={['ID','Good','Defect','Worker','Start','End']}
                  rows={d.results}
                  renderRow={(r,k)=>(
                    <tr key={k}>
                      <td className="p-2 text-blue-400 font-mono">{r.result_id}</td>
                      <td className="p-2 text-emerald-400 font-bold">{r.good_qty}</td>
                      <td className="p-2 text-red-400">{r.defect_qty}</td>
                      <td className="p-2">{r.worker_id||'-'}</td>
                      <td className="p-2 text-[10px]">{r.start_time||'-'}</td>
                      <td className="p-2 text-[10px]">{r.end_time||'-'}</td>
                    </tr>
                  )} />
              </div>
            )}
          </div>
          );
        })()}
      </Modal>

      {/* ── MODAL: LOT Trace (추적) ────────────────────────── */}
      <Modal open={modal.type==='lot_trace'} onClose={closeModal} title="LOT Traceability (추적)">
        <div className="space-y-4">
          <div className="flex gap-2">
            <Input ref={lotTraceRef} className="flex-1" placeholder="Enter LOT No (e.g. LOT-20260101-001)"/>
            <BtnSuccess onClick={async()=>{
              const lotNo=(lotTraceRef.current?.value || '').trim();
              if(!lotNo){showToast('LOT번호를 입력하세요',false);return;}
              try{
                const r=await axios.get(`/api/lot/trace/${lotNo}`);
                if(r.data.error){showToast(r.data.error,false);}else{setExtra(p=>({...p,lotTrace:r.data}));}
              }catch(err){showToast('LOT 추적 실패',false);}
            }}>Trace</BtnSuccess>
          </div>
          {extra.lotTrace && (
            <div className="space-y-3">
              <div className="bg-[#0f172a] p-3 rounded-lg border border-slate-800">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-bold text-xs">LOT: <span className="text-blue-400 font-mono">{extra.lotTrace.lot_no}</span></span>
                  <Badge v={extra.lotTrace.trace_complete ? 'PASS' : 'FAIL'}/>
                </div>
              </div>
              {/* Inventory info */}
              {(extra.lotTrace.inventory||[]).length>0 && (
                <div>
                  <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-1">Inventory</h4>
                  {extra.lotTrace.inventory.map((inv,i)=>(
                    <div key={i} className="bg-[#0f172a] p-2 rounded-lg border border-slate-800 mb-1 text-xs">
                      <span className="text-blue-400 font-mono">{inv.item_code}</span> <span className="text-white">{inv.item_name}</span>
                      <span className="text-emerald-400 ml-2 font-bold">{inv.qty} EA</span>
                      <span className="text-slate-500 ml-2">WH:{inv.warehouse} LOC:{inv.location||'-'}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Transactions */}
              {(extra.lotTrace.transactions||[]).length>0 && (
                <div>
                  <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-1">Transactions</h4>
                  <Table cols={['Slip','Item','Type','Qty','Warehouse','Supplier','Time']}
                    rows={extra.lotTrace.transactions}
                    renderRow={(t,k)=>(
                      <tr key={k}>
                        <td className="p-2 text-blue-400 font-mono text-[10px]">{t.slip_no}</td>
                        <td className="p-2">{t.item_code}</td>
                        <td className="p-2"><Badge v={t.type}/></td>
                        <td className="p-2 font-bold">{t.qty}</td>
                        <td className="p-2">{t.warehouse||'-'}</td>
                        <td className="p-2">{t.supplier||'-'}</td>
                        <td className="p-2 text-[10px] text-slate-500">{t.time||'-'}</td>
                      </tr>
                    )} />
                </div>
              )}
              {/* Work Orders */}
              {(extra.lotTrace.work_orders||[]).length>0 && (
                <div>
                  <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-1">Related Work Orders</h4>
                  {extra.lotTrace.work_orders.map((wo,i)=>(
                    <div key={i} className="bg-[#0f172a] p-2 rounded-lg border border-slate-800 mb-1 text-xs">
                      <div className="flex justify-between">
                        <span><span className="text-blue-400 font-mono">{wo.wo_id}</span> <span className="text-white">{wo.item_name}</span></span>
                        <Badge v={wo.status}/>
                      </div>
                      <div className="text-slate-500 text-[10px]">Equipment: {wo.equip_code||'-'} | Date: {wo.work_date}</div>
                      {(wo.results||[]).map((r,ri)=>(
                        <div key={ri} className="text-[10px] ml-4 text-slate-400">
                          Worker:{r.worker_id||'-'} Good:{r.good_qty} Defect:{r.defect_qty} [{r.start_time||'-'} ~ {r.end_time||'-'}]
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
              {/* Inspections */}
              {(extra.lotTrace.inspections||[]).length>0 && (
                <div>
                  <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-1">Quality Inspections</h4>
                  {extra.lotTrace.inspections.map((ins,i)=>(
                    <div key={i} className="bg-[#0f172a] p-2 rounded-lg border border-slate-800 mb-1 text-xs flex justify-between items-center">
                      <span><span className="text-blue-400 font-mono">{ins.inspection_id}</span> <span className="text-slate-400">{ins.type}</span></span>
                      <span><Badge v={ins.judgment}/> <span className="text-slate-500 text-[10px]">{ins.inspector_id||'-'} {ins.time||''}</span></span>
                    </div>
                  ))}
                </div>
              )}
              {(extra.lotTrace.inventory||[]).length===0 && (extra.lotTrace.transactions||[]).length===0 && (
                <div className="text-center text-slate-600 py-4">No trace data found for this LOT.</div>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* ── MODAL: User Approval (관리자 승인) ─────────────── */}
      <Modal open={modal.type==='user_approve'} onClose={closeModal} title="User Approval (사용자 승인)">
        <div className="space-y-3">
          {(extra.userList||[]).length > 0 ? (
            <div>
              <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-2">Pending Approval</h4>
              {(extra.userList||[]).filter(u=>!u.is_approved).length === 0 ? (
                <div className="text-center text-slate-600 py-4">No pending users</div>
              ) : (
                (extra.userList||[]).filter(u=>!u.is_approved).map(u=>(
                  <div key={u.user_id} className="bg-[#0f172a] p-3 rounded-lg border border-slate-800 mb-2 flex items-center justify-between">
                    <div>
                      <div className="text-white font-bold text-xs">{u.name} <span className="text-slate-500 font-mono text-[10px]">({u.user_id})</span></div>
                      <div className="text-slate-500 text-[10px]">{u.email||'-'} | Role: {u.role} | {u.created_at}</div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={async()=>{try{const r=await axios.put(`/api/auth/approve/${u.user_id}`,{approved:true});if(r.data.error){showToast(r.data.error,false);}else{showToast(`${u.user_id} approved`);const rr=await axios.get('/api/auth/users');setExtra(p=>({...p,userList:rr.data.users||[]}));}}catch(err){showToast('Approval failed',false);}}}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1 rounded text-[10px] font-bold cursor-pointer">Approve</button>
                      <button onClick={async()=>{try{const r=await axios.put(`/api/auth/approve/${u.user_id}`,{approved:false});if(r.data.error){showToast(r.data.error,false);}else{showToast(`${u.user_id} rejected`);const rr=await axios.get('/api/auth/users');setExtra(p=>({...p,userList:rr.data.users||[]}));}}catch(err){showToast('Rejection failed',false);}}}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-[10px] font-bold cursor-pointer">Reject</button>
                    </div>
                  </div>
                ))
              )}
              <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-2 mt-4">All Users</h4>
              <Table cols={['ID','Name','Role','Email','Approved','Created']}
                rows={extra.userList||[]}
                renderRow={(u,k)=>(
                  <tr key={k}>
                    <td className="p-2 text-blue-400 font-mono">{u.user_id}</td>
                    <td className="p-2 text-white">{u.name}</td>
                    <td className="p-2"><Badge v={u.role==='admin'?'RUNNING':u.role==='manager'?'HOLD':'NORMAL'}/> <span className="text-xs">{u.role}</span></td>
                    <td className="p-2 text-slate-500">{u.email||'-'}</td>
                    <td className="p-2">{u.is_approved ? <span className="text-emerald-400 font-bold">Yes</span> : <span className="text-red-400 font-bold">No</span>}</td>
                    <td className="p-2 text-[10px] text-slate-500">{u.created_at}</td>
                  </tr>
                )} />
            </div>
          ) : (
            <div className="text-center text-slate-600 py-4">Loading users...</div>
          )}
        </div>
      </Modal>

      {/* ── MODAL: AI Schedule Optimize (REQ-016) ────────── */}
      <Modal open={modal.type==='schedule_optimize'} onClose={closeModal} title="AI Schedule Optimization (일정최적화)">
        <div>
          <FormRow label="Select Plans to Optimize">
            <div className="max-h-40 overflow-y-auto bg-[#0f172a] rounded-lg border border-slate-800 p-2">
              {(extra.planList||[]).filter(p=>p.status!=='DONE').length>0 ? (extra.planList||[]).filter(p=>p.status!=='DONE').map(p=>(
                <label key={p.plan_id} className="flex items-center gap-2 py-1 cursor-pointer hover:bg-slate-800/30 px-1 rounded">
                  <input type="checkbox" checked={modalSelPlans.includes(p.plan_id)} onChange={e=>{
                    setModalSelPlans(prev=>e.target.checked?[...prev,p.plan_id]:prev.filter(id=>id!==p.plan_id));
                  }}/>
                  <span className="text-xs text-white">#{p.plan_id} - {p.item_name} (qty:{p.qty}, due:{p.due_date})</span>
                  <Badge v={p.priority}/>
                </label>
              )) : <span className="text-slate-600 text-xs">No active plans</span>}
            </div>
          </FormRow>
          <div className="flex justify-end gap-2 mb-4">
            <BtnSuccess onClick={async()=>{
              if(modalSelPlans.length===0){showToast('Select at least one plan',false);return;}
              try {
                const r=await axios.post('/api/ai/schedule-optimize',{plan_ids:modalSelPlans});
                if(r.data.error) throw {response:{data:r.data}};
                setModalSchedule(r.data);
                showToast(`Optimized: makespan ${r.data.makespan}min, util ${(r.data.utilization*100).toFixed(0)}%`);
              } catch(err){ showToast(err.response?.data?.error||'Optimization failed',false); }
            }}>Optimize</BtnSuccess>
          </div>
          {modalSchedule && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#0f172a] p-3 rounded-lg border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-500 uppercase">Makespan</div>
                  <div className="text-xl font-bold text-blue-400">{modalSchedule.makespan} min</div>
                </div>
                <div className="bg-[#0f172a] p-3 rounded-lg border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-500 uppercase">Utilization</div>
                  <div className="text-xl font-bold text-emerald-400">{(modalSchedule.utilization*100).toFixed(0)}%</div>
                </div>
              </div>
              <h4 className="text-slate-400 font-bold text-[10px] uppercase">Gantt Chart</h4>
              <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800 overflow-x-auto">
                {(() => {
                  const equips = [...new Set((modalSchedule.schedule||[]).map(s=>s.equip))];
                  const maxEnd = Math.max(...(modalSchedule.schedule||[]).map(s=>s.end_min),1);
                  const colors = ['bg-blue-500','bg-purple-500','bg-amber-500','bg-emerald-500','bg-red-500','bg-cyan-500','bg-pink-500'];
                  return equips.map((eq,ei)=>(
                    <div key={eq} className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] text-slate-400 w-20 truncate">{eq}</span>
                      <div className="flex-1 h-6 bg-slate-800 rounded relative" style={{minWidth:'300px'}}>
                        {(modalSchedule.schedule||[]).filter(s=>s.equip===eq).map((s,si)=>(
                          <div key={si} className={`absolute h-full rounded ${colors[s.plan_id%colors.length]} opacity-80 flex items-center justify-center`}
                            style={{left:`${(s.start_min/maxEnd)*100}%`,width:`${((s.end_min-s.start_min)/maxEnd)*100}%`}}
                            title={`Plan #${s.plan_id}: ${s.start_min}-${s.end_min}min`}>
                            <span className="text-[8px] text-white font-bold truncate px-1">P{s.plan_id}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ));
                })()}
                <div className="flex justify-between mt-1">
                  <span className="text-[9px] text-slate-600">0 min</span>
                  <span className="text-[9px] text-slate-600">{Math.max(...(modalSchedule.schedule||[]).map(s=>s.end_min),0)} min</span>
                </div>
              </div>
              <Table cols={['Seq','Plan ID','Equipment','Start (min)','End (min)','Duration']}
                rows={modalSchedule.schedule||[]}
                renderRow={(s,k)=>(
                  <tr key={k}>
                    <td className="p-2 text-white">{s.seq}</td>
                    <td className="p-2 text-blue-400 font-mono">#{s.plan_id}</td>
                    <td className="p-2 text-purple-400">{s.equip}</td>
                    <td className="p-2">{s.start_min}</td>
                    <td className="p-2">{s.end_min}</td>
                    <td className="p-2 text-amber-400 font-bold">{s.duration_min}m</td>
                  </tr>
                )} />
            </div>
          )}
        </div>
      </Modal>

    </div>
  );
};
export default App;
