/**
 * Network page — Service map stub page (simple view).
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { PageHeader, Card, LoadingSpinner, EmptyState, Badge } from '../components/ui';

const Network = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get('/api/network/service-map');
        setData(r.data);
      } catch (err) {
        showToast('Failed to load network data', false);
      }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState message="No network service map data" />;

  const services = data.services || data.nodes || (Array.isArray(data) ? data : []);
  const connections = data.connections || data.edges || [];

  return (
    <div className="space-y-4">
      <PageHeader title="Network Service Map" />

      {/* Service Nodes */}
      {services.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {services.map((svc, i) => (
            <div key={svc.id || svc.name || i} className="bg-[#1e293b]/30 rounded-xl border border-slate-800 p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-white text-xs font-bold">{svc.name || svc.service || '-'}</span>
                <Badge v={svc.status || 'RUNNING'} />
              </div>
              <div className="text-[10px] text-slate-500 space-y-1">
                {svc.host && <div>Host: <span className="text-slate-300 font-mono">{svc.host}</span></div>}
                {svc.port && <div>Port: <span className="text-slate-300 font-mono">{svc.port}</span></div>}
                {svc.type && <div>Type: <span className="text-slate-300">{svc.type}</span></div>}
                {svc.latency != null && <div>Latency: <span className="text-slate-300">{svc.latency}ms</span></div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Connections */}
      {connections.length > 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 overflow-auto">
          <table className="w-full text-left">
            <thead className="bg-[#1e293b] text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="p-3">From</th>
                <th className="p-3">To</th>
                <th className="p-3">Protocol</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {connections.map((conn, i) => (
                <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
                  <td className="p-3">{conn.from || conn.source || '-'}</td>
                  <td className="p-3">{conn.to || conn.target || '-'}</td>
                  <td className="p-3">{conn.protocol || conn.type || '-'}</td>
                  <td className="p-3"><Badge v={conn.status || 'RUNNING'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Fallback */}
      {services.length === 0 && connections.length === 0 && (
        <div className="bg-[#0f172a] rounded-xl border border-slate-800 p-6">
          <pre className="text-xs text-slate-400 overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Network;
