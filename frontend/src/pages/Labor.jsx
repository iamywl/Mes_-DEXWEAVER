import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['작업자ID','이름','스킬','등급','인증일'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.worker_id}</td><td className="p-2">{r.worker_name}</td><td className="p-2">{r.skill_type}</td><td className="p-2">{r.skill_level}</td><td className="p-2">{r.certified_date}</td></tr>;

export default function Labor() {
  return <GenericListPage title="인력 관리" apiPath="/api/labor/skills" columns={cols} renderRow={renderRow} searchFields={['worker_id','worker_name','skill_type']} />;
}
