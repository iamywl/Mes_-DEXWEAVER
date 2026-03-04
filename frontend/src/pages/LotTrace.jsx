import React, { useState } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function LotTrace() {
  const [lotNo, setLotNo] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const trace = async () => {
    if (!lotNo) return;
    setLoading(true);
    try { const r = await api.get(`/api/lot/trace/${lotNo}`); setData(r.data); } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="LOT 추적" />
      <div className="flex gap-2">
        <input value={lotNo} onChange={e=>setLotNo(e.target.value)} placeholder="LOT 번호 입력"
          className="border rounded px-3 py-1 flex-1" onKeyDown={e=>e.key==='Enter'&&trace()} />
        <button onClick={trace} className="px-4 py-1 bg-blue-600 text-white rounded">추적</button>
      </div>
      {loading && <LoadingSpinner />}
      {data && (
        <Card>
          <h3 className="font-bold mb-2">LOT: {data.lot_no}</h3>
          <pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
}
