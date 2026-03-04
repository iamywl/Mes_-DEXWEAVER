import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['교정ID','게이지ID','이름','주기(일)','다음교정일','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.calibration_id}</td><td className="p-2">{r.gauge_id}</td><td className="p-2">{r.gauge_name}</td><td className="p-2">{r.interval_days}</td><td className="p-2">{r.next_cal_date}</td><td className="p-2">{r.status}</td></tr>;

export default function Calibration() {
  return <GenericListPage title="교정 관리 (Calibration)" apiPath="/api/calibration/gauges" columns={cols} renderRow={renderRow} searchFields={['calibration_id','gauge_id','gauge_name']} />;
}
