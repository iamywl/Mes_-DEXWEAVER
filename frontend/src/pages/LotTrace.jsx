/**
 * LotTrace page — LOT traceability with input field for lot_no.
 */
import React, { useState } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, Input, Btn, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const LotTrace = () => {
  const [lotNo, setLotNo] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const trace = async () => {
    if (!lotNo.trim()) {
      showToast('Please enter a LOT number', false);
      return;
    }
    setLoading(true);
    setData(null);
    try {
      const r = await api.get(`/api/lot/trace/${lotNo.trim()}`);
      setData(r.data);
    } catch (err) {
      showToast('Failed to trace LOT', false);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="LOT Traceability" />

      <div className="flex gap-2 items-end">
        <div className="flex-1">
          <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1">LOT Number</label>
          <Input
            value={lotNo}
            onChange={e => setLotNo(e.target.value)}
            placeholder="Enter LOT number (e.g., LOT-2024-001)"
            className="w-full"
            onKeyDown={e => e.key === 'Enter' && trace()}
          />
        </div>
        <Btn onClick={trace} disabled={loading}>
          {loading ? 'Tracing...' : 'Trace'}
        </Btn>
      </div>

      {loading && <LoadingSpinner />}

      {data && !loading && (
        <div className="space-y-3">
          {/* LOT Info */}
          <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
            <h3 className="text-white text-xs font-bold mb-2">LOT Information</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-slate-300">
              <div>LOT No: <span className="text-white font-mono">{data.lot_no || lotNo}</span></div>
              <div>Item: <span className="text-white">{data.item_code || data.item || '-'}</span></div>
              <div>Qty: <span className="text-white">{data.quantity ?? '-'}</span></div>
              <div>Status: {data.status && <Badge v={data.status} />}</div>
            </div>
          </div>

          {/* Trace Steps */}
          {data.trace && data.trace.length > 0 && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
              <table className="w-full text-left">
                <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Step</th>
                    <th className="p-3">Process</th>
                    <th className="p-3">Equipment</th>
                    <th className="p-3">Worker</th>
                    <th className="p-3">Time</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {data.trace.map((step, i) => (
                    <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                      <td className="p-3">{i + 1}</td>
                      <td className="p-3">{step.process || step.process_code || '-'}</td>
                      <td className="p-3">{step.equipment || step.equip_code || '-'}</td>
                      <td className="p-3">{step.worker || step.operator || '-'}</td>
                      <td className="p-3">{step.timestamp || step.time || '-'}</td>
                      <td className="p-3"><Badge v={step.status || 'DONE'} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Raw data fallback */}
          {!data.trace && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
              <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {!data && !loading && (
        <EmptyState message="Enter a LOT number and click Trace to view traceability data" />
      )}
    </div>
  );
};

export default LotTrace;
