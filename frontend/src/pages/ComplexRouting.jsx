import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['라우팅ID','품목','유형','노드수','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.routing_id}</td><td className="p-2">{r.item_code}</td><td className="p-2">{r.routing_type}</td><td className="p-2">{r.nodes?.length||r.node_count||0}</td><td className="p-2">{r.status||"ACTIVE"}</td></tr>;

export default function ComplexRouting() {
  return <GenericListPage title="복합 라우팅" apiPath="/api/complex-routing" columns={cols} renderRow={renderRow} searchFields={['routing_id','item_code']} />;
}
