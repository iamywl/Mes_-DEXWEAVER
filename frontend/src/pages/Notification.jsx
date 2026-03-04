/**
 * Notification page — Notification list.
 * Columns: ID, Type, Message, Time, Read
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['ID', 'Type', 'Message', 'Time', 'Read'];

const renderRow = (row, i) => (
  <tr key={row.id || row.notification_id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.id || row.notification_id || '-'}</td>
    <td className="p-3">{row.type || row.noti_type || '-'}</td>
    <td className="p-3 max-w-xs truncate">{row.message || '-'}</td>
    <td className="p-3">{row.time || row.created_at || '-'}</td>
    <td className="p-3"><Badge v={row.read || row.is_read ? 'DONE' : 'PENDING'} /></td>
  </tr>
);

const Notification = () => (
  <GenericListPage
    title="Notifications"
    apiPath="/api/notifications"
    columns={columns}
    renderRow={renderRow}
    searchFields={['type', 'noti_type', 'message']}
  />
);

export default Notification;
