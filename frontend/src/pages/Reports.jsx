import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, Table, LoadingSpinner, EmptyState } from '../components/ui';

export default function Reports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('production');

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get(`/api/reports/${tab}`);
        setData(r.data);
      } catch {}
      setLoading(false);
    })();
  }, [tab]);

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <PageHeader title="보고서" />
      <div className="flex gap-2">
        {['production','quality'].map(t => (
          <button key={t} onClick={() => { setTab(t); setLoading(true); }}
            className={`px-3 py-1 rounded ${tab===t?'bg-blue-600 text-white':'bg-gray-200'}`}>
            {t==='production'?'생산':'품질'}
          </button>
        ))}
      </div>
      {data && <Card><pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre></Card>}
    </div>
  );
}
