/**
 * CMMS page — Preventive Maintenance schedule list.
 * Columns: ID, Equipment, Type, Status, Next Date
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Equipment', 'Type', 'Status', 'Next Date'];

const renderRow = (row, i) => (
  <tr key={row.id || row.pm_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.pm_id || '-'}</td>
    <td className="p-3">{row.equipment || row.equipment_name || row.equipment_code || row.equip_code || '-'}</td>
    <td className="p-3">{row.type || row.pm_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
    <td className="p-3">{row.next_date || row.next_pm_date || row.next_due_date || '-'}</td>
  </tr>
);

const CMMS = () => (
  <GenericListPage
    title="CMMS (Preventive Maintenance)"
    apiPath="/api/maintenance/pm"
    columns={columns}
    renderRow={renderRow}
    searchFields={['equipment', 'equipment_name', 'equipment_code', 'equip_code', 'type', 'pm_type', 'status']}
  />
);

export default CMMS;
