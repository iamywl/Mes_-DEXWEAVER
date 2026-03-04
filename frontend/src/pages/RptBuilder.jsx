import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['템플릿ID','이름','데이터소스','출력형식','작성자'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.template_id}</td><td className="p-2">{r.name}</td><td className="p-2">{r.data_source}</td><td className="p-2">{r.output_format}</td><td className="p-2">{r.created_by}</td></tr>;

export default function RptBuilder() {
  return <GenericListPage title="보고서 빌더" apiPath="/api/report-builder/templates" columns={cols} renderRow={renderRow} searchFields={['template_id','name']} />;
}
