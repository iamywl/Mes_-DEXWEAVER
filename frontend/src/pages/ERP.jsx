/**
 * ERP page — ERP sync configuration.
 * Columns: ID, Name, Direction, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Name', 'Direction', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.config_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.config_id || '-'}</td>
    <td className="p-3">{row.name || row.erp_system || row.table_name || '-'}</td>
    <td className="p-3">{row.direction || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const ERP = () => (
  <GenericListPage
    title="ERP Integration"
    apiPath="/api/erp/sync-config"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'config_id', 'name', 'erp_system', 'table_name', 'direction', 'status']}
  />
);

export default ERP;
