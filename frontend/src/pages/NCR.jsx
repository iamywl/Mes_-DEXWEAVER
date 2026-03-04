import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['NCR ID','품목','LOT','유형','심각도','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.ncr_id}</td><td className="p-2">{r.item_code}</td><td className="p-2">{r.lot_no}</td><td className="p-2">{r.ncr_type}</td><td className="p-2">{r.severity}</td><td className="p-2">{r.status}</td></tr>;

export default function NCR() {
  return <GenericListPage title="부적합 보고서 (NCR)" apiPath="/api/quality/ncr" columns={cols} renderRow={renderRow} searchFields={['ncr_id','item_code','lot_no']} />;
}
