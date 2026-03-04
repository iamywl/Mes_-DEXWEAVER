/**
 * Energy page — Energy consumption monitoring dashboard.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const Energy = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get('/api/energy/dashboard');
        setData(r.data);
      } catch (err) {
        showToast('Failed to load energy data', false);
      }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState message="No energy data available" />;

  const summary = data.summary || data;
  const byEquipment = data.by_equipment || data.equipment || [];
  const byPeriod = data.by_period || data.history || data.timeline || [];

  return (
    <div className="space-y-4">
      <PageHeader title="Energy Management" />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card
          title="Total Consumption"
          value={`${(summary.total_kwh ?? summary.total ?? 0).toLocaleString()} kWh`}
          color="text-blue-400"
        />
        <Card
          title="Peak Demand"
          value={`${(summary.peak_kw ?? summary.peak ?? 0).toLocaleString()} kW`}
          color="text-red-400"
        />
        <Card
          title="Cost"
          value={`${(summary.total_cost ?? summary.cost ?? 0).toLocaleString()}`}
          color="text-amber-400"
        />
        <Card
          title="Efficiency"
          value={summary.efficiency != null ? `${(summary.efficiency * 100).toFixed(1)}%` : '-'}
          color="text-emerald-400"
        />
      </div>

      {/* By Equipment */}
      {byEquipment.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
          <h3 className="text-white text-xs font-bold p-3 uppercase bg-[#1e293b]">Consumption by Equipment</h3>
          <table className="w-full text-left">
            <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="p-3">Equipment</th>
                <th className="p-3">Consumption (kWh)</th>
                <th className="p-3">% of Total</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {byEquipment.map((eq, i) => (
                <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                  <td className="p-3">{eq.equip_code || eq.equipment || eq.name || '-'}</td>
                  <td className="p-3 font-mono">{(eq.kwh ?? eq.consumption ?? 0).toLocaleString()}</td>
                  <td className="p-3">{eq.percentage != null ? `${eq.percentage.toFixed(1)}%` : '-'}</td>
                  <td className="p-3"><Badge v={eq.status || 'NORMAL'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Timeline */}
      {byPeriod.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
          <h3 className="text-white text-xs font-bold mb-3 uppercase">Consumption Timeline</h3>
          <div className="space-y-1">
            {byPeriod.map((p, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 w-20">{p.period || p.date || p.time || '-'}</span>
                <div className="flex-1 bg-slate-800 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-blue-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, ((p.kwh ?? p.value ?? 0) / (summary.peak_kw || 1)) * 100)}%` }}
                  />
                </div>
                <span className="text-slate-300 font-mono w-20 text-right">{(p.kwh ?? p.value ?? 0).toLocaleString()} kWh</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw fallback */}
      {byEquipment.length === 0 && byPeriod.length === 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
          <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Energy;
