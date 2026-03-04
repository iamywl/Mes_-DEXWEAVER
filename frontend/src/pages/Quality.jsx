import React from 'react';
import { Badge } from '../components/ui';
import GenericListPage from './GenericListPage';

const Quality = () => (
  <GenericListPage
    title="Quality / Defects"
    apiPath="/api/quality/defects"
    columns={['Date', 'Item', 'Defect Code', 'Qty', 'Description']}
    searchFields={['item_code', 'defect_code']}
    renderRow={(d, k) => (
      <tr key={k}>
        <td className="p-3 text-slate-400">{d.date || d.created_at}</td>
        <td className="p-3 text-white">{d.item_code}</td>
        <td className="p-3"><Badge v={d.defect_code || 'DEFECT'} /></td>
        <td className="p-3 text-red-400 font-bold">{d.qty || d.defect_qty}</td>
        <td className="p-3">{d.description}</td>
      </tr>
    )}
  />
);

export default Quality;
