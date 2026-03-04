import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['설비','From','To','셋업시간(분)','유형'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.equip_code}</td><td className="p-2">{r.from_item}</td><td className="p-2">{r.to_item}</td><td className="p-2">{r.setup_minutes}</td><td className="p-2">{r.setup_type}</td></tr>;

export default function SetupMatrix() {
  return <GenericListPage title="셋업 매트릭스" apiPath="/api/setup-matrix" columns={cols} renderRow={renderRow} searchFields={['equip_code','from_item','to_item']} />;
}
