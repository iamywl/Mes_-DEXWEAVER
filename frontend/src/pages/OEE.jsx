import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner, EmptyState } from '../components/ui';

export default function OEE() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const r = await api.get('/api/equipment/oee/dashboard'); setData(r.data); } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState message="OEE 데이터 없음" />;
  const items = data.oee_list || data.items || (Array.isArray(data) ? data : []);
  return (
    <div className="space-y-4">
      <PageHeader title="OEE (설비종합효율)" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((d,i) => (
          <Card key={i}>
            <h4 className="font-bold">{d.equip_code}</h4>
            <p className="text-2xl font-bold text-blue-600">{(d.oee*100||0).toFixed(1)}%</p>
            <div className="text-xs text-gray-500 mt-1">
              가동률 {(d.availability*100||0).toFixed(1)}% · 성능 {(d.performance*100||0).toFixed(1)}% · 품질 {(d.quality_rate*100||0).toFixed(1)}%
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
