import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [mesData, setMesData] = useState({ ITEMS: [], EQUIPMENTS: [], PROCESSES: [] });
  const [loading, setLoading] = useState(true);

  // FastAPI 서버 주소 (K8s NodePort 사용)
  const API_URL = "http://192.168.64.5:30461/api/data";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(API_URL);
        // FastAPI에서 보낸 대문자 키값(ITEMS 등)에 맞춰 저장
        setMesData(response.data);
      } catch (error) {
        console.error("데이터를 불러오는 중 오류 발생:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div style={{padding: '20px'}}>⚙️ 실시간 DB 데이터 로딩 중...</div>;

  return (
    <div style={{ padding: '40px', fontFamily: 'system-ui' }}>
      <h1>🏭 스마트 팩토리 실시간 MES 대시보드</h1>
      <p>연결 서버: {API_URL}</p>
      <hr />

      <section>
        <h2>📦 품목 현황 (ITEMS)</h2>
        <table border="1" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f4f4f4' }}>
              <th>코드</th><th>품목명</th><th>카테고리</th><th>단위</th>
            </tr>
          </thead>
          <tbody>
            {mesData.items?.map((item, index) => (
              <tr key={index}>
                <td>{item.item_code}</td><td>{item.name}</td><td>{item.category}</td><td>{item.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section style={{marginTop: '40px'}}>
        <h2>⚙️ 설비 상태 (EQUIPMENTS)</h2>
        <table border="1" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tr style={{ background: '#f4f4f4' }}>
            <th>설비명</th><th>현재 상태</th>
          </tr>
          {mesData.equipments?.map((eq, index) => (
            <tr key={index}>
              <td>{eq.eq_name}</td>
              <td style={{color: eq.status === 'RUNNING' ? 'green' : 'red'}}>{eq.status}</td>
            </tr>
          ))}
        </table>
      </section>
    </div>
  )
}

export default App
