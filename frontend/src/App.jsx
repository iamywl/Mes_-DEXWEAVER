import React, { useState, useEffect } from 'react';
import axios from 'axios';

const App = () => {
  const [items, setItems] = useState([]);
  const [equips, setEquips] = useState([]);
  const [status, setStatus] = useState('connecting');

  const fetchData = async () => {
    try {
      const res = await axios.get('http://192.168.64.5:30461/api/data');
      setItems(res.data.items || []);
      setEquips(res.data.equipments || []);
      setStatus('online');
    } catch (e) { 
      console.error("연결 오류");
      setStatus('offline');
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 bg-[#1e293b] p-6 rounded-3xl border border-slate-700 shadow-2xl">
          <div>
            <h1 className="text-3xl font-black text-white flex items-center gap-3">
              <span className="bg-blue-600 p-2 rounded-xl text-2xl">🚀</span>
              KNU MOBILITY MES
            </h1>
            <p className="text-slate-400 mt-1 font-medium">경북대학교 혁신아카데미 실시간 통합 관제</p>
          </div>
          <div className="flex items-center gap-3 bg-[#0f172a] px-5 py-3 rounded-2xl border border-slate-700">
            <div className={`w-3 h-3 rounded-full ${status === 'online' ? 'bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)]' : 'bg-red-500'}`}></div>
            <span className="text-xs font-bold uppercase tracking-widest">{status === 'online' ? 'System Live' : 'System Offline'}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 재고 현황 카드 */}
          <div className="lg:col-span-2 bg-[#1e293b] rounded-3xl shadow-xl border border-slate-700 overflow-hidden">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">📦 Inventory Master</h2>
              <span className="text-xs text-slate-400 font-mono">Count: {items.length}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[#161e2e] text-slate-400 text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-8 py-4">Part Code</th>
                    <th className="px-8 py-4">Item Name</th>
                    <th className="px-8 py-4 text-right">Unit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {items.map((item, i) => (
                    <tr key={i} className="hover:bg-blue-900/20 transition-all group">
                      <td className="px-8 py-5 font-mono text-blue-400 group-hover:text-blue-300">{item.item_code}</td>
                      <td className="px-8 py-5 font-bold text-slate-200">{item.name}</td>
                      <td className="px-8 py-5 text-right"><span className="bg-slate-800 text-slate-400 px-3 py-1 rounded-lg text-xs font-bold">{item.unit}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {items.length === 0 && <div className="p-20 text-center text-slate-500 animate-pulse">Connecting to Warehouse DB...</div>}
            </div>
          </div>

          {/* 설비 모니터링 카드 */}
          <div className="flex flex-col gap-6">
            <div className="bg-[#1e293b] rounded-3xl p-6 shadow-xl border border-slate-700">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">⚙️ Production Line</h2>
              <div className="space-y-4">
                {equips.map((eq, i) => (
                  <div key={i} className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-[10px] font-black text-slate-500 uppercase tracking-tighter">{eq.equipment_id}</span>
                      <span className={`px-2 py-1 rounded-md text-[10px] font-black ${eq.status === 'RUN' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-slate-800 text-slate-500'}`}>
                        {eq.status}
                      </span>
                    </div>
                    <div className="text-lg font-bold text-slate-100">{eq.name}</div>
                    {eq.status === 'RUN' && (
                      <div className="mt-3 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 animate-progress origin-left"></div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
