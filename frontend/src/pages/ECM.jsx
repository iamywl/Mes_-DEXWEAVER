import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['ECR ID','제목','유형','영향도','상태','요청자'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.ecr_id}</td><td className="p-2">{r.title}</td><td className="p-2">{r.change_type}</td><td className="p-2">{r.impact_level}</td><td className="p-2">{r.status}</td><td className="p-2">{r.requested_by}</td></tr>;

export default function ECM() {
  return <GenericListPage title="설계 변경 관리 (ECM)" apiPath="/api/ecm" columns={cols} renderRow={renderRow} searchFields={['ecr_id','title']} />;
}
