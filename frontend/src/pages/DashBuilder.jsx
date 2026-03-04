import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['레이아웃ID','이름','위젯수','작성자','수정일'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.layout_id}</td><td className="p-2">{r.name}</td><td className="p-2">{r.widgets?.length||0}</td><td className="p-2">{r.created_by}</td><td className="p-2">{r.updated_at}</td></tr>;

export default function DashBuilder() {
  return <GenericListPage title="대시보드 빌더" apiPath="/api/dashboard-builder/layouts" columns={cols} renderRow={renderRow} searchFields={['layout_id','name']} />;
}
