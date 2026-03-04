import React, { useState } from 'react';
import api from '../services/api';
import { PageHeader, Card } from '../components/ui';

export default function Barcode() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);

  const scan = async () => {
    if (!input) return;
    try { const r = await api.post('/api/barcode/scan', { barcode: input }); setResult(r.data); } catch {}
  };

  return (
    <div className="space-y-4">
      <PageHeader title="바코드 관리" />
      <div className="flex gap-2">
        <input value={input} onChange={e=>setInput(e.target.value)} placeholder="바코드 스캔/입력"
          className="border rounded px-3 py-1 flex-1" onKeyDown={e=>e.key==='Enter'&&scan()} />
        <button onClick={scan} className="px-4 py-1 bg-blue-600 text-white rounded">스캔</button>
      </div>
      {result && <Card><pre className="text-xs overflow-auto">{JSON.stringify(result, null, 2)}</pre></Card>}
    </div>
  );
}
