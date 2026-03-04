import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['문서ID','제목','유형','버전','상태','작성자'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.doc_id}</td><td className="p-2">{r.title}</td><td className="p-2">{r.doc_type}</td><td className="p-2">v{r.version}</td><td className="p-2">{r.status}</td><td className="p-2">{r.created_by}</td></tr>;

export default function DMS() {
  return <GenericListPage title="문서 관리 (DMS)" apiPath="/api/documents" columns={cols} renderRow={renderRow} searchFields={['doc_id','title','doc_type']} />;
}
