# DEXWEAVER MES Project

## Project Overview
- K8s 기반 클라우드 네이티브 MES (Manufacturing Execution System)
- 경북대학교 스마트 팩토리 프로젝트
- GS인증 표준 준수 (KISA 49, KS X 9003, ISO/IEC 25051)

## Tech Stack
- **Backend**: Python 3.9 FastAPI (app.py:727줄, 46 endpoints)
- **Frontend**: React 19 + Vite + Tailwind CSS 4 (frontend/src/App.jsx:2851줄)
- **DB**: PostgreSQL 15 (db/init.sql:1068줄, 21 tables)
- **Infra**: Kubernetes v1.30+, Cilium eBPF, Jenkins CI/CD
- **Auth**: JWT (PyJWT + bcrypt)
- **AI**: Prophet, XGBoost, scikit-learn (IsolationForest), OR-Tools, SHAP
- **Deploy**: ConfigMap-based (no Docker build needed)

## Key Directories
```
MES_PROJECT/
├── app.py                 # FastAPI main router (46 endpoints)
├── api_modules/           # Backend business logic (28 modules)
│   ├── database.py        # DB 연결 (psycopg2, get_db_connection())
│   ├── mes_auth.py        # FN-001~003: 로그인/회원가입/권한
│   ├── mes_items.py       # FN-004~007: 품목 CRUD
│   ├── mes_bom.py         # FN-008~009: BOM 전개/역전개
│   ├── mes_process.py     # FN-010~012: 공정/라우팅
│   ├── mes_equipment.py   # FN-013~014,032~034: 설비+AI고장예측
│   ├── mes_plan.py        # FN-015~017: 생산계획
│   ├── mes_work.py        # FN-020~024: 작업지시/실적
│   ├── mes_quality.py     # FN-025~027: 품질검사/불량
│   ├── mes_inventory.py   # FN-029~031: 재고 입/출/현황
│   ├── mes_reports.py     # FN-035~037: 통계/AI인사이트
│   ├── mes_ai_prediction.py  # FN-018: 수요예측(Prophet)
│   └── mes_defect_predict.py # FN-028: 불량예측(XGBoost)
├── frontend/src/App.jsx   # React SPA (14 menus, 단일파일)
├── db/init.sql            # DB schema + seed data (21 tables)
├── infra/                 # K8s manifests (7 YAML files)
├── doc/                   # Development docs
│   └── REQ/v6.0/          # v6.0 요구사항 (6개 문서, 95건)
├── research/              # Market research (dev docs와 분리 유지!)
├── init.sh                # One-click startup script
└── env.sh                 # Environment variables
```

## Coding Standards
- **Python**: PEP 8, type hints, Google-style docstrings, snake_case
- **JavaScript**: ESLint, 2-space indent, camelCase, JSDoc
- **Git**: Conventional commits, Korean descriptions OK

## DB Schema (21 tables)
users, user_permissions, items, bom, processes, equipments, routings,
equip_status_log, production_plans, work_orders, work_results,
quality_standards, inspections, inspection_details, defect_codes,
inventory, inventory_transactions, shipments, defect_history,
equip_sensors, ai_forecasts

## Important Rules
- Research docs (research/) ↔ dev docs (doc/) 반드시 분리 유지
- AI modules have graceful fallbacks when libraries unavailable
- All API endpoints require JWT auth except /api/health and /api/auth/login
- 문서/주석은 한국어 OK

---

## Token Optimization Rules (토큰 절약 규칙)

### 1. 파일 탐색 최소화
- **이 CLAUDE.md에 있는 정보는 다시 읽지 마라** — 디렉토리 구조, 모듈 매핑, DB 테이블 목록을 이미 알고 있으므로 탐색 불필요
- 파일 수정 전에만 해당 파일을 Read — 구조 파악 목적의 탐색은 하지 않기
- Agent(Explore)보다 Glob/Grep 직접 사용을 우선 — 단순 검색에 Agent 비용 낭비 금지

### 2. 코드 수정 패턴
- **백엔드 새 기능 추가 시**: `api_modules/` 에 새 모듈 생성 → `app.py`에 import + router 등록
- **프론트엔드 수정**: `frontend/src/App.jsx` 단일 파일 (v6.0에서 분리 예정)
- **DB 스키마 변경**: `db/init.sql` 수정
- **인프라 변경**: `infra/*.yaml` 수정

### 3. 반복 작업 패턴
| 작업 | 수정 파일 | 패턴 |
|:----:|:---------:|:----:|
| API 엔드포인트 추가 | `api_modules/mes_*.py` + `app.py` | 모듈 함수 작성 → app.py에 @app.post/get 데코레이터 |
| DB 테이블 추가 | `db/init.sql` | CREATE TABLE → INSERT seed data |
| 프론트엔드 메뉴 추가 | `frontend/src/App.jsx` | menuItems 배열에 추가 → renderXXX 함수 작성 |
| K8s 리소스 추가 | `infra/*.yaml` | Deployment + Service + ConfigMap |

### 4. 응답 간결화
- 코드 변경 시 변경 사항만 간결하게 설명 — 전체 파일 내용 반복 금지
- 이미 알려진 프로젝트 컨텍스트 재설명 금지
- 선택지 제시 시 3개 이하로 제한

### 5. v6.0 개발 참조
- **Claude 개발 가이드**: `doc/REQ/v6.0/Claude_Development_Guide.md` ← Task 실행 시 이것만 참조!
- 개발계획 (사람용): `doc/REQ/v6.0/Development_Plan.md`
- 요구사항: `doc/REQ/v6.0/Requirements_Specification.md` (95건)
- 기능명세: `doc/REQ/v6.0/Functional_Specification.md` (FN-001~066)
- DB 스키마: `doc/REQ/v6.0/DatabaseSchema.md` (40 tables)
- 인프라: `doc/REQ/v6.0/Infrastructure_Requirements.md`
- 갭 분석: `doc/REQ/v6.0/Gap_Analysis_Report.md`
- 테스트 데이터: `doc/REQ/v6.0/TestData_Generation_Strategy.md`

### 6. Task 실행 방법
- "Task 1-07 실행해줘" → Claude_Development_Guide.md의 해당 섹션 참조하여 코드 작성
- 한 세션에 하나의 Task만 실행
- Task에 명시된 파일만 수정 — 불필요한 탐색 금지
