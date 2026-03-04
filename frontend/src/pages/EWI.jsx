/**
 * EWI page — Electronic Work Instructions list.
 * Columns: ID, WO, Status, Steps
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'WO', 'Status', 'Steps'];

const renderRow = (row, i) => (
  <tr key={row.id || row.wi_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.wi_id || '-'}</td>
    <td className="p-3">{row.wo || row.work_order_id || row.wo_code || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
    <td className="p-3">{row.steps != null ? (Array.isArray(row.steps) ? row.steps.length : row.steps) : '-'}</td>
  </tr>
);

const EWI = () => (
  <GenericListPage
    title="Electronic Work Instructions (EWI)"
    apiPath="/api/work-instructions"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'wi_id', 'wo', 'work_order_id', 'wo_code', 'status']}
  />
);

export default EWI;
