import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['공급업체ID','이름','등급','점수','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.supplier_id}</td><td className="p-2">{r.name}</td><td className="p-2">{r.grade}</td><td className="p-2">{r.score}</td><td className="p-2">{r.status}</td></tr>;

export default function SQM() {
  return <GenericListPage title="공급업체 품질 관리 (SQM)" apiPath="/api/sqm/suppliers" columns={cols} renderRow={renderRow} searchFields={['supplier_id','name']} />;
}
