/**
 * ComplexRouting page — Complex routing management.
 * Columns: Code, Item, Steps, Type
 */
import React from 'react';
import GenericListPage from './GenericListPage';

const columns = ['Code', 'Item', 'Steps', 'Type'];

const renderRow = (row, i) => (
  <tr key={row.id || row.routing_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.code || row.routing_id || row.routing_code || '-'}</td>
    <td className="p-3">{row.item || row.item_code || row.item_name || '-'}</td>
    <td className="p-3">{row.steps != null ? (Array.isArray(row.steps) ? row.steps.length : row.steps) : (row.nodes?.length ?? row.node_count ?? '-')}</td>
    <td className="p-3">{row.type || row.routing_type || '-'}</td>
  </tr>
);

const ComplexRouting = () => (
  <GenericListPage
    title="Complex Routing"
    apiPath="/api/complex-routing"
    columns={columns}
    renderRow={renderRow}
    searchFields={['code', 'routing_id', 'routing_code', 'item', 'item_code', 'type', 'routing_type']}
  />
);

export default ComplexRouting;
