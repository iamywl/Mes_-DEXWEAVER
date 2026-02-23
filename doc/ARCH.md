# KNU MES 시스템 — 아키텍처 문서

> Kubernetes 기반 클라우드 네이티브 MES (Manufacturing Execution System) 아키텍처

---

## 1. 시스템 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                     VM (Ubuntu aarch64)                          │
│                  192.168.64.5 / c1master1                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Kubernetes Cluster (kubeadm v1.30+)          │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │
│  │  │ mes-frontend │  │   mes-api     │  │    postgres      │ │  │
│  │  │ nginx:alpine │  │ python:3.9   │  │ PostgreSQL 15    │ │  │
│  │  │  :80 (30173) │  │  :80 (30461) │  │  :5432           │ │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘ │  │
│  │         │                 │                  │             │  │
│  │         │   /api/* proxy  │   DATABASE_URL   │             │  │
│  │         │────────────────>│─────────────────>│             │  │
│  │         │                 │                  │             │  │
│  │  ┌──────┴──────────────────┴───────────────────┐          │  │
│  │  │           Cilium eBPF CNI + Hubble          │          │  │
│  │  └─────────────────────────────────────────────┘          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                    │
      :30173 (Web)        :30461 (API)      :30080 (Auth)
           │                    │              │
    ┌──────┴────────────────────┴──────────────┴──┐
    │              사용자 브라우저                   │
    │   http://192.168.64.5:30173                  │
    │   Keycloak OIDC 로그인 → JWT Bearer Token    │
    └──────────────────────────────────────────────┘
```

---

## 2. 기술 스택

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **인프라** | Kubernetes (kubeadm) | v1.28+ | 컨테이너 오케스트레이션 |
| **네트워크** | Cilium eBPF + Hubble | 최신 | CNI, 네트워크 정책, 플로우 모니터링 |
| **인증** | Keycloak (OIDC/PKCE) | 24.0.5 | SSO 인증 서버 |
| **DB** | PostgreSQL | 15 | 관계형 데이터 저장소 (19개 테이블) |
| **백엔드** | Python FastAPI | 0.109 | REST API 서버 (37개 엔드포인트) |
| **프론트엔드** | React 19 + Vite + Tailwind CSS 4 | 최신 | SPA 웹 UI (14개 메뉴) |
| **프론트엔드 서빙** | nginx:alpine | 최신 | 정적 파일 서빙 + API 리버스 프록시 |
| **CI/CD** | Jenkins (Jenkinsfile) | - | 린트 → 테스트 → 빌드 → 배포 파이프라인 |
| **배포 방식** | ConfigMap 기반 | - | Docker 빌드 없이 코드 배포 |

---

## 3. Kubernetes 리소스 구성

### 3.1 Pod / Deployment

| Deployment | Image | Port | NodePort | 역할 |
|------------|-------|------|----------|------|
| `mes-frontend` | `nginx:alpine` | 80 | **30173** | React 빌드 파일 서빙, API 리버스 프록시 |
| `mes-api` | `python:3.9-slim` | 80 | **30461** | FastAPI REST API 서버 |
| `postgres` | `postgres:15` | 5432 | - (ClusterIP) | PostgreSQL 데이터베이스 |
| `keycloak` | `keycloak` | 8080 | **30080** | Keycloak OIDC 인증 서버 |

### 3.2 ConfigMap

| ConfigMap | 내용 | 용도 |
|-----------|------|------|
| `api-code` | `app.py` + `api_modules/*.py` (27개 파일) | 백엔드 소스 코드를 Pod에 마운트 |
| `frontend-build` | `dist/` 디렉토리 (빌드 결과물) | React 빌드 파일을 nginx에 마운트 |
| `nginx-config` | `default.conf` | nginx 설정 (프록시 룰 포함) |

### 3.3 Secret / Storage

| 리소스 | 내용 |
|--------|------|
| `db-credentials` (Secret) | `DATABASE_URL=postgresql://postgres:mes1234@postgres:5432/mes_db` |
| `postgres-pv` (PersistentVolume) | 1Gi, hostPath `/mnt/data` |
| `postgres-pvc` (PersistentVolumeClaim) | postgres-pv에 바인딩 |
| `pip-cache` (hostPath Volume) | `/mnt/pip-cache` — API Pod의 pip 패키지 캐시 (재기동 시 다운로드 생략) |

### 3.4 배포 방식: ConfigMap 기반 (Docker 빌드 불필요)

```
소스 코드 수정
    │
    ├─ 백엔드: kubectl create configmap api-code --from-file=...
    │          kubectl rollout restart deployment mes-api
    │
    └─ 프론트엔드: npm run build
                   kubectl create configmap frontend-build --from-file=dist/
                   kubectl rollout restart deployment mes-frontend
```

기존 Docker 이미지를 수정하지 않고, ConfigMap만 갱신하여 코드를 배포합니다.
- `api-code` ConfigMap → `/mnt` 에 마운트 → 컨테이너 시작 시 `/app/`으로 복사 → pip install (캐시 활용) → 실행
- `frontend-build` ConfigMap → `/usr/share/nginx/html` 에 마운트 → nginx가 즉시 서빙
- `pip-cache` hostPath (`/mnt/pip-cache`) → `/pip-cache` 에 마운트 → pip 패키지 캐시 재사용

---

## 4. 백엔드 아키텍처

### 4.1 모듈 구조

```
app.py                          ← FastAPI 메인 라우터 (37개 엔드포인트)
│
├── api_modules/
│   ├── database.py             ← DB 연결 풀 (ThreadedConnectionPool)
│   │
│   ├── mes_auth.py             ← FN-001~003: 인증/권한
│   ├── mes_items.py            ← FN-004~007: 품목 관리
│   ├── mes_bom.py              ← FN-008~009: BOM 관리
│   ├── mes_process.py          ← FN-010~012: 공정/라우팅
│   ├── mes_equipment.py        ← FN-013~014, 032~034: 설비
│   ├── mes_plan.py             ← FN-015~017: 생산계획
│   ├── mes_work.py             ← FN-020~024: 작업지시/실적
│   ├── mes_quality.py          ← FN-025~027: 품질관리
│   ├── mes_inventory.py        ← FN-029~031: 재고관리
│   ├── mes_reports.py          ← FN-035~037: 리포트
│   │
│   ├── mes_ai_prediction.py    ← FN-018~019: AI 수요예측
│   ├── mes_defect_predict.py   ← FN-028: AI 불량예측
│   │
│   ├── k8s_service.py          ← Hubble API, Pod/서비스맵 조회
│   ├── sys_logic.py            ← 인프라 상태 (CPU/메모리)
│   │
│   ├── mes_dashboard.py        ← 대시보드 데이터
│   ├── mes_service.py          ← 서비스 유틸리티
│   ├── mes_master.py           ← 기준정보 유틸리티
│   ├── mes_production.py       ← 생산 유틸리티
│   ├── mes_execution.py        ← 실행 추적
│   ├── mes_work_order.py       ← 작업지시 유틸리티
│   ├── mes_inventory_status.py ← 재고 상태
│   ├── mes_inventory_movement.py ← 재고 이동
│   ├── mes_material_receipt.py ← 자재 입고
│   ├── mes_logistics.py        ← 물류 유틸리티
│   └── mes_logic.py            ← 비즈니스 로직
```

### 4.2 DB 연결 방식

```python
# database.py — 커넥션 풀링
ThreadedConnectionPool(minconn=2, maxconn=10, dsn=DATABASE_URL)

# 사용 패턴
conn = get_conn()       # 풀에서 커넥션 획득
try:
    cursor = conn.cursor()
    cursor.execute(SQL, params)
    ...
finally:
    release_conn(conn)  # 풀에 반환
```

- `get_conn()` / `release_conn()`: 직접 커넥션 관리
- `query_db(sql, params)`: RealDictCursor로 간편 쿼리
- `db_connection()`: 컨텍스트 매니저 (with문)

### 4.3 API 엔드포인트 목록 (37개)

| 영역 | Method | URL | 기능 코드 |
|------|--------|-----|-----------|
| 인증 | POST | `/api/auth/login` | FN-001 |
| 인증 | POST | `/api/auth/register` | FN-002 |
| 인증 | GET | `/api/auth/permissions/{user_id}` | FN-003 |
| 품목 | POST | `/api/items` | FN-004 |
| 품목 | GET | `/api/items` | FN-005 |
| 품목 | GET | `/api/items/{item_code}` | FN-006 |
| 품목 | PUT | `/api/items/{item_code}` | FN-007 |
| BOM | POST | `/api/bom` | FN-008 |
| BOM | GET | `/api/bom` | FN-008 |
| BOM | GET | `/api/bom/summary` | FN-008 |
| BOM | GET | `/api/bom/where-used/{item_code}` | FN-009 |
| BOM | GET | `/api/bom/explode/{item_code}` | FN-009 |
| 공정 | GET | `/api/processes` | FN-010 |
| 공정 | POST | `/api/processes` | FN-010 |
| 라우팅 | GET | `/api/routings` | FN-011 |
| 라우팅 | POST | `/api/routings` | FN-011 |
| 라우팅 | GET | `/api/routings/{item_code}` | FN-012 |
| 설비 | POST | `/api/equipments` | FN-013 |
| 설비 | GET | `/api/equipments` | FN-014 |
| 설비 | PUT | `/api/equipments/{equip_code}/status` | FN-032 |
| 설비 | GET | `/api/equipments/status` | FN-033 |
| 계획 | POST | `/api/plans` | FN-015 |
| 계획 | GET | `/api/plans` | FN-016 |
| 계획 | GET | `/api/plans/{plan_id}` | FN-017 |
| AI | POST | `/api/ai/demand-forecast` | FN-018 |
| AI | GET | `/api/ai/demand-prediction/{item_code}` | FN-018 |
| AI | POST | `/api/ai/schedule-optimize` | FN-019 |
| 작업 | POST | `/api/work-orders` | FN-020 |
| 작업 | GET | `/api/work-orders` | FN-021 |
| 작업 | GET | `/api/work-orders/{wo_id}` | FN-022 |
| 실적 | POST | `/api/work-results` | FN-023 |
| 대시보드 | GET | `/api/dashboard/production` | FN-024 |
| 품질 | POST | `/api/quality/standards` | FN-025 |
| 품질 | POST | `/api/quality/inspections` | FN-026 |
| 품질 | GET | `/api/quality/defects` | FN-027 |
| AI | POST | `/api/ai/defect-predict` | FN-028 |
| AI | POST | `/api/ai/defect-prediction` | FN-028 |
| 재고 | POST | `/api/inventory/in` | FN-029 |
| 재고 | POST | `/api/inventory/out` | FN-030 |
| 재고 | GET | `/api/inventory` | FN-031 |
| AI | POST | `/api/ai/failure-predict` | FN-034 |
| 리포트 | GET | `/api/reports/production` | FN-035 |
| 리포트 | GET | `/api/reports/quality` | FN-036 |
| AI | POST | `/api/ai/insights` | FN-037 |
| 인프라 | GET | `/api/infra/status` | - |
| K8s | GET | `/api/k8s/pods` | - |
| K8s | GET | `/api/k8s/logs/{name}` | - |
| 네트워크 | GET | `/api/network/flows` | - |
| 네트워크 | GET | `/api/network/topology` | - |
| 네트워크 | GET | `/api/network/hubble-flows` | - |
| 네트워크 | GET | `/api/network/service-map` | - |

---

## 5. 프론트엔드 아키텍처

### 5.1 기술 구성

| 항목 | 기술 |
|------|------|
| 프레임워크 | React 19 |
| 번들러 | Vite (rolldown-vite 7.2.5) |
| CSS | Tailwind CSS 4 |
| HTTP 클라이언트 | Axios |
| 서빙 | nginx:alpine (K8s ConfigMap 마운트) |

### 5.2 단일 페이지 구조

전체 UI가 `App.jsx` 하나에 구현되어 있습니다 (약 1,200라인).

```
App.jsx
├── 공통 컴포넌트
│   ├── Card          — 통계 카드
│   ├── Table         — 데이터 테이블
│   ├── Badge         — 상태 뱃지
│   ├── Input         — 입력 필드
│   ├── Btn           — 버튼
│   ├── FilterBar     — 필터 바 컨테이너
│   ├── FilterSelect  — 드롭다운 필터
│   ├── FilterSearch  — 텍스트 검색
│   └── FilterCount   — 필터 카운트
│
├── 상태 관리
│   ├── menu          — 현재 메뉴 (14개 중 1개)
│   ├── db            — 코어 데이터 (items, flows, pods, infra)
│   ├── extra         — 페이지별 데이터
│   ├── tf            — 테이블 필터 상태
│   ├── bomTab        — BOM 서브탭 (list/explode/where)
│   ├── procTab       — Process 서브탭 (master/routing/summary)
│   ├── hubbleFilter  — 네트워크 필터 상태
│   └── serviceMap    — Hubble 서비스맵 데이터
│
└── 14개 메뉴 렌더링
    ├── DASHBOARD       — 요약 카드 4개
    ├── ITEMS           — 품목 테이블 + 필터
    ├── BOM             — 3탭 (목록/전개/역전개)
    ├── PROCESS         — 3탭 (마스터/라우팅뷰어/요약)
    ├── EQUIPMENT       — 설비 카드 그리드 + 필터
    ├── PLANS           — 생산계획 테이블 + 진행률
    ├── WORK_ORDER      — 작업지시 테이블 + 필터
    ├── QUALITY         — 불량 요약 + 트렌드 차트
    ├── INVENTORY       — 재고 테이블 + 필터
    ├── AI_CENTER       — 수요/불량/고장 예측 3칸
    ├── REPORTS         — 생산/품질 리포트 + AI 인사이트
    ├── NETWORK_FLOW    — Hubble 서비스맵 SVG + 플로우 테이블
    ├── INFRA_MONITOR   — CPU/메모리 게이지
    └── K8S_MANAGER     — Pod 목록 + 로그 뷰어
```

### 5.3 데이터 흐름

```
┌──────────┐   axios   ┌───────────────┐   proxy   ┌──────────┐
│ App.jsx  │──────────>│ nginx (:80)   │─────────>│ mes-api  │
│ React    │<──────────│ /api/* → :80  │<─────────│ FastAPI  │
└──────────┘   JSON    └───────────────┘          └──────────┘
     │
     ├── fetchCore(): 5초 간격 자동 새로고침 (대시보드, 인프라, Pod)
     ├── useEffect[menu]: 메뉴 변경 시 해당 데이터 로드
     └── useEffect[NETWORK_FLOW]: 5초 간격 Hubble 데이터 새로고침
```

### 5.4 nginx 프록시 설정

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;    # ConfigMap: frontend-build
        try_files $uri $uri/ /index.html;  # SPA 라우팅
    }

    location /api/ {
        proxy_pass http://mes-api-service:80;  # K8s Service
    }
}
```

프론트엔드에서 `/api/*` 요청은 nginx가 백엔드 서비스로 프록시합니다.
이를 통해 CORS 이슈 없이 같은 도메인에서 API를 호출할 수 있습니다.

---

## 6. 데이터베이스 스키마

### 6.1 ERD 개요

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  users   │     │  items   │────>│   bom    │ (parent/child)
└──────────┘     └────┬─────┘     └──────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
    ┌─────┴────┐ ┌────┴─────┐ ┌──┴───────────┐
    │processes │ │routings  │ │prod_plans    │
    └────┬─────┘ └──────────┘ └──────┬───────┘
         │                           │
    ┌────┴─────┐              ┌──────┴───────┐
    │equipments│              │ work_orders  │
    └──────────┘              └──────┬───────┘
                                     │
                              ┌──────┴───────┐
                              │ work_results │
                              └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  inventory   │  │ inspections  │  │  shipments   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 6.2 테이블 목록 (19개)

| 테이블 | PK | 설명 | 주요 컬럼 |
|--------|-----|------|-----------|
| `users` | user_id | 사용자 | password, name, role |
| `user_permissions` | user_id+menu | 권한 | can_read, can_write |
| `items` | item_code | 품목 | name, category, unit, spec, safety_stock |
| `bom` | bom_id | BOM | parent_item, child_item, qty_per_unit, loss_rate |
| `processes` | process_code | 공정 | name, std_time_min, equip_code |
| `routings` | routing_id | 라우팅 | item_code, seq, process_code, cycle_time |
| `equipments` | equip_code | 설비 | name, capacity_per_hour, status |
| `equip_status_log` | log_id | 설비 이력 | equip_code, status, reason, changed_at |
| `production_plans` | plan_id | 생산계획 | item_code, plan_qty, due_date, priority, status |
| `work_orders` | wo_id | 작업지시 | plan_id, item_code, work_date, equip_code |
| `work_results` | result_id | 작업실적 | wo_id, good_qty, defect_qty, worker_id |
| `quality_standards` | standard_id | 품질 기준 | item_code, check_name, min/max/std |
| `inspections` | inspection_id | 검사 | item_code, lot_no, judgment |
| `inspection_details` | detail_id | 검사 상세 | measured_value, judgment |
| `defect_codes` | defect_code | 불량 코드 | name, description |
| `inventory` | inv_id | 재고 | item_code, lot_no, qty, warehouse |
| `inventory_transactions` | tx_id | 재고 트랜잭션 | tx_type, qty, slip_no |
| `shipments` | shipment_id | 출하 | item_code, ship_date, qty |
| `defect_history` | defect_id | 불량 이력 | temperature, pressure, speed, humidity |
| `equip_sensors` | sensor_id | 센서 데이터 | vibration, temperature, current_amp |
| `ai_forecasts` | forecast_id | AI 예측 결과 | model_type, result_json |

### 6.3 시드 데이터

| 데이터 | 건수 |
|--------|------|
| 사용자 | 10명 (admin 1, manager 2, worker 5, viewer 2) |
| 품목 | 20건 (RAW 8, SEMI 6, PRODUCT 6) |
| BOM | 20건 |
| 공정 | 10건 |
| 라우팅 | 12개 품목 (36 공정 단계) |
| 설비 | 10대 |
| 생산계획 | 20건 |
| 작업지시 | 40건 |
| 작업실적 | 60건 |
| 재고 | 30건 |
| 출하 이력 | 24건 (12개월 x 2품목) |
| 불량 이력 | 8건 |

---

## 7. AI 모듈

### 7.1 수요 예측 (Demand Prediction)

- **알고리즘**: 선형 회귀 (Linear Regression)
- **데이터 소스**: `shipments` 테이블에서 월별 출하 집계
- **입력**: 품목 코드 (예: ITEM003)
- **출력**: 향후 3개월 예측 수량 + 신뢰도

### 7.2 불량 예측 (Defect Prediction)

- **알고리즘**: 통계 기반 임계값 비교
- **데이터 소스**: `defect_history` 테이블에서 정상 범위 통계
- **입력**: temperature, pressure, speed, humidity
- **출력**: 불량 확률(%), 주요 원인, 권장 조치

### 7.3 고장 예측 (Failure Prediction)

- **알고리즘**: 센서 데이터 기반 이상 감지
- **데이터 소스**: `equip_sensors` 테이블
- **입력**: 설비 코드, 진동/온도/전류 센서 값
- **출력**: 고장 확률(%), 잔여 수명(시간), 권장 조치

---

## 8. 네트워크 모니터링 (Hubble)

### 8.1 구성

```
Cilium Agent (DaemonSet)
    │
    ├── eBPF 프로그램 → 커널 레벨 패킷 관찰
    │
    └── Hubble Relay (Deployment)
            │
            └── gRPC API → k8s_service.py → /api/network/*
```

### 8.2 서비스맵

- **계층형 레이아웃**: External → Ingress → Application → Backend/Infra
- **고정 Y좌표**: 서비스 교차 최소화를 위한 수동 배치
- **포트 오프셋**: 같은 노드에서 여러 연결이 겹치지 않도록 분산
- **SVG 렌더링**: 브라우저 내 실시간 렌더링 (5초 새로고침)

### 8.3 표시 정보

- 서비스 노드: 이름, 네임스페이스, 프로토콜, 포트, 트래픽 카운트
- 연결선: 프로토콜, 포트, 전달/차단 수, 애니메이션
- 플로우 테이블: 타임스탬프, 소스/목적지, 판정, 프로토콜, L7 정보

---

## 9. 프로젝트 디렉터리 구조

```
MES_PROJECT/
├── app.py                        # FastAPI 메인 라우터 (37 endpoints)
├── requirements.txt              # Python 의존성
├── Dockerfile                    # 백엔드 Docker 이미지
├── docker-compose.yml            # 로컬 개발용 (PostgreSQL)
├── Jenkinsfile                   # CI/CD 파이프라인 (Jenkins)
├── init.sh                      # VM 부팅 후 원클릭 시작 (병렬 배포 + 프로그레스 바)
├── env.sh                        # 환경 변수 중앙 관리 + 프로그레스 바 유틸
├── setup-keycloak.sh             # Keycloak Realm/Client/사용자 자동 설정
│
├── api_modules/                  # 백엔드 비즈니스 로직 (27개 모듈)
│   ├── database.py               #   커넥션 풀
│   ├── mes_auth.py               #   인증
│   ├── mes_items.py              #   품목
│   ├── mes_bom.py                #   BOM
│   ├── mes_process.py            #   공정/라우팅
│   ├── mes_equipment.py          #   설비
│   ├── mes_plan.py               #   생산계획
│   ├── mes_work.py               #   작업지시/실적
│   ├── mes_quality.py            #   품질
│   ├── mes_inventory.py          #   재고
│   ├── mes_reports.py            #   리포트
│   ├── mes_ai_prediction.py      #   AI 수요예측
│   ├── mes_defect_predict.py     #   AI 불량예측
│   ├── k8s_service.py            #   K8s/Hubble API
│   ├── sys_logic.py              #   인프라 상태
│   └── ...                       #   기타 유틸리티 모듈
│
├── frontend/                     # React 프론트엔드
│   ├── src/
│   │   └── App.jsx               #   14메뉴 SPA (~1200 lines)
│   ├── package.json              #   npm 의존성
│   ├── vite.config.js            #   Vite 빌드 설정
│   ├── nginx.conf                #   프로덕션 nginx 설정
│   ├── .env.development          #   개발 환경변수
│   ├── .env.production           #   프로덕션 환경변수
│   └── dist/                     #   빌드 결과물
│
├── db/
│   └── init.sql                  # DB 스키마 + 시드 데이터 (19테이블, 500+건)
│
├── infra/                        # Kubernetes 매니페스트 (init.sh에서 참조)
│   ├── postgres-pv.yaml          #   PV + PVC
│   ├── db-secret.yaml            #   DB 접속 Secret
│   ├── postgres.yaml             #   PostgreSQL Deployment + Service
│   ├── keycloak.yaml             #   Keycloak Deployment + Service
│   ├── mes-api.yaml              #   FastAPI Deployment + Service
│   ├── nginx-config.yaml         #   nginx ConfigMap
│   └── mes-frontend.yaml         #   Frontend Deployment + Service
│
├── doc/                          # 문서
│   ├── HOWTOSTART.md             #   시작 가이드
│   ├── ARCH.md                   #   아키텍처 문서 (이 파일)
│   ├── HANDOVER.md               #   인수인계 문서
│   ├── HOWTOCONTRIBUTE.md        #   기여 가이드
│   ├── CODE_REVIEW.md            #   코드 품질 검토서
│   ├── CICD_REVIEW.md            #   CI/CD 파이프라인 검토서
│   ├── USER_MANUAL.md            #   사용자 매뉴얼
│   └── MES_PRESENTATION.md      #   Marp 발표 자료
│
└── README.md                     # 프로젝트 개요
```

---

## 10. 환경 변수

| 변수 | 기본값 | 사용처 |
|------|--------|--------|
| `DATABASE_URL` | `postgresql://postgres:mes1234@postgres:5432/mes_db` | 백엔드 → DB 연결 |
| `CORS_ORIGINS` | `http://<IP>:30173,http://localhost:30173,...` | 백엔드 CORS 허용 (env.sh에서 자동 생성) |
| `JWT_SECRET` | `mes-secret-key-2026` | 인증 토큰 서명 |
| `VITE_API_URL` | (비어있음 → nginx 프록시) | 프론트엔드 API 기본 URL |

---

## 11. 네트워크 포트 맵

```
외부 접근 (NodePort)
  :30173  ──→  mes-frontend-service  ──→  nginx:80
  :30461  ──→  mes-api-service       ──→  FastAPI:80

클러스터 내부 (ClusterIP)
  postgres:5432  ──→  PostgreSQL
  mes-api-service:80  ──→  FastAPI (nginx에서 프록시)
```

---

## 12. 기능 코드 매핑 (FN-001 ~ FN-037)

| FN | 기능 | 백엔드 모듈 | 프론트엔드 메뉴 |
|----|------|------------|----------------|
| FN-001~003 | 인증/권한 | mes_auth.py | - |
| FN-004~007 | 품목 관리 | mes_items.py | ITEMS |
| FN-008~009 | BOM 관리 | mes_bom.py | BOM |
| FN-010~012 | 공정/라우팅 | mes_process.py | PROCESS |
| FN-013~014 | 설비 관리 | mes_equipment.py | EQUIPMENT |
| FN-015~017 | 생산계획 | mes_plan.py | PLANS |
| FN-018~019 | AI 수요예측 | mes_ai_prediction.py | AI_CENTER |
| FN-020~024 | 작업지시/실적 | mes_work.py | WORK_ORDER |
| FN-025~027 | 품질관리 | mes_quality.py | QUALITY |
| FN-028 | AI 불량예측 | mes_defect_predict.py | AI_CENTER |
| FN-029~031 | 재고관리 | mes_inventory.py | INVENTORY |
| FN-032~034 | 설비 모니터링/AI | mes_equipment.py | AI_CENTER |
| FN-035~037 | 리포트/AI 인사이트 | mes_reports.py | REPORTS |

---

**최종 업데이트**: 2026-02-23
