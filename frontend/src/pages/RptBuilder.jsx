/**
 * RptBuilder page — Report template builder.
 * Columns: ID, Name, Type
 */
import React from 'react';
import GenericListPage from './GenericListPage';

const columns = ['ID', 'Name', 'Type'];

const renderRow = (row, i) => (
  <tr key={row.id || row.template_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.template_id || '-'}</td>
    <td className="p-3">{row.name || '-'}</td>
    <td className="p-3">{row.type || row.output_format || row.data_source || '-'}</td>
  </tr>
);

const RptBuilder = () => (
  <GenericListPage
    title="Report Builder"
    apiPath="/api/report-builder/templates"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'template_id', 'name', 'type', 'output_format', 'created_by']}
  />
);

export default RptBuilder;
