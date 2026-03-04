import React, { useState } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function Dispatch() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const autoDispatch = async () => {
    setLoading(true);
    try { const r = await api.post('/api/dispatch/auto', {}); setResult(r.data); } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="자동 디스패칭" />
      <button onClick={autoDispatch} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700" disabled={loading}>
        {loading ? '실행 중...' : '자동 디스패칭 실행'}
      </button>
      {result && <Card><pre className="text-xs overflow-auto max-h-96">{JSON.stringify(result, null, 2)}</pre></Card>}
    </div>
  );
}
