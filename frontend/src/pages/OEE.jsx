/**
 * OEE page — Overall Equipment Effectiveness dashboard with gauges.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, LoadingSpinner, EmptyState } from '../components/ui';

/** Simple gauge circle rendered with CSS conic-gradient */
const Gauge = ({ label, value, color = '#3b82f6' }) => {
  const pct = Math.min(100, Math.max(0, (value || 0) * 100));
  const displayColor = pct >= 85 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="relative w-24 h-24 rounded-full flex items-center justify-center"
        style={{
          background: `conic-gradient(${displayColor} ${pct * 3.6}deg, #1e293b ${pct * 3.6}deg)`,
        }}
      >
        <div className="absolute w-18 h-18 bg-[#0f172a] rounded-full flex items-center justify-center">
          <span className="text-white font-black text-sm">{pct.toFixed(1)}%</span>
        </div>
      </div>
      <span className="text-slate-400 text-[10px] uppercase font-bold">{label}</span>
    </div>
  );
};

const OEE = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get('/api/equipment/oee/dashboard');
        setData(r.data);
      } catch (err) {
        showToast('Failed to load OEE data', false);
      }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState message="No OEE data available" />;

  const items = data.oee_list || data.items || data.equipment || (Array.isArray(data) ? data : []);

  // Overall summary
  const avgOEE = items.length > 0
    ? items.reduce((s, d) => s + (d.oee || 0), 0) / items.length
    : 0;
  const avgAvail = items.length > 0
    ? items.reduce((s, d) => s + (d.availability || 0), 0) / items.length
    : 0;
  const avgPerf = items.length > 0
    ? items.reduce((s, d) => s + (d.performance || 0), 0) / items.length
    : 0;
  const avgQual = items.length > 0
    ? items.reduce((s, d) => s + (d.quality_rate || d.quality || 0), 0) / items.length
    : 0;

  return (
    <div className="space-y-4">
      <PageHeader title="OEE Dashboard" />

      {/* Overall Summary Gauges */}
      <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
        <h3 className="text-white text-xs font-bold mb-4 uppercase">Overall Summary</h3>
        <div className="flex justify-around flex-wrap gap-4">
          <Gauge label="OEE" value={avgOEE} />
          <Gauge label="Availability" value={avgAvail} />
          <Gauge label="Performance" value={avgPerf} />
          <Gauge label="Quality" value={avgQual} />
        </div>
      </div>

      {/* Per-Equipment Cards */}
      {items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {items.map((d, i) => (
            <div key={d.equip_code || i} className="bg-[#1e293b]/30 rounded-xl border border-slate-800 p-4">
              <h4 className="text-white font-bold text-xs mb-3">{d.equip_code || d.equipment || `Equipment ${i + 1}`}</h4>
              <div className="flex justify-around">
                <Gauge label="OEE" value={d.oee} />
                <Gauge label="Avail" value={d.availability} />
                <Gauge label="Perf" value={d.performance} />
                <Gauge label="Qual" value={d.quality_rate || d.quality} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OEE;
