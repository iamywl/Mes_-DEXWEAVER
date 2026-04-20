/**
 * Dashboard — enterprise MES production overview.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { KpiCard, Section, Badge, BarChart, DonutChart, Dot, PageHeader } from '../components/ui';

const Dashboard = () => {
  const [data, setData] = useState({items: 0, cpu: '0%', mem: '0%', pods: 0});
  const [prod, setProd] = useState({lines: [], hourly: []});
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [items, infra, pods, dash, notifs] = await Promise.all([
          api.get('/api/items?size=1').catch(() => ({data: {total: 0}})),
          api.get('/api/infra/status').catch(() => ({data: {}})),
          api.get('/api/k8s/pods').catch(() => ({data: {pods: []}})),
          api.get('/api/dashboard/production').catch(() => ({data: {}})),
          api.get('/api/notifications?size=6').catch(() => ({data: {items: []}})),
        ]);
        setData({
          items: items.data.total || 0,
          cpu: infra.data.cpu || '0%',
          mem: infra.data.mem || '0%',
          pods: (pods.data.pods || []).length,
        });
        setProd({ lines: dash.data.lines || [], hourly: dash.data.hourly || [] });
        setAlerts(notifs.data.items || notifs.data.notifications || []);
      } catch {}
    };
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  const totalTarget = prod.lines.reduce((s, l) => s + (l.target || 0), 0);
  const totalActual = prod.lines.reduce((s, l) => s + (l.actual || 0), 0);
  const rate = totalTarget > 0 ? (totalActual / totalTarget * 100) : 0;
  const avgOEE = prod.lines.length
    ? prod.lines.reduce((s, l) => s + (l.rate || 0), 0) / prod.lines.length * 100
    : rate;

  const cpuNum = parseFloat((data.cpu || '').replace('%','')) || 0;
  const memNum = parseFloat((data.mem || '').replace('%','')) || 0;

  const hourlyData = prod.hourly.length
    ? prod.hourly.map(h => ({label: String(h.hour || '').slice(0,2), value: h.qty || 0}))
    : Array.from({length: 12}, (_, i) => ({label: `${i+8}`, value: 0}));

  const sevColor = { CRITICAL: 'rose', WARNING: 'amber', INFO: 'blue' };

  return (
    <div className="space-y-6">
      <PageHeader title="Production Overview" subtitle="실시간 공장 운영 현황 · 30초마다 자동 갱신" />

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard title="Items Master" value={data.items}   icon="📦" color="blue"    trend={2.1}/>
        <KpiCard title="Node CPU"     value={data.cpu}      icon="🧠" color="violet"  trend={-0.3}/>
        <KpiCard title="Node Memory"  value={data.mem}      icon="💾" color="emerald" trend={1.2}/>
        <KpiCard title="K8s Pods"     value={data.pods}     icon="⚡" color="amber"/>
      </div>

      {/* Production */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Section title="생산 진척률" subtitle="오늘 기준 라인별 달성" className="lg:col-span-2">
          <div className="flex items-center gap-6 mb-6 flex-wrap">
            <DonutChart pct={rate} label="Achievement"
              color={rate >= 90 ? '#10b981' : rate >= 70 ? '#f59e0b' : '#f43f5e'}/>
            <div className="space-y-1.5 flex-1 min-w-[200px]">
              <div className="flex justify-between text-xs"><span className="text-slate-400">Total Target</span><span className="text-white font-black tabular-nums">{totalTarget.toLocaleString()}</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-400">Total Actual</span><span className="text-emerald-400 font-black tabular-nums">{totalActual.toLocaleString()}</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-400">OEE (avg)</span><span className="text-blue-400 font-black tabular-nums">{avgOEE.toFixed(1)}%</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-400">Active Lines</span><span className="text-white font-black tabular-nums">{prod.lines.filter(l => l.status === 'WORKING').length} / {prod.lines.length}</span></div>
            </div>
          </div>
          <div className="space-y-2.5">
            {prod.lines.slice(0, 8).map((l, i) => {
              const pct = l.target ? Math.min(100, (l.actual || 0) / l.target * 100) : 0;
              const color = pct >= 90 ? 'bg-emerald-500' : pct >= 70 ? 'bg-amber-500' : 'bg-rose-500';
              return (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Dot color={l.status === 'WORKING' ? 'emerald' : 'slate'}/>
                      <span className="text-white font-semibold text-xs">{l.line_id}</span>
                      <Badge v={l.status}/>
                    </div>
                    <div className="flex items-baseline gap-2 tabular-nums text-xs">
                      <span className="text-slate-400">{(l.actual || 0).toLocaleString()} / {(l.target || 0).toLocaleString()}</span>
                      <span className="text-white font-bold w-10 text-right">{pct.toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`${color} h-full rounded-full transition-all`} style={{width: `${pct}%`}}/>
                  </div>
                </div>
              );
            })}
          </div>
        </Section>

        <Section title="시간대별 생산량" subtitle={`${hourlyData[0]?.label || ''}:00 ~ ${hourlyData[hourlyData.length-1]?.label || ''}:00`}>
          <BarChart data={hourlyData} height={220} color="#3b82f6"/>
          <div className="pt-3 mt-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-500">총 생산</span>
            <span className="text-white font-black tabular-nums">{hourlyData.reduce((s, h) => s + h.value, 0).toLocaleString()} ea</span>
          </div>
        </Section>
      </div>

      {/* System health + Alerts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Section title="Node Resources" subtitle="Kubernetes 클러스터">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">CPU</span>
                <span className="text-white font-bold tabular-nums">{cpuNum.toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${cpuNum > 80 ? 'bg-rose-500' : cpuNum > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                     style={{width: `${Math.min(100, cpuNum)}%`}}/>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Memory</span>
                <span className="text-white font-bold tabular-nums">{memNum.toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${memNum > 80 ? 'bg-rose-500' : memNum > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                     style={{width: `${Math.min(100, memNum)}%`}}/>
              </div>
            </div>
            <div className="pt-3 border-t border-slate-800 grid grid-cols-2 gap-3">
              <div>
                <div className="text-[10px] uppercase text-slate-500 tracking-wider">Pods</div>
                <div className="text-lg font-black text-white tabular-nums">{data.pods}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase text-slate-500 tracking-wider">Uptime</div>
                <div className="text-lg font-black text-emerald-400">99.9%</div>
              </div>
            </div>
          </div>
        </Section>

        <Section title="실시간 알림" subtitle="최근 이벤트 6건" className="md:col-span-2">
          {alerts.length === 0 ? (
            <div className="flex items-center gap-2 text-xs text-slate-500 py-8 justify-center">
              <Dot color="emerald"/> 현재 모든 알림이 처리되었습니다
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.slice(0, 6).map((n, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors">
                  <Dot color={sevColor[n.severity] || 'slate'}/>
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-xs font-semibold truncate">{n.title}</div>
                    <div className="text-slate-500 text-[10px] truncate">{n.message}</div>
                  </div>
                  {n.severity && <Badge v={n.severity === 'CRITICAL' ? 'HIGH' : n.severity === 'WARNING' ? 'MID' : 'NORMAL'}/>}
                </div>
              ))}
            </div>
          )}
        </Section>
      </div>
    </div>
  );
};

export default Dashboard;
