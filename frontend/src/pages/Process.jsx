/**
 * Process page — Process list with Code/Name/Std Time/Equipment/Status columns.
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['Code', 'Name', 'Std Time', 'Equipment', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.process_code || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.process_code || '-'}</td>
    <td className="p-3">{row.name || row.process_name || '-'}</td>
    <td className="p-3">{row.std_time ?? row.standard_time ?? row.std_time_min ?? '-'}</td>
    <td className="p-3">{row.equipment || row.equipment_name || row.equip_name || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const Process = () => (
  <GenericListPage
    title="Process Management"
    apiPath="/api/processes"
    columns={columns}
    renderRow={renderRow}
    searchFields={['process_code', 'name', 'process_name', 'equipment', 'equip_name']}
  />
);

export default Process;
