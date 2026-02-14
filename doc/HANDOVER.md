# KNU MES 시스템 — 개발자 인수인계 문서

> Kubernetes 기반 클라우드 네이티브 MES (Manufacturing Execution System)
> 경북대학교 스마트 팩토리 프로젝트

**문서 버전**: v5.2
**최종 작성일**: 2026-02-14

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [디렉터리 구조 및 파일 역할](#2-디렉터리-구조-및-파일-역할)
3. [핵심 동작 흐름](#3-핵심-동작-흐름)
4. [코드 변경 시 배포 방법](#4-코드-변경-시-배포-방법)
5. [데이터베이스 스키마 개요](#5-데이터베이스-스키마-개요)
6. [API 엔드포인트 전체 목록](#6-api-엔드포인트-전체-목록)
7. [기술 스택](#7-기술-스택)
8. [주의사항 및 알려진 이슈](#8-주의사항-및-알려진-이슈)
9. [트러블슈팅 가이드](#9-트러블슈팅-가이드)
10. [연락처 및 참고 자료](#10-연락처-및-참고-자료)

---

## 1. 프로젝트 개요

KNU MES는 경북대학교 스마트 팩토리 프로젝트로 개발된 **Kubernetes 기반 클라우드 네이티브 제조 실행 시스템(Manufacturing Execution System)**입니다.

### 1.1 시스템 특징

| 항목 | 내용 |
|------|------|
| **아키텍처** | 단일 VM 위 Kubernetes 클러스터 (kubeadm) |
| **배포 방식** | ConfigMap 기반 — Docker 이미지 빌드 없이 코드 배포 |
| **네트워크** | Cilium eBPF CNI + Hubble (네트워크 가시성) |
| **인증** | Keycloak OIDC (PKCE) |
| **기능 범위** | FN-001 ~ FN-037, 총 14개 메뉴, 37+ API 엔드포인트 |
| **AI 기능** | 수요예측 (선형 회귀), 불량예측 (통계 기반), 고장예측 (센서 이상 감지) |

### 1.2 14개 메뉴 구성

| 영역 | 메뉴 | 주요 기능 |
|------|------|-----------|
| 기준정보 | Items, BOM, Process, Equipment | 품목/BOM(목록, 전개, 역전개)/공정(마스터, 라우팅, 요약)/설비 관리 |
| 생산관리 | Plans, Work Order | 생산계획, 작업지시/실적 |
| 품질/재고 | Quality, Inventory | 불량 분석, 재고 현황 |
| AI 분석 | AI Center | 수요예측, 불량예측, 고장예측 |
| 리포트 | Reports | 생산/품질 리포트, AI 인사이트 |
| 모니터링 | Network, Infra, K8s | Hubble 서비스맵, CPU/메모리 모니터링, Pod 관리 |

---

## 2. 디렉터리 구조 및 파일 역할

```
MES_PROJECT/
├── init.sh                    # 통합 초기화 스크립트 (VM 부팅 후 실행)
├── env.sh                     # 환경 변수 설정 (모든 스크립트가 source)
├── setup-keycloak.sh          # Keycloak 자동 설정 스크립트
├── app.py                     # FastAPI 메인 라우터 (37+ API 엔드포인트)
├── test_app.py                # 테스트 파일
├── Dockerfile                 # 컨테이너 이미지 빌드 (참고용, 실제 배포는 ConfigMap)
├── tempid_pw.md               # 임시 계정 정보
│
├── api_modules/               # 백엔드 비즈니스 로직 모듈
│   ├── __init__.py
│   ├── database.py            # DB 커넥션 풀 (psycopg2 ThreadedConnectionPool)
│   ├── sys_logic.py           # 시스템 인프라 로직 (CPU/메모리, Pod 조회)
│   ├── k8s_service.py         # K8s/Hubble API 연동 (네트워크 플로우, 서비스맵)
│   ├── mes_auth.py            # 인증/권한 (FN-001~003)
│   ├── mes_items.py           # 품목 CRUD (FN-004~007)
│   ├── mes_bom.py             # BOM 관리, 전개, 역전개 (FN-008~009)
│   ├── mes_process.py         # 공정/라우팅 관리 (FN-010~012)
│   ├── mes_equipment.py       # 설비 관리, 고장예측 (FN-013~014, FN-032~034)
│   ├── mes_plan.py            # 생산계획, AI 스케줄링 (FN-015~017)
│   ├── mes_work.py            # 작업지시/실적 (FN-020~024)
│   ├── mes_quality.py         # 품질 관리 (FN-025~027)
│   ├── mes_inventory.py       # 재고 입출고 (FN-029~031)
│   ├── mes_ai_prediction.py   # AI 수요예측 (FN-018~019)
│   ├── mes_defect_predict.py  # AI 불량예측 (FN-028)
│   ├── mes_reports.py         # 생산/품질 리포트, AI 인사이트 (FN-035~037)
│   ├── mes_dashboard.py       # 대시보드 데이터
│   ├── mes_work_order.py      # 작업지시 (레거시)
│   ├── mes_execution.py       # 생산 실행 (레거시)
│   ├── mes_inventory_status.py    # 재고 상태 (레거시)
│   ├── mes_inventory_movement.py  # 재고 이동 (레거시)
│   ├── mes_material_receipt.py    # 자재 입고 (레거시)
│   ├── mes_performance.py     # 실적 (레거시)
│   ├── mes_logic.py           # 비즈니스 로직 (레거시)
│   ├── mes_logistics.py       # 물류 (레거시)
│   ├── mes_master.py          # 기준정보 (레거시)
│   ├── mes_production.py      # 생산 (레거시)
│   └── mes_service.py         # 서비스 (레거시)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # React 단일 페이지 (~88KB, 14개 메뉴 전체)
│   │   ├── main.jsx           # React 엔트리포인트
│   │   ├── api.js             # axios API 유틸 (사용되지 않음, 직접 axios 사용)
│   │   ├── BomList.jsx        # BOM 컴포넌트 (레거시, App.jsx로 통합됨)
│   │   ├── BOMManager.jsx     # BOM 관리 (레거시)
│   │   ├── BomRegistrationForm.jsx # BOM 등록 (레거시)
│   │   └── PlanForm.jsx       # 계획 폼 (레거시)
│   ├── package.json           # React 19, Vite (rolldown-vite 7.2.5), Tailwind CSS 4, keycloak-js
│   └── dist/                  # 빌드 결과물 (ConfigMap으로 K8s에 배포)
│
├── infra/                     # K8s 매니페스트 파일 (kubectl apply -f로 적용)
│   ├── postgres-pv.yaml       # PV + PVC
│   ├── db-secret.yaml         # DB 접속 Secret
│   ├── postgres.yaml          # PostgreSQL Deployment + Service
│   ├── keycloak.yaml          # Keycloak Deployment + Service (NodePort 30080)
│   ├── mes-api.yaml           # FastAPI Deployment + Service (NodePort 30461)
│   ├── nginx-config.yaml      # nginx reverse proxy ConfigMap
│   └── mes-frontend.yaml      # Frontend Deployment + Service (NodePort 30173)
│
├── db/
│   └── init.sql               # DB 초기화 SQL (19개 테이블 + 시드 데이터)
│
├── doc/
│   ├── ARCH.md                # 아키텍처 문서
│   ├── HOWTOSTART.md          # VM 부팅 후 시작 가이드
│   ├── USER_MANUAL.md         # 사용자 매뉴얼
│   └── HANDOVER.md            # 이 문서 (인수인계)
│
└── README.md                  # 프로젝트 개요
```

### 2.1 주요 파일 상세 설명

#### 스크립트 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `init.sh` | VM 부팅 후 전체 시스템을 기동하는 통합 초기화 스크립트 (9단계) | `sudo bash /root/MES_PROJECT/init.sh`로 실행 |
| `env.sh` | 모든 환경 변수를 중앙 관리. 다른 스크립트가 `source`하여 사용 | 하드코딩 금지. 변경 시 이 파일만 수정 |
| `setup-keycloak.sh` | Keycloak REST API를 호출하여 Realm, Client, 사용자를 자동 생성 | init.sh의 마지막 단계에서 자동 호출 |

#### 백엔드 핵심 파일

| 파일 | 역할 |
|------|------|
| `app.py` | FastAPI 메인 라우터. 모든 API 엔드포인트를 정의하고 각 모듈 함수를 호출 |
| `api_modules/database.py` | psycopg2 `ThreadedConnectionPool`로 DB 커넥션 풀 관리. `get_conn()`, `release_conn()`, `query_db()` 제공 |
| `api_modules/mes_*.py` (활성) | FN-001~037 기능별 비즈니스 로직 모듈 |
| `api_modules/mes_*.py` (레거시) | 초기 개발 시 작성된 모듈. `app.py`에서 import하지 않으나 ConfigMap에는 포함됨 |

#### 프론트엔드 핵심 파일

| 파일 | 역할 |
|------|------|
| `frontend/src/App.jsx` | 14개 메뉴 전체를 하나의 파일에 구현한 SPA (~88KB). 공통 UI 컴포넌트(Card, Table, FilterBar 등)와 상태 관리 포함 |
| `frontend/src/main.jsx` | React 엔트리포인트. Keycloak 초기화 및 App 렌더링 |
| `frontend/package.json` | 의존성 정의: React 19, rolldown-vite 7.2.5, Tailwind CSS 4, keycloak-js, axios |

---

## 3. 핵심 동작 흐름

### 3.1 시스템 기동 흐름 (init.sh)

```
init.sh 실행 (sudo bash /root/MES_PROJECT/init.sh)
    │
    ├─ [1/9] env.sh source → 환경 변수 및 공통 유틸 로드
    │
    ├─ [2/9] 시스템 기본 설정
    │         ├─ swapoff -a (swap 비활성화)
    │         ├─ mkdir -p /mnt/data (PV 경로 생성)
    │         └─ containerd/kubelet 재시작
    │
    ├─ [3/9] Kubernetes API 서버 대기 (최대 60초)
    │
    ├─ [4/9] Cilium 네트워크 복구
    │         └─ Cilium Pod 강제 재시작 → 정상 확인 대기
    │
    ├─ [5/9] 불량 Pod 정리 (Failed/Unknown/Error/CrashLoop)
    │
    ├─ [6/9] PostgreSQL DB 배포
    │         ├─ kubectl apply -f postgres-pv.yaml
    │         ├─ kubectl apply -f db-secret.yaml
    │         └─ kubectl apply -f postgres.yaml → Pod Ready 대기
    │
    ├─ [7/9] Keycloak 배포
    │         └─ kubectl apply -f keycloak.yaml (기동 30~60초 소요)
    │
    ├─ [8/9] 백엔드 API 배포
    │         ├─ ConfigMap 생성: app.py + api_modules/*.py → api-code
    │         └─ CORS_ORIGINS 치환 후 mes-api.yaml 적용
    │
    ├─ [9/9] 프론트엔드 빌드 & 배포
    │         ├─ npm install && npm run build
    │         ├─ ConfigMap 생성: dist/ → frontend-build
    │         ├─ kubectl apply -f nginx-config.yaml
    │         └─ kubectl apply -f mes-frontend.yaml
    │
    └─ 최종 검증
          ├─ 방화벽 개방 (ufw allow 30000:32767/tcp)
          ├─ rollout restart (ConfigMap 갱신 반영)
          ├─ 프론트엔드 HTTP 200 대기 (최대 90초)
          ├─ API 서버 HTTP 200 대기 (최대 180초, pip install 포함)
          └─ setup-keycloak.sh 실행 (Realm/Client/사용자 생성)
```

### 3.2 사용자 요청 흐름

```
사용자 브라우저
    │
    │  http://<IP>:30173
    ▼
nginx (mes-frontend, :30173)
    │
    ├─ 정적 파일 요청 (/, *.js, *.css)
    │   └─ /usr/share/nginx/html (ConfigMap: frontend-build)
    │
    └─ API 요청 (/api/*)
        │  proxy_pass http://mes-api-service:80
        ▼
    FastAPI (mes-api, :30461)
        │
        │  psycopg2 ThreadedConnectionPool
        ▼
    PostgreSQL (postgres, :5432)
```

### 3.3 인증 흐름

```
[1] 사용자가 브라우저에서 웹 UI 접속
        │
[2] main.jsx에서 keycloak-js 초기화
        │  Keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256' })
        ▼
[3] Keycloak 로그인 페이지로 리다이렉트 (:30080)
        │  OIDC Authorization Code Flow with PKCE
        ▼
[4] 사용자 인증 → Authorization Code 발급
        │
[5] keycloak-js가 Token Endpoint 호출 → JWT 토큰 수신
        │  access_token, refresh_token
        ▼
[6] API 호출 시 Bearer Token 포함
        │  axios.defaults.headers['Authorization'] = 'Bearer ' + token
        ▼
[7] FastAPI에서 토큰 검증 후 요청 처리
```

### 3.4 API Pod 시작 시퀀스

API Pod는 ConfigMap 방식이므로 컨테이너 시작 시 다음 과정이 실행됩니다:

```bash
# mes-api.yaml의 args:
mkdir -p /app/api_modules &&
cp /mnt/*.py /app/api_modules/ &&         # ConfigMap에서 소스 복사
mv /app/api_modules/app.py /app/app.py && # app.py를 상위로 이동
touch /app/api_modules/__init__.py &&     # __init__.py 생성
pip install --no-cache-dir fastapi uvicorn psycopg2-binary kubernetes pydantic psutil &&
python /app/app.py                         # 서버 기동 (port 80)
```

> **주의**: `pip install`이 매번 실행되므로 첫 기동 시 1~2분이 소요됩니다.

---

## 4. 코드 변경 시 배포 방법

### 4.1 백엔드 변경 (api_modules/*.py 또는 app.py)

```bash
# 1. 소스 코드 수정
vi /root/MES_PROJECT/api_modules/mes_items.py   # 예시

# 2. ConfigMap 재생성
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code \
  --from-file=app.py=/root/MES_PROJECT/app.py \
  --from-file=/root/MES_PROJECT/api_modules/

# 3. Pod 재시작 (새 ConfigMap 적용)
kubectl rollout restart deployment mes-api

# 4. 기동 확인 (pip install 포함 1~2분)
kubectl logs deployment/mes-api --tail=20 -f
```

### 4.2 프론트엔드 변경 (App.jsx 등)

```bash
# 1. 소스 코드 수정
vi /root/MES_PROJECT/frontend/src/App.jsx

# 2. 빌드
cd /root/MES_PROJECT/frontend
npm run build

# 3. ConfigMap 재생성
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/

# 4. Pod 재시작
kubectl rollout restart deployment mes-frontend

# 5. 확인
kubectl get pods -l app=mes-frontend
```

### 4.3 인프라 변경 (infra/*.yaml)

```bash
# YAML 수정 후 직접 적용
kubectl apply -f /root/MES_PROJECT/infra/mes-api.yaml

# 참고: mes-api.yaml에는 CORS_ORIGINS 플레이스홀더(__CORS_ORIGINS__)가 있으므로,
# 직접 apply할 때는 sed로 치환하거나 init.sh를 다시 실행해야 합니다.
source /root/MES_PROJECT/env.sh
sed "s|__CORS_ORIGINS__|${CORS_ORIGINS}|" \
  /root/MES_PROJECT/infra/mes-api.yaml | kubectl apply -f -
```

### 4.4 환경 변수 변경

```bash
# env.sh만 수정하면 됨 (다음 init.sh 실행 시 자동 반영)
vi /root/MES_PROJECT/env.sh

# 즉시 반영이 필요하면 init.sh 재실행
sudo bash /root/MES_PROJECT/init.sh
```

### 4.5 DB 스키마 변경

```bash
# 1. init.sql 수정
vi /root/MES_PROJECT/db/init.sql

# 2. DB Pod에 직접 접속하여 SQL 실행
kubectl exec -it deployment/postgres -- psql -U postgres -d mes_db

# 또는 DB를 완전히 초기화하려면:
kubectl delete deployment postgres
kubectl delete pvc postgres-pvc
kubectl delete pv postgres-pv
rm -rf /mnt/data/*
sudo bash /root/MES_PROJECT/init.sh
```

### 4.6 배포 방법 요약 표

| 변경 대상 | 수정 파일 | 배포 명령 | 소요 시간 |
|-----------|-----------|-----------|-----------|
| 백엔드 로직 | `api_modules/*.py` | ConfigMap 재생성 + `rollout restart mes-api` | 1~2분 (pip install) |
| API 라우터 | `app.py` | ConfigMap 재생성 + `rollout restart mes-api` | 1~2분 |
| 프론트엔드 | `frontend/src/App.jsx` | `npm run build` + ConfigMap 재생성 + `rollout restart mes-frontend` | 30초 |
| K8s 리소스 | `infra/*.yaml` | `kubectl apply -f` | 즉시 |
| 환경 변수 | `env.sh` | 수정만 (다음 init.sh 실행 시 반영) | - |
| DB 스키마 | `db/init.sql` | Pod 접속 후 SQL 실행 또는 DB 초기화 | 가변 |

---

## 5. 데이터베이스 스키마 개요

### 5.1 연결 정보

| 항목 | 값 |
|------|-----|
| DBMS | PostgreSQL 15 |
| HOST | `postgres` (K8s Service) |
| PORT | 5432 (ClusterIP, 외부 노출 안 됨) |
| DATABASE | `mes_db` |
| USER / PW | `postgres` / `mes1234` |
| DSN | `postgresql://postgres:mes1234@postgres:5432/mes_db` |

### 5.2 테이블 목록 (19개)

| # | 테이블 | PK | 설명 | 주요 컬럼 |
|---|--------|-----|------|-----------|
| 1 | `users` | user_id (VARCHAR) | 사용자 | password, name, email, role(admin/worker/viewer) |
| 2 | `user_permissions` | id (SERIAL) | 메뉴별 권한 | user_id, menu, can_read, can_write |
| 3 | `items` | item_code (VARCHAR) | 품목 마스터 | name, category(RAW/SEMI/PRODUCT), unit, spec, safety_stock |
| 4 | `bom` | bom_id (SERIAL) | BOM | parent_item, child_item, qty_per_unit, loss_rate |
| 5 | `processes` | process_code (VARCHAR) | 공정 | name, std_time_min, description, equip_code |
| 6 | `routings` | routing_id (SERIAL) | 라우팅 | item_code, seq, process_code, cycle_time_sec |
| 7 | `equipments` | equip_code (VARCHAR) | 설비 | name, process_code, capacity_per_hour, status(RUNNING/STOP/DOWN) |
| 8 | `equip_status_log` | log_id (SERIAL) | 설비 상태 이력 | equip_code, status, reason, changed_at |
| 9 | `production_plans` | plan_id (SERIAL) | 생산계획 | item_code, plan_qty, due_date, priority, status |
| 10 | `work_orders` | wo_id (VARCHAR) | 작업지시 | plan_id, item_code, work_date, equip_code, order_qty |
| 11 | `work_results` | result_id (SERIAL) | 작업실적 | wo_id, good_qty, defect_qty, worker_id |
| 12 | `quality_standards` | standard_id (SERIAL) | 품질 기준 | item_code, check_name, min_val, max_val, std_val |
| 13 | `inspections` | inspection_id (SERIAL) | 품질 검사 | item_code, lot_no, judgment |
| 14 | `inspection_details` | detail_id (SERIAL) | 검사 상세 | inspection_id, measured_value, judgment |
| 15 | `defect_codes` | defect_code (VARCHAR) | 불량 코드 | name, description |
| 16 | `inventory` | inv_id (SERIAL) | 재고 | item_code, lot_no, qty, warehouse |
| 17 | `inventory_transactions` | tx_id (SERIAL) | 재고 트랜잭션 | tx_type, qty, slip_no |
| 18 | `shipments` | shipment_id (SERIAL) | 출하 | item_code, ship_date, qty |
| 19 | `defect_history` | defect_id (SERIAL) | 불량 이력 (AI용) | temperature, pressure, speed, humidity |
| 20 | `equip_sensors` | sensor_id (SERIAL) | 센서 데이터 (AI용) | vibration, temperature, current_amp |
| 21 | `ai_forecasts` | forecast_id (SERIAL) | AI 예측 결과 | model_type, result_json |

> 참고: init.sql 기준으로 일부 테이블이 추가될 수 있으며, 실제로는 약 21개 테이블이 존재합니다.

### 5.3 ERD 개요

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  users   │     │  items   │────>│   bom    │ (parent_item / child_item)
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

### 5.4 시드 데이터 규모

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

## 6. API 엔드포인트 전체 목록

Swagger UI: `http://<IP>:30461/docs`

### 6.1 비즈니스 API (FN-001 ~ FN-037)

| 기능 코드 | Method | URL | 설명 | 모듈 |
|-----------|--------|-----|------|------|
| FN-001 | POST | `/api/auth/login` | 로그인 | mes_auth.py |
| FN-002 | POST | `/api/auth/register` | 사용자 등록 | mes_auth.py |
| FN-003 | GET | `/api/auth/permissions/{user_id}` | 권한 조회 | mes_auth.py |
| FN-004 | POST | `/api/items` | 품목 생성 | mes_items.py |
| FN-005 | GET | `/api/items` | 품목 목록 (검색, 페이징) | mes_items.py |
| FN-006 | GET | `/api/items/{item_code}` | 품목 상세 | mes_items.py |
| FN-007 | PUT | `/api/items/{item_code}` | 품목 수정 | mes_items.py |
| FN-008 | POST | `/api/bom` | BOM 등록 | mes_bom.py |
| FN-008 | GET | `/api/bom` | BOM 전체 목록 | mes_bom.py |
| FN-008 | GET | `/api/bom/summary` | BOM 통계 요약 | mes_bom.py |
| FN-009 | GET | `/api/bom/where-used/{item_code}` | BOM 역전개 (사용처) | mes_bom.py |
| FN-009 | GET | `/api/bom/explode/{item_code}` | BOM 전개 | mes_bom.py |
| FN-010 | GET | `/api/processes` | 공정 목록 | mes_process.py |
| FN-010 | POST | `/api/processes` | 공정 등록 | mes_process.py |
| FN-011 | GET | `/api/routings` | 라우팅 요약 (전체) | mes_process.py |
| FN-011 | POST | `/api/routings` | 라우팅 등록 | mes_process.py |
| FN-012 | GET | `/api/routings/{item_code}` | 품목별 라우팅 조회 | mes_process.py |
| FN-013 | POST | `/api/equipments` | 설비 등록 | mes_equipment.py |
| FN-014 | GET | `/api/equipments` | 설비 목록 | mes_equipment.py |
| FN-015 | POST | `/api/plans` | 생산계획 등록 | mes_plan.py |
| FN-016 | GET | `/api/plans` | 생산계획 목록 | mes_plan.py |
| FN-017 | GET | `/api/plans/{plan_id}` | 생산계획 상세 | mes_plan.py |
| FN-018 | POST | `/api/ai/demand-forecast` | AI 수요 예측 | mes_ai_prediction.py |
| FN-018 | GET | `/api/ai/demand-prediction/{item_code}` | AI 수요 예측 (GET) | mes_ai_prediction.py |
| FN-019 | POST | `/api/ai/schedule-optimize` | AI 스케줄 최적화 | mes_plan.py |
| FN-020 | POST | `/api/work-orders` | 작업지시 생성 | mes_work.py |
| FN-021 | GET | `/api/work-orders` | 작업지시 목록 | mes_work.py |
| FN-022 | GET | `/api/work-orders/{wo_id}` | 작업지시 상세 | mes_work.py |
| FN-023 | POST | `/api/work-results` | 작업실적 등록 | mes_work.py |
| FN-024 | GET | `/api/dashboard/production` | 생산 대시보드 | mes_work.py |
| FN-025 | POST | `/api/quality/standards` | 품질 기준 등록 | mes_quality.py |
| FN-026 | POST | `/api/quality/inspections` | 품질 검사 등록 | mes_quality.py |
| FN-027 | GET | `/api/quality/defects` | 불량 현황 조회 | mes_quality.py |
| FN-028 | POST | `/api/ai/defect-predict` | AI 불량 예측 | mes_defect_predict.py |
| FN-028 | POST | `/api/ai/defect-prediction` | AI 불량 예측 (별칭) | mes_defect_predict.py |
| FN-029 | POST | `/api/inventory/in` | 재고 입고 | mes_inventory.py |
| FN-030 | POST | `/api/inventory/out` | 재고 출고 | mes_inventory.py |
| FN-031 | GET | `/api/inventory` | 재고 현황 | mes_inventory.py |
| FN-032 | PUT | `/api/equipments/{equip_code}/status` | 설비 상태 변경 | mes_equipment.py |
| FN-033 | GET | `/api/equipments/status` | 설비 상태 대시보드 | mes_equipment.py |
| FN-034 | POST | `/api/ai/failure-predict` | AI 고장 예측 | mes_equipment.py |
| FN-035 | GET | `/api/reports/production` | 생산 리포트 | mes_reports.py |
| FN-036 | GET | `/api/reports/quality` | 품질 리포트 | mes_reports.py |
| FN-037 | POST | `/api/ai/insights` | AI 인사이트 | mes_reports.py |

### 6.2 인프라/모니터링 API

| Method | URL | 설명 | 모듈 |
|--------|-----|------|------|
| GET | `/api/infra/status` | CPU/메모리 사용률 | sys_logic.py |
| GET | `/api/k8s/pods` | Pod 목록 | sys_logic.py |
| GET | `/api/k8s/logs/{name}` | Pod 로그 조회 | k8s_service.py |
| GET | `/api/network/flows` | 네트워크 플로우 | k8s_service.py |
| GET | `/api/network/topology` | 네트워크 토폴로지 | k8s_service.py |
| GET | `/api/network/hubble-flows` | Hubble 플로우 | k8s_service.py |
| GET | `/api/network/service-map` | 서비스 의존성 맵 | k8s_service.py |
| GET | `/api/mes/data` | 대시보드 데이터 (레거시) | mes_dashboard.py |

---

## 7. 기술 스택

### 7.1 전체 기술 스택

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **인프라** | Kubernetes (kubeadm) | v1.30+ | 컨테이너 오케스트레이션 |
| **네트워크** | Cilium eBPF + Hubble | 최신 | CNI, 네트워크 정책, 플로우 모니터링 |
| **인증** | Keycloak | 최신 | OIDC IdP (PKCE 지원) |
| **DB** | PostgreSQL | 15 | 관계형 데이터베이스 (19+ 테이블) |
| **백엔드** | Python FastAPI | 0.109+ | REST API 서버 |
| **백엔드 런타임** | python:3.9-slim | 3.9 | 컨테이너 베이스 이미지 |
| **프론트엔드** | React | 19 | SPA 웹 UI |
| **번들러** | rolldown-vite | 7.2.5 | 빌드 도구 (Vite 호환) |
| **CSS** | Tailwind CSS | 4 | 유틸리티 기반 CSS |
| **HTTP 클라이언트** | Axios | 1.13+ | API 통신 |
| **인증 클라이언트** | keycloak-js | 26.2+ | 브라우저 측 OIDC 처리 |
| **웹 서버** | nginx:alpine | 최신 | 정적 파일 서빙 + API 리버스 프록시 |
| **배포 방식** | ConfigMap 기반 | - | Docker 빌드 없이 소스 직접 배포 |

### 7.2 Kubernetes 리소스 구성

| Deployment | Image | Port | NodePort | 역할 |
|------------|-------|------|----------|------|
| `mes-frontend` | `nginx:alpine` | 80 | **30173** | React 빌드 파일 서빙 + API 리버스 프록시 |
| `mes-api` | `python:3.9-slim` | 80 | **30461** | FastAPI REST API 서버 |
| `postgres` | `postgres:15` | 5432 | - (ClusterIP) | PostgreSQL 데이터베이스 |
| `keycloak` | `keycloak` | 8080 | **30080** | Keycloak 인증 서버 |

### 7.3 ConfigMap 구성

| ConfigMap | 내용 | 마운트 경로 |
|-----------|------|------------|
| `api-code` | `app.py` + `api_modules/*.py` | `/mnt` (시작 시 `/app/`으로 복사) |
| `frontend-build` | `dist/` 디렉터리 (빌드 결과물) | `/usr/share/nginx/html` |
| `nginx-config` | `default.conf` (프록시 설정) | `/etc/nginx/conf.d/` |

### 7.4 환경 변수 (env.sh)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `REAL_IP` | VM의 첫 번째 IP | 서비스 접속 IP |
| `PORT_FRONTEND` | 30173 | 프론트엔드 NodePort |
| `PORT_API` | 30461 | API NodePort |
| `PORT_KEYCLOAK` | 30080 | Keycloak NodePort |
| `KC_REALM` | mes-realm | Keycloak Realm 이름 |
| `KC_CLIENT_ID` | mes-frontend | Keycloak Client ID |
| `KC_ADMIN_USER` | admin | Keycloak 관리자 ID |
| `KC_ADMIN_PASS` | admin1234 | Keycloak 관리자 비밀번호 |
| `DATABASE_URL` | postgresql://postgres:mes1234@postgres:5432/mes_db | DB 연결 문자열 (Secret) |
| `CORS_ORIGINS` | `http://<IP>:30173,...` | CORS 허용 오리진 |

---

## 8. 주의사항 및 알려진 이슈

### 8.1 반드시 알아야 할 사항

| # | 주의사항 | 상세 |
|---|----------|------|
| 1 | **swap이 켜져 있으면 kubelet이 실패** | VM 재시작 시 swap이 다시 활성화됨. `init.sh`가 `swapoff -a`로 자동 처리하지만, 수동으로 kubectl 사용 시 반드시 확인 |
| 2 | **Cilium eBPF가 VM 재시작 후 초기화 실패 가능** | eBPF 맵이 리셋되면서 Pod 네트워크가 불통. `init.sh`가 Cilium Pod를 강제 재시작하여 자동 복구 |
| 3 | **API Pod는 ConfigMap 방식이라 pip install이 매번 실행** | Pod 재시작 시마다 패키지 설치 (1~2분). 네트워크 불안정 시 실패할 수 있음 |
| 4 | **프론트엔드는 단일 App.jsx 파일** | ~88KB 단일 파일이므로 변경 시 전체 빌드 필요. 컴포넌트 분리가 되어 있지 않음 |
| 5 | **레거시 모듈이 ConfigMap에 포함** | `app.py`에서 import하지 않는 레거시 모듈들도 ConfigMap에 포함됨. 삭제해도 무방하나 참고용으로 유지 중 |
| 6 | **DB 데이터는 hostPath PV 사용** | `/mnt/data`에 저장. VM 삭제 시 데이터 유실. 백업 필요 시 `pg_dump` 사용 |
| 7 | **CORS_ORIGINS에 __CORS_ORIGINS__ 플레이스홀더** | `mes-api.yaml`에 하드코딩되지 않고, `init.sh`가 `sed`로 치환. 수동 `kubectl apply` 시 주의 |

### 8.2 알려진 제한사항

| # | 제한사항 | 영향 |
|---|----------|------|
| 1 | 단일 노드 클러스터 | HA 구성 없음. 노드 장애 시 전체 시스템 다운 |
| 2 | TLS/HTTPS 미적용 | 모든 통신이 HTTP. 운영 환경에서는 인증서 설정 필요 |
| 3 | AI 모델이 통계 기반 | 별도 ML 프레임워크 없이 선형 회귀/임계값 비교 사용 |
| 4 | ConfigMap 크기 제한 | K8s ConfigMap은 1MB 제한. 프론트엔드 빌드 결과물이 커지면 문제 발생 가능 |
| 5 | keycloak-js가 프론트엔드에 직접 통합 | 토큰 갱신/만료 처리가 main.jsx에 의존 |

---

## 9. 트러블슈팅 가이드

### 9.1 K8s API 서버 연결 실패

```bash
# kubelet 상태 확인
systemctl status kubelet

# swap 비활성화 후 재시작
swapoff -a
systemctl restart kubelet

# 30초 후 확인
kubectl get nodes
```

### 9.2 Pod가 ContainerCreating에서 멈춤

```bash
# Cilium 네트워크 문제 — Pod 재시작
kubectl delete pod -n kube-system -l k8s-app=cilium --force
sleep 10
kubectl get pods
```

### 9.3 API 서버 응답 없음 (502 / Connection Refused)

```bash
# API Pod 로그 확인 — pip install 진행 중일 수 있음
kubectl logs deployment/mes-api --tail=30

# pip install 실패 시 Pod 재시작
kubectl rollout restart deployment mes-api
```

### 9.4 프론트엔드 빈 화면

```bash
# ConfigMap 재생성
cd /root/MES_PROJECT/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend
```

### 9.5 DB 연결 실패

```bash
# PostgreSQL Pod 상태 확인
kubectl get pods -l app=postgres
kubectl logs deployment/postgres --tail=20

# DB 접속 테스트
kubectl exec -it deployment/postgres -- psql -U postgres -d mes_db -c "SELECT 1;"
```

### 9.6 Keycloak 로그인 안 됨

```bash
# Keycloak Pod 상태 확인
kubectl get pods -l app=keycloak
kubectl logs deployment/keycloak --tail=30

# Realm 확인
curl -s http://localhost:30080/realms/mes-realm | python3 -m json.tool

# 재설정 필요 시
bash /root/MES_PROJECT/setup-keycloak.sh
```

### 9.7 전체 시스템 재시작

```bash
# 가장 확실한 방법: init.sh 재실행
sudo bash /root/MES_PROJECT/init.sh
```

### 9.8 상태 확인 명령어 모음

```bash
# Pod 상태 확인
kubectl get pods -o wide

# 모든 서비스 확인
kubectl get svc

# API 서버 헬스 체크
curl -s http://localhost:30461/api/infra/status

# 프론트엔드 헬스 체크
curl -s -o /dev/null -w '%{http_code}' http://localhost:30173

# Keycloak 헬스 체크
curl -s http://localhost:30080/realms/master | head -1

# DB 상태 확인
kubectl exec deployment/postgres -- pg_isready -U postgres

# Pod 로그 (실시간)
kubectl logs -f deployment/mes-api
kubectl logs -f deployment/mes-frontend
kubectl logs -f deployment/postgres
```

---

## 10. 연락처 및 참고 자료

### 10.1 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 프로젝트명 | 경북대학교 스마트 팩토리 MES |
| 버전 | v5.2 |
| 저장소 경로 | `/root/MES_PROJECT` |
| VM 접속 | `ssh c1_master1@192.168.64.5` → `sudo -s` |

### 10.2 테스트 계정

| 계정 | 비밀번호 | 역할 |
|------|----------|------|
| admin | admin1234 | 시스템 관리자 |
| worker01 | worker1234 | 작업자 |
| viewer01 | viewer1234 | 조회 전용 |

### 10.3 주요 접속 URL

| 서비스 | URL |
|--------|-----|
| 웹 UI | `http://<IP>:30173` |
| API Swagger 문서 | `http://<IP>:30461/docs` |
| Keycloak 관리 콘솔 | `http://<IP>:30080` |

### 10.4 관련 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 아키텍처 문서 | `doc/ARCH.md` | 시스템 구조, 모듈 상세, DB 스키마, API 목록 |
| 시작 가이드 | `doc/HOWTOSTART.md` | VM 부팅 후 시스템 기동 절차 |
| 사용자 매뉴얼 | `doc/USER_MANUAL.md` | 각 메뉴별 사용 방법 |
| README | `README.md` | 프로젝트 개요 및 빠른 시작 |

### 10.5 기능 코드 매핑 요약 (FN-001 ~ FN-037)

| FN 코드 | 기능 영역 | 백엔드 모듈 | 프론트엔드 메뉴 |
|---------|-----------|------------|----------------|
| FN-001~003 | 인증/권한 | mes_auth.py | (Keycloak 연동) |
| FN-004~007 | 품목 관리 | mes_items.py | ITEMS |
| FN-008~009 | BOM 관리 | mes_bom.py | BOM |
| FN-010~012 | 공정/라우팅 | mes_process.py | PROCESS |
| FN-013~014 | 설비 관리 | mes_equipment.py | EQUIPMENT |
| FN-015~017 | 생산계획 | mes_plan.py | PLANS |
| FN-018~019 | AI 수요예측/스케줄링 | mes_ai_prediction.py, mes_plan.py | AI_CENTER |
| FN-020~024 | 작업지시/실적 | mes_work.py | WORK_ORDER |
| FN-025~027 | 품질관리 | mes_quality.py | QUALITY |
| FN-028 | AI 불량예측 | mes_defect_predict.py | AI_CENTER |
| FN-029~031 | 재고관리 | mes_inventory.py | INVENTORY |
| FN-032~034 | 설비 모니터링/AI 고장예측 | mes_equipment.py | AI_CENTER |
| FN-035~037 | 리포트/AI 인사이트 | mes_reports.py | REPORTS |

---

**프로젝트**: 경북대학교 스마트 팩토리 MES
**최종 업데이트**: 2026-02-14
