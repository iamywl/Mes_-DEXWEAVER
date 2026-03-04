import React, { useState } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function SPC() {
  const [itemCode, setItemCode] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!itemCode) return;
    setLoading(true);
    try { const r = await api.get(`/api/quality/spc/${itemCode}`); setData(r.data); } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="SPC (통계적 공정 관리)" />
      <div className="flex gap-2">
        <input value={itemCode} onChange={e=>setItemCode(e.target.value)} placeholder="품목코드"
          className="border rounded px-3 py-1" />
        <button onClick={load} className="px-4 py-1 bg-blue-600 text-white rounded">조회</button>
      </div>
      {loading && <LoadingSpinner />}
      {data && <Card><pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre></Card>}
    </div>
  );
}
