/**
 * OPCUA page — OPC-UA connection configuration.
 * Columns: ID, URL, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'URL', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.config_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.config_id || '-'}</td>
    <td className="p-3 font-mono text-[10px]">{row.url || row.server_url || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const OPCUA = () => (
  <GenericListPage
    title="OPC-UA Configuration"
    apiPath="/api/opcua/config"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'config_id', 'url', 'server_url', 'status']}
  />
);

export default OPCUA;
