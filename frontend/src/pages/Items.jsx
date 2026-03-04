/**
 * Items page — FN-004~007: Item master CRUD with filtering.
 */
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useToast } from '../hooks/useToast';
import { Card, Table, Badge, Btn, BtnSuccess, Input, Select, FormRow, Modal,
  FilterBar, FilterSelect, FilterSearch, FilterCount, PageHeader } from '../components/ui';

const Items = () => {
  const {showToast} = useToast();
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState({search: '', category: 'ALL', status: 'ALL'});
  const [modal, setModal] = useState(null);

  const load = async () => {
    try {
      const r = await api.get('/api/items?size=200');
      setItems(r.data.items || []);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const categories = [...new Set(items.map(i => i.category).filter(Boolean))];
  const filtered = items.filter(i => {
    if (filter.search) {
      const s = filter.search.toLowerCase();
      if (!(i.item_code||'').toLowerCase().includes(s) && !(i.name||'').toLowerCase().includes(s)) return false;
    }
    if (filter.category !== 'ALL' && i.category !== filter.category) return false;
    if (filter.status !== 'ALL') {
      const st = i.stock <= 0 ? 'OUT' : i.stock < i.safety_stock ? 'LOW' : 'NORMAL';
      if (st !== filter.status) return false;
    }
    return true;
  });

  const handleCreate = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const r = await api.post('/api/items', {
        name: fd.get('name'), category: fd.get('category'), unit: fd.get('unit'),
        spec: fd.get('spec'), safety_stock: Number(fd.get('safety_stock') || 0),
      });
      showToast(`Item ${r.data.item_code} created`);
      setModal(null);
      load();
    } catch (err) { showToast(err.response?.data?.error || 'Failed', false); }
  };

  const handleDelete = async (code) => {
    if (!confirm(`Delete ${code}?`)) return;
    try {
      await api.delete(`/api/items/${code}`);
      showToast(`${code} deleted`);
      load();
    } catch { showToast('Delete failed', false); }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Items" actions={<BtnSuccess onClick={() => setModal('create')}>+ New Item</BtnSuccess>} />

      <FilterBar>
        <FilterSelect label="Category" value={filter.category} onChange={v => setFilter(p => ({...p, category: v}))}
          options={[{value: 'ALL', label: 'All'}, ...categories.map(c => ({value: c, label: c}))]} />
        <FilterSelect label="Status" value={filter.status} onChange={v => setFilter(p => ({...p, status: v}))}
          options={[{value:'ALL',label:'All'},{value:'NORMAL',label:'Normal'},{value:'LOW',label:'Low Stock'},{value:'OUT',label:'Out'}]} />
        <FilterSearch value={filter.search} onChange={v => setFilter(p => ({...p, search: v}))} placeholder="Search code, name..." />
        <FilterCount total={items.length} filtered={filtered.length} />
      </FilterBar>

      <Table cols={['Code','Name','Category','Unit','Spec','Stock','Safety','Status','Actions']}
        rows={filtered}
        renderRow={(i, k) => (
          <tr key={k}>
            <td className="p-3 font-mono text-blue-400">{i.item_code}</td>
            <td className="p-3 text-white font-bold">{i.name}</td>
            <td className="p-3"><Badge v={i.category} /></td>
            <td className="p-3">{i.unit}</td>
            <td className="p-3 text-slate-500">{i.spec}</td>
            <td className="p-3 text-blue-400 font-bold">{i.stock}</td>
            <td className="p-3">{i.safety_stock}</td>
            <td className="p-3"><Badge v={i.stock <= 0 ? 'OUT' : i.stock < i.safety_stock ? 'LOW' : 'NORMAL'} /></td>
            <td className="p-3">
              <button onClick={() => handleDelete(i.item_code)} className="text-red-400 hover:text-red-300 text-[10px] font-bold cursor-pointer">Del</button>
            </td>
          </tr>
        )} />

      <Modal open={modal === 'create'} onClose={() => setModal(null)} title="New Item">
        <form onSubmit={handleCreate}>
          <FormRow label="Name"><Input name="name" required className="w-full" /></FormRow>
          <FormRow label="Category">
            <Select name="category" onChange={() => {}} value="RAW"
              options={[{value:'RAW',label:'RAW'},{value:'SEMI',label:'SEMI'},{value:'PRODUCT',label:'PRODUCT'}]} className="w-full" />
          </FormRow>
          <FormRow label="Unit">
            <Select name="unit" onChange={() => {}} value="EA"
              options={[{value:'EA',label:'EA'},{value:'KG',label:'KG'},{value:'M',label:'M'},{value:'L',label:'L'}]} className="w-full" />
          </FormRow>
          <FormRow label="Spec"><Input name="spec" className="w-full" /></FormRow>
          <FormRow label="Safety Stock"><Input name="safety_stock" type="number" className="w-full" defaultValue="0" /></FormRow>
          <div className="flex justify-end gap-2 mt-4">
            <Btn type="button" onClick={() => setModal(null)} className="bg-slate-600">Cancel</Btn>
            <BtnSuccess type="submit">Create</BtnSuccess>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Items;
