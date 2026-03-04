import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['CAPA ID','유형','제목','상태','담당자','기한'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.capa_id}</td><td className="p-2">{r.capa_type}</td><td className="p-2">{r.title}</td><td className="p-2">{r.status}</td><td className="p-2">{r.assignee}</td><td className="p-2">{r.due_date}</td></tr>;

export default function CAPA() {
  return <GenericListPage title="CAPA (시정 및 예방 조치)" apiPath="/api/quality/capa" columns={cols} renderRow={renderRow} searchFields={['capa_id','title','status']} />;
}
