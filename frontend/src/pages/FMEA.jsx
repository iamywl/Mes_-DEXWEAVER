import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['FMEA ID','제목','유형','품목/공정','상태','작성자'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.fmea_id}</td><td className="p-2">{r.title}</td><td className="p-2">{r.fmea_type}</td><td className="p-2">{r.target_code}</td><td className="p-2">{r.status}</td><td className="p-2">{r.created_by}</td></tr>;

export default function FMEA() {
  return <GenericListPage title="FMEA (고장모드영향분석)" apiPath="/api/fmea" columns={cols} renderRow={renderRow} searchFields={['fmea_id','title','target_code']} />;
}
