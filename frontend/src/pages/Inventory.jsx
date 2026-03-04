import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Table, Badge, BtnSuccess, Input, FormRow, Modal,
  FilterBar, FilterSearch, FilterSelect, FilterCount, PageHeader } from '../components/ui';

const Inventory = () => {
  const {showToast} = useToast();
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState({search: '', status: 'ALL'});
  const [modal, setModal] = useState(null);

  const load = async () => {
    try { const r = await api.get('/api/inventory'); setItems(r.data.items || []); } catch {}
  };
  useEffect(() => { load(); }, []);

  const filtered = items.filter(i => {
    if (filter.search && !(i.item_code||'').toLowerCase().includes(filter.search.toLowerCase())
      && !(i.name||'').toLowerCase().includes(filter.search.toLowerCase())) return false;
    if (filter.status !== 'ALL' && i.status !== filter.status) return false;
    return true;
  });

  const handleIn = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const r = await api.post('/api/inventory/in', {item_code: fd.get('item_code'), qty: Number(fd.get('qty'))});
      showToast(`Received: ${r.data.lot_no}`); setModal(null); load();
    } catch (err) { showToast(err.response?.data?.error || 'Failed', false); }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Inventory" actions={<BtnSuccess onClick={() => setModal('in')}>+ Receive</BtnSuccess>} />
      <FilterBar>
        <FilterSelect label="Status" value={filter.status} onChange={v => setFilter(p => ({...p, status: v}))}
          options={[{value:'ALL',label:'All'},{value:'NORMAL',label:'Normal'},{value:'LOW',label:'Low'},{value:'OUT',label:'Out'}]} />
        <FilterSearch value={filter.search} onChange={v => setFilter(p => ({...p, search: v}))} />
        <FilterCount total={items.length} filtered={filtered.length} />
      </FilterBar>
      <Table cols={['Code','Name','Stock','Available','Safety','Status']}
        rows={filtered}
        renderRow={(i, k) => (
          <tr key={k}>
            <td className="p-3 font-mono text-blue-400">{i.item_code}</td>
            <td className="p-3 text-white">{i.name}</td>
            <td className="p-3 text-blue-400 font-bold">{i.stock}</td>
            <td className="p-3">{i.available}</td>
            <td className="p-3">{i.safety}</td>
            <td className="p-3"><Badge v={i.status} /></td>
          </tr>
        )} />
      <Modal open={modal === 'in'} onClose={() => setModal(null)} title="Receive Goods">
        <form onSubmit={handleIn}>
          <FormRow label="Item Code"><Input name="item_code" required className="w-full" /></FormRow>
          <FormRow label="Quantity"><Input name="qty" type="number" required className="w-full" /></FormRow>
          <div className="flex justify-end mt-4"><BtnSuccess type="submit">Receive</BtnSuccess></div>
        </form>
      </Modal>
    </div>
  );
};

export default Inventory;
