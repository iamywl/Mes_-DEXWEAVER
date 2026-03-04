/**
 * AICenter page — AI prediction center with demand forecast, defect prediction,
 * and failure prediction panels.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Card, PageHeader, Btn, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const TABS = [
  { key: 'demand', label: 'Demand Forecast', endpoint: '/api/ai/demand-forecast' },
  { key: 'defect', label: 'Defect Prediction', endpoint: '/api/ai/defect-predict' },
  { key: 'failure', label: 'Failure Prediction', endpoint: '/api/ai/failure-predict' },
];

const AICenter = () => {
  const [activeTab, setActiveTab] = useState('demand');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const fetchData = async (tab) => {
    const tabCfg = TABS.find(t => t.key === tab);
    if (!tabCfg) return;
    setLoading(true);
    setData(null);
    try {
      const r = await api.get(tabCfg.endpoint);
      setData(r.data);
    } catch (err) {
      showToast(`Failed to load ${tabCfg.label}`, false);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData(activeTab);
  }, [activeTab]);

  const renderDemand = () => {
    if (!data) return <EmptyState message="No demand forecast data" />;
    const forecasts = data.forecasts || data.predictions || (Array.isArray(data) ? data : []);
    return (
      <div className="space-y-3">
        {data.summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card title="Total Forecast" value={data.summary.total ?? '-'} color="text-blue-400" />
            <Card title="Avg Demand" value={data.summary.avg ?? '-'} color="text-emerald-400" />
            <Card title="Trend" value={data.summary.trend ?? '-'} color="text-amber-400" />
          </div>
        )}
        {forecasts.length > 0 ? (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
            <table className="w-full text-left">
              <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
                <tr>
                  <th className="p-3">Item</th>
                  <th className="p-3">Period</th>
                  <th className="p-3">Forecast Qty</th>
                  <th className="p-3">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {forecasts.map((f, i) => (
                  <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                    <td className="p-3">{f.item_code || f.item || '-'}</td>
                    <td className="p-3">{f.period || f.date || '-'}</td>
                    <td className="p-3 font-mono">{f.forecast_qty ?? f.quantity ?? f.value ?? '-'}</td>
                    <td className="p-3">{f.confidence != null ? `${(f.confidence * 100).toFixed(0)}%` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
            <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>
    );
  };

  const renderDefect = () => {
    if (!data) return <EmptyState message="No defect prediction data" />;
    const predictions = data.predictions || data.items || (Array.isArray(data) ? data : []);
    return (
      <div className="space-y-3">
        {predictions.length > 0 ? (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
            <table className="w-full text-left">
              <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
                <tr>
                  <th className="p-3">Item</th>
                  <th className="p-3">Process</th>
                  <th className="p-3">Risk Score</th>
                  <th className="p-3">Predicted Defect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {predictions.map((p, i) => (
                  <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                    <td className="p-3">{p.item_code || p.item || '-'}</td>
                    <td className="p-3">{p.process_code || p.process || '-'}</td>
                    <td className="p-3">
                      <span className={`font-mono ${(p.risk_score || 0) > 0.7 ? 'text-red-400' : (p.risk_score || 0) > 0.4 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {p.risk_score != null ? (p.risk_score * 100).toFixed(1) + '%' : '-'}
                      </span>
                    </td>
                    <td className="p-3">{p.defect_type || p.predicted_defect || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
            <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>
    );
  };

  const renderFailure = () => {
    if (!data) return <EmptyState message="No failure prediction data" />;
    const predictions = data.predictions || data.equipment || (Array.isArray(data) ? data : []);
    return (
      <div className="space-y-3">
        {predictions.length > 0 ? (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
            <table className="w-full text-left">
              <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
                <tr>
                  <th className="p-3">Equipment</th>
                  <th className="p-3">Risk Level</th>
                  <th className="p-3">Predicted Failure</th>
                  <th className="p-3">Remaining Life</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {predictions.map((p, i) => (
                  <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                    <td className="p-3">{p.equip_code || p.equipment || '-'}</td>
                    <td className="p-3">
                      <Badge v={p.risk_level || (p.anomaly_score > 0.7 ? 'HIGH' : p.anomaly_score > 0.4 ? 'MEDIUM' : 'LOW')} />
                    </td>
                    <td className="p-3">{p.predicted_failure || p.failure_type || '-'}</td>
                    <td className="p-3">{p.remaining_life != null ? `${p.remaining_life} hrs` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
            <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <PageHeader title="AI Prediction Center" />
      <div className="flex gap-2">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
              activeTab === tab.key
                ? 'bg-blue-600 text-white'
                : 'bg-[#1e293b] text-slate-400 hover:text-white border border-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {activeTab === 'demand' && renderDemand()}
          {activeTab === 'defect' && renderDefect()}
          {activeTab === 'failure' && renderFailure()}
        </>
      )}
    </div>
  );
};

export default AICenter;
