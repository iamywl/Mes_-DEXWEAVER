import React, { useState } from 'react';
import { bomService } from './api';

function BomList() {
  const [productItemCode, setProductItemCode] = useState('');
  const [bomComponents, setBomComponents] = useState([]);
  const [message, setMessage] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setMessage('');
    setBomComponents([]);
    if (!productItemCode) {
      setMessage('제품 코드를 입력해주세요.');
      return;
    }

    try {
      const response = await bomService.getBomByProduct(productItemCode);
      setBomComponents(response.data);
      if (response.data.length === 0) {
        setMessage('해당 제품에 대한 BOM 정보가 없습니다.');
      }
    } catch (error) {
      setMessage(`BOM 정보 조회 실패: ${error.response?.data?.detail || error.message}`);
      console.error('BOM 정보 조회 오류:', error);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>제품별 BOM 조회</h2>
      <form onSubmit={handleSearch}>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="searchProductItemCode" style={{ marginRight: '10px' }}>완제품 코드:</label>
          <input
            type="text"
            id="searchProductItemCode"
            value={productItemCode}
            onChange={(e) => setProductItemCode(e.target.value)}
            required
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
          <button type="submit" style={{ padding: '10px 15px', borderRadius: '4px', border: 'none', background: '#28a745', color: 'white', cursor: 'pointer', marginLeft: '10px' }}>조회</button>
        </div>
      </form>

      {message && <p style={{ marginTop: '10px', color: message.includes('실패') || message.includes('없습니다') ? 'red' : 'green' }}>{message}</p>}

      {bomComponents.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h3>'<span style={{color: 'blue'}}>{productItemCode}</span>' 의 구성품 목록</h3>
          <table border="1" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f4f4f4' }}>
                <th>부품 코드</th>
                <th>수량</th>
              </tr>
            </thead>
            <tbody>
              {bomComponents.map((component, index) => (
                <tr key={index}>
                  <td>{component.component_item_code}</td>
                  <td>{component.quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default BomList;