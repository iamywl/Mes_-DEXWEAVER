/**
 * BOM page — BOM list with Parent/Child/Qty/Unit columns.
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['Parent', 'Child', 'Qty', 'Unit'];

const renderRow = (row, i) => (
  <tr key={row.id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3">{row.parent_code || row.parent_item_code || '-'}</td>
    <td className="p-3">{row.child_code || row.child_item_code || '-'}</td>
    <td className="p-3">{row.quantity ?? row.qty ?? '-'}</td>
    <td className="p-3">{row.unit || '-'}</td>
  </tr>
);

const BOM = () => (
  <GenericListPage
    title="BOM (Bill of Materials)"
    apiPath="/api/bom"
    columns={columns}
    renderRow={renderRow}
    searchFields={['parent_code', 'child_code', 'parent_item_code', 'child_item_code']}
  />
);

export default BOM;
