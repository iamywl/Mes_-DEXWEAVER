import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['사이트ID','이름','위치','유형','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.site_id}</td><td className="p-2">{r.name}</td><td className="p-2">{r.location}</td><td className="p-2">{r.site_type}</td><td className="p-2">{r.status}</td></tr>;

export default function Multisite() {
  return <GenericListPage title="다중 사이트 관리" apiPath="/api/sites" columns={cols} renderRow={renderRow} searchFields={['site_id','name','location']} />;
}
