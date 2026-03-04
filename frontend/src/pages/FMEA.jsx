/**
 * FMEA page — Failure Mode and Effects Analysis.
 * Columns: ID, Item, Type, Status, Max RPN
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Item', 'Type', 'Status', 'Max RPN'];

const renderRow = (row, i) => (
  <tr key={row.id || row.fmea_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.fmea_id || '-'}</td>
    <td className="p-3">{row.item || row.item_code || row.target_code || row.title || '-'}</td>
    <td className="p-3">{row.type || row.fmea_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
    <td className="p-3 font-mono">{row.max_rpn ?? row.rpn ?? '-'}</td>
  </tr>
);

const FMEA = () => (
  <GenericListPage
    title="FMEA (Failure Mode & Effects Analysis)"
    apiPath="/api/fmea"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'fmea_id', 'item', 'item_code', 'target_code', 'title', 'type', 'fmea_type']}
  />
);

export default FMEA;
