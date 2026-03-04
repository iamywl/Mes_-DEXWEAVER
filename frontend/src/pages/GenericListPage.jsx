/**
 * GenericListPage — Reusable list page component for simple CRUD pages.
 * Used for pages that follow the pattern: fetch list → show table → basic filter.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Table, Badge, PageHeader, FilterBar, FilterSearch, FilterCount, LoadingSpinner, EmptyState } from '../components/ui';

const GenericListPage = ({title, apiPath, columns, renderRow, searchFields = []}) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.get(apiPath);
        const d = r.data;
        // Auto-detect array key
        const arrKey = Object.keys(d).find(k => Array.isArray(d[k]));
        setData(arrKey ? d[arrKey] : []);
      } catch {}
      setLoading(false);
    };
    load();
  }, [apiPath]);

  const filtered = data.filter(item => {
    if (!search) return true;
    const s = search.toLowerCase();
    return searchFields.some(f => (item[f] || '').toString().toLowerCase().includes(s))
      || JSON.stringify(item).toLowerCase().includes(s);
  });

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <PageHeader title={title} />
      {data.length > 0 && (
        <FilterBar>
          <FilterSearch value={search} onChange={setSearch} />
          <FilterCount total={data.length} filtered={filtered.length} />
        </FilterBar>
      )}
      {filtered.length > 0 ? (
        <Table cols={columns} rows={filtered} renderRow={renderRow} />
      ) : (
        <EmptyState message={`No ${title.toLowerCase()} data`} />
      )}
    </div>
  );
};

export default GenericListPage;
