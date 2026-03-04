/**
 * NCR page — Non-Conformance Report list.
 * Columns: ID, Item, LOT, Defect Type, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Item', 'LOT', 'Defect Type', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || row.ncr_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.ncr_id || '-'}</td>
    <td className="p-3">{row.item || row.item_code || '-'}</td>
    <td className="p-3 font-mono">{row.lot || row.lot_no || '-'}</td>
    <td className="p-3">{row.defect_type || row.defect_code || row.ncr_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'OPEN'} /></td>
  </tr>
);

const NCR = () => (
  <GenericListPage
    title="NCR (Non-Conformance Report)"
    apiPath="/api/quality/ncr"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'ncr_id', 'item', 'item_code', 'lot', 'lot_no', 'defect_type']}
  />
);

export default NCR;
