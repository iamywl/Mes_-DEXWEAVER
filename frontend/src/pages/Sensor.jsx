/**
 * Sensor page — MQTT sensor data collection config.
 * Columns: Topic, Equipment, Status
 */
import React from 'react';
import GenericListPage from './GenericListPage';
import { Badge } from '../components/ui';

const columns = ['Topic', 'Equipment', 'Status'];

const renderRow = (row, i) => (
  <tr key={row.id || i} className="text-xs text-slate-300 hover:bg-slate-800/40">
    <td className="p-3 font-mono">{row.topic || row.mqtt_topic || '-'}</td>
    <td className="p-3">{row.equipment || row.equipment_code || row.equip_code || '-'}</td>
    <td className="p-3"><Badge v={row.status || 'NORMAL'} /></td>
  </tr>
);

const Sensor = () => (
  <GenericListPage
    title="Sensor Data Collection (MQTT)"
    apiPath="/api/datacollect/mqtt/config"
    columns={columns}
    renderRow={renderRow}
    searchFields={['topic', 'mqtt_topic', 'equipment', 'equipment_code', 'equip_code']}
  />
);

export default Sensor;
