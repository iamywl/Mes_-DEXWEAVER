/**
 * Plans page — FN-015~017: Production plans CRUD.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Table, Badge, BtnSuccess, Input, FormRow, Modal,
  FilterBar, FilterSearch, FilterSelect, FilterCount, PageHeader } from '../components/ui';

const Plans = () => {
  const {showToast} = useToast();
  const [plans, setPlans] = useState([]);
  const [filter, setFilter] = useState({search: '', status: 'ALL'});
  const [modal, setModal] = useState(null);

  const load = async () => {
    try {
      const r = await api.get('/api/plans');
      setPlans(r.data.plans || []);
    } catch {}
  };
  useEffect(() => { load(); }, []);

  const filtered = plans.filter(p => {
    if (filter.search && !(p.item_code||'').toLowerCase().includes(filter.search.toLowerCase())) return false;
    if (filter.status !== 'ALL' && p.status !== filter.status) return false;
    return true;
  });

  const handleCreate = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api.post('/api/plans', {
        item_code: fd.get('item_code'), plan_qty: Number(fd.get('plan_qty')),
        start_date: fd.get('start_date'), end_date: fd.get('end_date'),
      });
      showToast('Plan created');
      setModal(null); load();
    } catch (err) { showToast(err.response?.data?.error || 'Failed', false); }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Production Plans" actions={<BtnSuccess onClick={() => setModal('create')}>+ New Plan</BtnSuccess>} />
      <FilterBar>
        <FilterSelect label="Status" value={filter.status} onChange={v => setFilter(p => ({...p, status: v}))}
          options={[{value:'ALL',label:'All'},{value:'DRAFT',label:'Draft'},{value:'CONFIRMED',label:'Confirmed'},{value:'DONE',label:'Done'}]} />
        <FilterSearch value={filter.search} onChange={v => setFilter(p => ({...p, search: v}))} />
        <FilterCount total={plans.length} filtered={filtered.length} />
      </FilterBar>
      <Table cols={['Plan ID','Item','Qty','Start','End','Status']}
        rows={filtered}
        renderRow={(p, k) => (
          <tr key={k}>
            <td className="p-3 font-mono text-blue-400">{p.plan_id}</td>
            <td className="p-3 text-white">{p.item_code}</td>
            <td className="p-3">{p.plan_qty}</td>
            <td className="p-3">{p.start_date}</td>
            <td className="p-3">{p.end_date}</td>
            <td className="p-3"><Badge v={p.status} /></td>
          </tr>
        )} />
      <Modal open={modal === 'create'} onClose={() => setModal(null)} title="New Plan">
        <form onSubmit={handleCreate}>
          <FormRow label="Item Code"><Input name="item_code" required className="w-full" /></FormRow>
          <FormRow label="Quantity"><Input name="plan_qty" type="number" required className="w-full" /></FormRow>
          <FormRow label="Start Date"><Input name="start_date" type="date" required className="w-full" /></FormRow>
          <FormRow label="End Date"><Input name="end_date" type="date" required className="w-full" /></FormRow>
          <div className="flex justify-end mt-4"><BtnSuccess type="submit">Create</BtnSuccess></div>
        </form>
      </Modal>
    </div>
  );
};

export default Plans;
