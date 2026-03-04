import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner, EmptyState } from '../components/ui';

export default function Infra() {
  const [data, setData] = useState(null);
  const [pods, setPods] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [infra, k8s] = await Promise.all([api.get('/api/infra/status'), api.get('/api/k8s/pods')]);
        setData(infra.data);
        setPods(k8s.data.pods || []);
      } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-4">
      <PageHeader title="인프라 모니터링" />
      {data && <Card><h3 className="font-bold mb-2">시스템 상태</h3><pre className="text-xs overflow-auto max-h-40">{JSON.stringify(data, null, 2)}</pre></Card>}
      {pods.length > 0 && (
        <Card>
          <h3 className="font-bold mb-2">K8s Pods ({pods.length})</h3>
          <div className="space-y-1">{pods.map((p,i) => (
            <div key={i} className="flex justify-between text-sm border-b py-1">
              <span>{p.name}</span><span className={p.status==='Running'?'text-green-600':'text-red-600'}>{p.status}</span>
            </div>
          ))}</div>
        </Card>
      )}
    </div>
  );
}
