import React, { useState } from 'react';
import { bomService } from './api';

function BomRegistrationForm() {
  const [productItemCode, setProductItemCode] = useState('');
  const [componentItemCode, setComponentItemCode] = useState('');
  const [quantity, setQuantity] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await bomService.createBom({
        product_item_code: productItemCode,
        component_item_code: componentItemCode,
        quantity: parseInt(quantity),
      });
      setMessage('BOM 등록 성공!');
      setProductItemCode('');
      setComponentItemCode('');
      setQuantity('');
    } catch (error) {
      setMessage(`BOM 등록 실패: ${error.response?.data?.detail || error.message}`);
      console.error('BOM 등록 오류:', error);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', marginBottom: '20px' }}>
      <h2>BOM 등록</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="productItemCode" style={{ marginRight: '10px' }}>완제품 코드:</label>
          <input
            type="text"
            id="productItemCode"
            value={productItemCode}
            onChange={(e) => setProductItemCode(e.target.value)}
            required
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="componentItemCode" style={{ marginRight: '10px' }}>부품 코드:</label>
          <input
            type="text"
            id="componentItemCode"
            value={componentItemCode}
            onChange={(e) => setComponentItemCode(e.target.value)}
            required
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="quantity" style={{ marginRight: '10px' }}>수량:</label>
          <input
            type="number"
            id="quantity"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
            min="1"
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
        </div>
        <button type="submit" style={{ padding: '10px 15px', borderRadius: '4px', border: 'none', background: '#007bff', color: 'white', cursor: 'pointer' }}>등록</button>
      </form>
      {message && <p style={{ marginTop: '10px', color: message.includes('실패') ? 'red' : 'green' }}>{message}</p>}
    </div>
  );
}

export default BomRegistrationForm;