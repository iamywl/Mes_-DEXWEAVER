/**
 * CAPA page — Corrective/Preventive Action list.
 * Columns: ID, Type, Status, Assigned, Due Date
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Type', 'Status', 'Assigned', 'Due Date'];

const renderRow = (row, i) => (
  <tr key={row.id || row.capa_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.capa_id || '-'}</td>
    <td className="p-3">{row.type || row.capa_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'OPEN'} /></td>
    <td className="p-3">{row.assigned || row.assigned_to || row.assignee || '-'}</td>
    <td className="p-3">{row.due_date || '-'}</td>
  </tr>
);

const CAPA = () => (
  <GenericListPage
    title="CAPA (Corrective & Preventive Action)"
    apiPath="/api/quality/capa"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'capa_id', 'type', 'capa_type', 'assigned', 'assigned_to', 'assignee', 'status']}
  />
);

export default CAPA;
