import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['공정코드','공정명','표준시간(분)','설비','설명'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.process_code}</td><td className="p-2">{r.name}</td><td className="p-2">{r.std_time_min}</td><td className="p-2">{r.equip_name||"-"}</td><td className="p-2">{r.description||"-"}</td></tr>;

export default function Process() {
  return <GenericListPage title="공정 관리" apiPath="/api/processes" columns={cols} renderRow={renderRow} searchFields={['process_code','name']} />;
}
