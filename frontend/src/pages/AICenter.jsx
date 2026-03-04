import React, { useState } from 'react';
import api from '../services/api';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

export default function AICenter() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runInsight = async () => {
    setLoading(true);
    try {
      const r = await api.post('/api/ai/insights', {});
      setResult(r.data);
    } catch { setResult({ error: 'AI 분석 실패' }); }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <PageHeader title="AI 센터" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><h3 className="font-bold mb-2">수요 예측</h3><p className="text-sm text-gray-600">Prophet 기반 수요 예측</p></Card>
        <Card><h3 className="font-bold mb-2">불량 예측</h3><p className="text-sm text-gray-600">XGBoost 기반 불량 예측</p></Card>
        <Card><h3 className="font-bold mb-2">설비 고장 예측</h3><p className="text-sm text-gray-600">IsolationForest 기반 이상 감지</p></Card>
      </div>
      <button onClick={runInsight} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700" disabled={loading}>
        {loading ? '분석 중...' : 'AI 인사이트 실행'}
      </button>
      {result && <Card><pre className="text-xs overflow-auto">{JSON.stringify(result, null, 2)}</pre></Card>}
    </div>
  );
}
