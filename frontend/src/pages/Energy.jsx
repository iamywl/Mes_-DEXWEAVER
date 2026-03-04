import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function Energy() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const r = await api.get('/api/energy/dashboard'); setData(r.data); } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <PageHeader title="에너지 관리" />
      {data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card><h3 className="font-bold">에너지 대시보드</h3><pre className="text-xs overflow-auto max-h-60">{JSON.stringify(data, null, 2)}</pre></Card>
        </div>
      ) : <Card>데이터 없음</Card>}
    </div>
  );
}
