/**
 * Infra page — Infrastructure monitoring.
 * Fetches /api/infra/status and /api/k8s/pods.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const Infra = () => {
  const [infraData, setInfraData] = useState(null);
  const [pods, setPods] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const [infraRes, podsRes] = await Promise.allSettled([
          api.get('/api/infra/status'),
          api.get('/api/k8s/pods'),
        ]);
        if (infraRes.status === 'fulfilled') setInfraData(infraRes.value.data);
        if (podsRes.status === 'fulfilled') setPods(podsRes.value.data.pods || podsRes.value.data || []);
      } catch (err) {
        showToast('Failed to load infrastructure data', false);
      }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;

  const sysInfo = infraData?.system || infraData;
  const runningPods = pods.filter(p => p.status === 'Running').length;

  return (
    <div className="space-y-4">
      <PageHeader title="Infrastructure Monitoring" />

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card title="Total Pods" value={pods.length || '-'} color="text-blue-400" />
        <Card title="Running" value={runningPods || '-'} color="text-emerald-400" />
        <Card title="Failed" value={pods.length - runningPods || 0} color={pods.length - runningPods > 0 ? 'text-red-400' : 'text-emerald-400'} />
        <Card title="Status" value={infraData?.status || 'OK'} color="text-amber-400" />
      </div>

      {/* System Info */}
      {sysInfo && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-4">
          <h3 className="text-white text-xs font-bold mb-2 uppercase">System Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-slate-300">
            {sysInfo.cpu != null && <div>CPU: <span className="text-white font-mono">{sysInfo.cpu}%</span></div>}
            {sysInfo.memory != null && <div>Memory: <span className="text-white font-mono">{sysInfo.memory}%</span></div>}
            {sysInfo.disk != null && <div>Disk: <span className="text-white font-mono">{sysInfo.disk}%</span></div>}
            {sysInfo.uptime && <div>Uptime: <span className="text-white">{sysInfo.uptime}</span></div>}
          </div>
          {!sysInfo.cpu && !sysInfo.memory && (
            <pre className="text-xs text-slate-400 overflow-auto max-h-40 mt-2">{JSON.stringify(sysInfo, null, 2)}</pre>
          )}
        </div>
      )}

      {/* K8s Pods Table */}
      {Array.isArray(pods) && pods.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
          <table className="w-full text-left">
            <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="p-3">Pod Name</th>
                <th className="p-3">Namespace</th>
                <th className="p-3">Status</th>
                <th className="p-3">Restarts</th>
                <th className="p-3">Age</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {pods.map((pod, i) => (
                <tr key={pod.name || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                  <td className="p-3 font-mono text-[10px]">{pod.name || '-'}</td>
                  <td className="p-3">{pod.namespace || '-'}</td>
                  <td className="p-3"><Badge v={pod.status || 'RUNNING'} /></td>
                  <td className="p-3">{pod.restarts ?? '-'}</td>
                  <td className="p-3">{pod.age || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!infraData && pods.length === 0 && (
        <EmptyState message="No infrastructure data available" />
      )}
    </div>
  );
};

export default Infra;
