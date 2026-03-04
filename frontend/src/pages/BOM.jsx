import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['품목코드','품목명','카테고리','부품수','총원가'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.item_code}</td><td className="p-2">{r.item_name}</td><td className="p-2">{r.category}</td><td className="p-2">{r.component_count}</td><td className="p-2">{r.total_cost?.toLocaleString()}</td></tr>;

export default function BOM() {
  return <GenericListPage title="BOM (자재명세서)" apiPath="/api/bom/summary" columns={cols} renderRow={renderRow} searchFields={['item_code','item_name']} />;
}
