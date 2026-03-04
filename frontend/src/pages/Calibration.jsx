/**
 * Calibration page — Gauge calibration management.
 * Columns: ID, Code, Status, Next Cal
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Code', 'Status', 'Next Cal'];

const renderRow = (row, i) => (
  <tr key={row.id || row.calibration_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.calibration_id || '-'}</td>
    <td className="p-3 font-mono">{row.code || row.gauge_id || row.gauge_code || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
    <td className="p-3">{row.next_cal || row.next_cal_date || row.next_calibration_date || '-'}</td>
  </tr>
);

const Calibration = () => (
  <GenericListPage
    title="Calibration Management"
    apiPath="/api/calibration/gauges"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'calibration_id', 'code', 'gauge_id', 'gauge_code', 'gauge_name', 'status']}
  />
);

export default Calibration;
