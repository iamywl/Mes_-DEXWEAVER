import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['지시서ID','제목','품목','공정','버전','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.wi_id}</td><td className="p-2">{r.title}</td><td className="p-2">{r.item_code}</td><td className="p-2">{r.process_code}</td><td className="p-2">v{r.version}</td><td className="p-2">{r.status}</td></tr>;

export default function EWI() {
  return <GenericListPage title="전자 작업 지시서 (EWI)" apiPath="/api/work-instructions" columns={cols} renderRow={renderRow} searchFields={['wi_id','title','item_code']} />;
}
