/**
 * Recipe page — Manufacturing recipe list.
 * Columns: ID, Item, Process, Version, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Item', 'Process', 'Version', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.recipe_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.recipe_id || '-'}</td>
    <td className="p-3">{row.item || row.item_code || row.item_name || '-'}</td>
    <td className="p-3">{row.process || row.process_code || row.process_name || '-'}</td>
    <td className="p-3">{row.version != null ? `v${row.version}` : '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const Recipe = () => (
  <GenericListPage
    title="Recipe Management"
    apiPath="/api/recipes"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'recipe_id', 'item', 'item_code', 'item_name', 'process', 'process_code']}
  />
);

export default Recipe;
