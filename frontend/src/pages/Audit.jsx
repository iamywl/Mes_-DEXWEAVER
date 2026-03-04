import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['ID','사용자','작업','대상','IP','시간'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.audit_id}</td><td className="p-2">{r.user_id}</td><td className="p-2">{r.action}</td><td className="p-2">{r.target}</td><td className="p-2">{r.ip_address}</td><td className="p-2">{r.created_at}</td></tr>;

export default function Audit() {
  return <GenericListPage title="감사 추적 (Audit Trail)" apiPath="/api/audit" columns={cols} renderRow={renderRow} searchFields={['user_id','action','target']} />;
}
