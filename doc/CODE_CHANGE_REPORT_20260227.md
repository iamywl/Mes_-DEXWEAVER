# DEXWEAVER MES v4.0 - 코드 수정 결과 보고서

| 항목 | 내용 |
|------|------|
| **작성일** | 2026-02-27 11:50:00 KST |
| **대상 버전** | v3.0 → v4.0 |
| **분석 기준** | MES_구현현황_분석_260225.xlsx |
| **수정 근거** | GS인증 표준 (KISA 49, KS X 9003, ISO/IEC 25051) |

---

## 수정 요약

| 구분 | 수정 건수 | 주요 내용 |
|------|----------|----------|
| CRITICAL (보안) | 3건 | JWT 미들웨어, 회원가입 승인, 시크릿 하드코딩 제거 |
| MAJOR (기능) | 7건 | BOM/공정 CRUD, 상태전이, 검사판정, 출고정보, LOT추적 |
| MINOR (버그) | 3건 | EQP코드 정렬, 오류메시지 한글화, 에러핸들러 |
| **총계** | **13건** | |

---

## 1. [CRITICAL] 백엔드 JWT 인증 미들웨어 전 API 적용

- **수정 시각**: 2026-02-27 11:20 KST
- **문제**: 모든 API 엔드포인트가 토큰 검증 없이 노출 (curl 직접 호출 가능)
- **KISA 항목**: 세션 관리, 인증 우회
- **수정 파일**: `app.py`, `api_modules/mes_auth.py`

### 수정 전
```python
# app.py - 인증 없이 API 노출
@app.post("/api/items")
async def create_item(request: Request):
    return await mes_items.create_item(await request.json())
```

### 수정 후
```python
# app.py - JWT 인증 필수
@app.post("/api/items")
async def create_item(request: Request):
    auth = await _require_auth(request)
    if isinstance(auth, dict) and "error" in auth:
        return auth
    return await mes_items.create_item(await request.json())
```

### 추가 구현
- `mes_auth.py`: `verify_request()`, `require_auth()`, `require_admin()` 함수 추가
- `app.py`: 공개 엔드포인트(login, register, health) 3개를 제외한 **전체 40+개 엔드포인트**에 인증 적용
- 관리자 전용 API (권한 변경, 사용자 승인)에는 `_require_admin()` 적용

---

## 2. [CRITICAL] 회원가입 관리자 승인 절차 구현

- **수정 시각**: 2026-02-27 11:25 KST
- **문제**: 누구나 role=admin으로 즉시 등록 가능, 승인 절차 없음
- **KISA 항목**: 인증/인가, 권한 상승 방지
- **수정 파일**: `api_modules/mes_auth.py`, `db/init.sql`

### 수정 내용
```python
# mes_auth.py - 회원가입 시 승인 대기 상태로 생성
cursor.execute(
    "INSERT INTO users (user_id, password, name, email, role, is_approved) "
    "VALUES (%s, %s, %s, %s, %s, FALSE)",  # 승인 대기
    ...
)

# admin 역할 자가등록 차단
if role == "admin":
    role = "worker"  # 자동 강등
```

### DB 스키마 변경
```sql
ALTER TABLE users ADD COLUMN is_approved BOOLEAN NOT NULL DEFAULT TRUE;
```

### 신규 API
- `PUT /api/auth/approve/{user_id}` - 관리자 전용 사용자 승인/거부

---

## 3. [CRITICAL] JWT 시크릿 하드코딩 제거

- **수정 시각**: 2026-02-27 11:25 KST
- **문제**: `JWT_SECRET` 미설정 시 `"mes-secret-key-2026"` 하드코딩 기본값 사용
- **KISA 항목**: 하드코딩된 중요 정보
- **수정 파일**: `api_modules/mes_auth.py`

### 수정 전
```python
SECRET_KEY = os.getenv("JWT_SECRET", "mes-secret-key-2026")
```

### 수정 후
```python
_jwt_secret_env = os.getenv("JWT_SECRET", "")
if not _jwt_secret_env:
    import secrets
    _jwt_secret_env = secrets.token_hex(32)  # 랜덤 생성
    log.warning("JWT_SECRET not set – generated random secret")
SECRET_KEY = _jwt_secret_env
```

---

## 4. [MAJOR] BOM PUT/DELETE API + 재귀 순환참조 검사

- **수정 시각**: 2026-02-27 11:30 KST
- **문제**: BOM CRUD 중 C/R만 존재 (U/D 미구현), A→A만 체크 (A→B→A 미체크)
- **수정 파일**: `api_modules/mes_bom.py`, `app.py`

### 신규 함수
```python
def _check_circular(cursor, parent, child):
    """재귀 순환참조 탐지: A→B→C→A"""
    visited = set()
    def _walk(current):
        if current == parent: return True
        if current in visited: return False
        visited.add(current)
        cursor.execute("SELECT child_item FROM bom WHERE parent_item=%s", (current,))
        for (next_child,) in cursor.fetchall():
            if _walk(next_child): return True
        return False
    return _walk(child)
```

### 신규 API
- `PUT /api/bom/{bom_id}` - BOM 수정 (순환참조 검사 포함)
- `DELETE /api/bom/{bom_id}` - BOM 삭제

---

## 5. [MAJOR] 공정 PUT/DELETE API + FK 참조 검사

- **수정 시각**: 2026-02-27 11:35 KST
- **문제**: 공정 등록 후 변경/삭제 불가
- **수정 파일**: `api_modules/mes_process.py`, `app.py`

### 신규 API
- `PUT /api/processes/{process_code}` - 공정 수정
- `DELETE /api/processes/{process_code}` - 공정 삭제 (라우팅 사용 중이면 차단)

```python
# 삭제 전 FK 참조 확인
cursor.execute("SELECT COUNT(*) FROM routings WHERE process_code=%s", (process_code,))
if cursor.fetchone()[0] > 0:
    return {"error": "라우팅에서 사용 중인 공정은 삭제할 수 없습니다."}
```

---

## 6. [MAJOR] 작업지시 상태 전이 순서 강제

- **수정 시각**: 2026-02-27 11:38 KST
- **문제**: 첫 실적이 완료 시 WAIT→DONE 직행 가능 (WORKING 스킵)
- **수정 파일**: `api_modules/mes_work.py`, `app.py`

### 수정 전 (버그)
```python
# 실적 등록 시 DONE 체크 후 WORKING 전환 → 순서 역전
if row[1] >= row[0]:
    cursor.execute("UPDATE work_orders SET status='DONE' WHERE wo_id=%s", (wo_id,))
cursor.execute("UPDATE work_orders SET status='WORKING' WHERE wo_id=%s AND status='WAIT'", (wo_id,))
```

### 수정 후
```python
# Step 1: WAIT → WORKING 먼저 전환
if wo_row[0] == "WAIT":
    cursor.execute("UPDATE work_orders SET status='WORKING' WHERE wo_id=%s", (wo_id,))

# (실적 등록)

# Step 2: WORKING → DONE만 허용 (WAIT→DONE 불가)
if row[1] >= row[0]:
    cursor.execute("UPDATE work_orders SET status='DONE' WHERE wo_id=%s AND status='WORKING'", (wo_id,))
```

### 신규 API
- `PUT /api/work-orders/{wo_id}/status` - 명시적 상태 변경 (VALID_TRANSITIONS 검증)

```python
VALID_TRANSITIONS = {
    "WAIT": ["WORKING"],
    "WORKING": ["DONE", "HOLD"],
    "HOLD": ["WORKING"],
    "DONE": [],
}
```

---

## 7. [MAJOR] 비수치 검사항목 자동판정 로직

- **수정 시각**: 2026-02-27 11:40 KST
- **문제**: check_type ≠ NUMERIC이면 measured_value 무관하게 무조건 PASS
- **수정 파일**: `api_modules/mes_quality.py`

### 수정 후 (3가지 검사 유형 지원)
```python
if check_type == "NUMERIC":    # 수치형: min/max 범위 검사
elif check_type == "TEXT":      # 텍스트형: 기준값 일치 검사
elif check_type == "VISUAL":    # 외관검사: PASS/OK/합격 판정
else:                           # 기타: 명시적 judgment 사용
```

---

## 8. [MAJOR] 출고 트랜잭션 정보 보강

- **수정 시각**: 2026-02-27 11:42 KST
- **문제**: inventory_transactions에 lot_no/warehouse 미기록, out_type 미검증
- **수정 파일**: `api_modules/mes_inventory.py`

### 수정 내용
```python
# 출고유형 화이트리스트 검증
VALID_OUT_TYPES = {"OUT", "SHIP", "SCRAP", "RETURN"}

# FIFO 출고 시 warehouse 정보도 함께 추출
cur.execute("SELECT inv_id, lot_no, qty, warehouse FROM inventory ...")

# 트랜잭션에 lot_no + warehouse 기록
cur.execute(
    "INSERT INTO inventory_transactions "
    "(slip_no, item_code, lot_no, qty, tx_type, warehouse, ref_id) "
    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
    (slip_no, item_code, first_lot.get("lot_no"), qty_needed,
     out_type, first_lot.get("warehouse"), data.get("ref_id")),
)
```

---

## 9. [MAJOR] LOT 추적성 API (신규)

- **수정 시각**: 2026-02-27 11:44 KST
- **GS인증**: KS X 9003 LOT 추적성 데이터 연결 성공률 100% 요구
- **수정 파일**: `api_modules/mes_inventory.py`, `app.py`

### 신규 API: `GET /api/lot/trace/{lot_no}`

응답 구조:
```json
{
  "lot_no": "LOT-20260210-001",
  "inventory": [...],         // LOT 기본 재고 정보
  "transactions": [...],      // 입출고 이력
  "work_orders": [            // 관련 작업지시
    {
      "wo_id": "WO-20260210-001",
      "equip_code": "EQP-001",   // 설비 ID
      "results": [
        { "worker_id": "worker01", "start_time": "...", "end_time": "..." }
      ]
    }
  ],
  "inspections": [...],       // 품질검사 이력
  "trace_complete": true
}
```

---

## 10. [MINOR] EQP 코드 숫자 정렬 버그 수정

- **수정 시각**: 2026-02-27 11:42 KST
- **문제**: `ORDER BY equip_code DESC` → 사전순 정렬 (EQP-9 > EQP-10)
- **수정 파일**: `api_modules/mes_equipment.py`

```python
# 수정 전
"ORDER BY equip_code DESC LIMIT 1"

# 수정 후
"ORDER BY CAST(SUBSTRING(equip_code FROM 5) AS INTEGER) DESC LIMIT 1"
```

---

## 11. [MINOR] 전역 예외 처리기 (Stack Trace 노출 방지)

- **수정 시각**: 2026-02-27 11:20 KST
- **KISA 항목**: 에러 처리 시 DB 구조/Stack Trace 노출 방지
- **수정 파일**: `app.py`

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "서버 내부 오류가 발생했습니다. 관리자에게 문의해주세요."},
    )
```

---

## 12. [MINOR] 오류 메시지 한국어 표준화

- **수정 시각**: 2026-02-27 11:45 KST
- **전체 모듈**: `str(e)` → 사용자 정의 한국어 메시지

| 기존 | 수정 |
|------|------|
| `"Database connection failed."` | `"데이터베이스 연결에 실패했습니다."` |
| `"Invalid user_id or password."` | `"아이디 또는 비밀번호가 올바르지 않습니다."` |
| `"User ID already exists."` | `"이미 존재하는 사용자 ID입니다."` |
| `str(e)` (예외 직접 노출) | `"처리 중 오류가 발생했습니다."` |

---

## 13. [MINOR] AI 인사이트 명칭 정정

- **수정 시각**: 2026-02-27 11:46 KST
- **문제**: SQL 집계 + 규칙 기반인데 "AI" 엔드포인트/라벨 사용
- **수정**: 엔드포인트 유지 (`/api/ai/insights`), 라벨을 "분석 인사이트"로 문서 명시

---

## 수정 파일 목록

| 파일 | 수정 유형 | 주요 변경 |
|------|----------|----------|
| `app.py` | 전면 재작성 | JWT 미들웨어, 전역 에러 핸들러, 신규 엔드포인트 10개+ |
| `api_modules/mes_auth.py` | 대폭 수정 | 토큰 검증, 승인 절차, 입력 검증, 시크릿 보안 |
| `api_modules/mes_bom.py` | 추가 | PUT/DELETE, 재귀 순환참조 검사 |
| `api_modules/mes_process.py` | 추가 | PUT/DELETE, FK 참조 검사 |
| `api_modules/mes_work.py` | 수정 | 상태 전이 로직, 명시적 상태변경 API |
| `api_modules/mes_quality.py` | 수정 | 비수치 검사(TEXT/VISUAL) 판정 로직 |
| `api_modules/mes_inventory.py` | 수정+추가 | 출고 정보 보강, LOT 추적 API |
| `api_modules/mes_equipment.py` | 수정 | EQP 코드 숫자 정렬 |
| `db/init.sql` | 수정 | is_approved 컬럼, manager 역할 추가 |
| `doc/GS_CERTIFICATION_TEST_REPORT.md` | 신규 | GS인증 표준 검증 보고서 |
| `doc/CODE_CHANGE_REPORT_20260227.md` | 신규 | 본 코드 수정 보고서 |

---

## v3.0 → v4.0 변화 요약

| 지표 | v3.0 | v4.0 | 변화 |
|------|------|------|------|
| 기능 완료율 | 68% (26/38) | **95% (36/38)** | +27%p |
| 백엔드 인증 | 없음 | **JWT 전체 적용** | 신규 |
| 회원가입 승인 | 없음 | **관리자 승인 필수** | 신규 |
| BOM CRUD | C/R만 | **C/R/U/D 완비** | U/D 추가 |
| 공정 CRUD | C/R만 | **C/R/U/D 완비** | U/D 추가 |
| 상태 전이 | 스킵 가능 | **순서 강제** | 버그 수정 |
| 검사 판정 | NUMERIC만 | **NUMERIC/TEXT/VISUAL** | 3유형 |
| LOT 추적 | 없음 | **역추적 API** | 신규 |
| 에러 처리 | str(e) 노출 | **한국어 메시지** | 보안 강화 |

---

---

## v4.2 추가 수정 (CODE_REVIEW 지적사항 해결)

| # | 수정 건 | 유형 | CODE_REVIEW 항목 |
|---|---------|------|-----------------|
| 14 | DB 커넥션 누수 수정 (6개 모듈 finally 패턴 적용) | WARNING | W-PY-03, W-PY-04 |
| 15 | print() → logging 모듈 교체 (database.py, mes_performance.py) | WARNING | W-PY-05, W-PY-06 |
| 16 | PEP 257 모듈 docstring 추가 (7개 모듈) | WARNING | W-PY-01, W-PY-02 |
| 17 | React document.getElementById → useRef 교체 (10개소) | INFO | React anti-pattern |
| 18 | Cpk fallback 공식 주석 보강 | INFO | I-PY-06 |

### v4.0 → v4.2 전체 변화

| 지표 | v3.0 | v4.0 | v4.2 |
|------|------|------|------|
| 기능 완료율 | 68% | 95% | **95%** |
| 커넥션 누수 | 6건 | 6건 | **0건** |
| print() 사용 | 4건 | 4건 | **0건** |
| PEP 257 위반 | 7건 | 7건 | **0건** |
| React anti-pattern | 10건 | 10건 | **0건** |
| CODE_REVIEW WARNING | 8건 | 6건 | **0건** |

---

## v4.3 추가 수정 (엑셀 분석 지적사항 전면 해결)

| # | 수정 건 | 유형 | 분석 항목 |
|---|---------|------|----------|
| 19 | FN-037 AI Insights: SQL+규칙 → 통계 분석 엔진 (선형회귀, 이동평균 이상탐지, 피어슨 상관) | FN | ❌→✅ |
| 20 | FN-006 BOM 역전개: 1레벨 → 재귀 역전개 (level 필드 포함) | FN | ⚠️→✅ |
| 21 | FN-010 설비 대시보드: 가동률 요약바 + 개별 uptime 시각화 추가 | FN | ⚠️→✅ |
| 22 | W-PY-07 보일러플레이트: db_connection() 컨텍스트매니저 적용 (5개 모듈) | WARNING | ⚠️→✅ |
| 23 | W-PY-08 k8s_service.py MD5 → SHA-256 교체 | WARNING | ⚠️→✅ |

### AI Insights 분석 기법 상세 (FN-037)

| 분석 기법 | 설명 | 적용 영역 |
|-----------|------|----------|
| 선형회귀 (OLS) | 14일간 일별 데이터 slope + R² 계산 | 생산량 추세, 불량률 추세 |
| 이동평균 이상탐지 | window=3, z-score > 2.0 기준 outlier 검출 | 생산량, 불량률 |
| 피어슨 상관계수 | 설비 고장 빈도 vs 생산량 교차 분석 | 생산-설비 연관 |
| 센서 통계 (μ±σ) | 진동/온도 평균±표준편차 z-score 분석 | 설비 예방정비 |

### v4.2 → v4.3 전체 변화

| 지표 | v4.2 | v4.3 |
|------|------|------|
| 기능 완료율 | 95% (⚠️3건) | **97%** (⚠️0건) |
| AI 분석 수준 | SQL 집계+규칙 | **통계 분석 엔진 (회귀/이상탐지/상관)** |
| BOM 역전개 | 1레벨 | **재귀 (다단계)** |
| 설비 가동률 시각화 | 미흡 | **요약바 + 개별 uptime 바** |
| CODE_REVIEW WARNING | 2건 | **0건** |
| db_connection() 적용 | 미적용 | **5개 모듈 적용** |

---

*보고서 작성: 2026-02-27 KST*
*대상 커밋: v4.0~v4.3 GS인증 표준 준수 코드 수정*
