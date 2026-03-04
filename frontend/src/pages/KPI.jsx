/**
 * KPI page — Key Performance Indicators with FPY charts.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, LoadingSpinner, EmptyState, Badge } from '../components/ui';

/** Simple horizontal bar for visualizing percentages */
const BarChart = ({ label, value, max = 100, color = 'bg-blue-500' }) => {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  const barColor = pct >= 90 ? 'bg-emerald-500' : pct >= 70 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="text-slate-400 w-24 truncate">{label}</span>
      <div className="flex-1 bg-slate-800 rounded-full h-4 overflow-hidden">
        <div className={`${barColor} h-full rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-white font-mono w-16 text-right">{value.toFixed(1)}%</span>
    </div>
  );
};

const KPI = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get('/api/kpi/fpy');
        setData(r.data);
      } catch (err) {
        showToast('Failed to load KPI data', false);
      }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState message="No KPI data available" />;

  const overallFpy = data.overall_fpy != null ? data.overall_fpy * 100 : null;
  const items = data.by_item || data.items || data.fpy_list || [];
  const processes = data.by_process || data.processes || [];

  return (
    <div className="space-y-4">
      <PageHeader title="KPI Dashboard" />

      {/* Overall FPY */}
      {overallFpy != null && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Card
            title="Overall FPY"
            value={`${overallFpy.toFixed(1)}%`}
            color={overallFpy >= 90 ? 'text-emerald-400' : overallFpy >= 70 ? 'text-amber-400' : 'text-red-400'}
          />
          <Card title="Target" value="95.0%" color="text-slate-400" />
          <Card
            title="Gap"
            value={`${(overallFpy - 95).toFixed(1)}%`}
            color={overallFpy >= 95 ? 'text-emerald-400' : 'text-red-400'}
          />
        </div>
      )}

      {/* FPY by Item */}
      {items.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
          <h3 className="text-white text-xs font-bold mb-3 uppercase">FPY by Item</h3>
          <div className="space-y-2">
            {items.map((item, i) => (
              <BarChart
                key={i}
                label={item.item_code || item.item || item.name || `Item ${i + 1}`}
                value={(item.fpy ?? item.rate ?? 0) * 100}
              />
            ))}
          </div>
        </div>
      )}

      {/* FPY by Process */}
      {processes.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
          <h3 className="text-white text-xs font-bold mb-3 uppercase">FPY by Process</h3>
          <div className="space-y-2">
            {processes.map((proc, i) => (
              <BarChart
                key={i}
                label={proc.process_code || proc.process || proc.name || `Process ${i + 1}`}
                value={(proc.fpy ?? proc.rate ?? 0) * 100}
              />
            ))}
          </div>
        </div>
      )}

      {/* Raw data fallback */}
      {items.length === 0 && processes.length === 0 && overallFpy == null && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
          <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default KPI;
