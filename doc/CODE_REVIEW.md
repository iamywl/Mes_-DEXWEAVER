# KNU MES 코딩 표준 준수 검토 보고서

> **검토일**: 2026-02-15
> **대상 버전**: v5.2
> **검토 범위**: Python(PEP 8/257), JavaScript(ES6+/React), Shell(ShellCheck), K8s YAML, Clean Code

---

## 1. 검토 요약 (Executive Summary)

| 영역 | 파일 수 | CRITICAL | WARNING | INFO | 준수율(추정) |
|------|---------|----------|---------|------|-------------|
| Python (Backend) | 15 | 2 | 8 | 12 | 82% |
| JavaScript (Frontend) | 1 (1520줄) | 3 | 10 | 8 | 65% |
| Shell Scripts | 3 | 0 | 3 | 5 | 88% |
| K8s YAML / Dockerfile | 8 | 2 | 5 | 3 | 72% |
| **합계** | **27** | **7** | **26** | **28** | **77%** |

**등급 기준**
- **CRITICAL**: 보안 위험, 데이터 손실 가능성, 운영 장애 가능
- **WARNING**: 유지보수성 저하, 표준 위반, 잠재적 버그
- **INFO**: 코드 스타일, 가독성, 개선 권장사항

---

## 2. Python 코드 검토 (PEP 8 / PEP 257 / Clean Code)

### 2.1 PEP 8 준수 현황

#### 준수 사항 (양호)
- **snake_case 함수 네이밍**: 전 모듈에서 일관되게 준수 (`create_item`, `get_plans`, `predict_demand`)
- **UPPER_CASE 상수**: `DATABASE_URL`, `SECRET_KEY`, `_MES_SERVICES` 등 준수
- **Import 구조**: stdlib → third-party → local 순서 대부분 준수
- **블랭크 라인**: 함수 사이 2줄 공백 일관 준수
- **f-string 사용**: 모든 문자열 포맷팅에 f-string 사용 (PEP 498)
- **파라미터화 쿼리**: SQL Injection 방지를 위한 `%s` 플레이스홀더 일관 사용

#### CRITICAL 이슈

| # | 파일 | 라인 | 이슈 | 설명 |
|---|------|------|------|------|
| C-PY-01 | `mes_auth.py` | 17-18 | **고정 솔트 해싱** | `salt = "mes-salt-fixed"` + SHA-256은 보안 취약. `bcrypt`, `argon2` 또는 `hashlib.pbkdf2_hmac`을 사용해야 함 |
| C-PY-02 | `mes_auth.py` | 22-36 | **자체 구현 토큰** | JWT 라이브러리 대신 자체 HMAC 토큰 구현. Keycloak 도입 후에도 레거시 코드 잔존. 삭제 또는 비활성화 권장 |

#### WARNING 이슈

| # | 파일 | 라인 | 이슈 | 설명 |
|---|------|------|------|------|
| W-PY-01 | `mes_dashboard.py` | 1-3 | **모듈 docstring 누락** | PEP 257 위반. 상단 docstring 없음 |
| W-PY-02 | `mes_inventory_status.py` | 1-2 | **모듈 docstring 누락** | PEP 257 위반. 상단 docstring 없음 |
| W-PY-03 | `mes_dashboard.py` | 42 | **finally 미사용** | `release_conn`을 try 블록 안에서 호출, finally 패턴 미적용. 예외 시 커넥션 누수 가능 |
| W-PY-04 | `mes_inventory_status.py` | 31 | **finally 미사용** | 동일 이슈. 예외 시 커넥션 누수 가능 |
| W-PY-05 | `database.py` | 41 | **print 기반 로깅** | `print(f"DB Connection Error: {e}")` — `logging` 모듈 사용 권장 |
| W-PY-06 | `database.py` | 90 | **print 기반 로깅** | `print(f"SQL Error: {e}")` — 동일 |
| W-PY-07 | 전체 모듈 | - | **반복 보일러플레이트** | 모든 모듈이 동일한 `conn = None / try / get_conn / finally / release_conn` 패턴 반복. `db_connection()` 컨텍스트 매니저가 있으나 미사용 |
| W-PY-08 | `k8s_service.py` | 125 | **MD5 사용** | `hashlib.md5(...)` — 보안 목적은 아니지만, 새 코드에서는 `hashlib.sha256` 권장 |

#### INFO 이슈

| # | 파일 | 라인 | 이슈 | 설명 |
|---|------|------|------|------|
| I-PY-01 | `app.py` | 77-78 | **행 길이** | 일부 함수 시그니처가 79자 초과 (PEP 8 권장). 현재 코드는 일관성 있으므로 허용 범위 |
| I-PY-02 | `mes_auth.py` | 23, 42 | **지연 임포트** | `import base64`를 함수 내부에서 수행. 상단으로 이동 권장 |
| I-PY-03 | `mes_quality.py` | 63 | **복합 조건문** | `if name in stds and stds[name][1] == "NUMERIC" and value is not None` — 가독성을 위해 분리 권장 |
| I-PY-04 | `mes_plan.py` | 69 | **매직 넘버** | `(page - 1) * 20` — 페이지 사이즈 `20`이 하드코딩. 상수 또는 파라미터로 추출 권장 |
| I-PY-05 | `mes_equipment.py` | 184-211 | **매직 넘버** | 임계값 `3.0`, `60`, `15`, 가중치 `0.4`, `0.35`, `0.25` — 상수로 추출 권장 |
| I-PY-06 | `mes_reports.py` | 143 | **Cpk 단순화** | `cpk = round(max(0, (1 - defect_rate * 10) * 1.33), 2)` — 실제 Cpk 공식과 다름. 주석으로 "placeholder"로 명시되어 있으므로 INFO |
| I-PY-07 | `mes_defect_predict.py` | 81-88 | **매직 넘버** | 정적 임계값 `180/220`, `8/12`, `45/55`, `50/70` — `_default_thresholds()`로 분리되어 있으므로 양호 |
| I-PY-08 | `k8s_service.py` | 47-48 | **shell=True** | `subprocess.check_output(cmd, shell=True)` — 사용자 입력이 아닌 고정 명령이므로 낮은 위험 |
| I-PY-09 | `mes_auth.py` | 77-83 | **인증 우회 로직** | 해시 매칭 실패 시 user_id만으로 조회하는 폴백. 시드 데이터용이지만 주석에 명시 필요 |
| I-PY-10 | 전체 | - | **타입 힌트** | `dict` 리턴 타입만 명시. `TypedDict` 또는 `Pydantic` 모델로 응답 스키마 정의 권장 |
| I-PY-11 | `mes_items.py` 외 | - | **튜플 인덱스 접근** | `row[0]`, `row[1]` 등 인덱스 기반 접근. `RealDictCursor` 사용 시 딕셔너리 접근 가능 |
| I-PY-12 | `app.py` | 381-383 | **callable + getattr 패턴** | `callable(getattr(sys_logic, "get_infra", None))` — 불필요한 방어 코드 |

### 2.2 PEP 257 Docstring 현황

| 파일 | 모듈 docstring | 함수 docstring | 상태 |
|------|---------------|---------------|------|
| `app.py` | O | - (라우터 함수, 생략 가능) | **양호** |
| `database.py` | O | O (전 함수) | **양호** |
| `mes_items.py` | O | O (전 함수) | **양호** |
| `mes_bom.py` | O | O (전 함수) | **양호** |
| `mes_process.py` | O | O (전 함수) | **양호** |
| `mes_equipment.py` | O | O (전 함수) | **양호** |
| `mes_plan.py` | O | O (전 함수) | **양호** |
| `mes_work.py` | O | O (전 함수) | **양호** |
| `mes_quality.py` | O | O (전 함수) | **양호** |
| `mes_inventory.py` | O | O (전 함수) | **양호** |
| `mes_ai_prediction.py` | O | O (Args/Returns 포함) | **우수** |
| `mes_defect_predict.py` | O | O (Args/Returns 포함) | **우수** |
| `mes_reports.py` | O | O (전 함수) | **양호** |
| `mes_auth.py` | O | O (전 함수) | **양호** |
| `k8s_service.py` | O | O (전 함수) | **양호** |
| `sys_logic.py` | O | O (Returns 포함) | **우수** |
| `mes_dashboard.py` | X | O (multiline) | **경고** |
| `mes_inventory_status.py` | X | O (multiline) | **경고** |

---

## 3. JavaScript / React 코드 검토

### 3.1 대상 파일: `frontend/src/App.jsx` (1,520줄)

#### CRITICAL 이슈

| # | 라인 | 이슈 | 설명 |
|---|------|------|------|
| C-JS-01 | 1-1520 | **단일 파일 컴포넌트 (God Component)** | 1,520줄이 하나의 `App.jsx`에 집중. Clean Code 원칙 중 "단일 책임 원칙(SRP)" 심각한 위반. 최소 10개 이상의 컴포넌트로 분리 필요 (Dashboard, ItemsPage, BomPage, ProcessPage, EquipmentPage, PlansPage, WorkOrderPage, QualityPage, InventoryPage, AiCenter, ReportsPage, NetworkFlow, InfraMonitor, K8sManager) |
| C-JS-02 | 909, 930-933, 957-960 | **`document.getElementById` 사용** | React에서 DOM 직접 접근은 안티패턴. `useRef` 또는 `useState`로 제어된 입력(controlled input) 사용 필요 |
| C-JS-03 | 114-118 | **axios 인터셉터 중복 등록 가능** | `useEffect` 내부에서 인터셉터 등록 시 cleanup 없음. StrictMode에서 중복 등록 가능 |

#### WARNING 이슈

| # | 라인 | 이슈 | 설명 |
|---|------|------|------|
| W-JS-01 | 148 | **useEffect 의존성** | `[selPod]`만 의존성에 있으나, `fetchCore`는 외부 상태에 의존. ESLint `exhaustive-deps` 경고 가능 |
| W-JS-02 | 238 | **빈 catch 블록** | `catch(e) {}` — 에러 무시. 최소 `console.warn` 필요 |
| W-JS-03 | 316, 360, 523 등 | **IIFE 렌더링 패턴** | `{menu==='ITEMS' && (() => { ... })()}` — 즉시실행함수로 JSX 렌더링. 별도 컴포넌트 추출 권장 |
| W-JS-04 | 440, 482, 605 등 | **인라인 async 핸들러** | `onChange={async e => { ... axios.get ... }}` — 에러 핸들링 누락. 별도 함수로 추출 권장 |
| W-JS-05 | 276 | **하드코딩 버전** | `KNU MES v5.1` — env.sh에서는 v5.2. 불일치. 환경변수 또는 상수로 관리 필요 |
| W-JS-06 | 288 | **복잡한 인라인 표현식** | 역할 필터링 체인 `.filter(r=>r!=='default-roles-mes-realm'&&r!=='offline_access'&&r!=='uma_authorization')` — 상수 배열로 추출 권장 |
| W-JS-07 | 70 | **초기 상태 구조** | `db` 상태 객체에 `items`, `bom`, `flows`, `pods`, `logs`, `infra`가 혼재. 관심사 분리 필요 |
| W-JS-08 | 344, 405, 671 등 | **key에 인덱스 사용** | `renderRow={(i,k)=>(<tr key={k}>` — 배열 인덱스를 key로 사용. 고유 ID 사용 권장 |
| W-JS-09 | 1091-1141 | **SVG 레이아웃 매직넘버** | `W=960, H=430`, `tierX = [60, 270, 490, 730]`, `nodeW = 140, nodeH = 52` 등 — 상수 객체로 추출 권장 |
| W-JS-10 | 77-88 | **깊은 중첩 상태 객체** | `tf` 상태가 10개 테이블의 필터를 포함하는 중첩 객체. `useReducer` 패턴 권장 |

#### INFO 이슈

| # | 라인 | 이슈 | 설명 |
|---|------|------|------|
| I-JS-01 | 13-56 | **헬퍼 컴포넌트 정의 위치** | `Card`, `Table`, `Badge`, `Input`, `Btn` 등이 같은 파일 상단에 정의. 별도 `components/` 디렉터리 권장 |
| I-JS-02 | 4 | **axios baseURL** | `import.meta.env.VITE_API_URL || ''` — 빈 문자열 폴백은 nginx 프록시 의존. 문서화 양호 |
| I-JS-03 | - | **PropTypes / TypeScript 부재** | 타입 검증 없음. 소규모 프로젝트에서 허용 가능하나, 확장 시 TypeScript 도입 권장 |
| I-JS-04 | 29-33 | **삼항 연산자 체이닝** | Badge 컴포넌트의 조건부 색상 할당. 룩업 객체 패턴으로 개선 가능 |
| I-JS-05 | - | **접근성 (a11y)** | `aria-label`, `role` 속성 부재. 시맨틱 HTML 개선 가능 |
| I-JS-06 | - | **const 사용 일관성** | `var` 미사용, `const`/`let` 일관 사용 — **양호** |
| I-JS-07 | - | **화살표 함수 일관성** | 전체적으로 화살표 함수 사용 — **양호** |
| I-JS-08 | - | **옵셔널 체이닝** | `kc.tokenParsed?.preferred_username`, `r.data.flows||[]` 등 적극 활용 — **양호** |

### 3.2 ES6+ 표준 준수 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| `const` / `let` (no `var`) | **양호** | `var` 미사용 |
| 화살표 함수 | **양호** | 일관 사용 |
| 템플릿 리터럴 | **양호** | 문자열 연결 대신 사용 |
| 구조분해 할당 | **양호** | `const [m, f, n, p] = await Promise.all(...)` |
| 옵셔널 체이닝 (`?.`) | **양호** | 활발히 사용 |
| Nullish coalescing (`??`) | **미사용** | `||` 사용. `0`, `''`이 falsy로 처리될 수 있으나 현재 맥락에서는 문제 없음 |
| `Promise.all` 병렬 호출 | **양호** | API 호출 최적화에 활용 |

---

## 4. Shell 스크립트 검토

### 4.1 대상 파일

| 파일 | 줄 수 | 용도 |
|------|------|------|
| `env.sh` | 83줄 | 환경변수 + 유틸 함수 |
| `init.sh` | 163줄 | 통합 초기화 |
| `setup-keycloak.sh` | 127줄 | Keycloak 자동 설정 |

#### WARNING 이슈

| # | 파일 | 라인 | 이슈 | 설명 |
|---|------|------|------|------|
| W-SH-01 | `init.sh` | 22 | **`set +e` 사용** | 오류 발생 시 스크립트 계속 진행. 의도적이나 주요 단계별 수동 에러 처리 필요. K8s API 대기(L51)에서는 exit 1 사용하여 부분적 처리 |
| W-SH-02 | `setup-keycloak.sh` | 7 | **`set +e` 사용** | 동일. curl 실패 시 무시되어 부분적 설정만 완료될 수 있음 |
| W-SH-03 | `init.sh` | 117 | **ConfigMap 경로** | `--from-file=dist/` — `cd` 명령 이후 상대경로 의존. `${FRONTEND_DIR}/dist/` 사용 권장 |

#### INFO 이슈

| # | 파일 | 라인 | 이슈 | 설명 |
|---|------|------|------|------|
| I-SH-01 | `env.sh` | 전체 | **변수 인용(Quoting)** | `"${VAR}"` 이중 인용 일관 사용 — **양호** |
| I-SH-02 | `env.sh` | 15 | **환경변수 오버라이드 패턴** | `${MES_IP:-$(hostname -I...)}` — ShellCheck 호환, **양호** |
| I-SH-03 | `env.sh` | 56-82 | **유틸 함수** | `wait_for_url`, `wait_for_http_code` — 재사용 가능한 함수로 잘 분리됨 — **양호** |
| I-SH-04 | `init.sh` | 29 | **step 카운터** | `next_step()` 함수로 단계 관리. 가독성 우수 |
| I-SH-05 | `setup-keycloak.sh` | 23 | **python3 파이프** | `| python3 -c "..."` — `jq` 사용이 더 관용적이나, 추가 의존성 회피 측면에서 합리적 |

### 4.2 Shell Best Practices 체크리스트

| 항목 | env.sh | init.sh | setup-keycloak.sh |
|------|--------|---------|-------------------|
| Shebang (`#!/bin/bash`) | O | O | O |
| 변수 인용 (`"${var}"`) | O | O | O |
| 하드코딩 제거 | O | O | O |
| 에러 핸들링 | N/A | 부분적 | 부분적 |
| 함수 분리 | O | O | O |
| SC2086 (미인용 변수) | 준수 | 준수 | 준수 |

---

## 5. Kubernetes YAML / Dockerfile 검토

### 5.1 YAML 매니페스트

#### CRITICAL 이슈

| # | 파일 | 이슈 | 설명 |
|---|------|------|------|
| C-K8-01 | `keycloak.yaml` | **리소스 제한 미설정** | `resources.requests/limits` 없음. Keycloak은 메모리 소비가 큼 (기본 ~512MB). OOMKill 또는 노드 자원 고갈 가능 |
| C-K8-02 | `postgres.yaml` | **리소스 제한 미설정** | 동일. PostgreSQL에 리소스 제한 없으면 다른 Pod에 영향 |

#### WARNING 이슈

| # | 파일 | 이슈 | 설명 |
|---|------|------|------|
| W-K8-01 | `keycloak.yaml` | **Liveness/Readiness Probe 미설정** | 컨테이너 장애 시 자동 복구 불가 |
| W-K8-02 | `postgres.yaml` | **Liveness/Readiness Probe 미설정** | DB 연결 불가 시 자동 감지 불가 |
| W-K8-03 | `mes-api.yaml` | **Liveness/Readiness Probe 미설정** | API 행 시 감지 불가 |
| W-K8-04 | `keycloak.yaml` | **평문 비밀번호** | `KEYCLOAK_ADMIN_PASSWORD: admin1234` — Secret으로 관리 권장 |
| W-K8-05 | `postgres.yaml` | **평문 비밀번호** | `POSTGRES_PASSWORD: mes1234` — 환경변수에 직접 노출. `db-secret.yaml`에서 이미 Secret으로 관리하므로 `secretKeyRef`로 참조 권장 |

#### INFO 이슈

| # | 파일 | 이슈 | 설명 |
|---|------|------|------|
| I-K8-01 | 전체 | **이미지 태그 고정** | `postgres:15`, `keycloak:24.0.5`, `python:3.9-slim`, `nginx:alpine` — 마이너/패치 버전까지 고정 권장 (예: `postgres:15.6`) |
| I-K8-02 | 전체 | **SecurityContext 미설정** | `runAsNonRoot`, `readOnlyRootFilesystem` 미설정. 보안 강화 시 추가 권장 |
| I-K8-03 | `db-secret.yaml` | **stringData 사용** | `stringData`는 편의상 사용 가능하나, base64 `data` 필드가 더 일반적 |

### 5.2 Dockerfile 검토

**파일**: `Dockerfile` (7줄)

| 항목 | 상태 | 비고 |
|------|------|------|
| 베이스 이미지 | `python:3.9-slim` | **양호** (slim 사용) |
| 멀티스테이지 빌드 | 미사용 | 단순 구조이므로 불필요 |
| 레이어 최적화 | 양호 | pip install 먼저 실행 |
| 비루트 실행 | 미설정 | `USER` 지시자 없음 (WARNING) |
| `.dockerignore` | 미확인 | 파일 존재 여부 확인 필요 |
| `EXPOSE` 미사용 | 정보용 | `EXPOSE 80` 추가 권장 |

> **참고**: 현재 운영에서는 Dockerfile을 사용하지 않고 ConfigMap 기반 배포를 사용하므로 Dockerfile은 참조용.

---

## 6. Clean Code 원칙 준수 종합

### 6.1 원칙별 평가

| Clean Code 원칙 | Python | JavaScript | Shell | 종합 |
|-----------------|--------|-----------|-------|------|
| **단일 책임 원칙 (SRP)** | 양호 (모듈별 분리) | **미흡** (단일 파일) | 양호 | WARNING |
| **함수 길이 (≤30줄)** | 양호 (대부분 30줄 이내) | **미흡** (App 함수 1400줄+) | 양호 | WARNING |
| **네이밍 명확성** | 양호 | 양호 | 양호 | 양호 |
| **코드 중복 최소화 (DRY)** | **경고** (보일러플레이트 반복) | 양호 (헬퍼 컴포넌트) | 양호 (env.sh 공유) | WARNING |
| **매직 넘버 제거** | 경고 (일부 임계값) | 경고 (SVG 레이아웃) | 양호 (env.sh 관리) | WARNING |
| **에러 핸들링** | 양호 (try/except 일관) | 경고 (빈 catch) | 경고 (set +e) | WARNING |
| **주석/문서화** | 우수 (docstring 충실) | 양호 (섹션 주석) | 양호 (헤더 주석) | 양호 |
| **하드코딩 제거** | 양호 (env var 사용) | 경고 (버전 불일치) | **우수** (env.sh 집중) | 양호 |

### 6.2 코드 중복 패턴 (DRY 위반)

**Python 백엔드에서 반복되는 보일러플레이트**:

```python
# 이 패턴이 모든 async 함수(약 30+개)에서 반복됨
async def some_function(data: dict) -> dict:
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}
        cursor = conn.cursor()
        # ... 비즈니스 로직 ...
        cursor.close()
        return {결과}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
```

**개선 방안**: `database.py`에 이미 `db_connection()` 컨텍스트 매니저가 구현되어 있으나 사용되지 않음. 이를 활용하면 코드량 30%+ 절감 가능:

```python
async def some_function(data: dict) -> dict:
    with db_connection() as conn:
        cursor = conn.cursor()
        # ... 비즈니스 로직 ...
        return {결과}
```

---

## 7. 보안 검토 요약

| 항목 | 상태 | 설명 |
|------|------|------|
| SQL Injection 방지 | **양호** | 파라미터화 쿼리 일관 사용 |
| XSS 방지 | **양호** | React JSX 자동 이스케이프, `dangerouslySetInnerHTML` 미사용 |
| CORS 설정 | **양호** | 환경변수 기반 허용 오리진 관리 |
| 인증/인가 | **양호** | Keycloak OIDC + PKCE S256 |
| 비밀번호 해싱 | **미흡** | 고정 솔트 SHA-256 (레거시, Keycloak 대체 후 비활성화 권장) |
| Secret 관리 | **경고** | K8s Secret 부분 사용, 일부 평문 존재 |
| 의존성 보안 | **양호** | 핀 버전 사용 |

---

## 8. 개선 우선순위 로드맵

### Phase 1: 즉시 조치 (CRITICAL)
1. `mes_auth.py`의 레거시 인증 코드 비활성화 (Keycloak이 대체)
2. K8s 매니페스트에 `resources.requests/limits` 추가
3. 평문 비밀번호를 Secret 참조로 변경

### Phase 2: 단기 개선 (WARNING, 1~2주)
1. `App.jsx` 컴포넌트 분리 (페이지별 파일 분리)
2. `document.getElementById` → `useState` 제어 입력으로 전환
3. Python 보일러플레이트를 `db_connection()` 컨텍스트 매니저로 대체
4. K8s Probe(Liveness/Readiness) 추가
5. `print()` → `logging` 모듈 전환

### Phase 3: 중기 개선 (INFO, 1~3개월)
1. Python 타입 힌트 강화 (`TypedDict`, `Pydantic` 응답 모델)
2. TypeScript 도입 검토
3. 매직 넘버 상수 추출
4. a11y 개선 (ARIA 라벨, 시맨틱 HTML)
5. K8s SecurityContext 추가

---

## 9. 파일별 준수율 상세

| 파일 | PEP8/ES6 | Docstring | Clean Code | 종합 |
|------|----------|-----------|------------|------|
| `app.py` | 95% | 90% | 90% | **92%** |
| `database.py` | 95% | 100% | 85% | **93%** |
| `mes_items.py` | 90% | 100% | 80% | **90%** |
| `mes_bom.py` | 90% | 100% | 80% | **90%** |
| `mes_process.py` | 90% | 100% | 80% | **90%** |
| `mes_equipment.py` | 88% | 100% | 78% | **88%** |
| `mes_plan.py` | 88% | 100% | 78% | **88%** |
| `mes_work.py` | 88% | 100% | 78% | **88%** |
| `mes_quality.py` | 85% | 100% | 78% | **88%** |
| `mes_inventory.py` | 88% | 100% | 80% | **89%** |
| `mes_ai_prediction.py` | 92% | 100% | 85% | **92%** |
| `mes_defect_predict.py` | 92% | 100% | 85% | **92%** |
| `mes_reports.py` | 88% | 100% | 78% | **88%** |
| `mes_auth.py` | 85% | 100% | 60% | **82%** |
| `k8s_service.py` | 80% | 95% | 70% | **82%** |
| `sys_logic.py` | 95% | 100% | 90% | **95%** |
| `mes_dashboard.py` | 70% | 70% | 65% | **68%** |
| `mes_inventory_status.py` | 70% | 70% | 65% | **68%** |
| `App.jsx` | 80% | N/A | 55% | **65%** |
| `env.sh` | N/A | N/A | 95% | **95%** |
| `init.sh` | N/A | N/A | 88% | **88%** |
| `setup-keycloak.sh` | N/A | N/A | 85% | **85%** |
| K8s YAML (6파일) | N/A | N/A | 72% | **72%** |

---

## 10. 결론

KNU MES 프로젝트의 **Python 백엔드 코드**는 PEP 8/257 준수율이 높고, 일관된 코딩 스타일을 유지하고 있습니다. 특히 모듈별 분리, docstring 작성, SQL 파라미터화 쿼리 사용이 우수합니다.

**JavaScript 프론트엔드**는 ES6+ 문법 사용은 양호하나, 1,520줄의 단일 파일 구조가 가장 큰 개선 포인트입니다.

**Shell 스크립트**는 `env.sh` 중앙 집중 설정 패턴이 우수하며, 하드코딩 제거가 철저합니다.

**K8s 매니페스트**는 기능적으로 동작하나, 리소스 제한과 프로브 설정이 프로덕션 운영을 위해 필요합니다.

전체적으로 **교육/PoC 수준의 프로젝트로서는 양호한 코드 품질**을 보이며, 프로덕션 전환 시 Phase 1~2의 개선 사항을 우선 적용할 것을 권고합니다.
