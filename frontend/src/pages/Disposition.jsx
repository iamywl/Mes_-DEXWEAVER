import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['처리ID','NCR ID','처분유형','수량','승인자','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.disposition_id}</td><td className="p-2">{r.ncr_id}</td><td className="p-2">{r.disposition_type}</td><td className="p-2">{r.qty}</td><td className="p-2">{r.approved_by||"-"}</td><td className="p-2">{r.status}</td></tr>;

export default function Disposition() {
  return <GenericListPage title="부적합 처리 (Disposition)" apiPath="/api/quality/disposition" columns={cols} renderRow={renderRow} searchFields={['disposition_id','ncr_id']} />;
}
