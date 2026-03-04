import React from 'react';
import { Badge } from '../components/ui';
import GenericListPage from './GenericListPage';

const WorkOrders = () => (
  <GenericListPage
    title="Work Orders"
    apiPath="/api/work-orders"
    columns={['WO ID', 'Item', 'Equipment', 'Qty', 'Date', 'Status']}
    searchFields={['wo_id', 'item_code', 'equip_code']}
    renderRow={(o, k) => (
      <tr key={k}>
        <td className="p-3 font-mono text-blue-400">{o.wo_id}</td>
        <td className="p-3 text-white">{o.item_code}</td>
        <td className="p-3">{o.equip_code}</td>
        <td className="p-3">{o.plan_qty || o.order_qty}</td>
        <td className="p-3">{o.work_date}</td>
        <td className="p-3"><Badge v={o.status} /></td>
      </tr>
    )}
  />
);

export default WorkOrders;
