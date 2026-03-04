/**
 * ECM page — Engineering Change Management.
 * Columns: ID, Title, Type, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Title', 'Type', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.ecr_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.ecr_id || '-'}</td>
    <td className="p-3">{row.title || '-'}</td>
    <td className="p-3">{row.type || row.change_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'OPEN'} /></td>
  </tr>
);

const ECM = () => (
  <GenericListPage
    title="Engineering Change Management (ECM)"
    apiPath="/api/ecm"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'ecr_id', 'title', 'type', 'change_type', 'status']}
  />
);

export default ECM;
