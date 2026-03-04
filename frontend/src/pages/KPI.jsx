import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function KPI() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const r = await api.get('/api/kpi/fpy'); setData(r.data); } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <PageHeader title="KPI 대시보드" />
      {data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card><h3 className="font-bold">초회 합격률 (FPY)</h3><p className="text-3xl font-bold text-blue-600">{(data.overall_fpy*100||0).toFixed(1)}%</p></Card>
          <Card><pre className="text-xs overflow-auto max-h-60">{JSON.stringify(data, null, 2)}</pre></Card>
        </div>
      ) : <Card>KPI 데이터를 불러올 수 없습니다.</Card>}
    </div>
  );
}
