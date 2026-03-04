/**
 * SetupMatrix page — Equipment setup time matrix.
 * Columns: Equipment, From, To, Setup Time
 */
import React from 'react';
import GenericListPage from './GenericListPage';

const columns = ['Equipment', 'From', 'To', 'Setup Time'];

const renderRow = (row, i) => (
  <tr key={row.id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3">{row.equipment || row.equip_code || row.equipment_code || '-'}</td>
    <td className="p-3">{row.from || row.from_item || row.from_product || '-'}</td>
    <td className="p-3">{row.to || row.to_item || row.to_product || '-'}</td>
    <td className="p-3">{row.setup_time ?? row.setup_minutes ?? '-'} min</td>
  </tr>
);

const SetupMatrix = () => (
  <GenericListPage
    title="Setup Matrix"
    apiPath="/api/setup-matrix"
    columns={columns}
    renderRow={renderRow}
    searchFields={['equipment', 'equip_code', 'from', 'from_item', 'to', 'to_item']}
  />
);

export default SetupMatrix;
