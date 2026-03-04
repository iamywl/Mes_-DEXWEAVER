import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner, EmptyState } from '../components/ui';

export default function Network() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const r = await api.get('/api/network/service-map'); setData(r.data); } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <PageHeader title="네트워크 모니터링" />
      {data ? <Card><pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre></Card> : <EmptyState message="네트워크 데이터 없음" />}
    </div>
  );
}
