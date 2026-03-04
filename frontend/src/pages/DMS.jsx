/**
 * DMS page — Document Management System.
 * Columns: ID, Title, Type, Status, Author
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Title', 'Type', 'Status', 'Author'];

const renderRow = (row, i) => (
  <tr key={row.id || row.doc_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.doc_id || '-'}</td>
    <td className="p-3">{row.title || '-'}</td>
    <td className="p-3">{row.type || row.doc_type || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
    <td className="p-3">{row.author || row.created_by || '-'}</td>
  </tr>
);

const DMS = () => (
  <GenericListPage
    title="Document Management (DMS)"
    apiPath="/api/documents"
    columns={columns}
    renderRow={renderRow}
    searchFields={['id', 'doc_id', 'title', 'type', 'doc_type', 'author', 'created_by']}
  />
);

export default DMS;
