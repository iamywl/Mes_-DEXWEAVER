# KNU MES 프로젝트 기여 가이드

> 이 문서는 KNU MES(Manufacturing Execution System) 프로젝트에 기여하기 위한 개발 환경 설정, 코드 컨벤션, 워크플로우, 그리고 기능 추가 방법을 안내합니다.

---

## 목차

1. [개발 환경 설정](#1-개발-환경-설정)
2. [코드 컨벤션](#2-코드-컨벤션)
3. [브랜치 전략](#3-브랜치-전략)
4. [개발 워크플로우](#4-개발-워크플로우)
5. [백엔드 기능 추가 방법](#5-백엔드-기능-추가-방법)
6. [프론트엔드 기능 추가 방법](#6-프론트엔드-기능-추가-방법)
7. [인프라 변경 방법](#7-인프라-변경-방법)
8. [테스트](#8-테스트)
9. [코드 리뷰 체크리스트](#9-코드-리뷰-체크리스트)

---

## 1. 개발 환경 설정

### 1.1 필수 도구

| 도구 | 최소 버전 | 용도 |
|------|-----------|------|
| **Node.js** | 18+ | 프론트엔드 빌드 및 개발 서버 |
| **Python** | 3.9+ | 백엔드 API 서버 |
| **kubectl** | 최신 안정 버전 | Kubernetes 클러스터 관리 |
| **kubeadm** | 최신 안정 버전 | Kubernetes 클러스터 초기화 |
| **Git** | 2.30+ | 버전 관리 |
| **Docker** | 20.10+ | 컨테이너 빌드 및 실행 |

### 1.2 프로젝트 클론 및 설정

```bash
# 1. 저장소 클론
git clone <repository-url>
cd MES_PROJECT

# 2. 백엔드 Python 의존성 설치
pip install -r requirements.txt

# 3. 프론트엔드 의존성 설치
cd frontend
npm install
cd ..

# 4. 환경 변수 확인
cat env.sh
```

### 1.3 로컬 개발 방법

**백엔드 (FastAPI)**

```bash
# 개발 서버 실행 (자동 리로드 포함)
python app.py

# 또는 uvicorn으로 직접 실행
uvicorn app:app --host 0.0.0.0 --port 80 --reload
```

- API 서버가 `http://localhost:80`에서 실행됩니다.
- Swagger UI는 `http://localhost:80/docs`에서 확인할 수 있습니다.

**프론트엔드 (React + Vite)**

```bash
cd frontend
npm run dev
```

- 개발 서버가 `http://localhost:3000`에서 실행됩니다.
- Vite의 HMR(Hot Module Replacement)이 활성화되어 코드 변경 시 자동으로 반영됩니다.

**Kubernetes 배포 환경**

```bash
# 전체 시스템 한 번에 기동
./init.sh
```

- 배포 후 프론트엔드: `http://<IP>:30173`
- 배포 후 API: `http://<IP>:30461/docs`

---

## 2. 코드 컨벤션

### 2.1 Python (백엔드)

- **스타일 가이드**: PEP 8을 준수합니다.
- **docstring**: 모든 모듈과 함수에 docstring을 작성합니다.
- **type hints**: 함수 매개변수와 반환값에 타입 힌트를 사용하는 것을 권장합니다.

```python
"""FN-XXX: 모듈 설명을 한 줄로 작성합니다."""

from api_modules.database import query_db


async def create_something(data: dict) -> dict:
    """새로운 항목을 생성합니다.

    Args:
        data: 생성할 항목의 데이터.

    Returns:
        생성된 항목 정보를 담은 딕셔너리.
    """
    result = query_db(
        "INSERT INTO table_name (col1, col2) VALUES (%s, %s)",
        (data["col1"], data.get("col2", "default")),
        fetch=False,
    )
    return {"status": "ok"} if result else {"error": "생성 실패"}
```

### 2.2 JavaScript / React (프론트엔드)

- **컴포넌트**: 함수형 컴포넌트(Function Component)만 사용합니다.
- **상태 관리**: React Hooks (`useState`, `useEffect`, `useRef`)를 사용합니다.
- **스타일링**: Tailwind CSS utility-first 방식을 사용합니다.
- **API 호출**: `axios`를 사용하며, `axios.defaults.baseURL`이 설정되어 있습니다.

```jsx
const MyComponent = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get('/api/my-endpoint').then(r => setData(r.data));
  }, []);

  return (
    <div className="bg-[#0f172a] p-4 rounded-xl">
      <Table cols={['ID', '이름']} rows={data}
        renderRow={row => (
          <tr key={row.id}>
            <td className="p-3 text-white">{row.id}</td>
            <td className="p-3 text-white">{row.name}</td>
          </tr>
        )}
      />
    </div>
  );
};
```

### 2.3 파일 네이밍 규칙

| 위치 | 규칙 | 예시 |
|------|------|------|
| `api_modules/` | `mes_*.py` (기능 모듈), `sys_*.py` (시스템 모듈) | `mes_items.py`, `mes_quality.py`, `sys_logic.py` |
| `infra/` | `*.yaml` (Kubernetes 매니페스트) | `mes-api.yaml`, `postgres.yaml` |
| `frontend/src/` | PascalCase `.jsx` (컴포넌트), camelCase `.js` (유틸리티) | `BomList.jsx`, `api.js` |
| `db/` | SQL 스크립트 | `init.sql` |

---

## 3. 브랜치 전략

Git Flow 기반의 브랜치 전략을 사용합니다.

### 3.1 브랜치 구조

```
main            ← 프로덕션 배포 브랜치 (항상 안정 상태 유지)
├── develop     ← 개발 통합 브랜치 (다음 릴리스 준비)
│   ├── feature/FN-038-new-module    ← 기능 개발
│   ├── feature/ui-dark-theme        ← 기능 개발
│   └── feature/api-pagination       ← 기능 개발
└── hotfix/fix-login-error           ← 긴급 수정 (main에서 분기)
```

| 브랜치 | 용도 | 분기 대상 | 머지 대상 |
|--------|------|-----------|-----------|
| `main` | 프로덕션 배포 | - | - |
| `develop` | 개발 통합 | `main` | `main` |
| `feature/*` | 기능 개발 | `develop` | `develop` |
| `hotfix/*` | 긴급 수정 | `main` | `main`, `develop` |

### 3.2 브랜치 생성 예시

```bash
# 새 기능 개발 시
git checkout develop
git pull origin develop
git checkout -b feature/FN-038-new-module

# 긴급 수정 시
git checkout main
git pull origin main
git checkout -b hotfix/fix-critical-bug
```

### 3.3 커밋 메시지 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.

**형식:**

```
<type>: <description>
```

**커밋 타입:**

| 타입 | 용도 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 추가 | `feat: add equipment failure prediction API` |
| `fix` | 버그 수정 | `fix: resolve login token expiration issue` |
| `docs` | 문서 변경 | `docs: update API endpoint documentation` |
| `refactor` | 코드 리팩토링 (기능 변경 없음) | `refactor: extract hardcoded YAML from init.sh` |
| `test` | 테스트 추가 또는 수정 | `test: add unit tests for quality module` |
| `style` | 코드 포맷 변경 (기능 변경 없음) | `style: fix PEP 8 line length warnings` |
| `chore` | 빌드, 설정 파일 변경 | `chore: update Python dependencies` |

**좋은 커밋 메시지 예시:**

```
feat: add filter functionality to all data tables
fix: resolve SQL injection vulnerability in item search
refactor: extract database connection logic into connection pool
docs: add HOWTOSTART and ARCH documentation
```

---

## 4. 개발 워크플로우

### 4.1 전체 흐름

```
Issue 생성 → 브랜치 생성 → 개발 → 테스트 → PR 생성 → 코드 리뷰 → 머지
```

### 4.2 상세 단계

#### 1단계: Issue 생성

- GitHub Issues에 작업 내용을 등록합니다.
- 기능 요구사항(FN-XXX) 번호가 있으면 제목에 포함합니다.
- 라벨을 활용합니다: `feature`, `bug`, `enhancement`, `documentation`.

#### 2단계: 브랜치 생성

```bash
git checkout develop
git pull origin develop
git checkout -b feature/FN-038-inventory-alert
```

#### 3단계: 개발

- 코드 컨벤션을 준수하며 개발합니다.
- 작은 단위로 자주 커밋합니다.
- 하드코딩을 피하고 `env.sh`에서 설정값을 관리합니다.

#### 4단계: 테스트

```bash
# 백엔드 테스트
pytest test_app.py -v

# 프론트엔드 테스트
cd frontend && npm test
```

#### 5단계: PR(Pull Request) 생성

```bash
git push origin feature/FN-038-inventory-alert
```

GitHub에서 PR을 생성합니다.

#### 6단계: 코드 리뷰 및 머지

- 최소 1명 이상의 리뷰어 승인을 받습니다.
- 리뷰 코멘트를 반영한 후 머지합니다.

### 4.3 PR 작성 요령

PR을 생성할 때 아래 템플릿을 참고하여 작성합니다.

```markdown
## 변경 내용 요약
- FN-038: 재고 부족 알림 기능 추가
- 안전 재고 이하 시 대시보드에 경고 표시

## 변경 파일
- `api_modules/mes_inventory.py`: 재고 알림 조회 API 추가
- `app.py`: `/api/inventory/alerts` 라우트 등록
- `frontend/src/App.jsx`: 대시보드에 알림 카드 추가

## 테스트 방법
1. `pytest test_app.py -v` 실행하여 전체 테스트 통과 확인
2. `curl http://localhost:30461/api/inventory/alerts` 로 API 응답 확인
3. 프론트엔드에서 대시보드 페이지 접속하여 알림 카드 표시 확인

## 스크린샷 (UI 변경 시)
<!-- UI가 변경된 경우 스크린샷을 첨부합니다 -->
```

---

## 5. 백엔드 기능 추가 방법

### 5.1 API 모듈 작성

`api_modules/mes_*.py` 파일에 새로운 기능 함수를 작성합니다.

**예시: `api_modules/mes_inventory.py`에 알림 기능 추가**

```python
"""FN-029~031: Inventory management module."""

from api_modules.database import query_db


async def get_alerts() -> dict:
    """안전 재고 이하 품목 목록을 조회합니다.

    Returns:
        알림 대상 품목 리스트를 담은 딕셔너리.
    """
    rows = query_db(
        "SELECT item_code, name, current_qty, safety_stock "
        "FROM inventory WHERE current_qty < safety_stock"
    )
    return {"alerts": rows, "count": len(rows)}
```

**핵심 규칙:**

- `api_modules/database.py`의 `query_db()` 함수를 사용합니다.
- `query_db(sql, params, fetch=True)`: SELECT 쿼리 시 `fetch=True` (기본값), INSERT/UPDATE/DELETE 시 `fetch=False`로 호출합니다.
- 커넥션 풀을 직접 다루어야 하는 경우 `get_conn()` / `release_conn()`을 사용합니다.
- 반드시 `try/except/finally` 블록에서 커넥션을 반환하거나, `db_connection()` 컨텍스트 매니저를 사용합니다.

### 5.2 `query_db()` 사용법

```python
from api_modules.database import query_db

# SELECT (fetch=True, 기본값) → 결과를 list[dict]로 반환
rows = query_db("SELECT * FROM items WHERE category = %s", ("RAW",))

# INSERT/UPDATE/DELETE (fetch=False) → 성공 시 True, 실패 시 [] 반환
result = query_db(
    "INSERT INTO items (item_code, name) VALUES (%s, %s)",
    ("ITM-00001", "볼트"),
    fetch=False,
)

# 파라미터 바인딩 (SQL 인젝션 방지)
# 올바른 방법: %s 플레이스홀더 사용
rows = query_db("SELECT * FROM items WHERE name = %s", (user_input,))

# 잘못된 방법: f-string 직접 삽입 (절대 금지)
# rows = query_db(f"SELECT * FROM items WHERE name = '{user_input}'")
```

### 5.3 `app.py`에 라우트 등록

```python
# app.py 상단에 import 추가
from api_modules import mes_inventory

# 적절한 섹션에 라우트 추가
# ── FN-029~031: Inventory ────────────────────────────────

@app.get("/api/inventory/alerts")
async def get_inventory_alerts():
    return await mes_inventory.get_alerts()


@app.post("/api/inventory/new-endpoint")
async def new_endpoint(request: Request):
    return await mes_inventory.new_function(await request.json())
```

**라우트 등록 규칙:**

- `app.py`에서 기능 번호(FN-XXX) 주석 섹션 아래에 등록합니다.
- GET 요청: 경로 매개변수와 쿼리 매개변수를 함수 시그니처에 직접 선언합니다.
- POST/PUT 요청: `Request` 객체에서 `await request.json()`으로 요청 본문을 읽어 모듈 함수에 전달합니다.

### 5.4 ConfigMap 재배포

백엔드 코드를 수정한 후 Kubernetes 환경에 반영하려면 ConfigMap을 재배포합니다.

```bash
# 1. 소스 코드 수정 후 ConfigMap 업데이트
kubectl create configmap mes-api-code \
  --from-file=app.py \
  --from-file=api_modules/ \
  -n default --dry-run=client -o yaml | kubectl apply -f -

# 2. Pod 재시작
kubectl rollout restart deployment mes-api

# 3. 배포 상태 확인
kubectl rollout status deployment mes-api
```

---

## 6. 프론트엔드 기능 추가 방법

### 6.1 App.jsx 내 메뉴/섹션 추가 패턴

현재 프로젝트는 `App.jsx` 내에서 `menu` 상태 값에 따라 섹션을 렌더링하는 구조입니다.

**1단계: 메뉴 상태 값 추가**

```jsx
// menu 상태에 새로운 값 추가
const [menu, setMenu] = useState('DASHBOARD');

// 메뉴 버튼에 항목 추가
<button onClick={() => setMenu('NEW_SECTION')}>새 섹션</button>
```

**2단계: 섹션 렌더링**

```jsx
{menu === 'NEW_SECTION' && (
  <div className="space-y-4">
    <h2 className="text-xl font-bold text-white">새 섹션 제목</h2>
    {/* 섹션 내용 */}
  </div>
)}
```

### 6.2 state 관리 및 API 호출

```jsx
const [items, setItems] = useState([]);
const [loading, setLoading] = useState(false);

// 데이터 로드
useEffect(() => {
  setLoading(true);
  axios.get('/api/items')
    .then(r => setItems(r.data.items || r.data))
    .catch(err => console.error('API Error:', err))
    .finally(() => setLoading(false));
}, [menu]);

// 데이터 생성
const handleCreate = async () => {
  try {
    const res = await axios.post('/api/items', { name: '신규 품목', category: 'RAW' });
    if (!res.data.error) {
      // 성공 시 목록 새로고침
      const updated = await axios.get('/api/items');
      setItems(updated.data.items || updated.data);
    }
  } catch (err) {
    console.error('Create Error:', err);
  }
};
```

### 6.3 공통 컴포넌트 활용

`App.jsx` 상단에 정의된 공통 컴포넌트를 활용합니다.

| 컴포넌트 | 용도 | 사용법 |
|----------|------|--------|
| `Card` | 통계 카드 (대시보드 KPI) | `<Card title="총 품목" value={items.length} color="text-blue-500" />` |
| `Table` | 데이터 테이블 | `<Table cols={['코드','이름']} rows={data} renderRow={row => ...} />` |
| `Badge` | 상태 배지 | `<Badge v="RUNNING" />` (RUNNING/DONE/PASS: 녹색, DOWN/FAIL: 빨간색) |
| `Input` | 텍스트 입력 | `<Input value={val} onChange={e => setVal(e.target.value)} placeholder="입력" />` |
| `Btn` | 액션 버튼 | `<Btn onClick={handleSave}>저장</Btn>` |
| `FilterBar` | 필터 영역 컨테이너 | `<FilterBar>{/* 필터 요소들 */}</FilterBar>` |
| `FilterSelect` | 드롭다운 필터 | `<FilterSelect label="상태" value={filter} onChange={setFilter} options={[{value:'ALL',label:'전체'}]} />` |
| `FilterSearch` | 검색 필터 | `<FilterSearch value={search} onChange={setSearch} placeholder="검색..." />` |

**종합 사용 예시:**

```jsx
{menu === 'ITEMS' && (
  <div className="space-y-4">
    <FilterBar>
      <FilterSelect label="카테고리" value={tf.items.category}
        onChange={v => setFilter('items','category',v)}
        options={[{value:'ALL',label:'전체'},{value:'RAW',label:'원자재'}]} />
      <FilterSearch value={tf.items.search}
        onChange={v => setFilter('items','search',v)} placeholder="품목 검색..." />
    </FilterBar>
    <Table cols={['코드','이름','카테고리','상태']} rows={filteredItems}
      renderRow={row => (
        <tr key={row.item_code}>
          <td className="p-3 text-white">{row.item_code}</td>
          <td className="p-3 text-white">{row.name}</td>
          <td className="p-3 text-slate-400">{row.category}</td>
          <td className="p-3"><Badge v={row.status} /></td>
        </tr>
      )} />
  </div>
)}
```

---

## 7. 인프라 변경 방법

### 7.1 Kubernetes 매니페스트 수정

인프라 관련 파일은 `infra/` 디렉토리에 위치합니다.

| 파일 | 용도 |
|------|------|
| `infra/mes-api.yaml` | 백엔드 API Deployment + Service |
| `infra/mes-frontend.yaml` | 프론트엔드 Deployment + Service |
| `infra/postgres.yaml` | PostgreSQL Deployment + Service |
| `infra/postgres-pv.yaml` | PostgreSQL PersistentVolume |
| `infra/db-secret.yaml` | DB 접속 정보 Secret |
| `infra/nginx-config.yaml` | Nginx 프록시 설정 ConfigMap |
| `infra/keycloak.yaml` | Keycloak 인증 서버 |

**매니페스트 수정 후 적용:**

```bash
# 특정 리소스 적용
kubectl apply -f infra/mes-api.yaml

# 전체 인프라 적용
kubectl apply -f infra/
```

### 7.2 `env.sh`에 새 변수 추가

설정값은 절대로 코드에 하드코딩하지 않으며, `env.sh`에서 환경 변수로 관리합니다.

```bash
# env.sh에 새 변수 추가 패턴
# 환경 변수가 설정되어 있으면 그 값을 사용하고, 없으면 기본값 사용
NEW_VARIABLE="${MES_NEW_VAR:-default_value}"
```

**변수 추가 시 준수 사항:**

- 변수명은 대문자 스네이크 케이스를 사용합니다.
- 외부 환경 변수에는 `MES_` 접두사를 붙입니다.
- 반드시 기본값(`:-default`)을 제공합니다.
- 해당 변수가 무엇인지 주석으로 설명합니다.

### 7.3 NodePort 범위

Kubernetes NodePort 서비스의 포트 범위는 **30000~32767**입니다.

현재 사용 중인 포트:

| 포트 | 서비스 |
|------|--------|
| `30173` | 프론트엔드 (React) |
| `30461` | 백엔드 API (FastAPI) |
| `30080` | Keycloak 인증 서버 |

새 서비스를 추가할 때는 기존 포트와 충돌하지 않는 포트를 선택하고, `env.sh`에 변수로 등록합니다.

```bash
# env.sh에 추가
PORT_NEW_SERVICE="${MES_PORT_NEW_SERVICE:-30XXX}"
```

---

## 8. 테스트

### 8.1 백엔드 테스트

```bash
# 전체 테스트 실행
pytest test_app.py -v

# 특정 테스트 클래스만 실행
pytest test_app.py::TestMESDataEndpoints -v

# 특정 테스트 함수만 실행
pytest test_app.py::TestMESDataEndpoints::test_get_mes_data_success -v
```

테스트 파일 구조 (`test_app.py`):

| 테스트 클래스 | 테스트 대상 |
|---------------|------------|
| `TestMESDataEndpoints` | 핵심 API 엔드포인트 (8개 테스트) |
| `TestErrorHandling` | 404/405 에러 케이스 (4개 테스트) |
| `TestResponseFormat` | JSON 스키마 검증 (5개 테스트) |
| `TestNetworkTopology` | 네트워크 토폴로지 집계 로직 (3개 테스트) |
| `TestInfraStatusParsing` | 인프라 상태 파싱 엣지 케이스 (3개 테스트) |
| `TestAIPrediction` | AI 예측 엔드포인트 (2개 테스트) |

### 8.2 프론트엔드 테스트

```bash
cd frontend

# 테스트 실행
npm test

# ESLint 검사
npm run lint
```

### 8.3 API 수동 테스트

**Swagger UI 사용:**

배포 환경에서 `http://<IP>:30461/docs`에 접속하면 모든 API를 인터랙티브하게 테스트할 수 있습니다.

**curl 사용:**

```bash
# GET 요청
curl -s http://<IP>:30461/api/items | python -m json.tool

# POST 요청
curl -s -X POST http://<IP>:30461/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "테스트 품목", "category": "RAW", "unit": "EA"}' \
  | python -m json.tool

# 특정 항목 조회
curl -s http://<IP>:30461/api/items/ITM-00001 | python -m json.tool

# 대시보드 데이터
curl -s http://<IP>:30461/api/mes/data | python -m json.tool
```

### 8.4 새 테스트 작성 가이드

```python
# test_app.py에 새 테스트 클래스 추가
class TestNewFeature:
    """새 기능에 대한 테스트."""

    def test_create_resource(self, client):
        """리소스 생성 API를 테스트합니다."""
        response = client.post(
            "/api/new-endpoint",
            json={"name": "test", "value": 100},
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" not in data

    def test_get_resource(self, client):
        """리소스 조회 API를 테스트합니다."""
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
        assert isinstance(response.json(), (dict, list))
```

---

## 9. 코드 리뷰 체크리스트

PR을 제출하기 전, 또는 다른 개발자의 PR을 리뷰할 때 아래 항목을 확인합니다.

### 9.1 일반 사항

- [ ] 커밋 메시지가 Conventional Commits 규칙을 따르는가?
- [ ] 불필요한 파일(`.pyc`, `node_modules/`, `__pycache__/`)이 포함되지 않았는가?
- [ ] 코드에 디버깅용 `print()`, `console.log()`가 남아 있지 않은가?

### 9.2 하드코딩 확인

- [ ] IP 주소, 포트 번호 등이 코드에 직접 작성되어 있지 않은가?
- [ ] 설정값이 `env.sh`의 환경 변수를 통해 관리되고 있는가?
- [ ] 데이터베이스 접속 정보가 `DATABASE_URL` 환경 변수를 사용하는가?
- [ ] CORS 오리진이 `CORS_ORIGINS` 환경 변수를 사용하는가?

### 9.3 보안 취약점

- [ ] SQL 쿼리에 파라미터 바인딩(`%s` 플레이스홀더)을 사용하는가? (f-string 직접 삽입 금지)
- [ ] 사용자 입력이 검증 없이 SQL에 직접 삽입되지 않는가?
- [ ] API 응답에 민감한 정보(비밀번호, 시크릿 키)가 포함되지 않는가?
- [ ] 비밀번호, API 키 등이 코드에 하드코딩되지 않았는가?

### 9.4 에러 핸들링

- [ ] 데이터베이스 연결 실패 시 적절한 에러 응답을 반환하는가?
- [ ] `try/except` 블록에서 커넥션이 반드시 반환(release)되는가?
- [ ] API 응답에 사용자가 이해할 수 있는 에러 메시지가 포함되는가?
- [ ] 프론트엔드에서 API 실패 시 적절한 폴백 처리가 있는가?

### 9.5 코드 품질

- [ ] Python 코드가 PEP 8 스타일을 준수하는가?
- [ ] 새 함수에 docstring이 작성되어 있는가?
- [ ] React 컴포넌트가 함수형으로 작성되었는가?
- [ ] 공통 컴포넌트(`Card`, `Table`, `Badge` 등)를 재사용하고 있는가?
- [ ] 파일 네이밍이 규칙(`mes_*.py`, `*.yaml`)에 맞는가?

### 9.6 인프라

- [ ] NodePort가 30000~32767 범위 내인가?
- [ ] 새 환경 변수가 `env.sh`에 기본값과 함께 등록되었는가?
- [ ] Kubernetes 매니페스트가 `infra/` 디렉토리에 위치하는가?

---

## 부록: 프로젝트 디렉토리 구조

```
MES_PROJECT/
├── app.py                    # FastAPI 메인 앱 (라우트 등록)
├── env.sh                    # 환경 변수 설정 파일
├── init.sh                  # 원클릭 기동 스크립트
├── requirements.txt          # Python 의존성
├── test_app.py               # 백엔드 테스트
├── Dockerfile                # API 서버 컨테이너 이미지
├── docker-compose.yml        # 로컬 개발용 Docker Compose
├── Jenkinsfile               # CI/CD 파이프라인
├── api_modules/              # 백엔드 API 모듈
│   ├── database.py           # DB 커넥션 풀 및 query_db()
│   ├── mes_items.py          # 품목 관리 (FN-004~007)
│   ├── mes_bom.py            # BOM 관리 (FN-008~009)
│   ├── mes_process.py        # 공정/라우팅 관리 (FN-010~012)
│   ├── mes_equipment.py      # 설비 관리 (FN-013~014, FN-032~034)
│   ├── mes_plan.py           # 생산 계획 (FN-015~017)
│   ├── mes_work.py           # 작업 지시/실적 (FN-020~024)
│   ├── mes_quality.py        # 품질 관리 (FN-025~027)
│   ├── mes_inventory.py      # 재고 관리 (FN-029~031)
│   ├── mes_reports.py        # 리포트 (FN-035~037)
│   ├── mes_ai_prediction.py  # AI 수요 예측 (FN-018~019)
│   ├── mes_defect_predict.py # AI 불량 예측 (FN-028)
│   ├── mes_auth.py           # 인증/권한 (FN-001~003)
│   ├── mes_dashboard.py      # 대시보드 데이터
│   ├── k8s_service.py        # Kubernetes/네트워크 서비스
│   └── sys_logic.py          # 시스템 인프라 로직
├── frontend/                 # React 프론트엔드
│   ├── package.json          # npm 의존성 및 스크립트
│   └── src/
│       ├── App.jsx           # 메인 애플리케이션 (전체 UI)
│       ├── api.js            # API 서비스 모듈
│       ├── main.jsx          # React 엔트리포인트
│       ├── BomList.jsx       # BOM 목록 컴포넌트
│       ├── BOMManager.jsx    # BOM 관리 컴포넌트
│       └── PlanForm.jsx      # 생산 계획 폼 컴포넌트
├── infra/                    # Kubernetes 매니페스트
│   ├── mes-api.yaml          # API Deployment + Service
│   ├── mes-frontend.yaml     # 프론트엔드 Deployment + Service
│   ├── postgres.yaml         # PostgreSQL Deployment + Service
│   ├── postgres-pv.yaml      # PersistentVolume
│   ├── db-secret.yaml        # DB 시크릿
│   ├── nginx-config.yaml     # Nginx 설정
│   └── keycloak.yaml         # Keycloak 인증 서버
├── db/                       # 데이터베이스 초기화 스크립트
└── doc/                      # 프로젝트 문서
    ├── HOWTOSTART.md          # 시작 가이드
    ├── ARCH.md                # 아키텍처 문서
    ├── HANDOVER.md            # 인수인계 문서
    ├── CODE_REVIEW.md         # 코드 품질 검토서
    ├── CICD_REVIEW.md         # CI/CD 파이프라인 검토서
    └── HOWTOCONTRIBUTE.md     # 기여 가이드 (본 문서)
```

---

## 문의

프로젝트에 대한 질문이나 제안이 있으면 GitHub Issues를 통해 등록해 주세요.
