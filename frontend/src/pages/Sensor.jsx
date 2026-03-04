import React, { useState } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function Sensor() {
  const [equip, setEquip] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!equip) return;
    setLoading(true);
    try { const r = await api.get(`/api/datacollect/realtime/${equip}`); setData(r.data); } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="센서 데이터 수집" />
      <div className="flex gap-2">
        <input value={equip} onChange={e=>setEquip(e.target.value)} placeholder="설비코드" className="border rounded px-3 py-1" />
        <button onClick={load} className="px-4 py-1 bg-blue-600 text-white rounded">조회</button>
      </div>
      {loading && <LoadingSpinner />}
      {data && <Card><pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre></Card>}
    </div>
  );
}
