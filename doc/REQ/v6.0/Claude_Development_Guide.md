# DEXWEAVER MES v6.0 — Claude 개발 가이드

> **목적**: Claude가 코드를 직접 작성할 때 참조하는 실행 가이드
> **원칙**: 각 Task는 독립적으로 실행 가능하며, 이전 Task의 산출물에 의존
> **토큰 절약**: 각 Task 실행 시 이 파일의 해당 섹션만 참조 — 전체 재탐색 금지

---

## 실행 규칙

1. **한 세션에 하나의 Task만 실행** — 완료 후 다음 세션에서 다음 Task
2. **파일 경로를 정확히 지정** — 탐색 없이 바로 수정
3. **기존 코드 패턴을 따라라** — app.py와 api_modules/*.py의 패턴을 그대로 적용
4. **테스트 데이터 포함** — DB 테이블 생성 시 seed data도 함께 작성
5. **변경 파일 목록을 먼저 확인** — 각 Task에 명시된 파일만 수정

---

## 현재 코드 패턴 (반드시 준수 — 실제 코드에서 추출)

### 백엔드 모듈 패턴 (api_modules/mes_xxx.py)

```python
"""FN-XXX: 모듈 설명."""
import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

async def create_xxx(data: dict) -> dict:
    """FN-XXX: 기능 설명."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 비즈니스 로직 (SQL 파라미터 바인딩 필수)
        cursor.execute("SELECT ... WHERE col = %s", (data.get("key"),))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return {"error": "데이터를 찾을 수 없습니다."}

        cursor.execute("INSERT INTO ... VALUES (%s, %s)", (val1, val2))
        conn.commit()
        cursor.close()
        return {"success": True, "id": generated_id}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}  # 또는 한글 고정 메시지
    finally:
        if conn:
            release_conn(conn)

async def get_xxx_list(filter1: str = None, filter2: str = None) -> dict:
    """FN-XXX: 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = "SELECT ... FROM ..."
        params = []
        if filter1:
            sql += " WHERE col = %s"
            params.append(filter1)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {"items": [{"col1": r[0], "col2": r[1]} for r in rows]}
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
```

**DB 접근 방법 3가지** (database.py 제공):
- `get_conn()` + `release_conn()` — 가장 많이 사용 (위 패턴)
- `query_db(sql, params, fetch=True)` — 간단한 SELECT에 편리 (RealDictCursor 사용)
- `db_connection()` 컨텍스트 매니저 — with문으로 자동 release

### 백엔드 라우트 등록 패턴 (app.py)

```python
# app.py 상단에 import 추가
from api_modules import mes_xxx

# 인증 헬퍼 (이미 존재 — 재사용)
# _require_auth(request) → payload dict 또는 {"error": "...", "_status": 401}
# _require_admin(request) → admin 전용
# _auth(request) → 선택적 인증 (None 허용)

# POST 엔드포인트 (body 필요)
@app.post("/api/xxx")
async def create_xxx(request: Request):
    auth = await _require_auth(request)
    if isinstance(auth, dict) and "error" in auth:
        return auth
    return await mes_xxx.create_xxx(await request.json())

# GET 엔드포인트 (query parameter)
@app.get("/api/xxx")
async def list_xxx(filter1: str = None, filter2: str = None,
                   page: int = 1, request: Request = None):
    auth = await _require_auth(request)
    if isinstance(auth, dict) and "error" in auth:
        return auth
    return await mes_xxx.get_xxx_list(filter1, filter2)

# GET with path parameter
@app.get("/api/xxx/{item_id}")
async def get_xxx(item_id: str, request: Request):
    auth = await _require_auth(request)
    if isinstance(auth, dict) and "error" in auth:
        return auth
    return await mes_xxx.get_xxx_detail(item_id)

# PUT 엔드포인트
@app.put("/api/xxx/{item_id}")
async def update_xxx(item_id: str, request: Request):
    auth = await _require_auth(request)
    if isinstance(auth, dict) and "error" in auth:
        return auth
    return await mes_xxx.update_xxx(item_id, await request.json())
```

### 프론트엔드 패턴 (frontend/src/App.jsx)

```jsx
// ① menus 배열에 항목 추가 (약 라인 30~)
const menus = [
  // ... 기존 14개 메뉴 ...
  {id:'SPC', label:'SPC'},        // 추가
  {id:'CAPA', label:'CAPA'},      // 추가
];

// ② 메인 콘텐츠 영역에 IIFE 패턴으로 렌더링 추가 (약 라인 560~)
{menu==='SPC' && (() => {
  // 이 안에서 useState, useEffect 사용 가능
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get('/api/quality/spc/ITM-00001');
        setData(r.data);
      } catch(err) { showToast('조회 실패', false); }
      setLoading(false);
    })();
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">SPC 관리도</h2>
      {/* 테이블/차트 등 */}
    </div>
  );
})()}
```

**프론트엔드 핵심 사항**:
- **React Router 미사용** — `useState('DASHBOARD')`로 메뉴 전환
- **axios 사용** (fetch 아님) — interceptor로 JWT 자동 첨부
- **IIFE 패턴** — `{menu==='XXX' && (() => { ... })()}`
- **토큰 관리** — `localStorage.getItem('mes_user')` → `JSON.parse()` → `user.token`
- **토스트** — `showToast(msg, ok=true)` 함수 사용
- **모달** — `setModal({type:'xxx', data:{...}})` 상태 관리
- **필터** — `tf` 객체 + `setFilter(table, field, val)` 함수

### ID 자동생성 패턴

```python
# 날짜 기반: WO-YYYYMMDD-SEQ, LOT-YYYYMMDD-SEQ, IN/OUT-YYYYMMDD-SEQ
date_part = date.today().strftime("%Y%m%d")
cursor.execute("SELECT COUNT(*) FROM table WHERE id LIKE %s", (f"PREFIX-{date_part}-%",))
seq = cursor.fetchone()[0] + 1
new_id = f"PREFIX-{date_part}-{seq:03d}"  # CAPA-20260303-001

# 순차 기반: ITM-00001, EQP-001, PRC-001
cursor.execute("SELECT code FROM table ORDER BY code DESC LIMIT 1")
row = cursor.fetchone()
seq = int(row[0].split("-")[1]) + 1 if row else 1
new_code = f"PREFIX-{seq:03d}"  # 또는 f"PREFIX-{seq:05d}"
```

### DB 테이블 패턴 (db/init.sql)

```sql
CREATE TABLE IF NOT EXISTS table_name (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    foreign_col VARCHAR(20) REFERENCES parent_table(parent_col),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE')),
    data_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(code)
);

CREATE INDEX IF NOT EXISTS idx_table_col ON table_name(column);

-- seed data
INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2') ON CONFLICT DO NOTHING;
```

---

## Phase 1 Tasks (총 13개)

### Task 1-01: 프론트엔드 API 서비스 레이어 분리 (NFR-001 부분)

**목표**: App.jsx 내 axios 호출을 서비스 레이어로 분리 (컴포넌트 분리는 후속 Task)
**현재 상태**:
- axios **이미 사용 중** (interceptor로 JWT 자동 첨부 포함)
- React Router **미사용** — `useState('DASHBOARD')` 기반 메뉴 전환
- 단일 파일 SPA (App.jsx 2851줄, IIFE 렌더링 패턴)

**수정 파일**:
- `frontend/src/services/api.js` — 신규: App.jsx의 axios 인스턴스/인터셉터 추출
- `frontend/src/App.jsx` — axios 직접 import → `api.js` import로 전환

**작업 내용**:
1. `frontend/src/services/api.js` 생성 — App.jsx에 이미 존재하는 axios 인스턴스 + interceptor 코드를 그대로 추출:
```javascript
import axios from 'axios';
const api = axios.create({ baseURL: '' });
api.interceptors.request.use(cfg => {
  const u = JSON.parse(localStorage.getItem('mes_user') || '{}');
  if (u.token) cfg.headers.Authorization = `Bearer ${u.token}`;
  return cfg;
});
export default api;
```
2. App.jsx에서 `axios` 직접 호출 → `api` import로 교체 (기존 IIFE 패턴/메뉴 구조 변경 없음)
3. **React Router 미도입** — 현재 상태 기반 라우팅 유지 (불필요한 구조 변경 회피)

**완료 기준**: `npm run build` 성공, 기존 14개 메뉴 모두 동작 유지

---

### Task 1-02: 인증 보일러플레이트 리팩토링 (NFR-004)

**목표**: app.py의 반복적 인증 보일러플레이트 간소화
**현재 상태**:
- app.py에 `_require_auth(request)`, `_require_admin(request)`, `_auth(request)` 헬퍼 이미 존재
- 각 엔드포인트마다 3줄 반복: `auth = await _require_auth(request)` → `if isinstance(auth, dict) and "error" in auth:` → `return auth`
- mes_auth.py의 `require_auth()` → payload dict 또는 `{"error": "...", "_status": 401}` 반환 (HTTPException 미사용)
- **API 응답 형식이 dict 기반** — HTTPException으로 전환 시 기존 프론트엔드 호환성 깨짐

**수정 파일**:
- `app.py` — FastAPI Depends를 활용한 인증 데코레이터 도입

**작업 내용**:
1. app.py에 인증 의존성 함수 추가 (기존 응답 형식 유지):
```python
from fastapi import Depends

async def auth_required(request: Request):
    """기존 _require_auth 래핑 — dict 에러 반환 시 JSONResponse로 변환."""
    result = await mes_auth.require_auth(request)
    if isinstance(result, dict) and "error" in result:
        status = result.pop("_status", 401)
        raise HTTPException(status_code=status, detail=result["error"])
    return result

async def admin_required(request: Request):
    """기존 _require_admin 래핑."""
    result = await mes_auth.require_admin(request)
    if isinstance(result, dict) and "error" in result:
        status = result.pop("_status", 403)
        raise HTTPException(status_code=status, detail=result["error"])
    return result
```
2. app.py에 exception_handler 추가 — HTTPException을 기존 dict 형식으로 변환:
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code,
                       content={"error": exc.detail})
```
3. 엔드포인트 리팩토링 (3줄 → 1줄 파라미터):
```python
# Before (현재)
@app.post("/api/xxx")
async def create_xxx(request: Request):
    auth = await _require_auth(request)
    if isinstance(auth, dict) and "error" in auth:
        return auth
    return await mes_xxx.create_xxx(await request.json())

# After (리팩토링)
@app.post("/api/xxx")
async def create_xxx(request: Request, user=Depends(auth_required)):
    return await mes_xxx.create_xxx(await request.json())
```
4. `/api/health`, `/api/auth/login`, `/api/auth/register`는 Depends 미적용 (현재와 동일)

**완료 기준**: 모든 API 엔드포인트 동작 확인, 프론트엔드 호환성 유지, 401/403 응답 형식 동일

---

### Task 1-03: Alembic 도입 (NFR-005)

**목표**: DB 마이그레이션 도구 셋업
**수정 파일**:
- `alembic.ini` — 신규
- `alembic/env.py` — 신규
- `alembic/versions/` — baseline 마이그레이션

**작업 내용**:
```bash
pip install alembic
alembic init alembic
```
1. `alembic.ini`의 sqlalchemy.url을 env.sh의 DB 접속 정보로 설정
2. `alembic/env.py` — 환경변수에서 DB URL 읽도록 수정
3. 현재 init.sql의 21개 테이블을 baseline으로 마이그레이션 생성:
   ```bash
   alembic revision --autogenerate -m "baseline: v4.0 21 tables"
   ```

**완료 기준**: `alembic upgrade head` → 21개 테이블 생성, `alembic downgrade -1` → 롤백 성공

---

### Task 1-04: Docker 빌드 전환 (NFR-002)

**목표**: ConfigMap 배포 → Docker 이미지 빌드 배포
**신규 파일**:
- `Dockerfile` — 백엔드 멀티스테이지
- `frontend/Dockerfile` — 프론트엔드 nginx
- `docker-compose.yml` — 개발 환경
- `.dockerignore`

**작업 내용**:
1. 백엔드 Dockerfile:
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
2. 프론트엔드 Dockerfile:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```
3. docker-compose.yml: postgres:15 + redis:7 + api + frontend
4. K8s 매니페스트(infra/*.yaml) 업데이트: image 참조 방식으로 변경

**완료 기준**: `docker compose up -d` → 전체 서비스 기동, API/프론트엔드 접속 확인

---

### Task 1-05: AI 모델 캐싱 (NFR-003)

**목표**: AI API 응답 5초 → <200ms
**수정 파일**:
- `api_modules/ai_model_cache.py` — 신규: 모델 캐시 매니저
- `api_modules/mes_ai_prediction.py` — Prophet 모델 캐싱 적용
- `api_modules/mes_defect_predict.py` — XGBoost 모델 캐싱 적용
- `api_modules/mes_equipment.py` — IsolationForest 모델 캐싱 적용

**작업 내용**:
1. `ai_model_cache.py` 생성:
```python
import joblib, os, hashlib
from datetime import datetime, timedelta

MODEL_DIR = "/tmp/mes_models"

class ModelCache:
    @staticmethod
    def get_or_train(model_key, train_func, data, max_age_hours=24):
        """캐시된 모델 반환 또는 재학습"""
        path = f"{MODEL_DIR}/{model_key}.joblib"
        if os.path.exists(path):
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if datetime.now() - mtime < timedelta(hours=max_age_hours):
                return joblib.load(path)
        model = train_func(data)
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, path)
        return model
```
2. 각 AI 모듈에서 매 요청 학습 → `ModelCache.get_or_train()` 호출로 교체

**완료 기준**: AI 예측 API 호출 시 2회차부터 <200ms

---

### Task 1-06: Phase 1 DB 테이블 생성 (SPC/CAPA/OEE/알림)

**목표**: Phase 1 신규 7개 테이블 + 인덱스 생성
**수정 파일**:
- `db/init.sql` — 테이블 추가 (또는 Alembic 마이그레이션)
- Alembic 마이그레이션 파일 — 신규

**생성 테이블** (DatabaseSchema.md 참조):
1. `spc_rules` — SPC 관리 규칙 (item_code, rule_type, ucl, lcl, target, sample_size)
2. `spc_violations` — SPC 위반 이력 (rule_id, inspection_id, violation_type, measured_value)
3. `capa` — 시정/예방 조치 (capa_type, title, status, assigned_to, due_date)
4. `capa_actions` — CAPA 조치 이력 (capa_id, action_type, description, result)
5. `oee_daily` — OEE 일일 집계 (equip_code, calc_date, availability, performance, quality_rate, oee)
6. `notifications` — 알림 (user_id, type, title, message, severity, is_read)
7. `notification_settings` — 알림 설정 (user_id, notification_type, channel, is_enabled)

**인덱스**: 14개 (DatabaseSchema.md의 "Phase 1 신규 테이블 인덱스" 섹션 참조)

**완료 기준**: 마이그레이션 성공, 테이블/인덱스 존재 확인

---

### Task 1-07: SPC 관리도 백엔드 (REQ-035, FN-038~040)

**목표**: SPC 관리도 API 구현
**신규 파일**: `api_modules/mes_spc.py`
**수정 파일**: `app.py` (라우트 3개 추가)

**API 엔드포인트**:
| 엔드포인트 | 메서드 | FN | 설명 |
|:----------:|:------:|:--:|:----:|
| `/api/quality/spc/{item_code}` | GET | FN-038 | SPC 관리도 데이터 (X-bar/R 차트) |
| `/api/quality/spc/rules` | POST | FN-039 | SPC 규칙 설정 |
| `/api/quality/cpk/{item_code}` | GET | FN-040 | Cp/Cpk 분석 |

**핵심 로직**:
- X-bar = 서브그룹 평균의 평균
- R-bar = 서브그룹 범위의 평균
- UCL_X = X-bar + A2 × R-bar, LCL_X = X-bar - A2 × R-bar
- A2 계수: {2:1.880, 3:1.023, 4:0.729, 5:0.577, 6:0.483}
- D3 계수: {2:0, 3:0, 4:0, 5:0, 6:0}
- D4 계수: {2:3.267, 3:2.575, 4:2.282, 5:2.115, 6:2.004}
- Cp = (USL-LSL)/(6σ), Cpk = min((USL-X̄)/(3σ), (X̄-LSL)/(3σ))
- Western Electric 규칙: ①1점>3σ ②연속2점>2σ ③연속4점>1σ ④연속8점한쪽

**완료 기준**: SPC API 3개 동작, 테스트 데이터로 관리도 생성 확인

---

### Task 1-08: CAPA 프로세스 백엔드 (REQ-036, FN-041~043)

**목표**: CAPA 워크플로우 API 구현
**신규 파일**: `api_modules/mes_capa.py`
**수정 파일**: `app.py` (라우트 3개 추가)

**API 엔드포인트**:
| 엔드포인트 | 메서드 | FN | 설명 |
|:----------:|:------:|:--:|:----:|
| `/api/quality/capa` | POST | FN-041 | CAPA 등록 |
| `/api/quality/capa/{capa_id}/status` | PUT | FN-042 | CAPA 워크플로우 상태 전이 |
| `/api/quality/capa` | GET | FN-043 | CAPA 목록/이력 조회 |

**상태 전이**: OPEN → INVESTIGATION → ACTION → VERIFICATION → CLOSED (REJECT→OPEN)

**완료 기준**: CAPA 생성→상태전이→완료 플로우 동작 확인

---

### Task 1-09: OEE 자동계산 백엔드 (REQ-037, FN-044~045)

**목표**: OEE API 구현
**신규 파일**: `api_modules/mes_oee.py`
**수정 파일**: `app.py` (라우트 2개 추가)

**API 엔드포인트**:
| 엔드포인트 | 메서드 | FN | 설명 |
|:----------:|:------:|:--:|:----:|
| `/api/equipment/oee/{equip_code}` | GET | FN-044 | OEE 자동 계산 |
| `/api/equipment/oee/dashboard` | GET | FN-045 | OEE 대시보드 |

**핵심 로직**:
- A = (계획가동시간 - 비가동시간) / 계획가동시간
- P = (이론CT × 총생산수) / 실제가동시간
- Q = 양품수 / 총생산수
- OEE = A × P × Q
- 6대 로스: 고장/셋업/단정지/속도저하/불량/초기수율

**완료 기준**: 설비별 OEE 계산 동작, 대시보드 데이터 반환

---

### Task 1-10: WebSocket 실시간 알림 (REQ-038, FN-046~047)

**목표**: 실시간 알림 시스템 구현
**신규 파일**: `api_modules/mes_notification.py`
**수정 파일**: `app.py` (WebSocket + REST 라우트 추가)

**API 엔드포인트**:
| 엔드포인트 | 메서드 | FN | 설명 |
|:----------:|:------:|:--:|:----:|
| `/ws/notifications` | WS | FN-046 | WebSocket 알림 채널 |
| `/api/notifications/settings` | POST/GET | FN-047 | 알림 설정 관리 |
| `/api/notifications` | GET | — | 알림 이력 조회 |
| `/api/notifications/{id}/read` | PUT | — | 알림 읽음 처리 |

**핵심 로직**:
- FastAPI WebSocket 엔드포인트
- ConnectionManager 클래스: 연결 관리, 채널별 구독, 브로드캐스트
- 알림 유형: EQUIP_DOWN, SPC_VIOLATION, INVENTORY_LOW, AI_WARNING, CAPA_DUE

**완료 기준**: WebSocket 연결/구독/알림수신 동작, 알림 설정 CRUD

---

### Task 1-11: LOT 추적 강화 (REQ-039, FN-048)

**목표**: LOT 계보 추적 API 구현
**신규 파일**: `api_modules/mes_lot_trace.py`
**수정 파일**: `app.py` (라우트 1개 추가)

**API 엔드포인트**:
| 엔드포인트 | 메서드 | FN | 설명 |
|:----------:|:------:|:--:|:----:|
| `/api/lot/genealogy/{lot_no}` | GET | FN-048 | LOT 계보 추적 (Forward/Backward) |

**핵심 로직**:
- Forward: lot_no → 출고(inventory_transactions) → 작업지시(work_orders) → 실적(work_results) → 완성품 LOT
- Backward: lot_no → 작업지시 → BOM 전개 → 원자재 LOT
- 재귀 탐색 (depth 제한으로 성능 보장)
- 리콜 시뮬레이션: 영향 LOT 수, 영향 품목, 영향 수량 산출

**완료 기준**: Forward/Backward 추적 동작, 트리 구조 반환

---

### Task 1-12: Phase 1 프론트엔드 (SPC/CAPA/OEE/알림/LOT)

**목표**: Phase 1 기능의 프론트엔드 UI 구현
**현재 상태**:
- App.jsx 단일 파일 (2851줄), IIFE 렌더링 패턴
- `const menus = [{id:'DASHBOARD', label:'Dashboard'}, ...]` (14개, 아이콘 없음)
- `{menu==='XXX' && (() => { ... })()}` 패턴으로 화면 렌더링
- axios 사용, `showToast(msg, ok)`, `setModal({type, data})`, `tf`/`setFilter` 필터 관리

**수정 파일**: `frontend/src/App.jsx`

**추가 메뉴 5개** (menus 배열에 추가):
| 메뉴 ID | 라벨 | 비고 |
|:--------:|:----:|:----:|
| SPC | SPC 관리도 | 기존 id 패턴: 대문자 |
| CAPA | CAPA 관리 | |
| OEE | OEE 대시보드 | |
| NOTIFICATION | 알림 센터 | |
| LOT_TRACE | LOT 추적 | |

**구현 패턴** (기존 IIFE 패턴 준수):
```jsx
// ① menus 배열에 추가
const menus = [
  // ... 기존 14개 ...
  {id:'SPC', label:'SPC 관리도'},
  {id:'CAPA', label:'CAPA 관리'},
  {id:'OEE', label:'OEE 대시보드'},
  {id:'NOTIFICATION', label:'알림 센터'},
  {id:'LOT_TRACE', label:'LOT 추적'},
];

// ② 메인 콘텐츠 영역에 IIFE 블록 추가
{menu==='SPC' && (() => {
  const [spcData, setSpcData] = useState([]);
  // ... useEffect + axios.get('/api/quality/spc/...') ...
  return (<div className="p-6">...</div>);
})()}
```

**각 화면 구성**:
- **SPC**: X-bar/R 차트(Recharts LineChart), Cp/Cpk 표시, 위반 경보 목록
- **CAPA**: 등록 폼, 상태별 칸반 보드, 워크플로우 타임라인
- **OEE**: OEE 게이지(RadialBarChart), A/P/Q 바 차트, 6대 로스 파레토
- **알림**: WebSocket 연결, 알림 목록, 미읽음 뱃지, 설정 모달 (`setModal`)
- **LOT 추적**: LOT 번호 입력, Forward/Backward 트리 시각화

**완료 기준**: 5개 메뉴 접속/조회/등록 동작, `npm run build` 성공

---

### Task 1-13: Phase 1 테스트 데이터 + 통합 테스트

**목표**: 신규 7개 테이블의 테스트 데이터 + 전체 통합 테스트
**신규 파일**:
- `db/seed_phase1.sql` — Phase 1 테스트 데이터
- `tests/test_spc.py` — SPC API 테스트
- `tests/test_capa.py` — CAPA API 테스트
- `tests/test_oee.py` — OEE API 테스트
- `tests/test_notification.py` — 알림 API 테스트
- `tests/test_lot_trace.py` — LOT 추적 테스트
- `tests/conftest.py` — pytest fixture (DB 연결, 인증 토큰)

**테스트 데이터 규모**:
| 테이블 | 건수 | 내용 |
|:------:|:----:|:----:|
| spc_rules | 10 | 5개 품목 × 2개 검사항목별 SPC 규칙 |
| spc_violations | 20 | 위반 이력 (resolved/unresolved) |
| capa | 10 | 상태별 2건씩 (OPEN~CLOSED) |
| capa_actions | 30 | CAPA당 3건 조치 |
| oee_daily | 150 | 15개 설비 × 10일간 OEE |
| notifications | 50 | 유형별 10건 |
| notification_settings | 20 | 사용자별 알림 설정 |

**완료 기준**: `pytest tests/ -v` 전체 통과, seed 데이터 정상 삽입

---

## Phase 1+ Tasks (총 8개)

### Task 1+-01: 보안 강화 (NFR-007, NFR-012, NFR-013)

**수정 파일**:
- `api_modules/security.py` — 신규: Rate Limiting, 보안 이벤트 로깅
- `app.py` — slowapi 미들웨어 등록
- `requirements.txt` — slowapi 추가

**작업**: slowapi Rate Limiting(로그인 5/min, 일반 API 100/min), JWT Secret 환경변수 전환, 5회 실패→15분 잠금

---

### Task 1+-02: 바코드/QR 지원 (REQ-052)

**신규 파일**: `api_modules/mes_barcode.py`
**수정 파일**: `app.py`, `frontend/src/App.jsx`

**API**: `/api/barcode/generate` (POST), `/api/barcode/scan` (POST)
**라이브러리**: python-barcode, qrcode, Pillow

---

### Task 1+-03: 전자 작업지시서 (REQ-053)

**신규 파일**: `api_modules/mes_ewi.py`
**수정 파일**: `app.py`, `frontend/src/App.jsx`

**API**: `/api/work-instructions` (POST/GET), `/api/work-instructions/{wi_id}/steps/{step_no}/sign` (POST)

---

### Task 1+-04: 부적합품 관리 NCR (REQ-054)

**신규 파일**: `api_modules/mes_ncr.py`
**수정 파일**: `app.py`, `frontend/src/App.jsx`

**API**: `/api/quality/ncr` (POST/GET), `/api/quality/ncr/{ncr_id}/disposition` (PUT)
**상태**: DETECTED → QUARANTINED → MRB_REVIEW → DISPOSITION → CLOSED

---

### Task 1+-05: SPC 자동격리 + 출하판정 (REQ-055, REQ-056)

**수정 파일**: `api_modules/mes_spc.py` (확장), `api_modules/mes_disposition.py` (신규)
**수정 파일**: `app.py`, `frontend/src/App.jsx`

**API**: `/api/quality/spc/auto-actions` (POST), `/api/quality/disposition` (POST/GET)

---

### Task 1+-06: FPY 자동계산 (REQ-057)

**신규 파일**: `api_modules/mes_kpi.py`
**수정 파일**: `app.py`, `frontend/src/App.jsx`

**API**: `/api/kpi/fpy` (GET)
**로직**: FPY = 1차 양품수 / 투입수, RTY = FPY₁ × FPY₂ × ... × FPYₙ

---

### Task 1+-07: 설비보전 KPI (REQ-058)

**수정 파일**: `api_modules/mes_kpi.py` (확장)
**수정 파일**: `app.py`, `frontend/src/App.jsx`

**API**: `/api/kpi/maintenance/{equip_code}` (GET)
**로직**: MTTF = 총가동시간/고장횟수, MTTR = 총수리시간/고장횟수, MTBF = MTTF + MTTR

---

### Task 1+-08: 모바일 반응형 UI (NFR-011)

**수정 파일**: `frontend/src/App.jsx` — Tailwind 반응형 클래스 적용
**대상 화면**: 작업지시, 실적입력, 품질검사, 설비상태 (4개 핵심 화면)
**패턴**: `className="hidden md:block"` / `className="grid grid-cols-1 md:grid-cols-3"`

---

## Phase 2 Tasks (총 7개)

### Task 2-01: asyncpg 전환 + Redis (NFR-006, NFR-009)
### Task 2-02: Phase 2 DB 테이블 (8개)
### Task 2-03: CMMS 유지보수 (REQ-040, FN-049~051)
### Task 2-04: 레시피 관리 (REQ-041, FN-052~053)
### Task 2-05: MQTT 데이터 수집 (REQ-042, FN-054~055)
### Task 2-06: 문서 관리 DMS (REQ-043, FN-056~057)
### Task 2-07: 노동 관리 (REQ-044, FN-058)

> Phase 2 Task의 상세 내용은 Phase 1 완료 후 작성 — 아키텍처 변경(asyncpg) 영향 반영 필요

---

## Phase 3 Tasks (총 6개)

### Task 3-01: Phase 3 DB 테이블 (4개)
### Task 3-02: ERP 연동 (REQ-045, FN-059)
### Task 3-03: OPC-UA 연동 (REQ-046, FN-060~061)
### Task 3-04: 다국어 지원 (REQ-047, FN-062)
### Task 3-05: 감사 추적 (REQ-049, FN-063~064)
### Task 3-06: 디지털 트윈 + 자원관리 (REQ-048, REQ-051)

> Phase 3 Task의 상세 내용은 Phase 2 완료 후 작성

---

## Task 실행 방법 (세션별)

각 세션에서 Claude에게 아래와 같이 요청:

```
Task 1-07 실행해줘
```

Claude는:
1. 이 파일에서 Task 1-07 섹션을 참조
2. 명시된 파일만 수정/생성
3. 기존 코드 패턴(이 파일 상단) 준수
4. 완료 기준 확인

**토큰 절약 팁**:
- 파일 경로를 직접 지정하므로 탐색 불필요
- API 스펙이 명시되어 있으므로 기능명세서 재참조 불필요
- 코드 패턴이 정의되어 있으므로 기존 코드 분석 최소화

---

*최종 업데이트: 2026-03-03*
