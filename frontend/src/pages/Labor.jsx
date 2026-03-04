/**
 * Labor page — Worker skill management.
 * Columns: Worker, Process, Skill Level
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['Worker', 'Process', 'Skill Level'];

const renderRow = (row, i) => (
  <tr key={row.id || row.worker_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3">{row.worker || row.worker_name || row.worker_id || '-'}</td>
    <td className="p-3">{row.process || row.process_code || row.skill_type || '-'}</td>
    <td className="p-3"><Badge v={row.skill_level || row.level || 'NORMAL'} /></td>
  </tr>
);

const Labor = () => (
  <GenericListPage
    title="Labor & Skill Management"
    apiPath="/api/labor/skills"
    columns={columns}
    renderRow={renderRow}
    searchFields={['worker', 'worker_name', 'worker_id', 'process', 'process_code', 'skill_type']}
  />
);

export default Labor;
