/**
 * SPC page — Statistical Process Control with item selector.
 * Stub: user enters item_code, fetches /api/quality/spc/{item_code}.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, Input, Btn, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const SPC = () => {
  const [itemCode, setItemCode] = useState('');
  const [items, setItems] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    const loadItems = async () => {
      try {
        const r = await api.get('/api/items?size=200');
        setItems(r.data.items || []);
      } catch {}
    };
    loadItems();
  }, []);

  const fetchSPC = async () => {
    if (!itemCode) {
      showToast('Please select or enter an item code', false);
      return;
    }
    setLoading(true);
    setData(null);
    try {
      const r = await api.get(`/api/quality/spc/${itemCode}`);
      setData(r.data);
    } catch (err) {
      showToast('Failed to load SPC data', false);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="SPC (Statistical Process Control)" />
      <div className="flex gap-2 items-end">
        <div className="flex-1">
          <label className="block text-slate-400 text-[10px] uppercase font-bold mb-1">Item Code</label>
          <div className="flex gap-2">
            {items.length > 0 ? (
              <select
                value={itemCode}
                onChange={e => setItemCode(e.target.value)}
                className="bg-[#0f172a] border border-slate-700 p-2 rounded-lg text-white text-xs flex-1"
              >
                <option value="">-- Select Item --</option>
                {items.map(it => (
                  <option key={it.item_code} value={it.item_code}>
                    {it.item_code} - {it.name}
                  </option>
                ))}
              </select>
            ) : (
              <Input
                value={itemCode}
                onChange={e => setItemCode(e.target.value)}
                placeholder="Enter item code"
                className="flex-1"
                onKeyDown={e => e.key === 'Enter' && fetchSPC()}
              />
            )}
            <Btn onClick={fetchSPC} disabled={loading}>
              {loading ? 'Loading...' : 'Analyze'}
            </Btn>
          </div>
        </div>
      </div>

      {loading && <LoadingSpinner />}

      {data && !loading && (
        <div className="space-y-3">
          {data.summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Card title="Mean" value={data.summary.mean?.toFixed(2) ?? '-'} color="text-blue-400" />
              <Card title="Std Dev" value={data.summary.std_dev?.toFixed(3) ?? '-'} color="text-emerald-400" />
              <Card title="Cp" value={data.summary.cp?.toFixed(2) ?? '-'} color="text-amber-400" />
              <Card title="Cpk" value={data.summary.cpk?.toFixed(2) ?? '-'} color="text-purple-400" />
            </div>
          )}
          {data.control_limits && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
              <h3 className="text-white text-xs font-bold mb-2">Control Limits</h3>
              <div className="grid grid-cols-3 gap-2 text-xs text-slate-300">
                <div>UCL: <span className="text-red-400 font-mono">{data.control_limits.ucl?.toFixed(3) ?? '-'}</span></div>
                <div>CL: <span className="text-blue-400 font-mono">{data.control_limits.cl?.toFixed(3) ?? '-'}</span></div>
                <div>LCL: <span className="text-red-400 font-mono">{data.control_limits.lcl?.toFixed(3) ?? '-'}</span></div>
              </div>
            </div>
          )}
          {data.measurements && data.measurements.length > 0 && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
              <table className="w-full text-left">
                <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">#</th>
                    <th className="p-3">Value</th>
                    <th className="p-3">In Control</th>
                    <th className="p-3">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {data.measurements.map((m, i) => (
                    <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                      <td className="p-3">{i + 1}</td>
                      <td className="p-3 font-mono">{m.value?.toFixed(3) ?? '-'}</td>
                      <td className="p-3"><Badge v={m.in_control ? 'PASS' : 'FAIL'} /></td>
                      <td className="p-3">{m.timestamp || m.time || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!data.measurements && !data.summary && (
            <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
              <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {!data && !loading && (
        <EmptyState message="Select an item code and click Analyze to view SPC data" />
      )}
    </div>
  );
};

export default SPC;
