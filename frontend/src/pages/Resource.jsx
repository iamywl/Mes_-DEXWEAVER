/**
 * Resource page — Resource management.
 * Columns: ID, Name, Type, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Name', 'Type', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.resource_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.resource_id || '-'}</td>
    <td className="p-3">{row.name || '-'}</td>
    <td className="p-3">{row.type || row.resource_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const Resource = () => (
  <GenericListPage
    title="Resource Management"
    apiPath="/api/resources"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'resource_id', 'name', 'type', 'resource_type']}
  />
);

export default Resource;
