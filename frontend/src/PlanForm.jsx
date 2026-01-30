import React, { useState, useEffect } from 'react';
import { itemService, productionPlanService } from './api';

const PlanForm = () => {
  const [itemCode, setItemCode] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [items, setItems] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await itemService.getAllItems();
        setItems(response.data);
        if (response.data.length > 0) {
          setItemCode(response.data[0].item_code);
        }
      } catch (error) {
        console.error('Error fetching items:', error);
        setMessage('Failed to load items.');
      }
    };
    fetchItems();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    if (!itemCode || quantity <= 0) {
      setMessage('Please select an item and enter a valid quantity.');
      return;
    }

    try {
      const newPlan = { item_code: itemCode, quantity: quantity };
      await productionPlanService.createProductionPlan(newPlan);
      setMessage('Production plan created successfully!');
      setQuantity(1); // Reset quantity after successful submission
    } catch (error) {
      console.error('Error creating production plan:', error);
      setMessage('Failed to create production plan.');
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Create New Production Plan</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="itemCode" className="block text-sm font-medium text-gray-700">Item</label>
          <select
            id="itemCode"
            value={itemCode}
            onChange={(e) => setItemCode(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm"
            required
          >
            {items.map((item) => (
              <option key={item.item_code} value={item.item_code}>
                {item.name} ({item.item_code})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="quantity" className="block text-sm font-medium text-gray-700">Quantity</label>
          <input
            type="number"
            id="quantity"
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            min="1"
            required
          />
        </div>
        {/* Date input is included in the prompt, but not in the backend ProductionPlanCreate model currently. */}
        {/* <div className="hidden"> */}
        {/*   <label htmlFor="planDate" className="block text-sm font-medium text-gray-700">Plan Date</label> */}
        {/*   <input */}
        {/*     type="date" */}
        {/*     id="planDate" */}
        {/*     value={planDate} */}
        {/*     onChange={(e) => setPlanDate(e.target.value)} */}
        {/*     className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" */}
        {/*   /> */}
        {/* </div> */}
        <button
          type="submit"
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Create Plan
        </button>
      </form>
      {message && <p className="mt-4 text-center text-sm font-medium text-indigo-600">{message}</p>}
    </div>
  );
};

export default PlanForm;
