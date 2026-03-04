/**
 * Dashboard page — production overview + system status.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Card, Badge } from '../components/ui';

const Dashboard = () => {
  const [data, setData] = useState({items: 0, cpu: '0%', mem: '0%', pods: 0});
  const [prod, setProd] = useState({lines: [], hourly: []});

  useEffect(() => {
    const load = async () => {
      try {
        const [items, infra, pods, dash] = await Promise.all([
          api.get('/api/items?size=1').catch(() => ({data: {total: 0}})),
          api.get('/api/infra/status').catch(() => ({data: {}})),
          api.get('/api/k8s/pods').catch(() => ({data: {pods: []}})),
          api.get('/api/dashboard/production').catch(() => ({data: {}})),
        ]);
        setData({
          items: items.data.total || 0,
          cpu: infra.data.cpu || '0%',
          mem: infra.data.mem || '0%',
          pods: (pods.data.pods || []).length,
        });
        setProd({
          lines: dash.data.lines || [],
          hourly: dash.data.hourly || [],
        });
      } catch {}
    };
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  const totalTarget = prod.lines.reduce((s, l) => s + (l.target || 0), 0);
  const totalActual = prod.lines.reduce((s, l) => s + (l.actual || 0), 0);
  const overallRate = totalTarget > 0 ? (totalActual / totalTarget * 100).toFixed(1) : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card title="Items" value={data.items} />
        <Card title="CPU" value={data.cpu} color="text-slate-200" />
        <Card title="Memory" value={data.mem} color="text-purple-400" />
        <Card title="Pods" value={data.pods} color="text-emerald-500" />
      </div>

      <div className="border-t border-slate-800 pt-4">
        <h3 className="text-white font-bold mb-4">Production Status (Today)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <Card title="Total Target" value={totalTarget} color="text-blue-400" />
          <Card title="Total Actual" value={totalActual} color="text-emerald-400" />
          <Card title="Achievement" value={`${overallRate}%`}
            color={overallRate >= 90 ? 'text-emerald-400' : overallRate >= 70 ? 'text-amber-400' : 'text-red-400'} />
        </div>

        {prod.lines.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-3">Line Status</h4>
              {prod.lines.map((l, i) => (
                <div key={i} className="bg-[#0f172a] p-3 rounded-xl border border-slate-800 mb-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white font-bold text-xs">{l.line_id}</span>
                    <Badge v={l.status} />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${l.rate >= 0.9 ? 'bg-emerald-500' : l.rate >= 0.7 ? 'bg-amber-500' : 'bg-red-500'}`}
                        style={{width: `${Math.min((l.rate || 0) * 100, 100)}%`}} />
                    </div>
                    <span className="text-xs text-slate-400">{l.actual}/{l.target}</span>
                    <span className={`text-[10px] font-bold ${l.rate >= 0.9 ? 'text-emerald-400' : l.rate >= 0.7 ? 'text-amber-400' : 'text-red-400'}`}>
                      {((l.rate || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div>
              <h4 className="text-slate-400 font-bold text-[10px] uppercase mb-3">Hourly Output</h4>
              <div className="bg-[#0f172a] p-4 rounded-xl border border-slate-800">
                {prod.hourly.length > 0 ? prod.hourly.map((h, i) => (
                  <div key={i} className="flex items-center gap-3 mb-1.5">
                    <span className="text-[10px] text-slate-500 w-8">{h.hour}:00</span>
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full"
                        style={{width: `${(h.qty / Math.max(...prod.hourly.map(x => x.qty), 1)) * 100}%`}} />
                    </div>
                    <span className="text-blue-400 text-[10px] font-bold w-10 text-right">{h.qty}</span>
                  </div>
                )) : <span className="text-slate-600 text-xs">No hourly data</span>}
              </div>
            </div>
          </div>
        )}
        {prod.lines.length === 0 && (
          <div className="text-slate-600 text-xs bg-[#0f172a] p-6 rounded-xl border border-slate-800 text-center">
            No production data for today
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
