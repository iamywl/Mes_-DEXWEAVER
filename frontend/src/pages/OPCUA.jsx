import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner, EmptyState } from '../components/ui';

export default function OPCUA() {
  const [configs, setConfigs] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [c, s] = await Promise.all([api.get('/api/opcua/config'), api.get('/api/opcua/status')]);
        setConfigs(c.data.configs || []);
        setStatus(s.data);
      } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <PageHeader title="OPC-UA 연결" />
      {status && <Card><h3 className="font-bold mb-2">연결 상태</h3><pre className="text-xs">{JSON.stringify(status, null, 2)}</pre></Card>}
      {configs.length > 0 ? configs.map((c,i) => (
        <Card key={i}><h4 className="font-bold">{c.config_id}</h4><p className="text-sm">{c.server_url} — {c.status}</p></Card>
      )) : <EmptyState message="OPC-UA 설정 없음" />}
    </div>
  );
}
