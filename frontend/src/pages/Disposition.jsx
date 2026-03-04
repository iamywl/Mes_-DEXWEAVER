/**
 * Disposition page — Quality disposition decisions list.
 * Columns: ID, LOT, Decision, Date
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'LOT', 'Decision', 'Date'];

const renderRow = (row, i) => (
  <tr key={row.id || row.disposition_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.disposition_id || '-'}</td>
    <td className="p-3 font-mono">{row.lot || row.lot_no || '-'}</td>
    <td className="p-3"><Badge v={row.decision || row.disposition || row.disposition_type || 'PENDING'} /></td>
    <td className="p-3">{row.date || row.decision_date || row.created_at || '-'}</td>
  </tr>
);

const Disposition = () => (
  <GenericListPage
    title="Disposition"
    apiPath="/api/quality/disposition"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'disposition_id', 'lot', 'lot_no', 'decision', 'disposition', 'disposition_type']}
  />
);

export default Disposition;
