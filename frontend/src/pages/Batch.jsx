/**
 * Batch page — Batch manufacturing management.
 * Columns: ID, Recipe, Status, Start, End
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Recipe', 'Status', 'Start', 'End'];

const renderRow = (row, i) => (
  <tr key={row.id || row.batch_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.batch_id || '-'}</td>
    <td className="p-3">{row.recipe || row.recipe_id || row.item_code || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'PENDING'} /></td>
    <td className="p-3">{row.start || row.start_date || row.started_at || '-'}</td>
    <td className="p-3">{row.end || row.end_date || row.ended_at || '-'}</td>
  </tr>
);

const Batch = () => (
  <GenericListPage
    title="Batch Management"
    apiPath="/api/batch"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'batch_id', 'recipe', 'recipe_id', 'item_code', 'status']}
  />
);

export default Batch;
