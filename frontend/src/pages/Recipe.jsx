import React from 'react';
import GenericListPage from './GenericListPage';

const cols = ['레시피ID','품목','버전','상태','승인자'];
const renderRow = (r,i) => <tr key={i} className="border-b hover:bg-gray-50"><td className="p-2">{r.recipe_id}</td><td className="p-2">{r.item_code}</td><td className="p-2">v{r.version}</td><td className="p-2">{r.status}</td><td className="p-2">{r.approved_by||"-"}</td></tr>;

export default function Recipe() {
  return <GenericListPage title="레시피 관리" apiPath="/api/recipes" columns={cols} renderRow={renderRow} searchFields={['recipe_id','item_code']} />;
}
