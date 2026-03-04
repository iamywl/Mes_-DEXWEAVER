import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['배치ID','품목','배치크기','상태','시작일','종료일'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.batch_id}</td><td className="p-2">{r.item_code}</td><td className="p-2">{r.batch_size}</td><td className="p-2">{r.status}</td><td className="p-2">{r.start_date}</td><td className="p-2">{r.end_date||"-"}</td></tr>;

export default function Batch() {
  return <GenericListPage title="배치 관리" apiPath="/api/batch" columns={cols} renderRow={renderRow} searchFields={['batch_id','item_code']} />;
}
