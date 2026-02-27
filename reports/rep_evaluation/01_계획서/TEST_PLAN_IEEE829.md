# DEXWEAVER MES v4.3 소프트웨어 테스트 계획서 (Software Test Plan)

| 항목 | 내용 |
|------|------|
| **문서 식별자** | TP-DEXWEAVER-MES-2026-001 |
| **작성일** | 2026-02-27 |
| **개정 이력** | Rev 1.0 (최초 작성) |
| **작성자** | QA팀 |
| **승인자** | 프로젝트 관리자 / 품질 보증 책임자 |
| **분류** | 대외비 (Confidential) |

---

## 평가 기준 및 근거 (Evaluation Criteria & Rationale)

> **본 테스트 계획서는 아래의 표준·기준을 적용 근거로 하여 작성되었다.**

### 적용 표준

| 적용 표준 | 조항/절 | 적용 근거 |
|-----------|---------|-----------|
| **IEEE 829-2008** | 전체 (§1~§18) | 본 문서의 구조·서식·필수 항목 정의 근거. IEEE 829는 소프트웨어 테스트 문서의 국제 표준 양식으로, 테스트 계획서(MTP)에 포함해야 할 18개 필수 섹션(식별자, 참조문서, 서론, 테스트 항목, 접근법, 합격기준, 일정 등)을 규정한다. |
| **IEEE 1012-2016** | §5 V&V 프로세스 | V-Model 기반 4단계 테스트(단위→통합→시스템→인수) 수준 분류 및 SIL 2 등급에 상응하는 검증 엄격도 결정 근거. |
| **ISO/IEC 25010:2023** | §4 품질 모델 | 8대 품질 특성 + 31개 부특성을 테스트 항목 도출의 기준 프레임워크로 적용. 각 부특성별 테스트 케이스를 매핑하여 품질 모델 전 영역 커버리지를 확보한다. |
| **ISO/IEC 25051:2014** | §6 시험 문서 | 문서-코드 정합성 검증 기준. 요구사항 명세(SRS)와 테스트 케이스 간 양방향 추적성을 보장한다. |
| **KS X 9003:2020** | 전체 | MES 기능 완전성 검증 기준. 제조실행시스템이 갖추어야 할 표준 기능(자재관리, 공정관리, 품질관리, 설비관리 등)의 구현 여부를 확인한다. |
| **GS인증 1등급 (TTA)** | 시험 항목 전체 | 국내 SW 품질 인증 시험 항목으로, 기능적합성·신뢰성·성능효율성·보안성·사용성·호환성·유지보수성·이식성 8개 영역의 합격 기준을 적용한다. |
| **KISA 49** | 49개 보안항목 | 소프트웨어 보안약점 진단 가이드 49개 항목(입력검증, 인증, 암호화, 에러처리 등) 중 해당 항목을 보안 테스트 케이스에 반영한다. |

### 테스트 수준별 합격 기준

| 테스트 수준 | 합격 기준 | 근거 |
|------------|-----------|------|
| 단위 테스트 (Unit) | 코드 커버리지 ≥ 70%, 전 TC PASS | IEEE 1012 §5.4, V-Model 최하위 |
| 통합 테스트 (Integration) | 모듈 간 인터페이스 전수 검증, 전 TC PASS | IEEE 1012 §5.5, API 계약 검증 |
| 시스템 테스트 (System) | 62건 요구사항 100% 커버, 합격률 ≥ 95% | ISO 25010 8대 특성, GS인증 기준 |
| 인수 테스트 (Acceptance) | FAT/SAT 전 항목 PASS, 고객 서명 | IEC 62381, GAMP 5 Appendix D9/D10 |

### 요구사항-테스트 매핑 기준

본 계획서는 62건의 요구사항(기능 38건 FN, 비기능 12건 NF, 보안 12건 SEC)을 테스트 케이스로 1:N 매핑하며, 매핑 완전성은 RTM(요구사항 추적 매트릭스)을 통해 양방향 추적성을 보장한다. 추적율 100% 미달 시 테스트 커버리지 부족으로 판정한다.

---

## 1. 테스트 계획 식별자 (Test Plan Identifier)

| 항목 | 내용 |
|------|------|
| **문서 ID** | TP-DEXWEAVER-MES-2026-001 |
| **대상 시스템** | DEXWEAVER Manufacturing Execution System (MES) |
| **대상 버전** | v4.3 |
| **적용 표준** | IEEE 829-2008 (Standard for Software and System Test Documentation) |
| **테스트 수준** | 단위(Unit) / 통합(Integration) / 시스템(System) / 인수(Acceptance) |
| **형상 관리** | Git (main 브랜치 기준, 커밋 2882674) |

본 문서는 IEEE 829-2008 표준에 따라 작성된 마스터 테스트 계획서(MTP)로서, DEXWEAVER MES v4.3의 전체 소프트웨어 검증 활동을 정의한다.

---

## 2. 참조 문서 (References)

### 2.1 국제/국가 표준

| 표준 번호 | 표준명 | 적용 영역 |
|-----------|--------|-----------|
| IEEE 829-2008 | Standard for Software and System Test Documentation | 본 테스트 계획서 구조 |
| IEEE 1012-2016 | Standard for System, Software, and Hardware V&V | 검증 및 확인(V&V) 프로세스 |
| ISO/IEC 25010:2023 | Systems and Software Quality Requirements and Evaluation | 8대 품질 특성 평가 기준 |
| ISO/IEC 25051:2014 | Requirements for Quality of Ready to Use Software Product | 문서-코드 정합성 |
| KS X 9003:2020 | 제조실행시스템(MES) 기능 표준 | MES 기능 완전성 검증 |
| KISA 49 | 소프트웨어 보안약점 진단가이드 (49개 항목) | 보안 취약점 테스트 |

### 2.2 인증 기준

| 인증 | 기관 | 적용 |
|------|------|------|
| GS인증 1등급 | TTA (한국정보통신기술협회) | 기능적합성, 신뢰성, 성능, 보안, 사용성, 호환성, 유지보수성, 이식성 |
| SP인증 3등급 | NIPA (정보통신산업진흥원) | 소프트웨어 프로세스 성숙도 |
| 스마트공장 (KOSMO) | 중소벤처기업부 | 데이터 연동, 상호운용성 |

### 2.3 프로젝트 내부 문서

| 문서 ID | 문서명 | 비고 |
|---------|--------|------|
| RTM-001 | 요구사항 추적 매트릭스 (RTM) | 62건 요구사항 추적 |
| BBT-001 | 블랙박스 테스트 결과 보고서 | 50건 API 테스트 결과 |
| SQV-001 | 소프트웨어 품질 검증 보고서 | ISO 25010 기반 86건 검증 |
| SRS-001 | 소프트웨어 요구사항 명세서 | FN-001~FN-038 정의 |
| DBS-001 | 데이터베이스 스키마 설계서 | 19개 테이블 + 시드 데이터 |

---

## 3. 서론 (Introduction)

### 3.1 목적 (Purpose)

본 테스트 계획서는 DEXWEAVER MES v4.3 시스템의 소프트웨어 품질을 체계적으로 검증하기 위한 마스터 테스트 계획을 정의한다. 본 계획은 다음 목표를 달성한다:

1. 62건의 요구사항(기능 38건, 비기능 12건, 보안 12건)에 대한 완전한 테스트 커버리지 확보
2. V-Model 기반 4단계 테스트(단위, 통합, 시스템, 인수)의 체계적 수행
3. GS인증 1등급, KISA 49 보안항목, KS X 9003 MES 기능 표준 충족 확인
4. AI 엔진 4종(수요예측, 스케줄최적화, 불량예측, 고장예측)의 정확도 및 안정성 검증
5. 테스트 산출물의 추적성(Traceability) 보장

### 3.2 범위 (Scope)

본 테스트 계획의 대상 범위는 다음과 같다:

- **백엔드 API 서버**: FastAPI 기반 40+ REST API 엔드포인트 (Python 3.12, uvicorn)
- **프론트엔드 SPA**: React 19 + Vite + Tailwind CSS 4 기반 단일 페이지 애플리케이션
- **데이터베이스**: PostgreSQL 15, 19개 테이블 + 시드 데이터, 커넥션 풀(psycopg2)
- **AI 엔진**: Prophet/Linear Regression, OR-Tools, XGBoost/SHAP, IsolationForest
- **배포 인프라**: Docker, docker-compose, Kubernetes 매니페스트
- **보안 체계**: JWT(HS256) + bcrypt + 파라미터화 쿼리 + 전역 예외 처리

### 3.3 제약사항 (Constraints)

| 제약 유형 | 내용 |
|-----------|------|
| 일정 | GS인증 심사 일정에 따라 테스트 완료 기한 준수 필요 |
| 환경 | 운영 환경(K8s 클러스터)과 테스트 환경(Docker Compose) 간 차이 존재 |
| 데이터 | AI 모델 학습에 충분한 이력 데이터가 필요하며, 초기 상태에서는 fallback 알고리즘 동작 |
| 인력 | 전담 QA 인력 및 도메인 전문가 확보 필요 |

---

## 4. 테스트 대상 항목 (Test Items)

### 4.1 백엔드 API 서버

| 구성 요소 | 기술 스택 | 버전 | 비고 |
|-----------|-----------|------|------|
| 웹 프레임워크 | FastAPI | 0.100+ | 비동기 ASGI 서버 |
| WSGI/ASGI 서버 | uvicorn | 0.24+ | 프로덕션 서버 |
| 데이터베이스 드라이버 | psycopg2-binary | 2.9+ | ThreadedConnectionPool |
| 인증 라이브러리 | PyJWT + bcrypt | 2.8+ / 4.1+ | HS256, bcrypt 해싱 |
| API 모듈 (18개) | `mes_auth`, `mes_items`, `mes_bom`, `mes_process`, `mes_equipment`, `mes_plan`, `mes_work`, `mes_quality`, `mes_inventory`, `mes_reports`, `mes_dashboard`, `mes_ai_prediction`, `mes_defect_predict`, `mes_inventory_status`, `mes_inventory_movement`, `mes_execution`, `k8s_service`, `sys_logic` | - | 총 4,726줄 |

### 4.2 프론트엔드 SPA

| 구성 요소 | 기술 스택 | 버전 |
|-----------|-----------|------|
| UI 프레임워크 | React | 19.x |
| 빌드 도구 | Vite | 6.x |
| CSS 프레임워크 | Tailwind CSS | 4.x |
| 상태 관리 | React Hooks (useState/useEffect) | - |
| HTTP 클라이언트 | fetch API | - |

### 4.3 데이터베이스

| 항목 | 상세 |
|------|------|
| DBMS | PostgreSQL 15 |
| 테이블 수 | 19개 (users, user_permissions, items, bom, processes, equipments, routings, equip_status_log, production_plans, work_orders, work_results, quality_standards, inspections, inspection_details, defect_codes, inventory, inventory_transactions, shipments, defect_history, equip_sensors, ai_forecasts) |
| 초기화 방식 | `init.sql` DDL + 시드 데이터 (Docker entrypoint) |
| 커넥션 풀 | ThreadedConnectionPool (minconn=2, maxconn=10) |

### 4.4 AI 엔진

| AI 엔진 | 기능 ID | 알고리즘 (Primary) | Fallback 알고리즘 | 입력 |
|---------|---------|-------------------|-------------------|------|
| 수요예측 | FN-018 | Facebook Prophet | Linear Regression | 출하/생산 이력 데이터 |
| 스케줄최적화 | FN-019 | OR-Tools / 규칙기반 | 설비별 부하 균등 배분 | 생산계획, 설비 가용성 |
| 불량예측 | FN-028 | XGBoost + SHAP | Threshold Scoring | 공정 파라미터(온도/압력/속도/습도) |
| 고장예측 | FN-034 | IsolationForest | Rule-based 임계값 | 설비 센서 데이터(진동/온도/전류) |

### 4.5 배포 인프라

| 구성 요소 | 파일 | 용도 |
|-----------|------|------|
| 컨테이너 이미지 | `Dockerfile` | Python 3.9-slim 기반 API 서버 이미지 |
| 로컬 개발환경 | `docker-compose.yml` | PostgreSQL + API 서버 구성 |
| 오케스트레이션 | K8s Deployment/Service | 프로덕션 배포 매니페스트 |

---

## 5. 소프트웨어 위험 이슈 (Software Risk Issues)

### 5.1 위험 식별 및 평가

| 위험 ID | 위험 항목 | 영향도 | 발생 가능성 | 위험 등급 | 완화 방안 |
|---------|----------|--------|------------|----------|----------|
| RISK-001 | AI 엔진 예측 정확도 부족 (학습 데이터 부재) | 높음 | 중간 | **높음** | Fallback 알고리즘 구현, 최소 데이터 요구량 검증 |
| RISK-002 | 동시접속 부하 시 DB 커넥션 풀 고갈 | 높음 | 낮음 | **중간** | maxconn=10 설정 검증, 스트레스 테스트 수행 |
| RISK-003 | JWT 시크릿 미설정 시 보안 취약 | 높음 | 중간 | **높음** | 환경변수 필수 검증, 미설정 시 랜덤 생성 확인 |
| RISK-004 | SQL Injection 취약점 | 높음 | 낮음 | **중간** | 전 모듈 파라미터화 쿼리 사용 검증 |
| RISK-005 | 프론트엔드-백엔드 API 스펙 불일치 | 중간 | 중간 | **중간** | E2E 통합 테스트로 검증 |
| RISK-006 | Docker/K8s 환경 간 동작 차이 | 중간 | 낮음 | **낮음** | 환경변수 기반 설정 분리 검증 |
| RISK-007 | 레거시 SHA-256 해시 마이그레이션 실패 | 중간 | 낮음 | **낮음** | 로그인 시 자동 마이그레이션 로직 검증 |
| RISK-008 | BOM 순환참조에 의한 무한루프 | 높음 | 낮음 | **중간** | 순환참조 탐지 로직 검증 |

### 5.2 위험 기반 테스트 우선순위

위험 등급 "높음" 항목(RISK-001, RISK-003)에 대해 테스트 우선순위를 최상위로 설정하며, 해당 항목의 테스트 케이스를 먼저 설계하고 실행한다.

---

## 6. 테스트 대상 기능 (Features to be Tested)

### 6.1 기능 요구사항 (38건)

#### 6.1.1 인증/권한 관리 (FN-001 ~ FN-003)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-001 | 사용자 로그인 (JWT 발행) | TC-FN-001-01 ~ 04 | `POST /api/auth/login` | `mes_auth.py` |
| FN-002 | 회원가입 (승인 대기) | TC-FN-002-01 ~ 03 | `POST /api/auth/register` | `mes_auth.py` |
| FN-003 | 사용자 목록/권한 관리 | TC-FN-003-01 ~ 04 | `GET/PUT /api/auth/users`, `GET/PUT /api/auth/permissions/{id}` | `mes_auth.py` |

#### 6.1.2 품목 관리 (FN-004 ~ FN-007)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-004 | 품목 등록 (CRUD - Create) | TC-FN-004-01 ~ 03 | `POST /api/items` | `mes_items.py` |
| FN-005 | 품목 조회 (검색/페이징/상세) | TC-FN-005-01 ~ 04 | `GET /api/items`, `GET /api/items/{code}` | `mes_items.py` |
| FN-006 | BOM 역전개 (재귀 탐색) | TC-FN-006-01 ~ 03 | `GET /api/bom/where-used/{code}` | `mes_bom.py` |
| FN-007 | 품목 삭제 | TC-FN-007-01 ~ 02 | `DELETE /api/items/{code}` | `mes_items.py` |

#### 6.1.3 BOM 관리 (FN-008 ~ FN-009)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-008 | BOM 등록/조회/수정/삭제 | TC-FN-008-01 ~ 05 | `POST/GET/PUT/DELETE /api/bom` | `mes_bom.py` |
| FN-009 | BOM 정전개 (Tree 구조) | TC-FN-009-01 ~ 02 | `GET /api/bom/explode/{code}` | `mes_bom.py` |

#### 6.1.4 공정/라우팅 관리 (FN-010 ~ FN-012)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-010 | 공정 CRUD | TC-FN-010-01 ~ 04 | `GET/POST/PUT/DELETE /api/processes` | `mes_process.py` |
| FN-011 | 공정-설비 연계 | TC-FN-011-01 ~ 02 | (공정/설비 FK 참조) | `mes_process.py` |
| FN-012 | 라우팅 관리 (등록/조회) | TC-FN-012-01 ~ 03 | `GET/POST /api/routings` | `mes_process.py` |

#### 6.1.5 설비 관리 (FN-013 ~ FN-014)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-013 | 설비 등록 (자동채번) | TC-FN-013-01 ~ 03 | `POST /api/equipments` | `mes_equipment.py` |
| FN-014 | 설비 목록 조회 (필터) | TC-FN-014-01 ~ 02 | `GET /api/equipments` | `mes_equipment.py` |

#### 6.1.6 생산 계획 (FN-015 ~ FN-017)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-015 | 생산계획 등록 | TC-FN-015-01 ~ 02 | `POST /api/plans` | `mes_plan.py` |
| FN-016 | 생산계획 조회 (필터/페이징) | TC-FN-016-01 ~ 03 | `GET /api/plans` | `mes_plan.py` |
| FN-017 | 생산계획 상세 조회 | TC-FN-017-01 | `GET /api/plans/{id}` | `mes_plan.py` |

#### 6.1.7 AI 계획 최적화 (FN-018 ~ FN-019)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-018 | AI 수요예측 (Prophet/LR) | TC-FN-018-01 ~ 04 | `POST /api/ai/demand-forecast` | `mes_ai_prediction.py` |
| FN-019 | AI 스케줄 최적화 | TC-FN-019-01 ~ 03 | `POST /api/ai/schedule-optimize` | `mes_plan.py` |

#### 6.1.8 작업지시/실적 (FN-020 ~ FN-024)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-020 | 작업지시 등록 (WO 자동채번) | TC-FN-020-01 ~ 03 | `POST /api/work-orders` | `mes_work.py` |
| FN-021 | 작업지시 목록 조회 | TC-FN-021-01 ~ 02 | `GET /api/work-orders` | `mes_work.py` |
| FN-022 | 작업지시 상세 조회 | TC-FN-022-01 | `GET /api/work-orders/{id}` | `mes_work.py` |
| FN-023 | 작업지시 상태 전이 (WAIT->WORKING->DONE) | TC-FN-023-01 ~ 04 | `PUT /api/work-orders/{id}/status` | `mes_work.py` |
| FN-024 | 실적 등록 (양품/불량) | TC-FN-024-01 ~ 02 | `POST /api/work-results` | `mes_work.py` |

#### 6.1.9 품질 관리 (FN-025 ~ FN-027)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-025 | 불량 현황 조회 | TC-FN-025-01 ~ 02 | `GET /api/quality/defects` | `mes_quality.py` |
| FN-026 | 품질 기준 등록 (NUMERIC/VISUAL/FUNCTIONAL) | TC-FN-026-01 ~ 03 | `POST /api/quality/standards` | `mes_quality.py` |
| FN-027 | 검사 실적 등록 (자동판정) | TC-FN-027-01 ~ 03 | `POST /api/quality/inspections` | `mes_quality.py` |

#### 6.1.10 AI 불량 예측 (FN-028)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-028 | AI 불량 예측 (XGBoost/SHAP) | TC-FN-028-01 ~ 04 | `POST /api/ai/defect-predict` | `mes_defect_predict.py` |

#### 6.1.11 재고 관리 (FN-029 ~ FN-031)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-029 | 재고 현황 조회 | TC-FN-029-01 ~ 02 | `GET /api/inventory` | `mes_inventory.py` |
| FN-030 | 입고 처리 (전표 자동채번) | TC-FN-030-01 ~ 03 | `POST /api/inventory/in` | `mes_inventory.py` |
| FN-031 | 출고 처리 (재고 부족 검증) | TC-FN-031-01 ~ 03 | `POST /api/inventory/out` | `mes_inventory.py` |

#### 6.1.12 설비 상태/AI 고장 예측 (FN-032 ~ FN-034)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-032 | 설비 상태 대시보드 (가동률) | TC-FN-032-01 ~ 02 | `GET /api/equipments/status` | `mes_equipment.py` |
| FN-033 | 설비 상태 변경 (이력 기록) | TC-FN-033-01 ~ 03 | `PUT /api/equipments/{code}/status` | `mes_equipment.py` |
| FN-034 | AI 설비 고장 예측 (IsolationForest) | TC-FN-034-01 ~ 04 | `POST /api/ai/failure-predict` | `mes_equipment.py` |

#### 6.1.13 보고서/분석 (FN-035 ~ FN-037)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-035 | 생산 보고서 (summary/trend/by_item) | TC-FN-035-01 ~ 02 | `GET /api/reports/production` | `mes_reports.py` |
| FN-036 | 품질 보고서 (defect_rate/Cpk/관리도) | TC-FN-036-01 ~ 02 | `GET /api/reports/quality` | `mes_reports.py` |
| FN-037 | AI 종합 인사이트 (통계 분석 엔진) | TC-FN-037-01 ~ 03 | `POST /api/ai/insights` | `mes_reports.py` |

#### 6.1.14 LOT 추적 및 기타 (FN-038, GS 기능)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | API Endpoint | 구현 모듈 |
|--------|-----------|-----------------|--------------|-----------|
| FN-038 | LOT 추적성 (재고->TX->WO->검사) | TC-FN-038-01 ~ 02 | `GET /api/lot/trace/{lot_no}` | `mes_inventory.py` |

### 6.2 비기능 요구사항 (12건)

| REQ-ID | 요구사항명 | 테스트 케이스 ID | 기준값 | 검증 방법 |
|--------|-----------|-----------------|--------|-----------|
| NF-001 | API 평균 응답시간 | TC-NF-001 | < 200ms | 10개 주요 API 응답시간 평균 측정 |
| NF-002 | API 최대 응답시간 | TC-NF-002 | < 2,000ms | AI 엔진 포함 전 API 최대 응답시간 |
| NF-003 | p95 응답시간 | TC-NF-003 | < 500ms | 95 백분위 응답시간 측정 |
| NF-004 | 동시접속 20건 처리 | TC-NF-004 | 20/20 성공 | concurrent.futures 동시 요청 |
| NF-005 | 동시접속 50건 처리 | TC-NF-005 | 50/50 성공 | 스트레스 테스트 |
| NF-006 | TPS (초당 처리량) | TC-NF-006 | > 40 TPS | 50건 동시 부하 시 TPS 측정 |
| NF-007 | 반복 안정성 (10회) | TC-NF-007 | 10/10 성공 | 동일 요청 10회 연속 실행 |
| NF-008 | 오류 후 복구성 | TC-NF-008 | 즉시 복구 | 비정상 요청 후 정상 요청 |
| NF-009 | 잘못된 입력 허용 오류 | TC-NF-009 | 안전 처리 | 음수, 빈값, 초대형 페이로드 |
| NF-010 | 비정상 페이로드 방어 | TC-NF-010 | 크래시 없음 | 100KB JSON, malformed JSON |
| NF-011 | Docker 컨테이너 배포 | TC-NF-011 | 정상 기동 | docker-compose up 검증 |
| NF-012 | 환경변수 기반 설정 | TC-NF-012 | 외부 주입 | DATABASE_URL, JWT_SECRET, CORS_ORIGINS |

### 6.3 보안 요구사항 (12건, KISA 49 기반)

| REQ-ID | 보안 요구사항 | 테스트 케이스 ID | KISA 분류 | 검증 방법 |
|--------|-------------|-----------------|-----------|-----------|
| SEC-001 | 미인증 API 차단 | TC-SEC-001 | 인증/인가 | 토큰 없이 보호 API 호출 |
| SEC-002 | 비밀번호 bcrypt 해싱 | TC-SEC-002 | 암호화 | DB 저장값 `$2b$` 접두어 검증 |
| SEC-003 | JWT 표준 구조 (3-part) | TC-SEC-003 | 토큰 관리 | 토큰 디코딩 구조 검증 |
| SEC-004 | JWT 만료 (exp) 필드 | TC-SEC-004 | 세션 관리 | 토큰 페이로드 exp 필드 존재 확인 |
| SEC-005 | JWT role 필드 (RBAC) | TC-SEC-005 | 접근 제어 | role 기반 권한 분리 검증 |
| SEC-006 | SQL Injection 방어 | TC-SEC-006 | 입력 검증 | `'; DROP TABLE--` 공격 시도 |
| SEC-007 | 시크릿 하드코딩 없음 | TC-SEC-007 | 보안 설정 | 소스코드 정적 분석 |
| SEC-008 | 스택트레이스 미노출 | TC-SEC-008 | 에러 처리 | 500 에러 시 응답 내용 검사 |
| SEC-009 | admin 자가등록 차단 | TC-SEC-009 | 권한 관리 | role=admin으로 회원가입 시도 |
| SEC-010 | SHA-256 해시 사용 (MD5 제거) | TC-SEC-010 | 암호 알고리즘 | k8s_service.py 코드 검사 |
| SEC-011 | 전역 예외 처리기 | TC-SEC-011 | 에러 처리 | `@app.exception_handler` 존재 검증 |
| SEC-012 | 파라미터화 쿼리 | TC-SEC-012 | SQL Injection | 전 모듈 `cursor.execute(sql, params)` 패턴 확인 |

---

## 7. 테스트 제외 대상 기능 (Features not to be Tested)

| 제외 항목 | 제외 사유 | 비고 |
|-----------|----------|------|
| 외부 ERP/SCM 연동 | 현재 버전에서 미구현. 향후 v5.0에서 대응 예정 | 인터페이스 설계만 존재 |
| 모바일 앱 (iOS/Android) | 네이티브 앱 미제공. React SPA의 반응형 레이아웃만 지원 | 모바일 브라우저 테스트는 수행 |
| 다국어 지원 (i18n) | 현재 한국어 단일 언어로 운영. 국제화 미구현 | 에러 메시지 한국어 표준화 완료 |
| 인쇄/PDF 출력 | 보고서 화면 조회만 지원. 인쇄/PDF 다운로드 미구현 | 브라우저 인쇄 기능으로 대체 가능 |
| LDAP/SSO 연동 | 자체 JWT 인증만 지원. 외부 인증 시스템 미연동 | 향후 OAuth 2.0 연동 고려 |
| 실시간 알림 (WebSocket) | REST API 기반 풀링(polling) 방식만 지원 | 향후 WebSocket 실시간 이벤트 고려 |
| 부하 테스트 (100건+) | 50건 동시접속까지만 검증. 대규모 부하 테스트는 별도 수행 | 운영 환경 구축 후 별도 계획 |

---

## 8. 테스트 접근 방법 (Approach)

### 8.1 V-Model 기반 4단계 테스트 전략

```
요구사항 분석  ──────────────────────────────────────  인수 테스트 (Level 4)
     │                                                    │
     ▼                                                    ▲
시스템 설계    ──────────────────────────────────────  시스템 테스트 (Level 3)
     │                                                    │
     ▼                                                    ▲
상세 설계     ──────────────────────────────────────  통합 테스트 (Level 2)
     │                                                    │
     ▼                                                    ▲
구현 (코딩)   ──────────────────────────────────────  단위 테스트 (Level 1)
```

### 8.2 Level 1: 단위 테스트 (Unit Testing)

| 항목 | 내용 |
|------|------|
| **목적** | 개별 함수/모듈의 입출력 정합성 검증 |
| **대상** | 18개 API 모듈의 핵심 함수 (~55개 함수) |
| **기법** | 화이트박스 (White-box), 구문 커버리지(Statement Coverage) |
| **도구** | pytest, unittest.mock |
| **책임** | 개발팀 |
| **테스트 케이스 예시** | |

| TC-ID | 대상 함수 | 입력 | 기대 출력 |
|-------|----------|------|----------|
| TC-UT-001 | `mes_auth._hash_password()` | `"test1234"` | bcrypt 해시 (`$2b$` 접두어) |
| TC-UT-002 | `mes_auth._verify_password()` | 정상 비밀번호 + 해시 | `True` |
| TC-UT-003 | `mes_auth._verify_password()` | 잘못된 비밀번호 + 해시 | `False` |
| TC-UT-004 | `mes_auth._create_token()` | `("admin", "admin")` | 3-part JWT 문자열 |
| TC-UT-005 | `mes_auth._sanitize_id()` | `"'; DROP TABLE--"` | `ValueError` 발생 |
| TC-UT-006 | `mes_bom.explode_bom()` | 존재하는 item_code | Tree 구조 JSON |
| TC-UT-007 | `mes_bom.where_used()` | 자재 item_code | 재귀 탐색 결과 (level 필드 포함) |
| TC-UT-008 | `mes_defect_predict._threshold_predict()` | 정상 파라미터 | `risk_level: LOW` |
| TC-UT-009 | `mes_defect_predict._threshold_predict()` | 범위 초과 파라미터 | `risk_level: HIGH` |
| TC-UT-010 | `database.query_db()` | 정상 SQL | 결과 리스트 반환 |

### 8.3 Level 2: 통합 테스트 (Integration Testing)

| 항목 | 내용 |
|------|------|
| **목적** | 모듈 간 인터페이스 및 데이터 흐름 검증 |
| **대상** | API 라우트 -> 모듈 함수 -> DB 쿼리 -> 응답 반환 경로 |
| **기법** | 그레이박스 (Gray-box), 인터페이스 테스트 |
| **도구** | pytest + httpx (FastAPI TestClient), Docker PostgreSQL |
| **책임** | 개발팀 + QA팀 |
| **테스트 케이스 예시** | |

| TC-ID | 통합 경로 | 검증 항목 |
|-------|----------|----------|
| TC-IT-001 | Auth -> JWT -> Protected API | JWT 토큰 획득 후 보호 API 정상 접근 |
| TC-IT-002 | Items -> BOM -> Routing | 품목 등록 후 BOM/라우팅에서 참조 가능 |
| TC-IT-003 | Plan -> WorkOrder -> WorkResult | 생산계획 -> 작업지시 -> 실적 등록 순서 |
| TC-IT-004 | Inventory In -> Inventory Out -> LOT Trace | 입고 -> 출고 -> LOT 추적 데이터 연계 |
| TC-IT-005 | Equipment -> Sensor -> AI Failure Predict | 설비 센서 데이터 -> AI 고장예측 연동 |
| TC-IT-006 | Quality Standards -> Inspection -> Defect Report | 품질기준 -> 검사실적 -> 불량현황 연동 |
| TC-IT-007 | DB Pool -> Concurrent Requests | 커넥션 풀 다중 요청 동시 처리 |
| TC-IT-008 | Auth(register) -> Auth(approve) -> Auth(login) | 가입 -> 승인 -> 로그인 전체 흐름 |

### 8.4 Level 3: 시스템 테스트 (System Testing)

| 항목 | 내용 |
|------|------|
| **목적** | 전체 시스템의 요구사항 충족 여부 검증 |
| **대상** | 62건 전체 요구사항 (FN 38 + NF 12 + SEC 12) |
| **기법** | 블랙박스 (Black-box), 요구사항 기반 테스트 |
| **도구** | Python requests + 자동화 스크립트, 성능 측정 도구 |
| **책임** | QA팀 |
| **하위 분류** | |

| 시스템 테스트 유형 | 테스트 수 | 기준 |
|------------------|----------|------|
| 기능 테스트 (Functional) | 38건 | FN-001~038 전수 검증 |
| 성능 테스트 (Performance) | 15건 | 응답시간, 동시접속, TPS |
| 보안 테스트 (Security) | 12건 | KISA 49 기반 취약점 테스트 |
| 신뢰성 테스트 (Reliability) | 12건 | 장애 허용, 복구, 반복 안정성 |
| 사용성 테스트 (Usability) | 5건 | 한국어 메시지, API 문서, 빌드 성공 |
| 호환성 테스트 (Compatibility) | 6건 | Docker, CORS, 환경변수 |
| 유지보수성 테스트 (Maintainability) | 7건 | 모듈화, 로깅, 코드 품질 |
| 이식성 테스트 (Portability) | 5건 | 컨테이너화, 환경 분리 |

### 8.5 Level 4: 인수 테스트 (Acceptance Testing)

| 항목 | 내용 |
|------|------|
| **목적** | 사용자/발주자 관점의 최종 수용 가능성 확인 |
| **대상** | 핵심 업무 시나리오 (End-to-End) |
| **기법** | 시나리오 기반 테스트, 체크리스트 검증 |
| **책임** | 발주자, 도메인 전문가, QA팀 |
| **시나리오 예시** | |

| TC-ID | 시나리오 | 기대 결과 |
|-------|---------|----------|
| TC-AT-001 | 관리자 로그인 -> 품목 등록 -> BOM 구성 -> 공정 등록 -> 라우팅 설정 -> 생산계획 수립 | 기준정보 일관성 유지 |
| TC-AT-002 | 작업자 로그인 -> 작업지시 확인 -> 상태 변경(WORKING) -> 실적 등록 -> 상태 변경(DONE) | 생산 실적 정상 기록 |
| TC-AT-003 | 입고 -> 생산 -> 출고 -> LOT 추적 -> 품질 검사 이력 확인 | 전체 추적성 보장 |
| TC-AT-004 | AI 수요예측 실행 -> 생산계획 반영 -> AI 스케줄 최적화 | AI 지원 의사결정 |
| TC-AT-005 | 설비 센서 이상 -> AI 고장예측 -> 예방정비 의사결정 | 사전 예방 체계 동작 |

---

## 9. 합격/불합격 판정 기준 (Item Pass/Fail Criteria)

### 9.1 개별 테스트 케이스 판정 기준

| 판정 | 조건 |
|------|------|
| **PASS** | 기대 결과와 실제 결과가 일치하며, 응답 시간 기준을 충족 |
| **FAIL** | 기대 결과와 실제 결과가 불일치하거나, 서버 크래시/비정상 종료 발생 |
| **BLOCK** | 선행 조건 미충족 또는 환경 문제로 테스트 수행 불가 |
| **N/A** | 해당 테스트 케이스가 현재 빌드에 적용 불가 |

### 9.2 테스트 수준별 합격 기준

| 테스트 수준 | 합격 기준 | 비고 |
|------------|----------|------|
| 단위 테스트 (Level 1) | Pass Rate >= 95%, Critical 결함 0건 | 핵심 함수 전수 통과 필수 |
| 통합 테스트 (Level 2) | Pass Rate >= 90%, 모듈 간 연동 결함 0건 | 데이터 흐름 정합성 확보 |
| 시스템 테스트 (Level 3) | Pass Rate >= 95%, Severity-High 결함 0건 | GS인증 기준 충족 |
| 인수 테스트 (Level 4) | 핵심 시나리오 100% 통과, 사용자 수용 승인 | 발주자 최종 확인 |

### 9.3 품질 특성별 합격 기준 (ISO/IEC 25010)

| 품질 특성 | 합격 기준 |
|----------|----------|
| 기능 적합성 | 38건 기능 요구사항 100% PASS |
| 신뢰성 | 비정상 입력 10종 전수 방어, 반복 안정성 10/10 |
| 성능 효율성 | 평균 응답시간 < 200ms, 최대 < 2,000ms, TPS > 40 |
| 보안성 | KISA 49 보안항목 12건 전수 PASS |
| 사용성 | 한국어 에러 메시지, API 문서 자동 생성, 빌드 성공 |
| 호환성 | Docker/K8s 배포, CORS 설정, JSON 응답 일관성 |
| 유지보수성 | 모듈 분리 10개 이상, docstring 비율 80% 이상, print문 0건 |
| 이식성 | Docker 컨테이너화, 환경변수 외부 주입 |

---

## 10. 중단 기준 및 재개 요건 (Suspension Criteria and Resumption Requirements)

### 10.1 중단 기준 (Suspension Criteria)

다음 조건 중 하나라도 발생하면 해당 수준의 테스트를 즉시 중단한다:

| 중단 조건 | 심각도 | 조치 |
|-----------|--------|------|
| 테스트 환경(DB, API 서버) 장애로 테스트 수행 불가 | Critical | 환경 복구 후 재개 |
| 핵심 기능(로그인, DB 연결)에서 크래시 발생 | Critical | 결함 수정 빌드 후 재개 |
| Severity-High 결함 누적 5건 이상 | High | 결함 분석 및 우선 수정 후 재개 |
| 테스트 데이터 오염 (시드 데이터 손상) | High | DB 재초기화 후 재개 |
| 빌드 배포 실패 (Docker 이미지 빌드 오류) | High | 빌드 문제 해결 후 재개 |

### 10.2 재개 요건 (Resumption Requirements)

| 재개 조건 | 검증 방법 |
|-----------|----------|
| 테스트 환경 정상화 확인 | `GET /api/health` 정상 응답 확인 |
| 결함 수정 빌드 배포 완료 | 형상 관리(Git) 커밋 확인, Docker 재빌드 |
| 회귀 테스트 (Regression) 통과 | 수정된 결함 관련 테스트 케이스 재실행 |
| 테스트 데이터 정합성 확인 | init.sql 재적용 후 시드 데이터 검증 |
| 중단 사유 해소 보고 | QA팀 -> 프로젝트 관리자 보고 |

---

## 11. 테스트 산출물 (Test Deliverables)

### 11.1 계획 단계 산출물

| 산출물 | 문서 ID | 작성 시점 |
|--------|---------|----------|
| 마스터 테스트 계획서 (본 문서) | TP-DEXWEAVER-MES-2026-001 | 테스트 착수 전 |
| 테스트 케이스 명세서 | TC-SPEC-001 | 테스트 설계 완료 시 |
| 테스트 데이터 명세서 | TD-SPEC-001 | 테스트 환경 구성 시 |

### 11.2 실행 단계 산출물

| 산출물 | 문서 ID | 작성 시점 |
|--------|---------|----------|
| 단위 테스트 결과 보고서 | UTR-001 | Level 1 완료 시 |
| 통합 테스트 결과 보고서 | ITR-001 | Level 2 완료 시 |
| 시스템 테스트 결과 보고서 (블랙박스) | STR-001 (BBT-001) | Level 3 완료 시 |
| 성능 테스트 결과 보고서 | PTR-001 | 성능 테스트 완료 시 |
| 보안 테스트 결과 보고서 | SECR-001 | 보안 테스트 완료 시 |
| 인수 테스트 결과 보고서 | ATR-001 | Level 4 완료 시 |

### 11.3 완료 단계 산출물

| 산출물 | 문서 ID | 작성 시점 |
|--------|---------|----------|
| 요구사항 추적 매트릭스 (RTM) | RTM-001 | 전 단계 완료 시 |
| 소프트웨어 품질 검증 보고서 | SQV-001 | 종합 검증 완료 시 |
| 결함 보고서 (Defect Log) | DL-001 | 수시 (결함 발견 시) |
| 테스트 종료 보고서 | TSR-001 | 테스트 활동 종료 시 |

---

## 12. 잔여 테스트 작업 (Remaining Test Tasks)

| 작업 ID | 작업 내용 | 선행 조건 | 담당 | 상태 |
|---------|----------|----------|------|------|
| RT-001 | 단위 테스트 케이스 상세 설계 (55개 함수) | 테스트 계획 승인 | 개발팀 | 미착수 |
| RT-002 | 통합 테스트 환경 구성 (Docker + pytest) | RT-001 | QA팀 | 미착수 |
| RT-003 | 성능 테스트 스크립트 작성 (부하 생성기) | 테스트 환경 구성 | QA팀 | 미착수 |
| RT-004 | 보안 테스트 도구 선정 및 스캔 수행 | 테스트 환경 구성 | 보안 담당 | 미착수 |
| RT-005 | AI 엔진 정확도 검증 데이터셋 구성 | 학습 데이터 확보 | 데이터팀 | 미착수 |
| RT-006 | 프론트엔드 UI 테스트 (Cypress/Playwright) | 프론트엔드 빌드 | 프론트엔드팀 | 미착수 |
| RT-007 | 인수 테스트 시나리오 검토 및 확정 | 발주자 협의 | QA팀 + 발주자 | 미착수 |
| RT-008 | 회귀 테스트 자동화 구축 (CI/CD 연동) | 테스트 스크립트 | DevOps팀 | 미착수 |
| RT-009 | K8s 운영 환경 배포 테스트 | K8s 클러스터 구축 | DevOps팀 | 미착수 |
| RT-010 | 테스트 종료 보고서 작성 | 전 단계 완료 | QA팀 | 미착수 |

---

## 13. 환경 요구사항 (Environmental Needs)

### 13.1 하드웨어 환경

| 환경 | 사양 | 용도 |
|------|------|------|
| 테스트 서버 | CPU 4코어+, RAM 8GB+, SSD 50GB+ | API 서버 + DB 운영 |
| 개발자 워크스테이션 | CPU 2코어+, RAM 8GB+, SSD 30GB+ | 단위/통합 테스트 실행 |
| 부하 테스트 클라이언트 | CPU 4코어+, RAM 8GB+ | 동시접속 부하 생성 |

### 13.2 소프트웨어 환경

| 구분 | 소프트웨어 | 버전 | 용도 |
|------|-----------|------|------|
| OS | Ubuntu | 24.04 LTS | 테스트 서버 운영체제 |
| 컨테이너 | Docker Engine | 24.x+ | 컨테이너 런타임 |
| 컨테이너 오케스트레이션 | docker-compose | 2.x+ | 로컬 환경 구성 |
| 프로그래밍 언어 | Python | 3.12+ | 백엔드 API 서버 |
| 데이터베이스 | PostgreSQL | 15+ | 데이터 저장소 |
| 노드 런타임 | Node.js | 20 LTS+ | 프론트엔드 빌드 |
| 패키지 매니저 | npm | 10+ | 프론트엔드 의존성 |

### 13.3 테스트 도구

| 도구 | 용도 | 비고 |
|------|------|------|
| pytest | 단위/통합 테스트 프레임워크 | Python 표준 테스트 도구 |
| httpx / FastAPI TestClient | API 통합 테스트 | 비동기 HTTP 클라이언트 |
| Python requests | 블랙박스 API 테스트 | HTTP 요청 기반 |
| concurrent.futures | 동시접속 부하 테스트 | 멀티스레드 동시 요청 |
| Cypress / Playwright | 프론트엔드 E2E 테스트 | 브라우저 자동화 (선택) |
| Git | 형상 관리 | 테스트 대상 버전 관리 |
| Docker | 테스트 환경 격리 | 재현 가능한 환경 구성 |

### 13.4 네트워크 환경

| 항목 | 설정 |
|------|------|
| API 서버 포트 | 80 (내부), 30173 (NodePort) |
| PostgreSQL 포트 | 5432 (내부), 5433 (docker-compose 외부) |
| CORS 허용 Origin | `http://localhost:30173`, `http://localhost:3000` |
| 프론트엔드 개발 서버 | 3000 (Vite dev server) |

---

## 14. 인력 및 교육 요구사항 (Staffing and Training Needs)

### 14.1 테스트 인력 구성

| 역할 | 인원 | 필요 역량 |
|------|------|----------|
| 테스트 관리자 (Test Manager) | 1명 | IEEE 829 표준, 테스트 계획/관리 경험 |
| QA 엔지니어 | 2명 | Python 테스트 자동화, REST API 테스트, SQL |
| 성능 테스트 엔지니어 | 1명 | 부하 테스트 도구, 성능 분석 |
| 보안 테스트 담당 | 1명 | KISA 보안 가이드라인, 취약점 분석 |
| 프론트엔드 QA | 1명 | React 테스트, 브라우저 호환성 테스트 |
| 도메인 전문가 (제조) | 1명 | MES 업무 프로세스, KS X 9003 |

### 14.2 교육 요구사항

| 교육 항목 | 대상 | 시간 | 내용 |
|-----------|------|------|------|
| MES 업무 프로세스 | QA팀 전원 | 4시간 | 품목/BOM/공정/작업지시/품질/재고 업무 흐름 |
| DEXWEAVER MES v4.3 아키텍처 | QA팀 전원 | 2시간 | FastAPI 모듈 구조, DB 스키마, AI 엔진 구성 |
| IEEE 829 테스트 문서 표준 | 테스트 관리자, QA | 2시간 | 테스트 계획/설계/결과 문서 작성법 |
| KISA 49 보안 테스트 | 보안 담당 | 4시간 | 49개 보안약점 진단 기법 |
| pytest + FastAPI TestClient | 개발팀 + QA | 2시간 | 자동화 테스트 작성 및 실행 |

---

## 15. 역할과 책임 (Responsibilities)

| 역할 | 담당자/팀 | 책임 |
|------|----------|------|
| 프로젝트 관리자 (PM) | PM | 테스트 계획 승인, 일정 조율, 리소스 배정 |
| 테스트 관리자 | QA팀장 | 테스트 계획 수립, 진행 관리, 결과 보고, 산출물 품질 보증 |
| 테스트 설계자 | QA 엔지니어 | 테스트 케이스 설계, 테스트 데이터 준비, 추적 매트릭스 유지 |
| 테스트 실행자 | QA 엔지니어 | 테스트 수행, 결함 보고, 회귀 테스트 실행 |
| 개발팀 리드 | 개발팀장 | 결함 수정, 단위 테스트 작성, 기술 지원 |
| 개발자 | 개발팀원 | 단위 테스트 구현, 결함 수정, 코드 리뷰 |
| 보안 담당 | 보안팀 | KISA 49 보안 테스트 수행, 취약점 분석 |
| DevOps 담당 | DevOps팀 | 테스트 환경 구축/유지, CI/CD 파이프라인 연동 |
| 발주자/사용자 대표 | 고객사 | 인수 테스트 참여, 최종 승인 |
| 품질 보증 책임자 (QAO) | 품질팀장 | 테스트 프로세스 감사, 품질 기준 준수 확인 |

---

## 16. 일정 (Schedule)

### 16.1 마스터 테스트 일정

| 단계 | 시작일 | 종료일 | 기간 | 산출물 |
|------|--------|--------|------|--------|
| **Phase 0: 테스트 계획** | 2026-02-24 | 2026-02-28 | 5일 | 테스트 계획서 (본 문서) |
| **Phase 1: 단위 테스트** | 2026-03-01 | 2026-03-07 | 7일 | UTR-001 (단위 테스트 결과) |
| **Phase 2: 통합 테스트** | 2026-03-08 | 2026-03-14 | 7일 | ITR-001 (통합 테스트 결과) |
| **Phase 3: 시스템 테스트** | 2026-03-15 | 2026-03-28 | 14일 | STR-001, PTR-001, SECR-001 |
| **Phase 4: 인수 테스트** | 2026-03-29 | 2026-04-04 | 7일 | ATR-001 (인수 테스트 결과) |
| **Phase 5: 결함 수정/회귀** | 2026-04-05 | 2026-04-11 | 7일 | 결함 수정 확인 보고서 |
| **Phase 6: 테스트 종료** | 2026-04-12 | 2026-04-14 | 3일 | TSR-001, RTM-001 최종판, SQV-001 |

### 16.2 주요 마일스톤

| 마일스톤 | 일자 | 조건 |
|---------|------|------|
| M1: 테스트 계획 승인 | 2026-02-28 | PM + QAO 승인 |
| M2: 단위 테스트 완료 | 2026-03-07 | Pass Rate >= 95% |
| M3: 통합 테스트 완료 | 2026-03-14 | 모듈 간 연동 결함 0건 |
| M4: 시스템 테스트 완료 | 2026-03-28 | GS인증 기준 충족 확인 |
| M5: 인수 테스트 합격 | 2026-04-04 | 발주자 수용 승인 |
| M6: 테스트 종료 보고 | 2026-04-14 | 전체 산출물 완료 |

---

## 17. 위험 및 비상 대책 (Risks and Contingencies)

### 17.1 테스트 위험 식별

| 위험 ID | 위험 항목 | 영향 | 발생 확률 | 대응 전략 |
|---------|----------|------|----------|----------|
| TR-001 | 테스트 일정 지연 | 높음 | 중간 | 우선순위 기반 테스트 실행, 자동화 비율 확대 |
| TR-002 | 테스트 환경 불안정 | 높음 | 낮음 | Docker 기반 환경 격리, 스냅샷 백업 |
| TR-003 | 결함 수정 지연으로 테스트 블록 | 중간 | 중간 | 결함 우선순위 분류, 대안 테스트 경로 활용 |
| TR-004 | AI 학습 데이터 부족 | 중간 | 높음 | 합성 데이터 생성, Fallback 알고리즘 검증에 집중 |
| TR-005 | QA 인력 부족 | 중간 | 중간 | 자동화 테스트 확대, 개발팀 단위 테스트 분담 |
| TR-006 | 요구사항 변경 (Scope Creep) | 높음 | 낮음 | 변경 관리 프로세스 적용, 영향 분석 후 테스트 계획 갱신 |
| TR-007 | 외부 의존성 라이브러리 업데이트 | 낮음 | 낮음 | Docker 이미지 고정 버전 사용, pip freeze 관리 |

### 17.2 비상 대책 (Contingency Plans)

| 시나리오 | 비상 대책 |
|---------|----------|
| 일정 2주 이상 지연 | 위험 기반 테스트(Risk-based Testing)로 전환, 고위험 테스트 케이스 우선 실행 |
| 테스트 환경 복구 불가 | 백업 Docker 이미지로 환경 재구성 (최대 2시간 이내 복구) |
| Critical 결함 다수 발견 | 테스트 중단 -> 결함 분석 회의 -> 수정 우선순위 결정 -> 긴급 패치 배포 |
| AI 엔진 라이브러리 미설치 | Fallback 알고리즘(Linear Regression, Threshold Scoring, Rule-based) 정상 동작 확인으로 대체 |
| GS인증 심사 일정 변경 | 핵심 테스트(기능, 보안, 성능)를 우선 완료하여 최소 합격 기준 확보 |

---

## 18. 승인 (Approvals)

본 테스트 계획서는 아래 서명인의 검토 및 승인을 거쳐 확정된다.

| 역할 | 성명 | 서명 | 일자 |
|------|------|------|------|
| 프로젝트 관리자 (PM) | _________________ | _________________ | ____/____/____ |
| 품질 보증 책임자 (QAO) | _________________ | _________________ | ____/____/____ |
| 테스트 관리자 | _________________ | _________________ | ____/____/____ |
| 개발팀 리드 | _________________ | _________________ | ____/____/____ |
| 발주자 대표 | _________________ | _________________ | ____/____/____ |

### 승인 이력

| 버전 | 일자 | 변경 내용 | 승인자 |
|------|------|----------|--------|
| Rev 1.0 | 2026-02-27 | 최초 작성 | - |

---

## 부록 A. 테스트 케이스 ID 체계

```
TC-[수준]-[요구사항ID]-[순번]

수준:
  FN   = 기능 요구사항 테스트 (시스템 테스트)
  NF   = 비기능 요구사항 테스트
  SEC  = 보안 요구사항 테스트
  UT   = 단위 테스트
  IT   = 통합 테스트
  AT   = 인수 테스트

예시:
  TC-FN-001-01  = FN-001(로그인)의 첫 번째 시스템 테스트 케이스
  TC-UT-005     = 5번째 단위 테스트 케이스
  TC-SEC-006    = SEC-006(SQL Injection 방어) 보안 테스트
  TC-AT-003     = 3번째 인수 테스트 시나리오
```

## 부록 B. 요구사항-테스트 케이스 매핑 요약

| 구분 | 요구사항 수 | 테스트 케이스 수 | 커버리지 |
|------|-----------|----------------|---------|
| 기능 요구사항 (FN-001 ~ FN-038) | 38건 | 약 95건 | 100% |
| 비기능 요구사항 (NF-001 ~ NF-012) | 12건 | 12건 | 100% |
| 보안 요구사항 (SEC-001 ~ SEC-012) | 12건 | 12건 | 100% |
| 단위 테스트 (UT) | - | 약 55건 | 핵심 함수 전수 |
| 통합 테스트 (IT) | - | 약 8건 | 주요 연동 경로 |
| 인수 테스트 (AT) | - | 5건 | 핵심 업무 시나리오 |
| **합계** | **62건** | **약 187건** | **100%** |

## 부록 C. 용어 정의

| 용어 | 정의 |
|------|------|
| MES (Manufacturing Execution System) | 제조실행시스템. 생산 현장의 실시간 데이터를 수집/관리하여 생산 효율을 최적화하는 시스템 |
| BOM (Bill of Materials) | 자재명세서. 제품 생산에 필요한 부품/자재의 계층 구조 |
| JWT (JSON Web Token) | 인증 토큰. Header.Payload.Signature 3-part 구조 |
| RBAC (Role-Based Access Control) | 역할 기반 접근 제어. admin/manager/worker/viewer 4단계 |
| LOT | 동일 조건에서 생산된 제품/자재 묶음의 추적 단위 |
| WO (Work Order) | 작업지시서. 생산계획에 따른 현장 작업 지시 |
| SPA (Single Page Application) | 단일 페이지 애플리케이션. 페이지 전환 없이 동적으로 UI 갱신 |
| TPS (Transactions Per Second) | 초당 처리량. 시스템 성능 지표 |
| Cpk (Process Capability Index) | 공정능력지수. 규격 대비 공정 산포 정도 |
| RTM (Requirements Traceability Matrix) | 요구사항 추적 매트릭스 |
| V&V (Verification and Validation) | 검증 및 확인 |

---

> 본 문서는 IEEE 829-2008 표준에 따라 작성되었으며, DEXWEAVER MES v4.3의 전체 테스트 활동을 계획하고 관리하기 위한 마스터 테스트 계획서입니다.
> 모든 테스트 활동은 본 계획에 정의된 절차와 기준에 따라 수행되어야 합니다.

**문서 끝 (End of Document)**
