import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['Study ID','이름','게이지','유형','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.study_id}</td><td className="p-2">{r.study_name}</td><td className="p-2">{r.gauge_id}</td><td className="p-2">{r.study_type}</td><td className="p-2">{r.status}</td></tr>;

export default function MSA() {
  return <GenericListPage title="측정시스템분석 (MSA)" apiPath="/api/msa/studies" columns={cols} renderRow={renderRow} searchFields={['study_id','study_name']} />;
}
