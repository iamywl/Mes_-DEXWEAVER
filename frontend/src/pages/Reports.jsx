/**
 * Reports page — Production report with Date/Item/Qty/Defects/Rate columns.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Table, Badge, PageHeader, FilterBar, FilterSearch, FilterCount, LoadingSpinner, EmptyState } from '../components/ui';

const columns = ['Date', 'Item', 'Qty', 'Defects', 'Rate'];

const Reports = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const { showToast } = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get('/api/reports/production');
        const d = r.data;
        const arrKey = Object.keys(d).find(k => Array.isArray(d[k]));
        setData(arrKey ? d[arrKey] : Array.isArray(d) ? d : []);
      } catch (err) {
        showToast('Failed to load reports', false);
      }
      setLoading(false);
    };
    load();
  }, []);

  const filtered = data.filter(item => {
    if (!search) return true;
    const s = search.toLowerCase();
    return JSON.stringify(item).toLowerCase().includes(s);
  });

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <PageHeader title="Production Reports" />
      {data.length > 0 && (
        <FilterBar>
          <FilterSearch value={search} onChange={setSearch} />
          <FilterCount total={data.length} filtered={filtered.length} />
        </FilterBar>
      )}
      {filtered.length > 0 ? (
        <Table
          cols={columns}
          rows={filtered}
          renderRow={(row, i) => (
            <tr key={i} className="text-xs text-slate-300 hover:bg-slate-800/40">
              <td className="p-3">{row.date || row.production_date || '-'}</td>
              <td className="p-3">{row.item || row.item_name || row.item_code || '-'}</td>
              <td className="p-3">{row.quantity ?? row.qty ?? '-'}</td>
              <td className="p-3">{row.defects ?? row.defect_count ?? '-'}</td>
              <td className="p-3">
                {row.rate != null
                  ? `${(Number(row.rate) * 100).toFixed(1)}%`
                  : row.defect_rate != null
                    ? `${Number(row.defect_rate).toFixed(1)}%`
                    : '-'}
              </td>
            </tr>
          )}
        />
      ) : (
        <EmptyState message="No production report data" />
      )}
    </div>
  );
};

export default Reports;
