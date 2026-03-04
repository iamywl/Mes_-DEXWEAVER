/**
 * Costing page — Work order cost breakdown.
 * Columns: WO, Material, Labor, Overhead, Total
 */
import React from 'react';
import GenericListPage from './GenericListPage';

const columns = ['WO', 'Material', 'Labor', 'Overhead', 'Total'];

const fmt = (v) => v != null ? Number(v).toLocaleString() : '-';

const renderRow = (row, i) => (
  <tr key={row.id || row.wo_code || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.wo || row.wo_code || row.work_order_id || '-'}</td>
    <td className="p-3 text-right">{fmt(row.material ?? row.material_cost)}</td>
    <td className="p-3 text-right">{fmt(row.labor ?? row.labor_cost)}</td>
    <td className="p-3 text-right">{fmt(row.overhead ?? row.overhead_cost)}</td>
    <td className="p-3 text-right font-bold">{fmt(row.total ?? row.total_cost)}</td>
  </tr>
);

const Costing = () => (
  <GenericListPage
    title="Cost Management"
    apiPath="/api/costing"
    columns={columns}
    renderRow={renderRow}
    searchFields={['wo', 'wo_code', 'work_order_id', 'item_code']}
  />
);

export default Costing;
