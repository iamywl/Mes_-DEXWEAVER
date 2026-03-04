import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['작업지시','품목','재료비','노무비','경비','총원가'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.wo_code}</td><td className="p-2">{r.item_code}</td><td className="p-2">{r.material_cost?.toLocaleString()}</td><td className="p-2">{r.labor_cost?.toLocaleString()}</td><td className="p-2">{r.overhead_cost?.toLocaleString()}</td><td className="p-2">{r.total_cost?.toLocaleString()}</td></tr>;

export default function Costing() {
  return <GenericListPage title="원가 관리" apiPath="/api/costing" columns={cols} renderRow={renderRow} searchFields={['wo_code','item_code']} />;
}
