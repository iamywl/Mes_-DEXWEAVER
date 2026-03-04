import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['ID','유형','메시지','읽음','시간'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.notification_id}</td><td className="p-2">{r.noti_type}</td><td className="p-2">{r.message}</td><td className="p-2">{r.is_read?"✓":"−"}</td><td className="p-2">{r.created_at}</td></tr>;

export default function Notification() {
  return <GenericListPage title="알림" apiPath="/api/notifications" columns={cols} renderRow={renderRow} searchFields={['message','noti_type']} />;
}
