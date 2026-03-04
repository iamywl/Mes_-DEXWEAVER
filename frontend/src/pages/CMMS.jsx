import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['PM ID','설비','유형','주기(일)','다음예정일','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.pm_id}</td><td className="p-2">{r.equip_code}</td><td className="p-2">{r.pm_type}</td><td className="p-2">{r.interval_days}</td><td className="p-2">{r.next_due_date}</td><td className="p-2">{r.status}</td></tr>;

export default function CMMS() {
  return <GenericListPage title="설비 보전 관리 (CMMS)" apiPath="/api/maintenance/pm" columns={cols} renderRow={renderRow} searchFields={['pm_id','equip_code']} />;
}
