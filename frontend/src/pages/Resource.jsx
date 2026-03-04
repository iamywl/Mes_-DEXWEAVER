import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['자원ID','이름','유형','용량','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.resource_id}</td><td className="p-2">{r.name}</td><td className="p-2">{r.resource_type}</td><td className="p-2">{r.capacity}</td><td className="p-2">{r.status}</td></tr>;

export default function Resource() {
  return <GenericListPage title="자원 관리" apiPath="/api/resources" columns={cols} renderRow={renderRow} searchFields={['resource_id','name','resource_type']} />;
}
