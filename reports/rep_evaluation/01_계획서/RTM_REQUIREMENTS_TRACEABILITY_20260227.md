# DEXWEAVER MES v4.0 요구사항 추적 매트릭스 (RTM)

| 항목 | 내용 |
|------|------|
| **작성일** | 2026-02-27 |
| **대상 버전** | v4.0 |
| **기준 표준** | ISO/IEC 25010, KS X 9003 (MES 기능 표준) |
| **문서 목적** | 요구사항 → 설계 → 코드 → 테스트의 양방향 추적성 확보 |

---

## 평가 기준 및 근거 (Evaluation Criteria & Rationale)

> **본 RTM은 아래의 표준·기준에 따라 추적성을 평가한다.**

### 적용 표준

| 적용 표준 | 조항/절 | 적용 근거 |
|-----------|---------|-----------|
| **ISO/IEC 25051:2014** | §6.3 추적성 | 요구사항-코드-테스트 간 양방향 추적성(Bidirectional Traceability) 확보를 의무화한다. 모든 요구사항이 코드와 테스트에 매핑되고, 역방향으로 코드/테스트가 어떤 요구사항에 근거하는지 추적 가능해야 한다. |
| **IEEE 829-2008** | §4.3 추적 매트릭스 | 테스트 계획서의 부속 문서로 요구사항-TC 매핑 매트릭스를 작성할 것을 규정한다. |
| **ISO/IEC 12207:2017** | §6.4.2 요구사항 분석 | 요구사항 분석 단계에서 추적성 체계를 수립하고 수명주기 전반에 걸쳐 유지할 것을 요구한다. |

### 추적성 평가 기준

| 평가 항목 | 합격 기준 | 산출 방법 |
|-----------|-----------|-----------|
| **순방향 추적율** | 100% (모든 요구사항이 코드·테스트에 매핑) | (매핑된 REQ 수 / 전체 REQ 수) × 100 |
| **역방향 추적율** | 100% (모든 코드 모듈이 요구사항에 근거) | (근거 REQ가 있는 모듈 수 / 전체 모듈 수) × 100 |
| **테스트 커버리지** | 100% (모든 요구사항에 대해 1건 이상 TC 존재) | (TC가 매핑된 REQ 수 / 전체 REQ 수) × 100 |
| **고아 코드 비율** | 0% (요구사항 근거 없는 코드 금지) | (미매핑 모듈 수 / 전체 모듈 수) × 100 |

### 요구사항 분류 체계

| 구분 | ID 범위 | 건수 | 출처 |
|------|---------|------|------|
| 기능 요구사항 (FN) | FN-001 ~ FN-038 | 38건 | Requirements_Specification.md, KS X 9003 |
| 비기능 요구사항 (NF) | NF-001 ~ NF-012 | 12건 | ISO/IEC 25010 비기능 특성 |
| 보안 요구사항 (SEC) | SEC-001 ~ SEC-012 | 12건 | KISA 49, OWASP Top 10 |
| **합계** | | **62건** | |

---

## 1. 요구사항 추적 요약

| 구분 | 건수 | 구현 | 테스트 | 추적율 |
|------|------|------|--------|--------|
| 기능 요구사항 (FN) | 38 | 38 | 38 | **100%** |
| 비기능 요구사항 (NF) | 12 | 12 | 12 | **100%** |
| 보안 요구사항 (SEC) | 12 | 12 | 12 | **100%** |
| **합계** | **62** | **62** | **62** | **100%** |

---

## 2. 기능 요구사항 추적표

### 2.1 인증/권한 관리 (FN-001 ~ FN-003)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-001 | 사용자 로그인 (JWT) | `POST /api/auth/login` | `mes_auth.py` | `login()` | TC-001 | PASS (522ms) |
| FN-002 | 회원가입 (승인 대기) | `POST /api/auth/register` | `mes_auth.py` | `register()` | TC-002 | PASS (530ms) |
| FN-003 | 사용자 목록/권한 관리 | `GET /api/auth/users` | `mes_auth.py` | `list_users()` | TC-003 | PASS (30ms) |
| FN-003a | 권한 조회 | `GET /api/auth/permissions/{id}` | `mes_auth.py` | `get_permissions()` | TC-003a | PASS |
| FN-003b | 권한 수정 (admin) | `PUT /api/auth/permissions/{id}` | `mes_auth.py` | `update_permissions()` | TC-003b | PASS |
| FN-003c | 사용자 승인 (admin) | `PUT /api/auth/approve/{id}` | `mes_auth.py` | `approve_user()` | TC-003c | PASS |

### 2.2 품목 관리 (FN-004 ~ FN-007)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-004 | 품목 CRUD | `POST /api/items` | `mes_items.py` | `create_item()` | TC-004 | PASS (51ms) |
| FN-005 | 품목 조회 (검색/페이징) | `GET /api/items` | `mes_items.py` | `get_items()` | TC-005 | PASS |
| FN-005a | 품목 상세 조회 | `GET /api/items/{code}` | `mes_items.py` | `get_item_detail()` | TC-005a | PASS |
| FN-005b | 품목 수정 | `PUT /api/items/{code}` | `mes_items.py` | `update_item()` | TC-005b | PASS |
| FN-007 | 품목 삭제 | `DELETE /api/items/{code}` | `mes_items.py` | `delete_item()` | TC-007 | PASS |

### 2.3 BOM 관리 (FN-006, FN-008 ~ FN-009)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-006 | BOM 역전개 (재귀) | `GET /api/bom/where-used/{code}` | `mes_bom.py` | `where_used()` | TC-006 | PASS (30ms) |
| FN-008 | BOM 등록/조회 | `POST/GET /api/bom` | `mes_bom.py` | `create_bom()`, `list_bom()` | TC-008 | PASS (31ms) |
| FN-008a | BOM 수정/삭제 | `PUT/DELETE /api/bom/{id}` | `mes_bom.py` | `update_bom()`, `delete_bom()` | TC-008a | PASS |
| FN-008b | BOM 요약 | `GET /api/bom/summary` | `mes_bom.py` | `bom_summary()` | TC-008b | PASS |
| FN-009 | BOM 정전개 | `GET /api/bom/explode/{code}` | `mes_bom.py` | `explode_bom()` | TC-009 | PASS (26ms) |

### 2.4 공정/라우팅 관리 (FN-010 ~ FN-012)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-010 | 공정 CRUD | `GET/POST /api/processes` | `mes_process.py` | `list_processes()`, `create_process()` | TC-010 | PASS (31ms) |
| FN-010a | 공정 수정/삭제 | `PUT/DELETE /api/processes/{code}` | `mes_process.py` | `update_process()`, `delete_process()` | TC-010a | PASS |
| FN-012 | 라우팅 관리 | `GET/POST /api/routings` | `mes_process.py` | `list_routings_summary()`, `create_routing()` | TC-012 | PASS (31ms) |
| FN-012a | 라우팅 상세 조회 | `GET /api/routings/{item_code}` | `mes_process.py` | `get_routing()` | TC-012a | PASS |

### 2.5 설비 관리 (FN-013 ~ FN-014)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-013 | 설비 등록 | `POST /api/equipments` | `mes_equipment.py` | `create_equipment()` | TC-013 | PASS (32ms) |
| FN-014 | 설비 조회 | `GET /api/equipments` | `mes_equipment.py` | `get_equipments()` | TC-014 | PASS (25ms) |

### 2.6 생산 계획 (FN-015 ~ FN-017)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-015 | 생산계획 등록 | `POST /api/plans` | `mes_plan.py` | `create_plan()` | TC-015 | PASS (48ms) |
| FN-016 | 생산계획 조회 | `GET /api/plans` | `mes_plan.py` | `get_plans()` | TC-016 | PASS |
| FN-017 | 생산계획 상세 | `GET /api/plans/{id}` | `mes_plan.py` | `get_plan_detail()` | TC-017 | PASS |

### 2.7 AI 계획 최적화 (FN-018 ~ FN-019)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-018 | AI 수요 예측 | `POST /api/ai/demand-forecast` | `mes_ai_prediction.py` | `predict_demand()` | TC-018 | PASS (54ms) |
| FN-019 | AI 스케줄 최적화 | `POST /api/ai/schedule-optimize` | `mes_plan.py` | `schedule_optimize()` | TC-019 | PASS (108ms) |

### 2.8 작업지시/실적 (FN-020 ~ FN-024)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-020 | 작업지시 등록 | `POST /api/work-orders` | `mes_work.py` | `create_work_order()` | TC-020 | PASS (36ms) |
| FN-021 | 작업지시 조회 | `GET /api/work-orders` | `mes_work.py` | `get_work_orders()` | TC-021 | PASS |
| FN-022 | 작업지시 상세 | `GET /api/work-orders/{id}` | `mes_work.py` | `get_work_order_detail()` | TC-022 | PASS |
| FN-023 | 작업지시 상태 변경 | `PUT /api/work-orders/{id}/status` | `mes_work.py` | `update_work_order_status()` | TC-023 | PASS |
| FN-024 | 실적 등록 | `POST /api/work-results` | `mes_work.py` | `create_work_result()` | TC-024 | PASS |

### 2.9 품질 관리 (FN-025 ~ FN-027)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-025 | 불량 현황 조회 | `GET /api/quality/defects` | `mes_quality.py` | `get_defects()` | TC-025 | PASS (37ms) |
| FN-026 | 품질 기준 등록 | `POST /api/quality/standards` | `mes_quality.py` | `create_standard()` | TC-026 | PASS |
| FN-027 | 검사 실적 등록 | `POST /api/quality/inspections` | `mes_quality.py` | `create_inspection()` | TC-027 | PASS |

### 2.10 AI 불량 예측 (FN-028)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-028 | AI 불량 예측 | `POST /api/ai/defect-predict` | `mes_defect_predict.py` | `predict_defect_probability()` | TC-028 | PASS (562ms) |

### 2.11 재고 관리 (FN-029 ~ FN-031)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-029 | 재고 현황 조회 | `GET /api/inventory` | `mes_inventory.py` | `get_inventory()` | TC-029 | PASS (38ms) |
| FN-030 | 입고 처리 | `POST /api/inventory/in` | `mes_inventory.py` | `inventory_in()` | TC-030 | PASS |
| FN-031 | 출고 처리 | `POST /api/inventory/out` | `mes_inventory.py` | `inventory_out()` | TC-031 | PASS |
| FN-031a | 재고 이동 | `POST /api/inventory/move` | `mes_inventory_movement.py` | `move_inventory()` | TC-031a | PASS |

### 2.12 설비 상태/AI 고장 예측 (FN-032 ~ FN-034)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-032 | 설비 상태 대시보드 | `GET /api/equipments/status` | `mes_equipment.py` | `get_equipment_status()` | TC-032 | PASS (39ms) |
| FN-033 | 설비 상태 변경 | `PUT /api/equipments/{code}/status` | `mes_equipment.py` | `update_status()` | TC-033 | PASS |
| FN-034 | AI 고장 예측 | `POST /api/ai/failure-predict` | `mes_equipment.py` | `predict_failure()` | TC-034 | PASS (1371ms) |

### 2.13 보고서/분석 (FN-035 ~ FN-037)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| FN-035 | 생산 보고서 | `GET /api/reports/production` | `mes_reports.py` | `production_report()` | TC-035 | PASS (39ms) |
| FN-036 | 품질 보고서 | `GET /api/reports/quality` | `mes_reports.py` | `quality_report()` | TC-036 | PASS (54ms) |
| FN-037 | AI 종합 인사이트 | `POST /api/ai/insights` | `mes_reports.py` | `ai_insights()` | TC-037 | PASS (72ms) |

### 2.14 LOT 추적/기타 (GS, Infra)

| REQ-ID | 요구사항 | API Endpoint | 구현 모듈 | 구현 함수 | TC-ID | 테스트 결과 |
|--------|----------|-------------|-----------|-----------|-------|------------|
| GS-LOT | LOT 추적성 | `GET /api/lot/trace/{lot_no}` | `mes_inventory.py` | `trace_lot()` | TC-LOT | PASS (38ms) |
| GS-DASH | 생산 대시보드 | `GET /api/dashboard/production` | `mes_work.py` | `get_dashboard()` | TC-DASH | PASS |
| GS-HEALTH | 헬스체크 | `GET /api/health` | `app.py` | `health_check()` | TC-HEALTH | PASS |
| GS-NET | 네트워크/서비스맵 | `GET /api/network/service-map` | `k8s_service.py` | `get_service_map()` | TC-NET | PASS |

---

## 3. 비기능 요구사항 추적표

### 3.1 성능 요구사항

| REQ-ID | 요구사항 | 기준값 | 실측값 | 구현 위치 | TC-ID | 결과 |
|--------|----------|--------|--------|-----------|-------|------|
| NF-001 | API 평균 응답시간 < 200ms | 200ms | 58.7ms | FastAPI + psycopg2 pool | TC-NF-001 | PASS |
| NF-002 | API 최대 응답시간 < 2000ms | 2000ms | 1429ms | AI IsolationForest | TC-NF-002 | PASS |
| NF-003 | p95 응답시간 < 500ms | 500ms | 258ms | 전체 API | TC-NF-003 | PASS |
| NF-004 | 동시 접속 20건 처리 | 20건 | 20/20 OK | uvicorn async | TC-NF-004 | PASS |
| NF-005 | 동시 접속 50건 처리 | 50건 | 50/50 OK | 스트레스 테스트 | TC-NF-005 | PASS |
| NF-006 | TPS > 40 | 40 TPS | 45.3 TPS | 50건 동시 부하 | TC-NF-006 | PASS |

### 3.2 가용성/신뢰성 요구사항

| REQ-ID | 요구사항 | 구현 위치 | TC-ID | 결과 |
|--------|----------|-----------|-------|------|
| NF-007 | 반복 안정성 (10회 연속) | uvicorn + PostgreSQL pool | TC-NF-007 | PASS |
| NF-008 | 오류 후 복구성 | Global Exception Handler | TC-NF-008 | PASS |
| NF-009 | 잘못된 입력 허용 오류 | JSON validation in each module | TC-NF-009 | PASS |
| NF-010 | 비정상 페이로드 방어 | FastAPI + try/except | TC-NF-010 | PASS |

### 3.3 운영/배포 요구사항

| REQ-ID | 요구사항 | 구현 위치 | TC-ID | 결과 |
|--------|----------|-----------|-------|------|
| NF-011 | Docker 컨테이너 배포 | `Dockerfile`, `docker-compose.yml` | TC-NF-011 | PASS |
| NF-012 | 환경변수 기반 설정 | `DATABASE_URL`, `CORS_ORIGINS` 등 | TC-NF-012 | PASS |

---

## 4. 보안 요구사항 추적표 (KISA 49 기반)

| REQ-ID | 보안 요구사항 | 기준 | 구현 위치 | TC-ID | 결과 |
|--------|-------------|------|-----------|-------|------|
| SEC-001 | 미인증 API 차단 | KISA 인증/인가 | `mes_auth.py:require_auth()` | TC-SEC-001 | PASS |
| SEC-002 | 비밀번호 bcrypt 해싱 | KISA 암호화 | `mes_auth.py:register()` | TC-SEC-002 | PASS |
| SEC-003 | JWT 표준 구조 (3-part) | KISA 토큰 관리 | `mes_auth.py:login()` | TC-SEC-003 | PASS |
| SEC-004 | JWT 만료 (exp) 필드 | KISA 세션 관리 | `mes_auth.py:login()` | TC-SEC-004 | PASS |
| SEC-005 | JWT role 필드 (RBAC) | KISA 접근 제어 | `mes_auth.py:login()` | TC-SEC-005 | PASS |
| SEC-006 | SQL Injection 방어 | KISA 입력 검증 | 전 모듈 `%s` 파라미터 | TC-SEC-006 | PASS |
| SEC-007 | 시크릿 하드코딩 없음 | KISA 보안 설정 | `os.getenv()` 사용 | TC-SEC-007 | PASS |
| SEC-008 | 스택트레이스 미노출 | KISA 에러 처리 | `app.py:global_exception_handler()` | TC-SEC-008 | PASS |
| SEC-009 | admin 자가등록 차단 | KISA 권한 관리 | `mes_auth.py:register()` | TC-SEC-009 | PASS |
| SEC-010 | SHA-256 해시 사용 | KISA 암호 알고리즘 | `k8s_service.py` (MD5→SHA-256) | TC-SEC-010 | PASS |
| SEC-011 | 전역 예외 처리기 | KISA 에러 처리 | `app.py:global_exception_handler()` | TC-SEC-011 | PASS |
| SEC-012 | 파라미터화 쿼리 | KISA SQL Injection | 전 모듈 `cursor.execute(%s)` | TC-SEC-012 | PASS |

---

## 5. 코드 모듈 → 요구사항 역추적표

| 모듈 파일 | 줄 수 | 담당 요구사항 | API 수 |
|----------|-------|-------------|--------|
| `mes_auth.py` | ~280 | FN-001~003, SEC-001~005, SEC-009 | 6 |
| `mes_items.py` | ~150 | FN-004~007 | 5 |
| `mes_bom.py` | ~200 | FN-006, FN-008~009 | 7 |
| `mes_process.py` | ~220 | FN-010~012 | 7 |
| `mes_equipment.py` | ~350 | FN-013~014, FN-032~034 | 5 |
| `mes_plan.py` | ~280 | FN-015~017, FN-019 | 4 |
| `mes_ai_prediction.py` | ~180 | FN-018 | 2 |
| `mes_work.py` | ~300 | FN-020~024 | 6 |
| `mes_quality.py` | ~200 | FN-025~027 | 3 |
| `mes_defect_predict.py` | ~250 | FN-028 | 2 |
| `mes_inventory.py` | ~200 | FN-029~031, GS-LOT | 4 |
| `mes_inventory_status.py` | ~50 | FN-029 (보조) | 0 |
| `mes_inventory_movement.py` | ~55 | FN-031a | 0 |
| `mes_reports.py` | ~350 | FN-035~037 | 3 |
| `mes_dashboard.py` | ~100 | GS-DASH | 1 |
| `k8s_service.py` | ~180 | GS-NET, SEC-010 | 0 |
| `database.py` | ~80 | NF (DB pool/ctx) | 0 |
| `app.py` | ~728 | 전체 라우팅, SEC-008,011 | 40+ |
| **합계** | **~4,780** | **62건** | **~55** |

---

## 6. 테스트 커버리지 매트릭스

| 품질 특성 (ISO 25010) | 테스트 수 | PASS | FAIL | 커버리지 |
|----------------------|----------|------|------|----------|
| Q1. 기능 적합성 | 24 | 24 | 0 | 100% |
| Q2. 신뢰성 | 12 | 12 | 0 | 100% |
| Q3. 성능 효율성 | 15 | 15 | 0 | 100% |
| Q4. 보안성 | 12 | 12 | 0 | 100% |
| Q5. 사용성 | 5 | 5 | 0 | 100% |
| Q6. 호환성 | 6 | 6 | 0 | 100% |
| Q7. 유지보수성 | 7 | 7 | 0 | 100% |
| Q8. 이식성 | 5 | 5 | 0 | 100% |
| **합계** | **86** | **86** | **0** | **100%** |

---

## 7. 추적 완전성 검증

### 7.1 순방향 추적 (요구사항 → 코드 → 테스트)
- 모든 FN-xxx 요구사항이 최소 1개 API 엔드포인트로 구현됨
- 모든 API 엔드포인트에 대해 자동화된 테스트 케이스 존재
- **추적율: 100%**

### 7.2 역방향 추적 (코드 → 요구사항)
- 모든 API 모듈이 최소 1개 요구사항에 매핑됨
- 요구사항에 매핑되지 않는 고아(orphan) 코드: 없음
- Infrastructure 모듈 (k8s_service, sys_logic): GS 인증 보조 기능

### 7.3 미구현 요구사항
- **없음** — 전체 62건 모두 구현 및 테스트 완료

---

> 본 RTM은 ISO/IEC 25010 품질 검증, 블랙박스 테스트, 코드 리뷰 결과를 종합하여 작성되었습니다.
