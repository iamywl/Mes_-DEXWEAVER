/**
 * Dispatch page — Auto-dispatch stub page.
 */
import React, { useState } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, Btn, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const Dispatch = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const autoDispatch = async () => {
    setLoading(true);
    setResult(null);
    try {
      const r = await api.post('/api/dispatch/auto', {});
      setResult(r.data);
      showToast('Auto-dispatch completed');
    } catch (err) {
      showToast('Auto-dispatch failed', false);
    }
    setLoading(false);
  };

  const assignments = result?.assignments || result?.dispatches || (Array.isArray(result) ? result : []);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Auto Dispatch"
        actions={
          <Btn onClick={autoDispatch} disabled={loading}>
            {loading ? 'Running...' : 'Run Auto Dispatch'}
          </Btn>
        }
      />

      <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
        <p className="text-slate-400 text-xs">
          Auto-dispatch uses optimization algorithms (OR-Tools) to automatically assign work orders
          to equipment based on capacity, setup times, and due dates.
        </p>
      </div>

      {loading && <LoadingSpinner />}

      {result && !loading && assignments.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
          <table className="w-full text-left">
            <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="p-3">Work Order</th>
                <th className="p-3">Equipment</th>
                <th className="p-3">Start</th>
                <th className="p-3">End</th>
                <th className="p-3">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {assignments.map((a, i) => (
                <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                  <td className="p-3 font-mono">{a.wo_code || a.work_order || '-'}</td>
                  <td className="p-3">{a.equip_code || a.equipment || '-'}</td>
                  <td className="p-3">{a.start_time || a.start || '-'}</td>
                  <td className="p-3">{a.end_time || a.end || '-'}</td>
                  <td className="p-3"><Badge v={a.priority || 'NORMAL'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {result && !loading && assignments.length === 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
          <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}

      {!result && !loading && (
        <EmptyState message="Click 'Run Auto Dispatch' to generate optimized work order assignments" />
      )}
    </div>
  );
};

export default Dispatch;
