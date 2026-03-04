/**
 * SQM page — Supplier Quality Management.
 * Columns: ID, Name, ASL Status, Score
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Name', 'ASL Status', 'Score'];

const renderRow = (row, i) => (
  <tr key={row.id || row.supplier_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.supplier_id || '-'}</td>
    <td className="p-3">{row.name || row.supplier_name || '-'}</td>
    <td className="p-3"><Badge v={row.asl_status || row.grade || row.status || 'NORMAL'} /></td>
    <td className="p-3">{row.score ?? '-'}</td>
  </tr>
);

const SQM = () => (
  <GenericListPage
    title="SQM (Supplier Quality Management)"
    apiPath="/api/sqm/suppliers"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'supplier_id', 'name', 'supplier_name', 'asl_status', 'grade', 'status']}
  />
);

export default SQM;
