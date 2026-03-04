/**
 * Audit page — Audit trail log.
 * Columns: ID, User, Action, Entity, Time
 */
import React from 'react';
import GenericListPage from './GenericListPage';

const columns = ['ID', 'User', 'Action', 'Entity', 'Time'];

const renderRow = (row, i) => (
  <tr key={row.id || row.audit_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.audit_id || '-'}</td>
    <td className="p-3">{row.user || row.user_id || row.username || '-'}</td>
    <td className="p-3">{row.action || '-'}</td>
    <td className="p-3">{row.entity || row.target || '-'}</td>
    <td className="p-3">{row.time || row.created_at || row.timestamp || '-'}</td>
  </tr>
);

const Audit = () => (
  <GenericListPage
    title="Audit Trail"
    apiPath="/api/audit"
    columns={columns}
    renderRow={renderRow}
    searchFields={['user', 'user_id', 'username', 'action', 'entity', 'target']}
  />
);

export default Audit;
