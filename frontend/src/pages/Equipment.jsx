/**
 * Equipment page — FN-013~014: Equipment list + status.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Table, Badge, BtnSuccess, Input, Select, FormRow, Modal,
  FilterBar, FilterSearch, FilterSelect, FilterCount, PageHeader } from '../components/ui';

const Equipment = () => {
  const {showToast} = useToast();
  const [equips, setEquips] = useState([]);
  const [filter, setFilter] = useState({search: '', status: 'ALL'});
  const [modal, setModal] = useState(null);

  const load = async () => {
    try {
      const r = await api.get('/api/equipments');
      setEquips(r.data.equipments || []);
    } catch {}
  };
  useEffect(() => { load(); }, []);

  const filtered = equips.filter(e => {
    if (filter.search && !(e.equip_code||'').toLowerCase().includes(filter.search.toLowerCase())
      && !(e.name||'').toLowerCase().includes(filter.search.toLowerCase())) return false;
    if (filter.status !== 'ALL' && e.status !== filter.status) return false;
    return true;
  });

  const handleCreate = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const r = await api.post('/api/equipments', {
        name: fd.get('name'), process_code: fd.get('process_code'),
        capacity_per_hour: Number(fd.get('capacity') || 100),
      });
      showToast(`Equipment ${r.data.equip_code} created`);
      setModal(null); load();
    } catch (err) { showToast(err.response?.data?.error || 'Failed', false); }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Equipment" actions={<BtnSuccess onClick={() => setModal('create')}>+ New Equipment</BtnSuccess>} />
      <FilterBar>
        <FilterSelect label="Status" value={filter.status} onChange={v => setFilter(p => ({...p, status: v}))}
          options={[{value:'ALL',label:'All'},{value:'RUNNING',label:'Running'},{value:'STOP',label:'Stop'},{value:'DOWN',label:'Down'}]} />
        <FilterSearch value={filter.search} onChange={v => setFilter(p => ({...p, search: v}))} />
        <FilterCount total={equips.length} filtered={filtered.length} />
      </FilterBar>
      <Table cols={['Code','Name','Process','Capacity/hr','Status','Install Date']}
        rows={filtered}
        renderRow={(e, k) => (
          <tr key={k}>
            <td className="p-3 font-mono text-blue-400">{e.equip_code}</td>
            <td className="p-3 text-white font-bold">{e.name}</td>
            <td className="p-3">{e.process_code}</td>
            <td className="p-3">{e.capacity_per_hour}</td>
            <td className="p-3"><Badge v={e.status} /></td>
            <td className="p-3 text-slate-500">{e.install_date}</td>
          </tr>
        )} />
      <Modal open={modal === 'create'} onClose={() => setModal(null)} title="New Equipment">
        <form onSubmit={handleCreate}>
          <FormRow label="Name"><Input name="name" required className="w-full" /></FormRow>
          <FormRow label="Process Code"><Input name="process_code" className="w-full" /></FormRow>
          <FormRow label="Capacity/hr"><Input name="capacity" type="number" className="w-full" defaultValue="100" /></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <BtnSuccess type="submit">Create</BtnSuccess>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Equipment;
