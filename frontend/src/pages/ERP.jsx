import React, { useState, useEffect } from 'react';
import api from '../services/api';
import GenericListPage from './GenericListPage';
import { PageHeader, Card, LoadingSpinner } from '../components/ui';

const cols = ['설정ID','시스템','방향','테이블','주기','상태'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50">
  <td className="p-2">{r.config_id}</td><td className="p-2">{r.erp_system}</td>
  <td className="p-2">{r.direction}</td><td className="p-2">{r.table_name}</td>
  <td className="p-2">{r.sync_interval}</td><td className="p-2">{r.status}</td>
</tr>;

export default function ERP() {
  return <GenericListPage title="ERP 연동" apiPath="/api/erp/sync-config" columns={cols} renderRow={renderRow} searchFields={['config_id','erp_system']} />;
}
