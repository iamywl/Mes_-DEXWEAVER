# KNU MES 시스템 — 개발자 인수인계 문서

> Kubernetes 기반 클라우드 네이티브 MES (Manufacturing Execution System)
> 경북대학교 스마트 팩토리 프로젝트

**문서 버전**: v5.5
**최종 작성일**: 2026-03-12

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [디렉터리 구조 및 파일 역할](#2-디렉터리-구조-및-파일-역할)
3. [핵심 동작 흐름](#3-핵심-동작-흐름)
   - 3.2.1 [API 요청 라이프사이클 상세](#321-api-요청-라이프사이클-request-lifecycle-상세)
   - 3.3.1 [인증/권한 상세 메커니즘](#331-인증권한-상세-메커니즘)
   - 3.5 [비즈니스 로직 상세 동작](#35-비즈니스-로직-상세-동작) (BOM, 생산관리, 재고, 품질검사)
   - 3.6 [AI 모듈 동작 원리](#36-ai-모듈-동작-원리) (수요예측, 불량예측, 고장예측, Fallback)
   - 3.7 [DB 트랜잭션 처리 패턴](#37-db-트랜잭션-처리-패턴)
   - 3.8 [에러 핸들링 메커니즘](#38-에러-핸들링-메커니즘)
4. [코드 변경 시 배포 방법](#4-코드-변경-시-배포-방법)
5. [데이터베이스 스키마 개요](#5-데이터베이스-스키마-개요)
6. [API 엔드포인트 전체 목록](#6-api-엔드포인트-전체-목록)
7. [기술 스택](#7-기술-스택)
8. [CI/CD 파이프라인](#8-cicd-파이프라인)
9. [주의사항 및 알려진 이슈](#9-주의사항-및-알려진-이슈)
10. [트러블슈팅 가이드](#10-트러블슈팅-가이드)
11. [연락처 및 참고 자료](#11-연락처-및-참고-자료)

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
├── test_app.py                # 테스트 파일 (25개 테스트)
├── Jenkinsfile                # CI/CD 파이프라인 (Jenkins)
├── requirements.txt           # Python 의존성
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
│   ├── HOWTOCONTRIBUTE.md     # 기여 가이드
│   ├── CODE_REVIEW.md         # 코드 품질 검토서
│   ├── CICD_REVIEW.md         # CI/CD 파이프라인 검토서
│   ├── USER_MANUAL.md         # 사용자 매뉴얼
│   ├── MES_PRESENTATION.md    # Marp 발표 자료
│   └── HANDOVER.md            # 이 문서 (인수인계)
│
└── README.md                  # 프로젝트 개요
```

### 2.1 주요 파일 상세 설명

#### 스크립트 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `init.sh` | VM 부팅 후 전체 시스템을 기동하는 통합 초기화 스크립트 (11단계, 병렬 배포 + 프로그레스 바) | `sudo bash /root/MES_PROJECT/init.sh`로 실행 |
| `env.sh` | 모든 환경 변수를 중앙 관리 + 프로그레스 바 유틸 함수 포함. 다른 스크립트가 `source`하여 사용 | 하드코딩 금지. 변경 시 이 파일만 수정 |
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

### 3.1 시스템 기동 흐름 (init.sh — 최적화 버전 v5.4)

실시간 프로그레스 바와 병렬 배포가 적용된 11단계 기동 프로세스입니다.

```
init.sh 실행 (sudo bash /root/MES_PROJECT/init.sh)
    │
    ├─ env.sh source → 환경 변수 + 프로그레스 바 유틸 로드
    │
    ├─ [1] 시스템설정: swapoff, /mnt/data 생성, containerd/kubelet 재시작
    ├─ [2] K8s API 대기 (최대 60초)
    ├─ [3] Cilium 네트워크 복구 (이미 Running이면 스킵)
    ├─ [4] 불량 Pod 정리
    │
    ├─ [5+6] ── 병렬 배포 ──────────────────────────────────
    │  ├─ DB: postgres-pv → db-secret → postgres.yaml + Ready 대기
    │  └─ Keycloak: keycloak.yaml (동시 apply)
    │
    ├─ [7] 백엔드: ConfigMap(api-code) → CORS 치환 → mes-api.yaml
    │       (pip install은 hostPath 캐시(/mnt/pip-cache) 재사용)
    │
    ├─ [8] 프론트 빌드: dist/ 존재 + 소스 미변경 → 빌드 스킵
    │       (변경 감지 시만 npm install + build)
    ├─ [9] 프론트 배포: ConfigMap(frontend-build) + rollout restart
    │
    ├─ [10] ── 병렬 Health Check ───────────────────────────
    │  ├─ 프론트엔드 HTTP 200 (백그라운드)
    │  ├─ API 서버 HTTP 200 (백그라운드)
    │  └─ Keycloak 응답 (백그라운드)
    │
    └─ [11] Keycloak 설정: Realm/Client/사용자 자동 생성

    프로그레스 바: [2:15] ████████████████████ 100%  ● ● ● ● ● ● ● ● ● ● ●
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

#### 3.2.1 API 요청 라이프사이클 (Request Lifecycle) 상세

브라우저에서 API 응답을 받기까지의 전체 흐름을 단계별로 설명합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│  시퀀스 다이어그램: API 요청 전체 흐름                              │
└─────────────────────────────────────────────────────────────────┘

Browser          nginx(:80)       K8s Service       uvicorn/ASGI     FastAPI          Handler         PostgreSQL
  │                 │                │                 │               │                │               │
  │ POST /api/items │                │                 │               │                │               │
  │────────────────>│                │                 │               │                │               │
  │                 │ proxy_pass     │                 │               │                │               │
  │                 │ /api/*         │                 │               │                │               │
  │                 │───────────────>│                 │               │                │               │
  │                 │                │ ClusterIP       │               │                │               │
  │                 │                │ round-robin     │               │                │               │
  │                 │                │────────────────>│               │                │               │
  │                 │                │                 │ ASGI scope    │                │               │
  │                 │                │                 │ 생성          │                │               │
  │                 │                │                 │──────────────>│                │               │
  │                 │                │                 │               │                │               │
  │                 │                │                 │  ┌────────────────────────┐    │               │
  │                 │                │                 │  │ 미들웨어 체인 (순서대로) │    │               │
  │                 │                │                 │  │ 1. CORSMiddleware      │    │               │
  │                 │                │                 │  │ 2. api_version_rewrite │    │               │
  │                 │                │                 │  │ 3. RateLimiter (slowapi)│   │               │
  │                 │                │                 │  │ 4. Prometheus 계측     │    │               │
  │                 │                │                 │  └────────────────────────┘    │               │
  │                 │                │                 │               │                │               │
  │                 │                │                 │               │ Depends:       │               │
  │                 │                │                 │               │ auth_required  │               │
  │                 │                │                 │               │ JWT 검증       │               │
  │                 │                │                 │               │───────────────>│               │
  │                 │                │                 │               │               │ SQL 쿼리       │
  │                 │                │                 │               │               │──────────────>│
  │                 │                │                 │               │               │  결과 반환     │
  │                 │                │                 │               │               │<──────────────│
  │                 │                │                 │               │ JSONResponse   │               │
  │                 │                │                 │               │<──────────────│               │
  │                 │                │                 │<──────────────│                │               │
  │                 │                │<────────────────│               │                │               │
  │                 │<───────────────│                 │               │                │               │
  │<────────────────│                │                 │               │                │               │
  │  JSON Response  │                │                 │               │                │               │
```

**각 단계별 상세 처리:**

| 단계 | 컴포넌트 | 처리 내용 |
|------|---------|-----------|
| **1. 브라우저** | React (axios) | `Authorization: Bearer <JWT>` 헤더 포함하여 HTTP 요청 전송 |
| **2. nginx** | nginx:alpine | `location /api/` 매칭 → `proxy_pass http://mes-api-service:80`로 포워딩. `X-Real-IP`, `X-Forwarded-For` 헤더 추가 |
| **3. K8s Service** | ClusterIP | `mes-api-service` Service가 Pod IP로 라운드로빈 로드밸런싱 |
| **4. uvicorn** | ASGI 서버 | HTTP 요청을 ASGI scope(type, path, headers, body)로 변환. 이벤트 루프에서 비동기 처리 |
| **5. 미들웨어 체인** | FastAPI | (1) CORS: Origin 검증 및 헤더 추가 → (2) api_version_rewrite: `/api/v1/*` → `/api/*` 경로 재작성 → (3) slowapi: Rate Limit 검사 → (4) Prometheus: 요청 메트릭 수집 |
| **6. 라우터 매칭** | APIRouter | `app.include_router()`로 등록된 10개 라우터에서 경로 매칭. 예: `POST /api/items` → `master_router` |
| **7. Depends 실행** | auth_deps.py | `auth_required` → `mes_auth.require_auth()` → JWT 토큰 추출/검증 → 실패 시 HTTPException(401) |
| **8. 핸들러 실행** | mes_*.py | 비즈니스 로직 실행: DB 커넥션 획득 → SQL 실행 → 결과 가공 → 커넥션 반환 |
| **9. 응답 반환** | JSONResponse | dict → JSON 직렬화 → ASGI → uvicorn → HTTP Response로 역순 전달 |

**에러 발생 시 분기:**
- JWT 인증 실패 → `auth_deps.py`에서 `HTTPException(401)` → `http_exception_handler`가 `{"error": "..."}` 반환
- Rate Limit 초과 → slowapi가 `RateLimitExceeded` 예외 → `_rate_limit_exceeded_handler` 반환
- 비즈니스 로직 에러 → `{"error": "..."}` dict 반환 (HTTP 200이지만 error 키 포함)
- 예상치 못한 예외 → `global_exception_handler`가 스택 트레이스를 로그에만 기록하고 `{"error": "서버 내부 오류"}` 반환 (KISA 49 준수)

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

#### 3.3.1 인증/권한 상세 메커니즘

##### JWT 기반 인증 (mes_auth.py)

현재 시스템은 Keycloak OIDC와 별도로 **자체 JWT 인증**을 백엔드에서 수행합니다.
`mes_auth.py`에서 PyJWT + bcrypt를 사용합니다.

**로그인 API 내부 동작 시퀀스:**

```
클라이언트                    Router (auth.py)          mes_auth.login()           security.py              PostgreSQL
  │                            │                          │                          │                       │
  │ POST /api/auth/login       │                          │                          │                       │
  │ {user_id, password}        │                          │                          │                       │
  │───────────────────────────>│                          │                          │                       │
  │                            │ rate limit 확인           │                          │                       │
  │                            │ (5/minute per IP)        │                          │                       │
  │                            │                          │                          │                       │
  │                            │ check_login_lock(uid)    │                          │                       │
  │                            │─────────────────────────────────────────────────────>│                       │
  │                            │                          │                          │ 잠금 여부 확인          │
  │                            │                          │                          │ _locked_accounts 조회  │
  │                            │<────────────────────────────────────────────────────│                       │
  │                            │                          │                          │                       │
  │                            │ mes_auth.login(uid, pw)  │                          │                       │
  │                            │─────────────────────────>│                          │                       │
  │                            │                          │ _sanitize_id(uid)        │                       │
  │                            │                          │ 정규식 검증: ^[a-zA-Z0-9_]{3,30}$               │
  │                            │                          │                          │                       │
  │                            │                          │ SELECT user_id, name,    │                       │
  │                            │                          │ role, password,          │                       │
  │                            │                          │ is_approved              │                       │
  │                            │                          │ FROM users               │                       │
  │                            │                          │─────────────────────────────────────────────────>│
  │                            │                          │                          │                       │
  │                            │                          │ ┌─────────────────────────────────────────┐      │
  │                            │                          │ │ 비밀번호 검증 분기:                       │      │
  │                            │                          │ │                                         │      │
  │                            │                          │ │ 1. _is_legacy_hash() 확인               │      │
  │                            │                          │ │    → len==64 & 모두 hex → SHA-256 레거시│      │
  │                            │                          │ │    → _verify_legacy_password()          │      │
  │                            │                          │ │    → 성공 시 bcrypt로 자동 마이그레이션   │      │
  │                            │                          │ │    → UPDATE users SET password=bcrypt   │      │
  │                            │                          │ │                                         │      │
  │                            │                          │ │ 2. bcrypt 해시인 경우                    │      │
  │                            │                          │ │    → bcrypt.checkpw(pw, stored_hash)    │      │
  │                            │                          │ └─────────────────────────────────────────┘      │
  │                            │                          │                          │                       │
  │                            │                          │ _create_token(uid, role)  │                       │
  │                            │                          │ JWT 생성                  │                       │
  │                            │                          │                          │                       │
  │                            │<─────────────────────────│                          │                       │
  │                            │ {token, user{id,name,role}}                         │                       │
  │<───────────────────────────│                          │                          │                       │
```

##### JWT 토큰 구조 상세

```
┌──────────────────────────────────────────────────────────────┐
│                      JWT 토큰 구조                            │
├──────────────┬───────────────────────┬───────────────────────┤
│   Header     │      Payload          │     Signature         │
│  (Base64)    │     (Base64)          │     (Base64)          │
├──────────────┼───────────────────────┼───────────────────────┤
│ {            │ {                     │ HMAC-SHA256(          │
│  "alg":"HS256│  "user_id": "admin",  │   base64(header) +   │
│  "typ":"JWT" │  "role": "admin",     │   "." +              │
│ }            │  "iat": 1710000000,   │   base64(payload),   │
│              │  "exp": 1710028800    │   SECRET_KEY          │
│              │ }                     │ )                     │
└──────────────┴───────────────────────┴───────────────────────┘

iat: 토큰 발행 시각 (Unix timestamp)
exp: 만료 시각 (iat + JWT_EXPIRY_HOURS * 3600, 기본 8시간)
SECRET_KEY: 환경변수 JWT_SECRET (미설정 시 랜덤 생성, 재시작 시 변경됨)
```

##### JWT 검증 흐름 (모든 인증 필요 API 공통)

```
API 요청 도착
    │
    ▼
auth_deps.auth_required() [FastAPI Depends]
    │
    ▼
mes_auth.require_auth(request)
    │
    ├─ Authorization 헤더 추출
    │  "Bearer eyJhbGciOi..." → "eyJhbGciOi..."
    │
    ▼
mes_auth._verify_token(token)
    │
    ├─ jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    │
    ├─ 성공 → payload dict 반환
    │         {"user_id": "admin", "role": "admin", "iat": ..., "exp": ...}
    │
    ├─ ExpiredSignatureError → None 반환
    │   → require_auth()가 {"error": "인증이 필요합니다", "_status": 401} 반환
    │   → auth_deps.py가 HTTPException(401) 발생
    │
    └─ InvalidTokenError → None 반환 (위조/변조된 토큰)
        → 동일하게 401 처리
```

##### 권한 체크 메커니즘 (Role-Based Access Control)

```
역할 계층:
┌─────────┬──────────────────────────────────────────┐
│  역할   │ 허용 범위                                 │
├─────────┼──────────────────────────────────────────┤
│ admin   │ 모든 기능 + 사용자 관리/승인/권한 변경     │
│ manager │ 모든 비즈니스 기능 읽기/쓰기               │
│ worker  │ 작업 관련 기능 읽기/쓰기                   │
│ viewer  │ 조회 전용                                 │
└─────────┴──────────────────────────────────────────┘

인증 의존성 체인:
┌─────────────────────┐     ┌──────────────────────┐
│ auth_required        │     │ admin_required        │
│ (모든 인증 API)       │     │ (관리자 전용 API)      │
│                     │     │                      │
│ require_auth() 호출  │     │ require_auth() 호출   │
│ → payload 반환       │     │ → role=="admin" 검증  │
│ → 실패 시 401        │     │ → 실패 시 403         │
└─────────────────────┘     └──────────────────────┘

메뉴별 세분화 권한 (user_permissions 테이블):
- user_id, menu, can_read, can_write
- FN-003: GET /api/auth/permissions/{user_id}로 조회
- 현재는 라우터 레벨에서 admin/auth 2단계만 적용
- 메뉴별 세분화는 프론트엔드에서 UI 렌더링 제어에 활용
```

##### 계정 보안 (NFR-013, security.py)

```
로그인 실패 추적 흐름:

실패 1회 → _login_failures[uid].append(timestamp)
실패 2회 → 동일
  ...
실패 5회 → _locked_accounts[uid] = now + 15분
           → "계정이 잠겼습니다. 15분 후 다시 시도해주세요."

잠금 해제 조건:
  (1) 15분 경과 → 다음 로그인 시도 시 자동 해제
  (2) 로그인 성공 → 실패 카운터 + 잠금 모두 초기화

실패 윈도우: 30분 이내의 실패만 카운트 (오래된 실패는 cutoff로 제거)

주의: 메모리 기반이므로 Pod 재시작 시 잠금 상태 초기화됨
```

### 3.4 API Pod 시작 시퀀스

API Pod는 ConfigMap 방식이므로 컨테이너 시작 시 다음 과정이 실행됩니다:

```bash
# mes-api.yaml의 args:
mkdir -p /app/api_modules &&
cp /mnt/*.py /app/api_modules/ &&         # ConfigMap에서 소스 복사
mv /app/api_modules/app.py /app/app.py && # app.py를 상위로 이동
touch /app/api_modules/__init__.py &&     # __init__.py 생성
pip install --cache-dir /pip-cache fastapi uvicorn psycopg2-binary kubernetes pydantic psutil &&
python /app/app.py                         # 서버 기동 (port 80)
```

> **v5.4 최적화**: pip 캐시를 hostPath 볼륨(`/mnt/pip-cache` → Pod 내 `/pip-cache`)으로 마운트하여 재기동 시 패키지 다운로드를 생략합니다. 최초 기동 시에만 1~2분 소요됩니다.

### 3.5 비즈니스 로직 상세 동작

#### 3.5.1 BOM 전개/역전개 알고리즘 (mes_bom.py)

##### BOM 전개 (explode_bom) — 재귀적 하향 탐색

완제품에서 시작하여 모든 하위 자재와 소요량을 트리 구조로 계산합니다.

```
explode_bom("PROD-001", qty=10)

알고리즘: _explode(parent, parent_qty, level)

Level 0: PROD-001 (수량: 10)
    │
    ├─ Level 1: SEMI-001 (qty_per_unit=2, loss_rate=5%)
    │  │  required_qty = 2 × 10 × (1 + 5/100) = 21.0
    │  │
    │  ├─ Level 2: RAW-001 (qty_per_unit=3, loss_rate=2%)
    │  │  required_qty = 3 × 21.0 × (1 + 2/100) = 64.26
    │  │
    │  └─ Level 2: RAW-002 (qty_per_unit=1, loss_rate=0%)
    │     required_qty = 1 × 21.0 × (1 + 0/100) = 21.0
    │
    └─ Level 1: SEMI-002 (qty_per_unit=1, loss_rate=3%)
       required_qty = 1 × 10 × (1 + 3/100) = 10.3
       │
       └─ Level 2: RAW-003 (qty_per_unit=4, loss_rate=1%)
          required_qty = 4 × 10.3 × (1 + 1/100) = 41.61

소요량 계산 공식:
  required_qty = qty_per_unit × parent_qty × (1 + loss_rate / 100)

재귀 종료 조건: 해당 parent_item에 child_item이 없으면 빈 리스트 반환
순환참조 방지: create_bom() 시 _check_circular()로 사전 차단
```

##### BOM 역전개 (where_used) — 재귀적 상향 탐색

특정 자재가 어떤 상위 품목에 사용되는지 역추적합니다.

```
where_used("RAW-001")

알고리즘: _walk_up(code, level)

RAW-001
    │
    ├─ Level 1: SEMI-001 (직접 상위)
    │  SELECT parent_item FROM bom WHERE child_item = 'RAW-001'
    │
    └─ Level 2: PROD-001 (간접 상위)
       SELECT parent_item FROM bom WHERE child_item = 'SEMI-001'

순환 방지: visited set으로 이미 방문한 노드 스킵
결과: [{level:1, parent_item:"SEMI-001"}, {level:2, parent_item:"PROD-001"}]
```

##### 순환참조 검사 (_check_circular)

```
BOM 등록 시 순환참조 체크:

_check_circular(parent="A", child="C")

1. child "C"에서 시작
2. C의 하위 자재 조회 (SELECT child_item FROM bom WHERE parent_item = 'C')
3. 각 하위 자재에 대해 재귀 탐색
4. 탐색 중 parent "A"를 발견하면 → True (순환 감지, 등록 거부)
5. visited set으로 이미 방문한 노드 스킵 → 무한루프 방지
6. 모든 경로에서 "A"를 찾지 못하면 → False (등록 허용)
```

#### 3.5.2 생산관리 상태 전이 (mes_work.py)

##### 생산계획 → 작업지시 → 실적의 상태 전이 다이어그램

```
┌──────────────────────────────────────────────────────────────┐
│                  생산계획 (production_plans) 상태              │
│                                                              │
│  ┌──────┐  작업지시 생성   ┌──────────┐                       │
│  │ WAIT │ ───────────────> │ PROGRESS │                       │
│  └──────┘                  └──────────┘                       │
│                                                              │
│  * create_work_order() 시 자동으로 WAIT → PROGRESS 전이       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  작업지시 (work_orders) 상태                   │
│                                                              │
│  ┌──────┐  실적등록/명시적전이  ┌─────────┐  실적완료   ┌──────┐│
│  │ WAIT │ ─────────────────> │ WORKING │ ──────────> │ DONE ││
│  └──────┘                    └─────────┘             └──────┘│
│                                    │                         │
│                                    │ 보류                    │
│                                    ▼                         │
│                               ┌──────┐                       │
│                               │ HOLD │                       │
│                               └──┬───┘                       │
│                                  │ 재개                      │
│                                  ▼                           │
│                             ┌─────────┐                      │
│                             │ WORKING │ (→ DONE 가능)         │
│                             └─────────┘                      │
│                                                              │
│  유효한 상태 전이 (VALID_TRANSITIONS):                         │
│  WAIT    → [WORKING]                                         │
│  WORKING → [DONE, HOLD]                                      │
│  HOLD    → [WORKING]                                         │
│  DONE    → [] (최종 상태, 변경 불가)                            │
└──────────────────────────────────────────────────────────────┘
```

##### 실적 등록 시 자동 상태 전이 (create_work_result)

```
create_work_result(data) 내부 처리 흐름:

Step 1: 작업지시 상태 확인
  ├─ DONE → 에러 ("이미 완료된 작업지시")
  ├─ WAIT → 자동으로 WORKING으로 전이 (UPDATE SET status='WORKING')
  └─ WORKING/HOLD → 그대로 진행

Step 2: 실적 INSERT
  INSERT INTO work_results (wo_id, good_qty, defect_qty, ...)

Step 3: 완료 판정
  SELECT plan_qty, SUM(good_qty) FROM work_orders + work_results
  │
  ├─ SUM(good_qty) >= plan_qty
  │   → WORKING → DONE (자동 완료)
  │   ※ WAIT → DONE 직접 전이는 불가 (Step 1에서 WORKING으로 먼저 전이)
  │
  └─ SUM(good_qty) < plan_qty
      → 상태 유지, progress_pct 계산하여 반환

모든 작업은 단일 트랜잭션 내에서 실행 (conn.commit() / conn.rollback())
```

#### 3.5.3 재고 트랜잭션 처리 (mes_inventory.py)

##### 입고 처리 (inventory_in)

```
inventory_in(data) 흐름:

1. LOT 번호 자동 생성: LOT-{YYYYMMDD}-{SEQ:03d}
2. 전표번호 생성: IN-{YYYYMMDD}-{SEQ:03d}
3. UPSERT (INSERT ... ON CONFLICT DO UPDATE):
   - (item_code, lot_no, warehouse) 조합이 기존에 있으면 qty 누적
   - 없으면 신규 INSERT
4. inventory_transactions에 이력 INSERT (tx_type='IN')
5. 캐시 무효화 (cache_delete("inventory:*"), cache_delete("items:*"))
6. COMMIT

※ 동시성 제어: PostgreSQL의 ON CONFLICT + row-level lock으로 처리
```

##### 출고 처리 (inventory_out) — FIFO 로직

```
inventory_out(data) 흐름:

1. 유효성 검증 (품목코드 필수, 수량 > 0, 출고유형 ∈ {OUT,SHIP,SCRAP,RETURN})
2. 전표번호 생성: OUT-{YYYYMMDD}-{SEQ:03d}

3. FIFO 출고 알고리즘:
   ┌─────────────────────────────────────────────────────┐
   │ SELECT inv_id, lot_no, qty, warehouse               │
   │ FROM inventory                                      │
   │ WHERE item_code = %s AND qty > 0                    │
   │ ORDER BY created_at ASC  ← 오래된 LOT부터 (FIFO)     │
   └─────────────────────────────────────────────────────┘

   remaining = 출고 요청 수량 (예: 50)

   LOT-001 (qty=30) → use=30, remaining=20
     UPDATE inventory SET qty = qty - 30 WHERE inv_id = ...
   LOT-002 (qty=25) → use=20, remaining=0
     UPDATE inventory SET qty = qty - 20 WHERE inv_id = ...

   ※ remaining > 0 (재고 부족) → conn.rollback() + 에러 반환
      "재고 부족. 부족 수량: {remaining}"

4. 트랜잭션 이력 INSERT (tx_type=out_type)
5. COMMIT
6. 캐시 무효화
```

```
FIFO 출고 시퀀스 다이어그램:

Handler              inventory 테이블             inventory_transactions
  │                       │                              │
  │ SELECT (FIFO순)       │                              │
  │──────────────────────>│                              │
  │  LOT-001: 30개        │                              │
  │  LOT-002: 25개        │                              │
  │<──────────────────────│                              │
  │                       │                              │
  │ UPDATE qty -= 30      │                              │
  │──────────────────────>│                              │
  │ UPDATE qty -= 20      │                              │
  │──────────────────────>│                              │
  │                       │                              │
  │ INSERT tx (slip, qty, type)                          │
  │─────────────────────────────────────────────────────>│
  │                       │                              │
  │ COMMIT                │                              │
```

#### 3.5.4 품질검사 판정 로직 (mes_quality.py)

##### 검사 판정 자동화 (create_inspection)

```
create_inspection(data) 판정 흐름:

1. 품목의 품질 기준 로드
   SELECT check_name, check_type, min_value, max_value
   FROM quality_standards WHERE item_code = %s

2. 각 검사 항목별 판정:

   ┌────────────┬─────────────────────────────────────────┐
   │ check_type │ 판정 로직                                │
   ├────────────┼─────────────────────────────────────────┤
   │ NUMERIC    │ min_value ≤ measured_value ≤ max_value  │
   │            │ → 범위 벗어나면 FAIL                     │
   ├────────────┼─────────────────────────────────────────┤
   │ TEXT       │ value.upper() == std_value.upper()       │
   │            │ → 불일치하면 FAIL                        │
   ├────────────┼─────────────────────────────────────────┤
   │ VISUAL     │ value ∈ {"PASS","OK","합격","양호","정상"}│
   │            │ → 그 외 값이면 FAIL                      │
   │            │ → value=None이면 명시적 judgment 사용     │
   ├────────────┼─────────────────────────────────────────┤
   │ 기타/미등록 │ 명시적 judgment 필드 사용                │
   └────────────┴─────────────────────────────────────────┘

3. 종합 판정:
   - 전체 항목 중 하나라도 FAIL → overall = "FAIL"
   - 모두 PASS → overall = "PASS"
   - fail_items 목록으로 불합격 항목 반환

4. DB 저장:
   INSERT INTO inspections (judgment=overall)
   INSERT INTO inspection_details (각 항목별 judgment)
   COMMIT
```

### 3.6 AI 모듈 동작 원리

#### 3.6.1 수요예측 (mes_ai_prediction.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                    수요예측 파이프라인                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 데이터 수집                                                  │
│     ├─ shipments 테이블 존재 확인                                │
│     ├─ 있으면: 월별 출하 수량 집계 (GROUP BY month)               │
│     └─ 없으면: work_results의 good_qty를 수요 대리 변수로 사용    │
│                                                                 │
│  2. 데이터 검증                                                  │
│     └─ 최소 3개 데이터 포인트 필요 (미달 시 에러 반환)             │
│                                                                 │
│  3. 모델 선택 분기                                               │
│     ├─ Prophet 설치 + 4개 이상 데이터                             │
│     │   └─ _prophet_predict()                                    │
│     └─ 그 외                                                     │
│         └─ _linear_predict() (선형 회귀 fallback)                │
│                                                                 │
│  4-A. Prophet 경로:                                              │
│     ┌────────────────────────────────────────────┐               │
│     │ DataFrame 구성: ds(날짜), y(수량)           │               │
│     │ ModelCache.get_or_train() — 캐시된 모델 재사용│              │
│     │ Prophet 설정:                               │               │
│     │   yearly_seasonality=True                   │               │
│     │   seasonality_mode='multiplicative'         │               │
│     │ make_future_dataframe(periods=N, freq='MS') │               │
│     │ predict() → yhat, yhat_lower, yhat_upper    │               │
│     │ → 계절성 분해 컴포넌트 포함                  │               │
│     └────────────────────────────────────────────┘               │
│                                                                 │
│  4-B. 선형 회귀 경로 (fallback):                                 │
│     ┌────────────────────────────────────────────┐               │
│     │ 최소자승법: y = slope × x + intercept       │               │
│     │ slope = (n·Σxy - Σx·Σy) / (n·Σx² - (Σx)²)│               │
│     │ intercept = (Σy - slope·Σx) / n            │               │
│     │ RMSE 계산 → 95% 신뢰구간 (±1.96×RMSE)      │               │
│     │ → lower_bound, upper_bound 포함             │               │
│     └────────────────────────────────────────────┘               │
│                                                                 │
│  5. 응답: {model, predictions[{month, qty, lower, upper}]}      │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.6.2 불량예측 (mes_defect_predict.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                    불량예측 파이프라인                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  입력: {temperature, pressure, speed, humidity}                  │
│                                                                 │
│  1. 학습 데이터 로드                                             │
│     SELECT temperature, pressure, speed, humidity,              │
│            defect_count, total_count                             │
│     FROM defect_history LIMIT 500                               │
│                                                                 │
│  2. 모델 선택 분기                                               │
│     ├─ XGBoost 설치 + 10개 이상 학습 데이터                       │
│     │   └─ _xgboost_predict()                                    │
│     └─ 그 외                                                     │
│         └─ _threshold_predict() (임계값 기반 fallback)           │
│                                                                 │
│  3-A. XGBoost 경로:                                              │
│     ┌────────────────────────────────────────────┐               │
│     │ Feature Engineering:                       │               │
│     │   X = [temp, pressure, speed, humidity]    │               │
│     │   y = defect_count / total_count (불량률)   │               │
│     │                                            │               │
│     │ XGBRegressor 학습:                          │               │
│     │   n_estimators=100, max_depth=4, lr=0.1    │               │
│     │   objective='reg:squarederror'             │               │
│     │   ModelCache.get_or_train() 캐시            │               │
│     │                                            │               │
│     │ 예측: model.predict(X_input) → 불량률       │               │
│     │                                            │               │
│     │ SHAP 해석:                                  │               │
│     │   TreeExplainer(model)                     │               │
│     │   shap_values → 각 feature의 기여도         │               │
│     │   ※ SHAP 실패 시 feature_importances_ 사용  │               │
│     │                                            │               │
│     │ 리스크 판정:                                │               │
│     │   >10% → HIGH (즉시 파라미터 조정)          │               │
│     │   >5%  → MEDIUM (모니터링 강화)             │               │
│     │   ≤5%  → LOW (현재 설정 유지)               │               │
│     └────────────────────────────────────────────┘               │
│                                                                 │
│  3-B. 임계값 기반 경로 (fallback):                               │
│     ┌────────────────────────────────────────────┐               │
│     │ 학습데이터 5건 이상 → 동적 임계값 (평균±2σ)  │               │
│     │ 미만 → 하드코딩 임계값:                     │               │
│     │   temperature: 180~220 (weight=0.4)        │               │
│     │   pressure:    8~12   (weight=0.3)         │               │
│     │   speed:       45~55  (weight=0.2)         │               │
│     │   humidity:    50~70  (weight=0.1)         │               │
│     │                                            │               │
│     │ 범위 이탈 시 weight만큼 defect_prob 가산    │               │
│     │ 최대 1.0 (100%)                            │               │
│     └────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.6.3 고장예측 (mes_equipment.py — predict_failure)

```
┌─────────────────────────────────────────────────────────────────┐
│                    설비 고장예측 파이프라인                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  입력: {equip_code, sensor: {vibration, temperature, current}}  │
│                                                                 │
│  1. 센서 데이터 저장                                             │
│     INSERT INTO equip_sensors (vibration, temperature, current) │
│                                                                 │
│  2. 이력 데이터 로드                                             │
│     SELECT vibration, temperature, current_amp                  │
│     FROM equip_sensors WHERE equip_code = %s                    │
│     ORDER BY recorded_at DESC LIMIT 200                         │
│                                                                 │
│  3. 모델 선택 분기                                               │
│     ├─ scikit-learn 설치 + 10개 이상 이력                         │
│     │   └─ _iforest_predict()                                    │
│     └─ 그 외                                                     │
│         └─ _rule_based_predict() (규칙 기반 fallback)            │
│                                                                 │
│  4-A. IsolationForest 경로:                                      │
│     ┌────────────────────────────────────────────┐               │
│     │ IsolationForest 학습:                      │               │
│     │   n_estimators=100, contamination=0.1      │               │
│     │   ModelCache.get_or_train() 캐시            │               │
│     │                                            │               │
│     │ 이상 점수 계산:                             │               │
│     │   raw_score = clf.decision_function(input)  │               │
│     │   anomaly_score = max(0, min(1, 0.5-raw))  │               │
│     │   ※ sklearn은 낮을수록 이상 → 변환 필요     │               │
│     │                                            │               │
│     │ 기여도 분석 (SHAP 대체):                    │               │
│     │   z_score = |input - mean| / std           │               │
│     │   contribution = (z_i / Σz) × anomaly      │               │
│     │                                            │               │
│     │ 잔여 수명 추정:                             │               │
│     │   remaining_hours = (1 - anomaly) × 500    │               │
│     └────────────────────────────────────────────┘               │
│                                                                 │
│  4-B. 규칙 기반 경로 (fallback):                                 │
│     ┌────────────────────────────────────────────┐               │
│     │ 임계값:                                    │               │
│     │   vibration > 3.0   → (val-3)/3 × 0.40    │               │
│     │   temperature > 60  → (val-60)/30 × 0.35  │               │
│     │   current > 15      → (val-15)/10 × 0.25  │               │
│     │                                            │               │
│     │ 판정:                                      │               │
│     │   >70% → "즉시 점검 필요"                   │               │
│     │   >40% → "48시간 내 점검 권장"              │               │
│     │   ≤40% → "정상 범위"                        │               │
│     └────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.6.4 Graceful Fallback 메커니즘

모든 AI 모듈은 라이브러리 미설치 시에도 정상 동작하는 fallback 패턴을 따릅니다.

```
┌─────────────────────────────────────────────────────────────────┐
│  import 시점 분기 (모듈 로딩 시 1회 실행)                         │
│                                                                 │
│  try:                                                           │
│      from prophet import Prophet    # 또는 xgboost, sklearn     │
│      HAS_LIBRARY = True                                         │
│  except ImportError:                                            │
│      HAS_LIBRARY = False                                        │
│      log.warning("... falling back to ...")                     │
│                                                                 │
│  예측 함수 내부:                                                 │
│  if HAS_LIBRARY and len(training_data) >= THRESHOLD:            │
│      return _ml_predict(...)     # ML 모델 사용                  │
│  else:                                                          │
│      return _fallback_predict(...)  # 통계/규칙 기반             │
│                                                                 │
│  모듈별 fallback 구성:                                           │
│  ┌─────────────────┬──────────────┬──────────────┬────────────┐ │
│  │ 모듈            │ ML 모델      │ Fallback      │ 최소 데이터│ │
│  ├─────────────────┼──────────────┼──────────────┼────────────┤ │
│  │ 수요예측        │ Prophet      │ 선형 회귀     │ 4건 / 3건  │ │
│  │ 불량예측        │ XGBoost+SHAP │ 임계값 점수   │ 10건       │ │
│  │ 고장예측        │ IsolationForest│ 규칙 기반   │ 10건       │ │
│  └─────────────────┴──────────────┴──────────────┴────────────┘ │
│                                                                 │
│  ModelCache: AI 모델을 메모리에 캐시하여 재학습 방지              │
│  (ai_model_cache.py의 ModelCache.get_or_train())                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.7 DB 트랜잭션 처리 패턴

#### 3.7.1 데이터베이스 연결 (database.py)

```
┌─────────────────────────────────────────────────────────────────┐
│  ThreadedConnectionPool (psycopg2)                               │
│                                                                 │
│  _pool = ThreadedConnectionPool(                                │
│      minconn=2,       ← 최소 유지 커넥션                         │
│      maxconn=10,      ← 최대 커넥션 (동시 처리 상한)              │
│      dsn=DATABASE_URL,                                          │
│      connect_timeout=5  ← 연결 타임아웃 5초                      │
│  )                                                              │
│                                                                 │
│  Lazy Initialization: 첫 요청 시 풀 생성 (_get_pool())          │
│  풀 닫힘 감지: _pool.closed 체크 → 자동 재생성                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.7.2 두 가지 커넥션 사용 패턴

```
패턴 A: 수동 관리 (트랜잭션 제어 필요 시)
───────────────────────────────────────
conn = get_conn()           # 풀에서 커넥션 획득
try:
    cursor = conn.cursor()
    cursor.execute(SQL1, params)
    cursor.execute(SQL2, params)
    conn.commit()           # 모든 쿼리 성공 시 커밋
    cursor.close()
except Exception:
    conn.rollback()         # 하나라도 실패 시 전체 롤백
finally:
    release_conn(conn)      # 반드시 풀에 반환 (미반환 시 풀 고갈)

사용처: mes_auth.login(), mes_work.create_work_result(),
        mes_inventory.inventory_out() 등 (다중 쿼리 트랜잭션)


패턴 B: Context Manager (단순 조회/단일 쿼리)
────────────────────────────────────────────
with db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(SQL, params)
    rows = cursor.fetchall()
    cursor.close()
    # yield 후 finally에서 자동 release_conn()

사용처: mes_bom.list_bom(), mes_bom.explode_bom() 등 (읽기 전용)


패턴 C: query_db() 유틸 (가장 간단한 형태)
──────────────────────────────────────────
rows = query_db("SELECT * FROM items WHERE category=%s", ("RAW",))
# fetch=True: SELECT → list of RealDictRow 반환
# fetch=False: INSERT/UPDATE → commit + True 반환
# 에러 시: rollback + [] 반환

내부 동작:
  conn = get_conn()
  cursor(cursor_factory=RealDictCursor)  ← 결과를 dict로 반환
  execute(sql, params)
  fetch? → fetchall() : commit()
  release_conn(conn)
```

#### 3.7.3 커서 타입별 차이

```
┌──────────────┬──────────────────────────────────────────────┐
│ 커서 타입     │ 반환 형태                                     │
├──────────────┼──────────────────────────────────────────────┤
│ 기본 cursor() │ tuple: (val1, val2, ...) → r[0], r[1]로 접근│
│              │ 사용처: mes_auth, mes_work, mes_quality 등   │
├──────────────┼──────────────────────────────────────────────┤
│ RealDictCursor│ dict: {"col": val, ...} → r["col"]로 접근  │
│              │ 사용처: query_db() 유틸                       │
│              │ DictCursor와 차이: RealDict는 순수 dict 반환 │
│              │ DictCursor는 OrderedDict 반환               │
└──────────────┴──────────────────────────────────────────────┘

현재 코드에서는 대부분 기본 cursor() + tuple 인덱싱을 사용합니다.
query_db()만 RealDictCursor를 사용합니다.
```

#### 3.7.4 SQL 인젝션 방어 (파라미터 바인딩)

```
┌─────────────────────────────────────────────────────────────┐
│  psycopg2 파라미터 바인딩 원리                                │
│                                                             │
│  ✅ 안전한 방식 (전체 코드에서 사용):                         │
│  cursor.execute(                                            │
│      "SELECT * FROM users WHERE user_id = %s", (uid,)       │
│  )                                                          │
│  → psycopg2가 내부적으로 값을 이스케이프 처리                 │
│  → uid = "'; DROP TABLE users; --" 입력해도 안전              │
│  → %s는 Python 문자열 포매팅이 아닌 DB 드라이버 바인딩        │
│                                                             │
│  ⚠️ 동적 SQL 사용 부분 (f-string):                          │
│  일부 모듈에서 WHERE 절을 동적 구성할 때 f-string을 사용하나  │
│  값 자체는 항상 %s 파라미터로 전달:                           │
│                                                             │
│  where = []                                                 │
│  params = []                                                │
│  if status:                                                 │
│      where.append("wo.status = %s")  ← 컬럼명만 하드코딩    │
│      params.append(status)           ← 값은 파라미터 바인딩  │
│  where_sql = "WHERE " + " AND ".join(where)                 │
│  cursor.execute(f"SELECT ... {where_sql}", params)          │
│                                                             │
│  추가 방어: mes_auth._sanitize_id()로 user_id 패턴 검증     │
│  정규식: ^[a-zA-Z0-9_]{3,30}$ (영문/숫자/언더스코어만 허용)  │
└─────────────────────────────────────────────────────────────┘
```

### 3.8 에러 핸들링 메커니즘

#### 3.8.1 FastAPI 예외 처리 계층 (app.py)

```
예외 처리 우선순위 (위에서 아래로):

┌──────────────────────────────────────────────────────────────┐
│  1. HTTPException 핸들러                                     │
│     @app.exception_handler(HTTPException)                    │
│     → auth_deps.py에서 발생한 401/403 등                     │
│     → {"error": exc.detail} 반환                             │
│                                                              │
│  2. 404 Not Found 핸들러                                     │
│     @app.exception_handler(404)                              │
│     → 존재하지 않는 경로 요청 시                              │
│     → {"error": "요청한 리소스를 찾을 수 없습니다."} 반환     │
│                                                              │
│  3. Rate Limit 핸들러                                        │
│     app.add_exception_handler(RateLimitExceeded, ...)        │
│     → slowapi 라이브러리의 기본 핸들러                        │
│     → 429 Too Many Requests 반환                             │
│                                                              │
│  4. 전역 예외 핸들러 (catch-all)                              │
│     @app.exception_handler(Exception)                        │
│     → 모든 미처리 예외를 캡처                                 │
│     → log.error()로 스택 트레이스 기록 (서버 로그에만)         │
│     → 클라이언트에는 스택 트레이스 노출 안 함 (KISA 49 준수)  │
│     → {"error": "서버 내부 오류가 발생했습니다."} 반환 (500)  │
└──────────────────────────────────────────────────────────────┘
```

#### 3.8.2 비즈니스 로직 에러 패턴 (mes_*.py)

```
모든 비즈니스 모듈은 동일한 에러 반환 패턴을 따릅니다:

async def some_function(data: dict) -> dict:
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}  ← DB 연결 실패

        # 비즈니스 유효성 검증
        if not valid:
            return {"error": "구체적인 한국어 에러 메시지"}  ← 유효성 실패

        # SQL 실행
        cursor.execute(...)
        conn.commit()
        return {"success": True, ...}  ← 성공

    except ValueError as ve:
        return {"error": str(ve)}  ← 입력값 검증 실패

    except Exception:
        if conn:
            conn.rollback()  ← 예외 시 트랜잭션 롤백
        return {"error": "처리 중 오류가 발생했습니다."}  ← 일반 에러

    finally:
        if conn:
            release_conn(conn)  ← 커넥션 반환 보장

※ 주의: 비즈니스 에러는 HTTP 200으로 반환됩니다 (error 키 유무로 판별).
  HTTP 4xx/5xx는 인증 실패(auth_deps.py)와 시스템 에러(global handler)에서만 발생.
```

#### 3.8.3 프론트엔드 에러 처리 (App.jsx)

```
프론트엔드 에러 처리 흐름:

1. API 호출 (axios)
   axios.post('/api/items', data, {
       headers: { Authorization: 'Bearer ' + token }
   })

2. 응답 처리 분기:
   .then(res => {
       if (res.data.error) {
           // 비즈니스 에러 (HTTP 200이지만 error 키 존재)
           showNotification(res.data.error, 'error')
       } else {
           // 성공
           showNotification('처리 완료', 'success')
       }
   })
   .catch(err => {
       // HTTP 에러 (401, 403, 500 등)
       if (err.response?.status === 401) {
           // 토큰 만료 → 재로그인 유도
       }
       showNotification('서버 오류', 'error')
   })

3. 전역 axios 인터셉터 (설정 시):
   axios.interceptors.response.use(
       response => response,
       error => {
           if (error.response?.status === 401) {
               // 토큰 갱신 또는 로그아웃 처리
           }
           return Promise.reject(error)
       }
   )
```

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

## 8. CI/CD 파이프라인

### 8.1 개요

Jenkins 기반 CI/CD 파이프라인이 `Jenkinsfile`에 정의되어 있습니다.
ConfigMap 기반 배포 방식에 맞춰 작성되었으며, `init.sh`와 동일한 배포 흐름을 따릅니다.

### 8.2 파이프라인 단계

```
Clean → Lint → Test → Build FE → Deploy DB → Deploy Keycloak
  → Deploy Backend → Deploy Frontend → Verify & Configure
```

| 단계 | 내용 | 도구 |
|------|------|------|
| **Lint** | Python (black, flake8, isort) + JS (eslint) | pip, npx |
| **Test** | pytest (25개 테스트) + npm test | pytest, vitest |
| **Build FE** | `npm run build` | Vite |
| **Deploy DB** | `infra/postgres-pv.yaml` + `postgres.yaml` + Secret | kubectl |
| **Deploy Keycloak** | `infra/keycloak.yaml` + `setup-keycloak.sh` | kubectl, curl |
| **Deploy Backend** | ConfigMap(`api-code`) + `infra/mes-api.yaml` + CORS 치환 | kubectl, sed |
| **Deploy Frontend** | ConfigMap(`frontend-build`) + `infra/mes-frontend.yaml` | kubectl |
| **Verify** | rollout status + HTTP 200 확인 | kubectl, curl |

### 8.3 테스트 커버리지

현재 25개 테스트가 인프라/네트워크/AI 엔드포인트를 커버합니다.
비즈니스 API(items, bom, plans 등)는 DB 의존성으로 인해 미커버 상태입니다.

> 상세 분석: `doc/CICD_REVIEW.md` 참조

---

## 9. 주의사항 및 알려진 이슈

### 9.1 Keycloak 24.x VERIFY_PROFILE 이슈

Keycloak 24.x에서는 `VERIFY_PROFILE` Required Action이 기본 활성화됩니다.
사용자에게 `lastName`, `email` 필드가 없으면 로그인 시 "Account is not fully set up" 오류가 발생합니다.

**해결**: `setup-keycloak.sh`에서 자동 처리됩니다.
- VERIFY_PROFILE Required Action 비활성화
- 사용자 생성 시 `lastName`, `email`, `emailVerified=true` 포함

수동 해결이 필요한 경우:
```bash
bash /root/MES_PROJECT/setup-keycloak.sh
```

### 9.2 반드시 알아야 할 사항

| # | 주의사항 | 상세 |
|---|----------|------|
| 1 | **swap이 켜져 있으면 kubelet이 실패** | VM 재시작 시 swap이 다시 활성화됨. `init.sh`가 `swapoff -a`로 자동 처리하지만, 수동으로 kubectl 사용 시 반드시 확인 |
| 2 | **Cilium eBPF가 VM 재시작 후 초기화 실패 가능** | eBPF 맵이 리셋되면서 Pod 네트워크가 불통. `init.sh`가 Cilium Pod를 강제 재시작하여 자동 복구 |
| 3 | **API Pod는 ConfigMap 방식이라 pip install이 매번 실행** | v5.4부터 hostPath 캐시(`/mnt/pip-cache`)를 사용하여 재기동 시 빠름. 최초 기동만 1~2분 소요 |
| 4 | **프론트엔드는 단일 App.jsx 파일** | ~88KB 단일 파일이므로 변경 시 전체 빌드 필요. 컴포넌트 분리가 되어 있지 않음 |
| 5 | **레거시 모듈이 ConfigMap에 포함** | `app.py`에서 import하지 않는 레거시 모듈들도 ConfigMap에 포함됨. 삭제해도 무방하나 참고용으로 유지 중 |
| 6 | **DB 데이터는 hostPath PV 사용** | `/mnt/data`에 저장. VM 삭제 시 데이터 유실. 백업 필요 시 `pg_dump` 사용 |
| 7 | **CORS_ORIGINS에 __CORS_ORIGINS__ 플레이스홀더** | `mes-api.yaml`에 하드코딩되지 않고, `init.sh`가 `sed`로 치환. 수동 `kubectl apply` 시 주의 |

### 9.3 알려진 제한사항

| # | 제한사항 | 영향 |
|---|----------|------|
| 1 | 단일 노드 클러스터 | HA 구성 없음. 노드 장애 시 전체 시스템 다운 |
| 2 | TLS/HTTPS 미적용 | 모든 통신이 HTTP. 운영 환경에서는 인증서 설정 필요 |
| 3 | AI 모델이 통계 기반 | 별도 ML 프레임워크 없이 선형 회귀/임계값 비교 사용 |
| 4 | ConfigMap 크기 제한 | K8s ConfigMap은 1MB 제한. 프론트엔드 빌드 결과물이 커지면 문제 발생 가능 |
| 5 | keycloak-js가 프론트엔드에 직접 통합 | 토큰 갱신/만료 처리가 main.jsx에 의존 |

---

## 10. 트러블슈팅 가이드

### 10.1 K8s API 서버 연결 실패

```bash
# kubelet 상태 확인
systemctl status kubelet

# swap 비활성화 후 재시작
swapoff -a
systemctl restart kubelet

# 30초 후 확인
kubectl get nodes
```

### 10.2 Pod가 ContainerCreating에서 멈춤

```bash
# Cilium 네트워크 문제 — Pod 재시작
kubectl delete pod -n kube-system -l k8s-app=cilium --force
sleep 10
kubectl get pods
```

### 10.3 API 서버 응답 없음 (502 / Connection Refused)

```bash
# API Pod 로그 확인 — pip install 진행 중일 수 있음
kubectl logs deployment/mes-api --tail=30

# pip install 실패 시 Pod 재시작
kubectl rollout restart deployment mes-api
```

### 10.4 프론트엔드 빈 화면

```bash
# ConfigMap 재생성
cd /root/MES_PROJECT/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend
```

### 10.5 DB 연결 실패

```bash
# PostgreSQL Pod 상태 확인
kubectl get pods -l app=postgres
kubectl logs deployment/postgres --tail=20

# DB 접속 테스트
kubectl exec -it deployment/postgres -- psql -U postgres -d mes_db -c "SELECT 1;"
```

### 10.6 Keycloak 로그인 안 됨

```bash
# Keycloak Pod 상태 확인
kubectl get pods -l app=keycloak
kubectl logs deployment/keycloak --tail=30

# Realm 확인
curl -s http://localhost:30080/realms/mes-realm | python3 -m json.tool

# 재설정 필요 시
bash /root/MES_PROJECT/setup-keycloak.sh
```

### 10.7 전체 시스템 재시작

```bash
# 가장 확실한 방법: init.sh 재실행
sudo bash /root/MES_PROJECT/init.sh
```

### 10.8 상태 확인 명령어 모음

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

## 11. 연락처 및 참고 자료

### 11.1 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 프로젝트명 | 경북대학교 스마트 팩토리 MES |
| 버전 | v5.5 |
| 저장소 경로 | `/root/MES_PROJECT` |
| VM 접속 | `ssh c1_master1@192.168.64.5` → `sudo -s` |

### 11.2 테스트 계정

| 계정 | 비밀번호 | 역할 |
|------|----------|------|
| admin | admin1234 | 시스템 관리자 |
| worker01 | worker1234 | 작업자 |
| viewer01 | viewer1234 | 조회 전용 |

### 11.3 주요 접속 URL

| 서비스 | URL |
|--------|-----|
| 웹 UI | `http://<IP>:30173` |
| API Swagger 문서 | `http://<IP>:30461/docs` |
| Keycloak 관리 콘솔 | `http://<IP>:30080` |

### 11.4 관련 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 아키텍처 문서 | `doc/ARCH.md` | 시스템 구조, 모듈 상세, DB 스키마, API 목록 |
| 시작 가이드 | `doc/HOWTOSTART.md` | VM 부팅 후 시스템 기동 절차 |
| 기여 가이드 | `doc/HOWTOCONTRIBUTE.md` | 개발 환경, 코드 컨벤션, 브랜치 전략, PR 워크플로우 |
| 코드 품질 검토서 | `doc/CODE_REVIEW.md` | PEP8/JS/Shell/K8s 코딩 표준 준수 검토 |
| CI/CD 검토서 | `doc/CICD_REVIEW.md` | CI/CD 파이프라인 구축 현황 및 개선 사항 |
| 사용자 매뉴얼 | `doc/USER_MANUAL.md` | 각 메뉴별 사용 방법 |
| 발표 자료 | `doc/MES_PRESENTATION.md` | Marp 슬라이드 |
| README | `README.md` | 프로젝트 개요 및 빠른 시작 |

### 11.5 기능 코드 매핑 요약 (FN-001 ~ FN-037)

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
**최종 업데이트**: 2026-03-12
