/**
 * Multisite page — Multi-site management.
 * Columns: Code, Name, Type, Timezone
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['Code', 'Name', 'Type', 'Timezone'];

const renderRow = (row, i) => (
  <tr key={row.id || row.site_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.code || row.site_id || row.site_code || '-'}</td>
    <td className="p-3">{row.name || '-'}</td>
    <td className="p-3">{row.type || row.site_type || '-'}</td>
    <td className="p-3">{row.timezone || row.location || '-'}</td>
  </tr>
);

const Multisite = () => (
  <GenericListPage
    title="Multi-Site Management"
    apiPath="/api/sites"
    columns={columns}
    renderRow={renderRow}
    searchFields={['code', 'site_id', 'site_code', 'name', 'type', 'site_type', 'timezone', 'location']}
  />
);

export default Multisite;
