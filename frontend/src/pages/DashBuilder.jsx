/**
 * DashBuilder page — Dashboard layout builder.
 * Columns: ID, Name, Created
 */
import React from 'react';
import GenericListPage from './GenericListPage';

const columns = ['ID', 'Name', 'Created'];

const renderRow = (row, i) => (
  <tr key={row.id || row.layout_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.layout_id || '-'}</td>
    <td className="p-3">{row.name || '-'}</td>
    <td className="p-3">{row.created || row.created_at || row.updated_at || '-'}</td>
  </tr>
);

const DashBuilder = () => (
  <GenericListPage
    title="Dashboard Builder"
    apiPath="/api/dashboard-builder/layouts"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'layout_id', 'name', 'created_by']}
  />
);

export default DashBuilder;
