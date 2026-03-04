/**
 * MSA page — Measurement System Analysis studies.
 * Columns: ID, Gauge, Type, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Gauge', 'Type', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.study_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.study_id || '-'}</td>
    <td className="p-3">{row.gauge || row.gauge_id || row.gauge_name || '-'}</td>
    <td className="p-3">{row.type || row.study_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const MSA = () => (
  <GenericListPage
    title="MSA (Measurement System Analysis)"
    apiPath="/api/msa/studies"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'study_id', 'gauge', 'gauge_id', 'gauge_name', 'type', 'study_type']}
  />
);

export default MSA;
