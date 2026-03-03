# DEXWEAVER MES v6.0 -- 테스트 데이터 생성 전략

> **버전**: v6.0
> **작성일**: 2026-03-03
> **작성 근거**: DatabaseSchema.md, init.sql (v4.0 seed data)
> **대상 테이블**: 40개 (기존 21 + Phase 1: 7 + Phase 2: 8 + Phase 3: 4)

---

## 1. 개요

### 1.1 목적

본 문서는 DEXWEAVER MES v6.0의 40개 테이블에 대한 테스트 데이터 생성 전략을 정의한다. 개발(Dev), 스테이징(Staging), 부하테스트(Load Test) 환경별로 일관성 있는 데이터를 자동 생성하여, 기능 검증과 성능 테스트의 신뢰성을 확보하는 것이 목적이다.

### 1.2 범위

| 구분 | 테이블 수 | 대상 |
|:----:|:---------:|:----:|
| 기존 v4.0 | 21개 | users, user_permissions, items, bom, processes, equipments, routings, equip_status_log, production_plans, work_orders, work_results, quality_standards, inspections, inspection_details, defect_codes, inventory, inventory_transactions, shipments, defect_history, equip_sensors, ai_forecasts |
| Phase 1 신규 | 7개 | spc_rules, spc_violations, capa, capa_actions, oee_daily, notifications, notification_settings |
| Phase 2 신규 | 8개 | maintenance_plans, maintenance_orders, recipes, recipe_parameters, mqtt_config, sensor_data, documents, worker_skills |
| Phase 3 신규 | 4개 | erp_sync_config, erp_sync_log, opcua_config, audit_trail |

### 1.3 데이터 생성 접근 방식

| 접근 방식 | 적용 대상 | 도구 |
|:---------:|:---------:|:----:|
| SQL 스크립트 | 마스터 데이터, 코드 테이블, 소량 트랜잭션 | PostgreSQL `INSERT`, `generate_series()` |
| Python/Faker | 대량 트랜잭션, 시계열 데이터, 이상치 주입 | `faker`, `numpy`, `psycopg2` |
| 하이브리드 | 마스터(SQL) 후 트랜잭션(Python) 순차 실행 | Makefile / shell script 오케스트레이션 |

---

## 2. 테이블 의존성 순서 (Dependency DAG)

FK 의존 관계를 분석하여 삽입 순서를 결정한다. 순환 참조(processes <-> equipments)는 deferred constraint 또는 2-pass 전략으로 해결한다.

### 2.1 Layer 구조

```
Layer 0 (FK 없음 — 독립 테이블)
  ├── users
  ├── items
  ├── defect_codes
  ├── erp_sync_config       [Phase 3]
  └── (processes*, equipments* — 순환 참조, 먼저 FK 없이 INSERT 후 UPDATE)

Layer 1 (Layer 0 테이블만 참조)
  ├── user_permissions       → users
  ├── bom                    → items (parent, child)
  ├── processes.equip_code   → equipments (ALTER 후 UPDATE)
  ├── equipments.process_code→ processes (ALTER 후 UPDATE)
  ├── routings               → items, processes
  ├── production_plans       → items
  ├── quality_standards      → items
  ├── inventory              → items
  ├── shipments              → items
  ├── spc_rules              → items                      [Phase 1]
  ├── notification_settings  → users                      [Phase 1]
  ├── recipes                → items, processes, users    [Phase 2]
  ├── mqtt_config            → equipments                 [Phase 2]
  ├── opcua_config           → equipments                 [Phase 3]
  ├── documents              → items, processes, users    [Phase 2]
  ├── worker_skills          → users, processes           [Phase 2]
  └── erp_sync_log           → erp_sync_config            [Phase 3]

Layer 2 (Layer 0 + Layer 1 테이블 참조)
  ├── work_orders            → production_plans, items, equipments
  ├── equip_status_log       → equipments
  ├── inspections            → items
  ├── defect_history         → items, equipments
  ├── equip_sensors          → equipments
  ├── inventory_transactions → items
  ├── ai_forecasts           → (item_code, equip_code — soft FK)
  ├── oee_daily              → equipments                 [Phase 1]
  ├── notifications          → users                      [Phase 1]
  ├── maintenance_plans      → equipments                 [Phase 2]
  ├── recipe_parameters      → recipes                    [Phase 2]
  ├── sensor_data            → equipments                 [Phase 2]
  └── audit_trail            → (soft FK — table_name, changed_by)  [Phase 3]

Layer 3 (Layer 2 테이블 참조)
  ├── work_results           → work_orders
  ├── inspection_details     → inspections
  ├── spc_violations         → spc_rules, inspections, users  [Phase 1]
  ├── capa                   → users                      [Phase 1]
  └── maintenance_orders     → maintenance_plans, equipments, users  [Phase 2]

Layer 4 (Layer 3 테이블 참조)
  ├── capa_actions           → capa, users                [Phase 1]
  └── (추가 의존 없음)
```

### 2.2 권장 삽입 순서 (스크립트 실행 순서)

```
Step 1:  users, items, defect_codes, erp_sync_config
Step 2:  processes (equip_code = NULL), equipments (process_code = NULL)
Step 3:  ALTER FK + UPDATE (processes.equip_code, equipments.process_code)
Step 4:  user_permissions, bom, routings, production_plans, quality_standards,
         inventory, shipments, spc_rules, notification_settings, recipes,
         mqtt_config, opcua_config, documents, worker_skills, erp_sync_log
Step 5:  work_orders, equip_status_log, inspections, defect_history,
         equip_sensors, inventory_transactions, ai_forecasts, oee_daily,
         notifications, maintenance_plans, recipe_parameters, sensor_data,
         audit_trail
Step 6:  work_results, inspection_details, spc_violations, capa,
         maintenance_orders
Step 7:  capa_actions
```

---

## 3. 데이터 볼륨 매트릭스

| # | 테이블명 | 데이터 유형 | Dev (건) | Staging (건) | Load Test (건) |
|:-:|:--------:|:----------:|:--------:|:------------:|:--------------:|
| 1 | users | Master | 10 | 50 | 200 |
| 2 | user_permissions | Master | 20 | 200 | 1,000 |
| 3 | items | Master | 20 | 100 | 500 |
| 4 | bom | Master | 20 | 150 | 800 |
| 5 | processes | Master | 10 | 30 | 100 |
| 6 | equipments | Master | 15 | 50 | 200 |
| 7 | routings | Master | 40 | 200 | 1,000 |
| 8 | equip_status_log | Transaction | 25 | 500 | 50,000 |
| 9 | production_plans | Transaction | 25 | 200 | 5,000 |
| 10 | work_orders | Transaction | 50 | 500 | 20,000 |
| 11 | work_results | Transaction | 75 | 1,000 | 50,000 |
| 12 | quality_standards | Master | 30 | 150 | 500 |
| 13 | inspections | Transaction | 30 | 500 | 20,000 |
| 14 | inspection_details | Transaction | 30 | 1,500 | 60,000 |
| 15 | defect_codes | Master | 8 | 20 | 50 |
| 16 | inventory | Transaction | 35 | 300 | 5,000 |
| 17 | inventory_transactions | Transaction | 50 | 1,000 | 50,000 |
| 18 | shipments | Transaction | 144 | 500 | 10,000 |
| 19 | defect_history | Timeseries | 50 | 2,000 | 100,000 |
| 20 | equip_sensors | Timeseries | 100 | 5,000 | 500,000 |
| 21 | ai_forecasts | Transaction | 10 | 100 | 2,000 |
| 22 | spc_rules | Master | 15 | 50 | 200 |
| 23 | spc_violations | Transaction | 20 | 300 | 10,000 |
| 24 | capa | Transaction | 10 | 50 | 1,000 |
| 25 | capa_actions | Transaction | 30 | 150 | 3,000 |
| 26 | oee_daily | Timeseries | 100 | 1,000 | 30,000 |
| 27 | notifications | Transaction | 50 | 500 | 50,000 |
| 28 | notification_settings | Master | 30 | 200 | 1,000 |
| 29 | maintenance_plans | Master | 15 | 50 | 200 |
| 30 | maintenance_orders | Transaction | 20 | 200 | 5,000 |
| 31 | recipes | Master | 10 | 50 | 200 |
| 32 | recipe_parameters | Master | 40 | 200 | 800 |
| 33 | mqtt_config | Master | 15 | 50 | 200 |
| 34 | sensor_data | Timeseries | 500 | 50,000 | 5,000,000 |
| 35 | documents | Master | 20 | 100 | 500 |
| 36 | worker_skills | Master | 30 | 150 | 1,000 |
| 37 | erp_sync_config | Master | 5 | 10 | 20 |
| 38 | erp_sync_log | Transaction | 50 | 500 | 20,000 |
| 39 | opcua_config | Master | 10 | 30 | 100 |
| 40 | audit_trail | Timeseries | 200 | 5,000 | 500,000 |

> **총 볼륨 추정**: Dev ~1,900건 / Staging ~71,000건 / Load Test ~6,900,000건

---

## 4. 테이블별 생성 규칙

### 4.1 기존 v4.0 테이블 (21개)

#### 4.1.1 users (사용자)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| user_id | 패턴: `admin`, `mgr{01-05}`, `worker{01-20}`, `viewer{01-05}`. Dev 환경에서는 init.sql의 10명 유지 |
| password | bcrypt 해시 고정값 사용. Dev/Staging 동일 비밀번호(`test1234`) |
| name | Faker `ko_KR.name()` + 직책 접미사 (관리자/부장/기술자/작업자 등) |
| email | `{user_id}@knu.ac.kr` 패턴 |
| role | 분포: admin 10%, manager 20%, worker 60%, viewer 10% |
| is_approved | TRUE 90%, FALSE 10% (미승인 계정 테스트용) |
| created_at | `2025-01-01` ~ `2026-02-28` 범위 랜덤 |

#### 4.1.2 user_permissions (사용자 권한)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| user_id | FK: `users.user_id`에서 랜덤 선택 |
| menu | 고정 목록: `ALL`, `DASHBOARD`, `PRODUCTION_PLAN`, `WORK_ORDER`, `QUALITY`, `EQUIPMENT`, `INVENTORY`, `REPORTS` |
| can_read | admin/manager → TRUE, worker → 담당 메뉴만 TRUE, viewer → TRUE |
| can_write | admin → TRUE, manager → TRUE, worker → 담당 메뉴만 TRUE, viewer → FALSE |

> UNIQUE(user_id, menu) 준수. admin 역할은 `ALL` 메뉴 1건만 생성.

#### 4.1.3 items (품목 마스터)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | 패턴: `ITEM{001-999}`. Dev: ITEM001~ITEM020 (init.sql 기준) |
| name | 현실적 품목명. RAW: 원자재명, SEMI: 가공품명, PRODUCT: 완제품명 |
| category | 분포: RAW 40%, SEMI 30%, PRODUCT 30% |
| unit | RAW: KG/M/EA, SEMI: EA, PRODUCT: EA/SET |
| spec | 품목별 현실적 규격 문자열 (예: `SUS304 두께2mm`, `AL6061 Phi10mm`) |
| safety_stock | RAW: 100~1000, SEMI: 50~200, PRODUCT: 10~50 |
| created_at | `2024-01-01` ~ `2025-12-31` 랜덤 |

#### 4.1.4 bom (자재명세서)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| parent_item | FK: `items.item_code` 중 SEMI/PRODUCT 품목만 |
| child_item | FK: `items.item_code` 중 parent보다 하위 카테고리 (PRODUCT→SEMI/RAW, SEMI→RAW) |
| qty_per_unit | DECIMAL(10,4). 범위: 0.1~10.0. 소수점 이하 1자리 위주 |
| loss_rate | 범위: 0.0~5.0%. 평균 2.0% |

> UNIQUE(parent_item, child_item) 준수. 순환 BOM 금지 (PRODUCT→SEMI→RAW 단방향).

#### 4.1.5 processes (공정)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| process_code | 패턴: `PRC-{001-100}`. Dev: PRC-001~PRC-010 |
| name | 현실적 공정명: 절단, CNC가공, 프레스, 열처리, 도금, 사출성형, 조립, 검사, 포장 등 |
| std_time_min | 범위: 5~60분. 공정별 현실적 값 |
| description | 공정 설명 텍스트 |
| equip_code | FK: `equipments.equip_code`. 초기 INSERT 시 NULL, 이후 UPDATE |

#### 4.1.6 equipments (설비)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| equip_code | 패턴: `EQP-{001-200}`. Dev: EQP-001~EQP-015 |
| name | 현실적 설비명: 레이저절단기, CNC선반, 유압프레스, 열처리로, 사출기, 조립라인, SMT라인 등 |
| process_code | FK: `processes.process_code`. 초기 INSERT 시 NULL, 이후 UPDATE |
| capacity_per_hour | 범위: 30~300. 설비 유형별 현실값 |
| status | 분포: RUNNING 70%, STOP 20%, DOWN 10% |
| install_date | `2020-01-01` ~ `2025-12-31`. 설비 유형에 따라 현실적 분포 |

#### 4.1.7 routings (라우팅)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` 중 SEMI/PRODUCT |
| seq | 1부터 순차 증가. 품목당 2~6개 공정 |
| process_code | FK: `processes.process_code`. BOM 구조에 맞는 현실적 공정 순서 |
| cycle_time | 범위: 5~45분. `processes.std_time_min` 기반 +/- 20% |

> UNIQUE(item_code, seq) 준수.

#### 4.1.8 equip_status_log (설비 상태 이력)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| equip_code | FK: `equipments.equip_code` |
| status | 상태 전이 규칙: RUNNING→STOP→RUNNING, RUNNING→DOWN→STOP→RUNNING (Markov chain 기반, 섹션 5 참조) |
| reason | 상태별 사유 매핑: STOP → `정기 점검/툴 교체/오일 교체`, DOWN → `고장 유형 설명`, RUNNING → `재가동/점검 완료` |
| worker_id | `users.user_id` 중 worker 역할에서 랜덤 |
| changed_at | 시간순 보장. 이전 레코드 대비 30분~48시간 간격 |

#### 4.1.9 production_plans (생산 계획)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` 중 SEMI/PRODUCT |
| plan_qty | SEMI: 200~800, PRODUCT: 50~200 |
| due_date | `2025-11-01` ~ `2026-06-30` 범위. 월 2~4건 |
| priority | 분포: HIGH 40%, MID 40%, LOW 20% |
| status | 시간 기반: due_date < NOW → DONE 80%/PROGRESS 20%, due_date >= NOW → WAIT 60%/PROGRESS 30%/DONE 10% |

#### 4.1.10 work_orders (작업 지시)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| wo_id | 패턴: `WO-{YYYYMMDD}-{001-999}` |
| plan_id | FK: `production_plans.plan_id` |
| item_code | FK: `items.item_code`. production_plans.item_code와 일치 |
| work_date | plan의 due_date 이전 5~15일 범위 |
| equip_code | FK: `equipments.equip_code`. routings 기반 해당 공정의 설비 |
| plan_qty | production_plans.plan_qty를 2~3건으로 분할 |
| status | 시간 기반: work_date < NOW-7d → DONE, work_date 근접 → WORKING, 미래 → WAIT |

#### 4.1.11 work_results (작업 실적)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| wo_id | FK: `work_orders.wo_id` 중 DONE/WORKING 상태 |
| good_qty | `work_orders.plan_qty * (0.93~0.99)`. 정수 반올림 |
| defect_qty | `plan_qty - good_qty`. 불량률 1~7% |
| defect_code | FK(soft): `defect_codes.defect_code`. 불량 시 랜덤 선택, 양품 100%이면 NULL |
| worker_id | `users.user_id` 중 worker 역할 |
| start_time | work_date + 08:00 또는 20:00 (주간/야간 교대) |
| end_time | start_time + 4~10시간 |

#### 4.1.12 quality_standards (품질 검사 기준)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` 중 SEMI/PRODUCT |
| check_name | 품목별 현실적 검사항목: 길이, 폭, 외경, 무게, 전압, 저항, 외관검사 등 |
| check_type | NUMERIC 60%, VISUAL 25%, FUNCTIONAL 15% |
| std_value | NUMERIC 타입만. 품목별 현실값 |
| min_value | `std_value * 0.99` 또는 `std_value - tolerance` |
| max_value | `std_value * 1.01` 또는 `std_value + tolerance` |
| unit | mm, g, V, W, Ohm, Ra, MPa 등 |

#### 4.1.13 inspections (품질 검사 결과)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| inspect_type | 분포: INCOMING 40%, PROCESS 40%, OUTGOING 20% |
| item_code | FK: `items.item_code`. INCOMING → RAW, PROCESS → SEMI, OUTGOING → PRODUCT |
| lot_no | 패턴: `LOT-{YYYYMMDD}-{001-999}` |
| judgment | PASS 85%, FAIL 15% |
| inspected_at | work_results.end_time 직후 또는 입고일 당일 |
| inspector_id | `users.user_id` 중 검사 권한 보유자 |

#### 4.1.14 inspection_details (검사 상세)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| inspection_id | FK: `inspections.inspection_id` |
| check_name | `quality_standards.check_name`과 매칭 |
| measured_value | NUMERIC: `std_value + Normal(0, sigma)` (sigma = (max-min)/6). VISUAL/FUNCTIONAL: NULL |
| judgment | measured_value가 min~max 범위 내 → PASS, 이탈 → FAIL |

> ON DELETE CASCADE (inspections 삭제 시 연쇄 삭제). 검사당 2~5건 상세.

#### 4.1.15 defect_codes (불량 코드)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| defect_code | 패턴: `DEF-{유형}`. 고정 목록: DEF-VISUAL, DEF-DIMEN, DEF-FUNC, DEF-MATERIAL, DEF-ASSEMBLY, DEF-PLATING, DEF-WELD, DEF-ELEC |
| name | 한글 불량명 |
| description | 불량 유형 설명 텍스트 |

> Dev 환경에서는 init.sql의 8개 코드 그대로 사용. Load Test 시 DEF-SCRATCH, DEF-CRACK 등 추가.

#### 4.1.16 inventory (재고)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` |
| lot_no | 패턴: `LOT-{YYYYMMDD}-{seq}` |
| qty | RAW: 100~2500, SEMI: 50~350, PRODUCT: 8~100 |
| warehouse | RAW → WH01, SEMI → WH02, PRODUCT → WH03 |
| location | 패턴: `{A/B/C}-{01-10}-{01-05}`. 창고별 구역 매핑 |

> UNIQUE(item_code, lot_no, warehouse) 준수.

#### 4.1.17 inventory_transactions (재고 이동 전표)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| slip_no | 패턴: `{IN/OUT/MV}-{YYYYMMDD}-{001-999}` |
| item_code | FK: `items.item_code` |
| lot_no | 기존 inventory.lot_no 참조 |
| qty | 양의 정수. IN: 입고수량, OUT: 출고수량, MOVE: 이동수량 |
| tx_type | IN(입고) 40%, OUT(출고) 40%, MOVE(이동) 20% |
| warehouse | inventory.warehouse 참조 |
| location | inventory.location 참조 |
| ref_id | IN(원자재): NULL, IN(반제품/완제품): `WO-*`, OUT(생산투입): `WO-*`, OUT(출하): `SHIP-*` |
| supplier | IN(원자재)만 해당: 포스코, 노벨리스, LS전선, LG화학 등 현실적 업체명 |

#### 4.1.18 shipments (출하 이력)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` 중 PRODUCT |
| ship_date | `2024-03-01` ~ `2026-03-31`. 월 2~4회 패턴 |
| qty | 제품별 기본수량 +/- 20%, 연간 5~10% 증가 트렌드, 계절 패턴 적용 (섹션 5 참조) |
| customer | 고정 고객 리스트: 현대모비스, 만도, LG전자, 보쉬코리아, 삼성전자 등 |

#### 4.1.19 defect_history (불량 이력)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` 중 SEMI/PRODUCT |
| equip_code | FK: `equipments.equip_code` |
| recorded_at | 작업일 기준. 09:00~17:00 |
| temperature | 정상 범위: 175~215 C, 이상 범위: 225~245 C. 분포는 섹션 5 참조 |
| pressure | 정상: 7.5~12.5, 이상: 13.0~16.0 |
| speed | 정상: 40~55, 이상: 56~65 |
| humidity | 정상: 48~62%, 이상: 70~85% |
| defect_count | 정상: `total_count * 0.005~0.03`, 이상: `total_count * 0.05~0.15` |
| total_count | 100~400. 작업 규모에 비례 |

> AI 불량 예측 모델 학습용. 정상:이상:경계 = 40%:35%:25% 비율로 생성.

#### 4.1.20 equip_sensors (설비 센서 데이터)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| equip_code | FK: `equipments.equip_code` |
| vibration | 정상: 0.2~1.5 mm/s, 경고: 1.5~3.0 mm/s, 위험: 3.0~6.0 mm/s. Gaussian + drift |
| temperature | 정상: 22~45 C, 경고: 45~60 C, 위험: 60~90 C |
| current_amp | 정상: 5~12 A, 경고: 12~16 A, 위험: 16~22 A |
| recorded_at | 1시간 간격 (08:00~17:00). 시간순 보장 |

> AI 고장 예측용. 설비별 패턴: 안정(EQP-003), 서서히 악화(EQP-005), 간헐적 이상(EQP-011), 고장(EQP-013).

#### 4.1.21 ai_forecasts (AI 예측 결과)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| model_type | 고정 목록: `DEMAND_FORECAST`, `DEFECT_PREDICTION`, `EQUIPMENT_FAILURE` |
| item_code | DEMAND_FORECAST/DEFECT_PREDICTION: `items.item_code`, EQUIPMENT_FAILURE: NULL |
| equip_code | EQUIPMENT_FAILURE: `equipments.equip_code`, 나머지: NULL |
| result_json | 모델별 JSON 구조. 예: `{"predicted_qty": 120, "confidence": 0.87, "period": "2026-03"}` |
| created_at | 최근 30일 내. 모델별 일 1회 실행 패턴 |

### 4.2 Phase 1 신규 테이블 (7개)

#### 4.2.1 spc_rules (SPC 관리 규칙)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| item_code | FK: `items.item_code` 중 SEMI/PRODUCT |
| check_name | `quality_standards.check_name`과 매칭. NUMERIC 타입만 |
| rule_type | 분포: WESTERN_ELECTRIC 50%, NELSON 30%, CUSTOM 20% |
| sample_size | 3, 5, 7 중 선택. 기본값 5 |
| ucl | `quality_standards.max_value` 또는 `target + 3*sigma` |
| lcl | `quality_standards.min_value` 또는 `target - 3*sigma` |
| target | `quality_standards.std_value` |
| is_active | TRUE 90%, FALSE 10% |

#### 4.2.2 spc_violations (SPC 위반 이력)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| rule_id | FK: `spc_rules.rule_id` |
| inspection_id | FK: `inspections.inspection_id` |
| violation_type | `RULE_1_BEYOND_3SIGMA`, `RULE_2_SEVEN_SAME_SIDE`, `RULE_3_SIX_INCREASING`, `RULE_4_FOURTEEN_ALTERNATING` 등 |
| measured_value | UCL 초과 또는 LCL 미만 값. `ucl + Uniform(0.01, 1.0)` 또는 `lcl - Uniform(0.01, 1.0)` |
| detected_at | `inspections.inspected_at`과 동일 |
| resolved | TRUE 60%, FALSE 40% (미해결 위반 테스트용) |
| resolved_by | FK: `users.user_id`. resolved=TRUE일 때만 설정 |

#### 4.2.3 capa (시정/예방 조치)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| capa_type | CA(시정조치) 60%, PA(예방조치) 40% |
| title | 패턴: `[CA/PA]-{YYYYMM}-{001}` + 요약 (예: `[CA]-202602-001 도금두께 불량 시정`) |
| description | 상세 설명 텍스트. Faker 기반 문장 생성 |
| source_type | QUALITY_ISSUE 40%, SPC_VIOLATION 25%, CUSTOMER_COMPLAINT 20%, AUDIT 15% |
| source_ref | source_type에 따라: inspection_id, violation_id, 또는 외부 참조 ID |
| status | 분포: OPEN 15%, INVESTIGATION 20%, ACTION 25%, VERIFICATION 20%, CLOSED 20% |
| priority | HIGH 30%, MID 50%, LOW 20% |
| assigned_to | FK: `users.user_id` 중 manager/worker |
| due_date | created_at + 7~30일 |
| created_by | FK: `users.user_id` 중 manager |
| closed_at | status=CLOSED일 때만 설정. due_date 전후 |

#### 4.2.4 capa_actions (CAPA 조치 이력)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| capa_id | FK: `capa.capa_id` |
| action_type | 시간순: ROOT_CAUSE → CORRECTIVE → PREVENTIVE → VERIFICATION. CAPA당 1~4건 |
| description | 조치 유형별 현실적 텍스트 |
| result | action_type=VERIFICATION일 때 결과 텍스트. 나머지는 NULL 또는 진행 상태 |
| performed_by | FK: `users.user_id` |
| performed_at | capa.created_at 이후 순차 증가. 조치 간 1~7일 간격 |

#### 4.2.5 oee_daily (OEE 일일 집계)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| equip_code | FK: `equipments.equip_code` |
| calc_date | `2025-11-01` ~ 현재. 설비당 1일 1건 |
| availability | 범위: 0.70~0.98. 정상 설비 평균 0.90 |
| performance | 범위: 0.75~0.98. 평균 0.88 |
| quality_rate | 범위: 0.90~0.99. 평균 0.96 |
| oee | `availability * performance * quality_rate`. 범위: 0.60~0.95, 평균 0.76 |
| planned_time_min | 8시간(480분) 또는 16시간(960분, 2교대) |
| actual_run_min | `planned_time_min * availability` |
| ideal_cycle_min | `60 / equipments.capacity_per_hour` |
| total_produced | `actual_run_min / ideal_cycle_min * performance` |
| good_produced | `total_produced * quality_rate` |

> UNIQUE(equip_code, calc_date) 준수. 주말 제외(월~금).

#### 4.2.6 notifications (알림)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| user_id | FK: `users.user_id`. NULL이면 전체 알림 (10%) |
| type | 분포: EQUIP_DOWN 25%, SPC_VIOLATION 20%, INVENTORY_LOW 20%, AI_WARNING 20%, CAPA_DUE 15% |
| title | 유형별 템플릿: `[설비고장] {equip_name} 긴급 정지`, `[SPC 위반] {item_name} {check_name} 관리한계 이탈` 등 |
| message | 상세 내용 텍스트 |
| severity | EQUIP_DOWN → CRITICAL, SPC_VIOLATION → WARNING, 나머지 → INFO/WARNING 혼합 |
| source_type | 발생 모듈명. type과 매핑 |
| source_ref | 관련 테이블의 레코드 ID |
| is_read | TRUE 70%, FALSE 30% |

#### 4.2.7 notification_settings (알림 설정)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| user_id | FK: `users.user_id` |
| notification_type | 모든 알림 유형에 대해 생성 |
| channel | WEBSOCKET, EMAIL 각 1건씩 |
| is_enabled | WEBSOCKET: TRUE 95%, EMAIL: TRUE 60% |

> UNIQUE(user_id, notification_type, channel) 준수. 사용자당 최대 10건(5유형 x 2채널).

### 4.3 Phase 2 신규 테이블 (8개)

#### 4.3.1 maintenance_plans (예방보전 계획)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| equip_code | FK: `equipments.equip_code`. 설비당 1~2건 |
| pm_type | TIME_BASED 50%, USAGE_BASED 30%, CONDITION_BASED 20% |
| interval_days | TIME_BASED: 30/60/90/180일. 나머지: NULL |
| interval_hours | USAGE_BASED: 500/1000/2000시간. 나머지: NULL |
| checklist | JSON 배열: `[{"item": "오일 레벨 확인", "type": "CHECK"}, {"item": "필터 교체", "type": "REPLACE"}]` |
| last_performed | 최근 수행일. next_due - interval_days 전후 |
| next_due | 현재 날짜 기준 -30일 ~ +90일 범위 |
| is_active | TRUE 85%, FALSE 15% |

#### 4.3.2 maintenance_orders (정비 작업지시)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| mo_id | 패턴: `MO-{YYYYMMDD}-{001-999}` |
| pm_id | FK: `maintenance_plans.pm_id`. PM(예방) 시 연결. CM/BM은 NULL |
| equip_code | FK: `equipments.equip_code` |
| mo_type | PM(예방) 50%, CM(사후) 30%, BM(고장) 20% |
| description | 유형별 현실적 작업 내용. PM: 점검 항목, CM: 부품 교체, BM: 고장 수리 |
| assigned_to | FK: `users.user_id` 중 worker/manager |
| status | PLANNED 20%, IN_PROGRESS 15%, COMPLETED 55%, CANCELLED 10% |
| start_time | COMPLETED/IN_PROGRESS: 계획일 + 08:00 |
| end_time | COMPLETED: start_time + 1~8시간 |
| cost | PM: 50,000~500,000원, CM: 100,000~2,000,000원, BM: 500,000~10,000,000원 |
| parts_used | JSON: `[{"part": "베어링 SKF6205", "qty": 2, "cost": 45000}]` |

#### 4.3.3 recipes (레시피 마스터)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| recipe_code | 패턴: `RCP-{item_code}-{process_code}`. 예: `RCP-ITEM015-PRC-008` |
| item_code | FK: `items.item_code` 중 SEMI/PRODUCT |
| process_code | FK: `processes.process_code`. routings 기반 |
| version | 1~3. 품목-공정 조합당 최소 1건, 최대 3건 |
| status | version별: 최신 → ACTIVE, 이전 → OBSOLETE, 신규 → DRAFT/APPROVED |
| description | 공정별 레시피 설명 |
| approved_by | FK: `users.user_id` 중 manager. ACTIVE/OBSOLETE 상태만 |

> UNIQUE(recipe_code, version) 준수.

#### 4.3.4 recipe_parameters (레시피 파라미터)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| recipe_id | FK: `recipes.recipe_id` |
| param_name | 공정별 현실적 파라미터명: 온도, 압력, 속도, RPM, 시간, 전류, 전압 등 |
| param_type | NUMERIC 80%, TEXT 10%, BOOLEAN 10% |
| target_value | 공정별 현실값. 온도: 180~250 C, 압력: 5~20 MPa, 속도: 30~100 m/min |
| min_value | `target_value * 0.90` (10% 하한) |
| max_value | `target_value * 1.10` (10% 상한) |
| unit | C, MPa, m/min, RPM, sec, A, V 등 |

> 레시피당 3~8개 파라미터.

#### 4.3.5 mqtt_config (MQTT 수집 설정)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| broker_url | `mqtt://broker.dexweaver.local:1883` 또는 `mqtts://broker.dexweaver.local:8883` |
| topic_pattern | 패턴: `factory/line{1-3}/{equip_code}/+`. 예: `factory/line1/EQP-001/temperature` |
| equip_code | FK: `equipments.equip_code` |
| sensor_type | `TEMPERATURE`, `VIBRATION`, `CURRENT`, `PRESSURE`, `HUMIDITY` |
| collect_interval_sec | 5, 10, 30, 60 중 선택. 기본 10초 |
| is_active | TRUE 90%, FALSE 10% |

#### 4.3.6 sensor_data (센서 수집 데이터)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| equip_code | FK: `equipments.equip_code` |
| sensor_type | `TEMPERATURE`, `VIBRATION`, `CURRENT`, `PRESSURE`, `HUMIDITY` |
| value | sensor_type별 범위. 온도: 20~200 C, 진동: 0.5~5.0 mm/s, 전류: 3~25 A, 압력: 1~30 MPa, 습도: 30~90%. 상세 분포는 섹션 5 참조 |
| collected_at | 10초~60초 간격. `2026-01-01` ~ 현재 |
| source | MQTT 70%, OPCUA 20%, MANUAL 10% |

> **주의**: Load Test 시 500만건. 월별 파티셔닝 권장. Python 스크립트로 batch INSERT 필수.

#### 4.3.7 documents (문서 관리)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| doc_type | 분포: SOP 30%, WI 25%, QC_REPORT 20%, SPEC 15%, MANUAL 10% |
| title | 유형별 템플릿: `[SOP] {process_name} 표준작업절차서`, `[WI] {item_name} 작업지시서` 등 |
| file_path | 패턴: `/documents/{doc_type}/{YYYY}/{filename}.pdf` |
| file_size | 100,000~5,000,000 bytes (100KB~5MB) |
| version | 1~3 |
| item_code | FK(nullable): `items.item_code`. SPEC/QC_REPORT만 연결 |
| process_code | FK(nullable): `processes.process_code`. SOP/WI만 연결 |
| uploaded_by | FK: `users.user_id` 중 manager/worker |
| is_active | 최신 version → TRUE, 이전 → FALSE |

#### 4.3.8 worker_skills (작업자 스킬매트릭스)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| user_id | FK: `users.user_id` 중 worker 역할 |
| process_code | FK: `processes.process_code`. 작업자당 2~5개 공정 |
| skill_level | 경력 기반: BEGINNER 20%, INTERMEDIATE 35%, ADVANCED 30%, EXPERT 15% |
| certified | ADVANCED/EXPERT → TRUE 80%, BEGINNER/INTERMEDIATE → FALSE 80% |
| cert_expiry | certified=TRUE: 현재 + 6개월~2년. certified=FALSE: NULL |
| updated_at | 최근 6개월 내 |

> UNIQUE(user_id, process_code) 준수.

### 4.4 Phase 3 신규 테이블 (4개)

#### 4.4.1 erp_sync_config (ERP 연동 설정)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| erp_type | SAP 50%, ORACLE 30%, ETC 20% |
| connection_url | 패턴: `https://erp.company.com/api/v2/{entity}` |
| sync_direction | INBOUND 35%, OUTBOUND 35%, BIDIRECTIONAL 30% |
| entity_type | ORDER, INVENTORY, BOM, ITEM 각 1건 이상 |
| mapping_config | JSON: `{"mes_field": "item_code", "erp_field": "MATNR", "transform": "UPPER"}` |
| sync_interval_min | 15, 30, 60, 120, 1440(일 1회) 중 선택 |
| is_active | TRUE 80%, FALSE 20% |

#### 4.4.2 erp_sync_log (ERP 동기화 이력)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| sync_id | FK: `erp_sync_config.sync_id` |
| direction | INBOUND/OUTBOUND. erp_sync_config.sync_direction 기반 |
| entity_type | erp_sync_config.entity_type과 일치 |
| records_processed | 범위: 1~500 |
| records_success | `records_processed * (0.95~1.00)` |
| records_failed | `records_processed - records_success` |
| error_detail | records_failed > 0 일 때: `Duplicate key`, `Invalid format`, `Connection timeout` 등 |
| synced_at | sync_interval_min 간격으로 순차 생성 |

#### 4.4.3 opcua_config (OPC-UA 설정)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| server_url | 패턴: `opc.tcp://plc-{line}.dexweaver.local:4840` |
| equip_code | FK: `equipments.equip_code` |
| node_id | 패턴: `ns=2;s={equip_code}.{sensor_type}`. 예: `ns=2;s=EQP-001.Temperature` |
| sensor_type | `TEMPERATURE`, `VIBRATION`, `CURRENT`, `PRESSURE` |
| subscribe_interval_ms | 500, 1000, 2000, 5000 중 선택 |
| is_active | TRUE 85%, FALSE 15% |

#### 4.4.4 audit_trail (감사 추적)

| 컬럼 | 생성 규칙 |
|:----:|:--------:|
| table_name | 40개 테이블명 중 선택. 빈도: work_orders 20%, work_results 15%, inspections 15%, inventory 10%, 기타 40% |
| record_id | 해당 테이블의 PK 값 (문자열 변환) |
| action | INSERT 50%, UPDATE 40%, DELETE 10% |
| old_value | INSERT: NULL. UPDATE/DELETE: 변경 전 JSON |
| new_value | DELETE: NULL. INSERT/UPDATE: 변경 후 JSON |
| changed_by | `users.user_id` |
| changed_at | `2025-11-01` ~ 현재. 시간순 보장 |
| ip_address | `192.168.1.{10-254}` 또는 `10.0.{1-10}.{10-254}` |

> Load Test 시 50만건. 월별 파티셔닝 권장. 매 DML 트리거 시뮬레이션.

---

## 5. 시계열 데이터 시뮬레이션

### 5.1 센서 데이터 (sensor_data, equip_sensors)

**기본 모델**: Gaussian Process + Linear Drift + Anomaly Injection

```
value(t) = baseline + drift(t) + noise(t) + anomaly(t)

where:
  baseline    = 센서 유형별 정상 중심값
  drift(t)    = alpha * t  (설비 열화에 의한 선형 드리프트, alpha = 0.001~0.01/hour)
  noise(t)    = Normal(0, sigma)  (sigma = 정상 범위의 5%)
  anomaly(t)  = spike * Bernoulli(p=0.05)  (5% 확률로 이상치 주입)
```

**센서 유형별 파라미터**:

| 센서 유형 | baseline | sigma | drift alpha | anomaly spike | 단위 |
|:---------:|:--------:|:-----:|:-----------:|:-------------:|:----:|
| TEMPERATURE | 40.0 | 2.0 | 0.005 | +20~+50 | C |
| VIBRATION | 1.0 | 0.2 | 0.003 | +2.0~+5.0 | mm/s |
| CURRENT | 10.0 | 0.5 | 0.002 | +5.0~+12.0 | A |
| PRESSURE | 10.0 | 0.8 | 0.001 | +5.0~+15.0 | MPa |
| HUMIDITY | 55.0 | 3.0 | 0.0 (무드리프트) | +15~+30 | % |

**설비별 시나리오**:

| 설비 | 시나리오 | drift alpha | anomaly rate |
|:----:|:--------:|:-----------:|:------------:|
| EQP-001 (레이저절단기) | 정상 → 경고 전이 | 0.008 | 3% |
| EQP-003 (CNC선반) | 안정 유지 | 0.001 | 1% |
| EQP-005 (유압프레스) | 서서히 악화 | 0.015 | 8% |
| EQP-009 (사출기) | 안정 유지 | 0.001 | 1% |
| EQP-011 (조립라인A) | 간헐적 이상 | 0.003 | 15% (burst) |
| EQP-013 (SMT라인) | 고장 직전 급등 | 0.05 | 20% |
| EQP-014 (3차원측정기) | 매우 안정 | 0.0005 | 0.5% |

### 5.2 설비 상태 전이 (equip_status_log) -- Markov Chain

**상태 전이 확률 행렬** (1시간 단위):

```
         RUNNING   STOP    DOWN
RUNNING [ 0.970    0.020   0.010 ]
STOP    [ 0.600    0.350   0.050 ]
DOWN    [ 0.000    0.300   0.700 ]
```

**규칙**:
- DOWN → RUNNING 직접 전이 불가 (반드시 STOP(정비) 거쳐야 함)
- 야간(20:00~06:00) RUNNING→STOP 확률 2배 증가
- DOWN 상태 지속시간: Exponential(mean=8시간)
- STOP 상태 지속시간: Exponential(mean=2시간)

**상태별 사유 생성**:

| 전이 | 사유 풀 (랜덤 선택) |
|:----:|:-------------------:|
| RUNNING → STOP | 정기 점검, 툴 교체, 자재 대기, 교대 시간, 오일/필터 교체, 금형 교체 |
| RUNNING → DOWN | 모터 과열, 유압 누유, 센서 오류, 벨트 파손, 전기 이상, PLC 오류 |
| STOP → RUNNING | 점검 완료 재가동, 툴 교체 완료, 자재 투입 완료, 교대 인수인계 완료 |
| DOWN → STOP | 고장 원인 파악 중, 부품 교체 대기, 외부 수리 업체 호출 |

### 5.3 생산 데이터 -- 교대 패턴

**교대 스케줄**:

| 교대 | 시간 | 가동률 | 비고 |
|:----:|:----:|:------:|:----:|
| 주간 (A조) | 08:00 ~ 20:00 | 90% | 기본 생산 |
| 야간 (B조) | 20:00 ~ 08:00(+1) | 80% | 야간 감소 |
| 주말 | - | 0% | 비가동 (특근 시 50%) |

**작업 실적 생성 규칙**:
- `start_time`: 교대 시작 + Uniform(0, 30분)
- `end_time`: start_time + `cycle_time * qty / capacity_per_hour * 60` + Uniform(0, 60분)
- `good_qty`: `plan_qty * Uniform(0.93, 0.99)` (정수 반올림)
- `defect_qty`: `plan_qty - good_qty`
- 야간 교대 불량률 1.5배 가중

### 5.4 불량 발생 -- Poisson Distribution

**모델**:

```
defect_count ~ Poisson(lambda)

where:
  lambda_base  = total_count * base_defect_rate
  base_defect_rate:
    - 정상 조건: 0.01 ~ 0.03 (1~3%)
    - 이상 조건: 0.05 ~ 0.15 (5~15%)
    - 경계 조건: 0.03 ~ 0.05 (3~5%)
```

**이상 조건 트리거** (다음 중 하나 이상 해당 시):
- temperature > 220 C
- humidity > 70%
- pressure > 13.0 MPa
- 설비 vibration > 2.5 mm/s

**불량 코드 가중 분포**:

| 불량 코드 | 기본 가중치 | 이상 조건 시 가중치 |
|:---------:|:----------:|:------------------:|
| DEF-VISUAL | 0.25 | 0.15 |
| DEF-DIMEN | 0.25 | 0.30 |
| DEF-FUNC | 0.10 | 0.15 |
| DEF-MATERIAL | 0.10 | 0.10 |
| DEF-ASSEMBLY | 0.15 | 0.10 |
| DEF-PLATING | 0.05 | 0.10 |
| DEF-WELD | 0.05 | 0.05 |
| DEF-ELEC | 0.05 | 0.05 |

### 5.5 출하 -- 계절 패턴 (Seasonal Pattern)

**모델**:

```
qty(t) = base_qty * (1 + trend * t) * seasonal_factor(month) * (1 + noise)

where:
  base_qty         = 제품별 기본 출하량
  trend            = 0.005/month (월 0.5% 성장)
  seasonal_factor  = 아래 테이블 참조
  noise            = Normal(0, 0.05) (5% 변동)
```

**월별 계절 팩터**:

| 월 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|:--:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:--:|:--:|:--:|
| factor | 0.90 | 0.85 | 1.00 | 1.05 | 1.10 | 1.00 | 0.95 | 0.90 | 1.10 | 1.15 | 1.05 | 0.95 |

> 1~2월: 설 연휴 영향 감소, 5월/9~10월: 산업 수요 증가, 7~8월: 하계 휴가 영향.

**제품별 base_qty (월간)**:

| 제품 | base_qty | 고객 수 | 회/월 |
|:----:|:--------:|:-------:|:-----:|
| ITEM015 (전자제어장치) | 75 | 3 | 2 |
| ITEM016 (유압밸브) | 40 | 2 | 1 |
| ITEM017 (센서모듈) | 70 | 2 | 2 |
| ITEM018 (모터드라이버) | 30 | 2 | 1 |
| ITEM019 (산업용커넥터) | 115 | 2 | 2 |
| ITEM020 (제어패널) | 20 | 2 | 1 |

---

## 6. SQL 스크립트 구조

### 6.1 디렉토리 레이아웃

```
db/
├── init.sql                    # 기존 v4.0 스키마 + 시드 데이터
├── seed/
│   ├── 00_master.sql           # Layer 0: users, items, defect_codes, erp_sync_config
│   ├── 01_infrastructure.sql   # Layer 1: processes, equipments + FK, bom, routings,
│   │                           #          quality_standards, spc_rules, recipes,
│   │                           #          mqtt_config, opcua_config, documents,
│   │                           #          worker_skills, notification_settings
│   ├── 02_planning.sql         # Layer 2: production_plans, work_orders,
│   │                           #          maintenance_plans, inventory
│   ├── 03_execution.sql        # Layer 2~3: work_results, inspections,
│   │                           #            inspection_details, equip_status_log,
│   │                           #            inventory_transactions, shipments
│   ├── 04_phase1.sql           # Phase 1: spc_violations, capa, capa_actions,
│   │                           #          oee_daily, notifications
│   └── 05_phase3.sql           # Phase 3: erp_sync_log, audit_trail
├── seed_all.sh                 # 전체 시드 실행 스크립트
└── truncate_all.sql            # 전체 데이터 초기화 (역순 삭제)
```

### 6.2 샘플 SQL -- 대표 테이블 3개

#### 6.2.1 마스터 데이터: spc_rules

```sql
-- 00_master.sql (일부) 또는 04_phase1.sql

INSERT INTO spc_rules (item_code, check_name, rule_type, sample_size, ucl, lcl, target, is_active)
VALUES
  -- 금속프레임 길이 관리
  ('ITEM009', '프레임길이', 'WESTERN_ELECTRIC', 5, 300.5000, 299.5000, 300.0000, TRUE),
  ('ITEM009', '프레임폭',   'WESTERN_ELECTRIC', 5, 150.5000, 149.5000, 150.0000, TRUE),
  -- CNC가공부품 외경 관리
  ('ITEM010', '외경',       'NELSON',           5,  10.0100,   9.9900,  10.0000, TRUE),
  ('ITEM010', '표면조도',   'WESTERN_ELECTRIC', 5,   1.6000,   0.0000,   0.8000, TRUE),
  ('ITEM010', '진원도',     'NELSON',           3,   0.0050,   0.0000,   0.0025, TRUE),
  -- 사출성형품 무게 관리
  ('ITEM011', '무게',       'WESTERN_ELECTRIC', 5, 122.0000, 118.0000, 120.0000, TRUE),
  ('ITEM011', '두께',       'CUSTOM',           5,   2.7000,   2.3000,   2.5000, TRUE),
  -- 도금부품 도금두께
  ('ITEM013', '도금두께',   'WESTERN_ELECTRIC', 5,  12.0000,   8.0000,  10.0000, TRUE),
  -- 전자제어장치 전압
  ('ITEM015', '전압출력',   'NELSON',           5,   5.1000,   4.9000,   5.0000, TRUE),
  ('ITEM015', '소비전력',   'WESTERN_ELECTRIC', 5,  15.0000,   0.0000,  12.0000, TRUE),
  -- 유압밸브 내압
  ('ITEM016', '내압시험',   'WESTERN_ELECTRIC', 5,  40.0000,  30.0000,  35.0000, TRUE),
  ('ITEM016', '누설검사',   'NELSON',           3,   0.1000,   0.0000,   0.0500, TRUE),
  -- 센서모듈 정확도
  ('ITEM017', '온도정확도', 'WESTERN_ELECTRIC', 5,   0.5000,   0.0000,   0.2500, TRUE),
  ('ITEM017', '압력정확도', 'NELSON',           5,   1.0000,   0.0000,   0.5000, TRUE),
  -- 비활성 규칙 (테스트용)
  ('ITEM014', '길이',       'CUSTOM',           7,  50.2000,  49.8000,  50.0000, FALSE)
ON CONFLICT DO NOTHING;
```

#### 6.2.2 트랜잭션 데이터: oee_daily

```sql
-- 04_phase1.sql (일부)

-- generate_series를 활용한 OEE 벌크 생성 (설비 x 날짜 조합)
INSERT INTO oee_daily (equip_code, calc_date, availability, performance, quality_rate, oee,
                       planned_time_min, actual_run_min, ideal_cycle_min,
                       total_produced, good_produced)
SELECT
  e.equip_code,
  d.calc_date,
  -- availability: 0.82~0.98 범위 (랜덤)
  ROUND((0.82 + random() * 0.16)::numeric, 4) AS availability,
  -- performance: 0.80~0.96 범위
  ROUND((0.80 + random() * 0.16)::numeric, 4) AS performance,
  -- quality_rate: 0.92~0.99 범위
  ROUND((0.92 + random() * 0.07)::numeric, 4) AS quality_rate,
  -- oee: 계산은 트리거/후처리로 대체 가능
  ROUND(((0.82 + random() * 0.16) *
         (0.80 + random() * 0.16) *
         (0.92 + random() * 0.07))::numeric, 4) AS oee,
  480 AS planned_time_min,  -- 8시간 기본
  ROUND(480 * (0.82 + random() * 0.16))::int AS actual_run_min,
  ROUND((60.0 / e.capacity_per_hour)::numeric, 2) AS ideal_cycle_min,
  ROUND(480 * (0.82 + random() * 0.16) / (60.0 / e.capacity_per_hour)
        * (0.80 + random() * 0.16))::int AS total_produced,
  ROUND(480 * (0.82 + random() * 0.16) / (60.0 / e.capacity_per_hour)
        * (0.80 + random() * 0.16)
        * (0.92 + random() * 0.07))::int AS good_produced
FROM equipments e
CROSS JOIN (
  SELECT generate_series('2025-11-01'::date, '2026-02-28'::date, '1 day') AS calc_date
) d
WHERE EXTRACT(DOW FROM d.calc_date) NOT IN (0, 6)  -- 주말 제외
  AND e.status != 'DOWN'  -- 고장 설비 제외 (별도 처리)
ON CONFLICT (equip_code, calc_date) DO NOTHING;
```

#### 6.2.3 시계열 데이터: audit_trail

```sql
-- 05_phase3.sql (일부)

-- 작업지시 관련 감사 추적 (INSERT 이벤트)
INSERT INTO audit_trail (table_name, record_id, action, old_value, new_value, changed_by, changed_at, ip_address)
SELECT
  'work_orders',
  wo.wo_id,
  'INSERT',
  NULL,
  jsonb_build_object(
    'wo_id', wo.wo_id,
    'plan_id', wo.plan_id,
    'item_code', wo.item_code,
    'work_date', wo.work_date,
    'equip_code', wo.equip_code,
    'plan_qty', wo.plan_qty,
    'status', 'WAIT'
  ),
  CASE (random() * 3)::int
    WHEN 0 THEN 'admin'
    WHEN 1 THEN 'mgr01'
    WHEN 2 THEN 'mgr02'
    ELSE 'worker01'
  END,
  wo.work_date - interval '3 days' + (random() * interval '2 days'),
  '192.168.1.' || (10 + (random() * 244)::int)
FROM work_orders wo
ON CONFLICT DO NOTHING;

-- 작업지시 상태 변경 감사 추적 (UPDATE 이벤트)
INSERT INTO audit_trail (table_name, record_id, action, old_value, new_value, changed_by, changed_at, ip_address)
SELECT
  'work_orders',
  wo.wo_id,
  'UPDATE',
  jsonb_build_object('status', 'WAIT'),
  jsonb_build_object('status', wo.status),
  CASE (random() * 4)::int
    WHEN 0 THEN 'worker01'
    WHEN 1 THEN 'worker02'
    WHEN 2 THEN 'worker03'
    WHEN 3 THEN 'worker04'
    ELSE 'mgr01'
  END,
  wo.work_date + (random() * interval '8 hours'),
  '192.168.1.' || (10 + (random() * 244)::int)
FROM work_orders wo
WHERE wo.status IN ('WORKING', 'DONE')
ON CONFLICT DO NOTHING;
```

### 6.3 실행 스크립트 (seed_all.sh)

```bash
#!/bin/bash
set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-mes_db}"
DB_USER="${DB_USER:-postgres}"

SEED_DIR="$(dirname "$0")/seed"

echo "=== DEXWEAVER MES v6.0 Seed Data Loading ==="
echo "Target: ${DB_HOST}:${DB_PORT}/${DB_NAME}"

for sql_file in "$SEED_DIR"/0*.sql; do
  echo "[$(date +%T)] Loading $(basename "$sql_file") ..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
       -f "$sql_file" --set ON_ERROR_STOP=on
done

echo "[$(date +%T)] SQL seed complete. Running Python generators..."
python3 scripts/seed/generate_sensor_data.py --env "${ENV:-dev}"
python3 scripts/seed/generate_timeseries.py --env "${ENV:-dev}"

echo "=== Seed Data Loading Complete ==="
```

---

## 7. Python 스크립트 구조

### 7.1 디렉토리 레이아웃

```
scripts/
└── seed/
    ├── __init__.py
    ├── config.py               # DB 연결 설정, 환경별 볼륨 상수
    ├── generate_sensor_data.py # sensor_data 대량 생성 (이상치 주입)
    ├── generate_timeseries.py  # equip_sensors, equip_status_log, defect_history
    ├── generate_oee.py         # oee_daily 계산 기반 생성
    ├── generate_audit_trail.py # audit_trail 대량 생성
    ├── faker_utils.py          # Faker 공용 유틸 (한국어, MES 도메인)
    └── requirements.txt        # faker, numpy, psycopg2-binary, python-dotenv
```

### 7.2 requirements.txt

```
faker>=24.0.0
numpy>=1.26.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
tqdm>=4.66.0
```

### 7.3 config.py -- 환경별 볼륨 설정

```python
"""환경별 데이터 생성 볼륨 설정"""
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "mes_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

VOLUME = {
    "dev": {
        "sensor_data_days": 7,
        "sensor_interval_sec": 60,
        "equip_sensor_days": 7,
        "audit_trail_count": 200,
    },
    "staging": {
        "sensor_data_days": 90,
        "sensor_interval_sec": 30,
        "equip_sensor_days": 90,
        "audit_trail_count": 5000,
    },
    "loadtest": {
        "sensor_data_days": 365,
        "sensor_interval_sec": 10,
        "equip_sensor_days": 365,
        "audit_trail_count": 500000,
    },
}

# 설비 목록 (init.sql 기준)
EQUIP_CODES = [
    "EQP-001", "EQP-002", "EQP-003", "EQP-004", "EQP-005",
    "EQP-006", "EQP-007", "EQP-008", "EQP-009", "EQP-010",
    "EQP-011", "EQP-012", "EQP-013", "EQP-014", "EQP-015",
]

SENSOR_TYPES = ["TEMPERATURE", "VIBRATION", "CURRENT", "PRESSURE", "HUMIDITY"]
```

### 7.4 generate_sensor_data.py -- 센서 데이터 + 이상치 주입

```python
#!/usr/bin/env python3
"""
DEXWEAVER MES v6.0 -- sensor_data 테이블 대량 생성 스크립트
Gaussian + drift + 5% anomaly injection 모델 적용
"""
import argparse
import sys
from datetime import datetime, timedelta

import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

from config import DB_CONFIG, VOLUME, EQUIP_CODES, SENSOR_TYPES

# 센서 유형별 파라미터 정의
SENSOR_PARAMS = {
    "TEMPERATURE": {
        "baseline": 40.0,
        "sigma": 2.0,
        "drift_alpha": 0.005,
        "anomaly_spike_min": 20.0,
        "anomaly_spike_max": 50.0,
        "unit_min": 20.0,
        "unit_max": 200.0,
    },
    "VIBRATION": {
        "baseline": 1.0,
        "sigma": 0.2,
        "drift_alpha": 0.003,
        "anomaly_spike_min": 2.0,
        "anomaly_spike_max": 5.0,
        "unit_min": 0.1,
        "unit_max": 10.0,
    },
    "CURRENT": {
        "baseline": 10.0,
        "sigma": 0.5,
        "drift_alpha": 0.002,
        "anomaly_spike_min": 5.0,
        "anomaly_spike_max": 12.0,
        "unit_min": 1.0,
        "unit_max": 30.0,
    },
    "PRESSURE": {
        "baseline": 10.0,
        "sigma": 0.8,
        "drift_alpha": 0.001,
        "anomaly_spike_min": 5.0,
        "anomaly_spike_max": 15.0,
        "unit_min": 1.0,
        "unit_max": 50.0,
    },
    "HUMIDITY": {
        "baseline": 55.0,
        "sigma": 3.0,
        "drift_alpha": 0.0,
        "anomaly_spike_min": 15.0,
        "anomaly_spike_max": 30.0,
        "unit_min": 10.0,
        "unit_max": 99.0,
    },
}

# 설비별 열화 시나리오 (drift 배수, anomaly rate 오버라이드)
EQUIP_SCENARIOS = {
    "EQP-001": {"drift_mult": 1.6, "anomaly_rate": 0.03},   # 정상→경고
    "EQP-003": {"drift_mult": 0.2, "anomaly_rate": 0.01},   # 안정
    "EQP-005": {"drift_mult": 3.0, "anomaly_rate": 0.08},   # 서서히 악화
    "EQP-009": {"drift_mult": 0.2, "anomaly_rate": 0.01},   # 안정
    "EQP-011": {"drift_mult": 0.6, "anomaly_rate": 0.15},   # 간헐적 이상
    "EQP-013": {"drift_mult": 10.0, "anomaly_rate": 0.20},  # 고장 직전
    "EQP-014": {"drift_mult": 0.1, "anomaly_rate": 0.005},  # 매우 안정
}
DEFAULT_SCENARIO = {"drift_mult": 1.0, "anomaly_rate": 0.05}

ANOMALY_RATE_DEFAULT = 0.05
BATCH_SIZE = 5000


def generate_sensor_values(
    equip_code: str,
    sensor_type: str,
    num_points: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """단일 설비-센서 조합의 시계열 값 생성"""
    params = SENSOR_PARAMS[sensor_type]
    scenario = EQUIP_SCENARIOS.get(equip_code, DEFAULT_SCENARIO)

    baseline = params["baseline"]
    sigma = params["sigma"]
    drift_alpha = params["drift_alpha"] * scenario["drift_mult"]
    anomaly_rate = scenario["anomaly_rate"]

    t = np.arange(num_points, dtype=np.float64)

    # Gaussian noise
    noise = rng.normal(0, sigma, num_points)

    # Linear drift
    drift = drift_alpha * t

    # Anomaly injection (Bernoulli * Uniform spike)
    anomaly_mask = rng.random(num_points) < anomaly_rate
    spike_values = rng.uniform(
        params["anomaly_spike_min"],
        params["anomaly_spike_max"],
        num_points,
    )
    anomalies = anomaly_mask * spike_values

    # Combine
    values = baseline + drift + noise + anomalies

    # Clamp to physical range
    values = np.clip(values, params["unit_min"], params["unit_max"])

    return np.round(values, 4)


def generate_timestamps(
    start_dt: datetime,
    num_points: int,
    interval_sec: int,
) -> list[datetime]:
    """08:00~20:00 가동 시간 내 타임스탬프 생성"""
    timestamps = []
    current = start_dt
    while len(timestamps) < num_points:
        hour = current.hour
        weekday = current.weekday()
        # 주말 건너뛰기
        if weekday >= 5:
            current += timedelta(days=(7 - weekday))
            current = current.replace(hour=8, minute=0, second=0)
            continue
        # 비가동 시간 건너뛰기
        if hour < 8:
            current = current.replace(hour=8, minute=0, second=0)
            continue
        if hour >= 20:
            current += timedelta(days=1)
            current = current.replace(hour=8, minute=0, second=0)
            continue
        timestamps.append(current)
        current += timedelta(seconds=interval_sec)
    return timestamps


def main():
    parser = argparse.ArgumentParser(description="Generate sensor_data for MES v6.0")
    parser.add_argument("--env", choices=["dev", "staging", "loadtest"], default="dev")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    vol = VOLUME[args.env]
    rng = np.random.default_rng(args.seed)

    end_dt = datetime(2026, 3, 1, 8, 0, 0)
    start_dt = end_dt - timedelta(days=vol["sensor_data_days"])
    interval_sec = vol["sensor_interval_sec"]

    print(f"=== sensor_data generation ({args.env}) ===")
    print(f"Period: {start_dt.date()} ~ {end_dt.date()}")
    print(f"Interval: {interval_sec}s")

    # 타임스탬프 한 번만 생성 (모든 설비-센서 공유)
    timestamps = generate_timestamps(start_dt, 999_999_999, interval_sec)
    # 실제 포인트 수: 가동시간만 고려
    working_hours_per_day = 12  # 08:00~20:00
    working_days = vol["sensor_data_days"] * 5 / 7  # 주말 제외
    num_points = int(working_days * working_hours_per_day * 3600 / interval_sec)
    timestamps = timestamps[:num_points]

    print(f"Points per equip-sensor: {num_points:,}")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_inserted = 0

    for equip_code in tqdm(EQUIP_CODES, desc="Equipment"):
        for sensor_type in SENSOR_TYPES:
            values = generate_sensor_values(equip_code, sensor_type, num_points, rng)
            source_choices = rng.choice(
                ["MQTT", "OPCUA", "MANUAL"],
                size=num_points,
                p=[0.70, 0.20, 0.10],
            )

            rows = [
                (equip_code, sensor_type, float(v), ts, src)
                for v, ts, src in zip(values, timestamps, source_choices)
            ]

            # Batch insert
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                execute_values(
                    cursor,
                    """INSERT INTO sensor_data
                       (equip_code, sensor_type, value, collected_at, source)
                       VALUES %s ON CONFLICT DO NOTHING""",
                    batch,
                )
                conn.commit()
                total_inserted += len(batch)

    cursor.close()
    conn.close()

    print(f"\n=== Complete: {total_inserted:,} rows inserted ===")


if __name__ == "__main__":
    main()
```

### 7.5 faker_utils.py -- MES 도메인 Faker 확장

```python
"""DEXWEAVER MES 도메인 전용 Faker 유틸리티"""
from faker import Faker

fake = Faker("ko_KR")

# 불량 사유 풀
DEFECT_REASONS = {
    "DEF-VISUAL": ["스크래치 발견", "표면 변색", "찍힘 발생", "이물질 부착"],
    "DEF-DIMEN": ["치수 상한 이탈", "치수 하한 이탈", "공차 초과", "진원도 불량"],
    "DEF-FUNC": ["동작 불량", "성능 미달", "응답 지연", "출력 이상"],
    "DEF-MATERIAL": ["소재 기포", "내부 크랙", "이물질 혼입", "경도 부족"],
    "DEF-ASSEMBLY": ["부품 오조립", "나사 토크 부족", "갭 불량", "커넥터 미체결"],
    "DEF-PLATING": ["도금 박리", "도금 얼룩", "두께 부족", "변색"],
    "DEF-WELD": ["비드 불량", "기공 발생", "언더컷", "슬래그 잔류"],
    "DEF-ELEC": ["단선", "합선", "절연저항 미달", "접촉 불량"],
}

# 정비 작업 사유 풀
MAINTENANCE_REASONS = {
    "PM": ["정기 점검", "오일 교체", "필터 교체", "벨트 장력 조정", "보정 작업"],
    "CM": ["마모 부품 교체", "센서 재보정", "누유 수리", "배선 보수"],
    "BM": ["모터 소손 교체", "유압 실린더 교체", "PLC 모듈 교체", "컨베이어 벨트 교체"],
}

# 고객사 풀
CUSTOMERS = [
    "현대모비스", "만도", "LG전자", "보쉬코리아", "파카하니핀",
    "삼성전자", "LG이노텍", "두산로보틱스", "현대로보틱스",
    "TE코리아", "한국몰렉스", "LS일렉트릭", "슈나이더코리아",
    "ST마이크로", "ABB코리아", "지멘스코리아",
]

# 공급업체 풀
SUPPLIERS = {
    "SUS": ["포스코", "현대제철", "동국제강"],
    "AL": ["노벨리스", "조일알미늄"],
    "WIRE": ["LS전선", "대한전선"],
    "PLASTIC": ["LG화학", "롯데케미칼", "한화솔루션"],
    "RUBBER": ["평화고무", "한국타이어"],
    "IC": ["ST마이크로", "TI코리아", "인피니언"],
    "BOLT": ["삼흥볼트", "동양볼트"],
    "SEAL": ["실리콘코리아", "NOK코리아"],
}


def random_ip() -> str:
    """사내 IP 주소 생성"""
    subnet = fake.random_element(["192.168.1", "192.168.2", "10.0.1", "10.0.2"])
    host = fake.random_int(min=10, max=254)
    return f"{subnet}.{host}"


def random_defect_reason(defect_code: str) -> str:
    """불량 코드별 사유 랜덤 선택"""
    reasons = DEFECT_REASONS.get(defect_code, ["원인 미상"])
    return fake.random_element(reasons)
```

---

## 8. 데이터 정합성 검증

### 8.1 참조 무결성 검증 쿼리

```sql
-- ================================================================
-- 8.1.1  FK 참조 무결성: 모든 FK가 부모 테이블에 존재하는지 확인
-- ================================================================

-- user_permissions → users
SELECT 'user_permissions.user_id' AS fk_check,
       COUNT(*) AS orphan_count
FROM user_permissions up
LEFT JOIN users u ON up.user_id = u.user_id
WHERE u.user_id IS NULL;

-- bom → items (parent, child)
SELECT 'bom.parent_item' AS fk_check,
       COUNT(*) AS orphan_count
FROM bom b
LEFT JOIN items i ON b.parent_item = i.item_code
WHERE i.item_code IS NULL
UNION ALL
SELECT 'bom.child_item',
       COUNT(*)
FROM bom b
LEFT JOIN items i ON b.child_item = i.item_code
WHERE i.item_code IS NULL;

-- work_orders → production_plans, items, equipments
SELECT 'work_orders.plan_id' AS fk_check,
       COUNT(*) AS orphan_count
FROM work_orders wo
LEFT JOIN production_plans pp ON wo.plan_id = pp.plan_id
WHERE pp.plan_id IS NULL
UNION ALL
SELECT 'work_orders.equip_code',
       COUNT(*)
FROM work_orders wo
LEFT JOIN equipments e ON wo.equip_code = e.equip_code
WHERE e.equip_code IS NULL;

-- spc_violations → spc_rules, inspections
SELECT 'spc_violations.rule_id' AS fk_check,
       COUNT(*) AS orphan_count
FROM spc_violations sv
LEFT JOIN spc_rules sr ON sv.rule_id = sr.rule_id
WHERE sr.rule_id IS NULL
UNION ALL
SELECT 'spc_violations.inspection_id',
       COUNT(*)
FROM spc_violations sv
LEFT JOIN inspections i ON sv.inspection_id = i.inspection_id
WHERE i.inspection_id IS NULL;

-- sensor_data → equipments
SELECT 'sensor_data.equip_code' AS fk_check,
       COUNT(*) AS orphan_count
FROM sensor_data sd
LEFT JOIN equipments e ON sd.equip_code = e.equip_code
WHERE e.equip_code IS NULL;

-- erp_sync_log → erp_sync_config
SELECT 'erp_sync_log.sync_id' AS fk_check,
       COUNT(*) AS orphan_count
FROM erp_sync_log el
LEFT JOIN erp_sync_config ec ON el.sync_id = ec.sync_id
WHERE ec.sync_id IS NULL;
```

### 8.2 비즈니스 규칙 검증 쿼리

```sql
-- ================================================================
-- 8.2.1  BOM 순환 참조 방지: PRODUCT→SEMI→RAW 단방향 확인
-- ================================================================
SELECT 'BOM circular reference' AS rule_check,
       COUNT(*) AS violation_count
FROM bom b
JOIN items parent ON b.parent_item = parent.item_code
JOIN items child  ON b.child_item  = child.item_code
WHERE (parent.category = 'RAW')
   OR (parent.category = 'SEMI' AND child.category IN ('SEMI', 'PRODUCT'))
   OR (parent.category = 'PRODUCT' AND child.category = 'PRODUCT');

-- ================================================================
-- 8.2.2  작업 실적 수량 정합성: good_qty + defect_qty <= plan_qty
-- ================================================================
SELECT 'work_results qty overflow' AS rule_check,
       COUNT(*) AS violation_count
FROM work_results wr
JOIN work_orders wo ON wr.wo_id = wo.wo_id
WHERE (wr.good_qty + wr.defect_qty) > wo.plan_qty * 1.1;  -- 10% 오차 허용

-- ================================================================
-- 8.2.3  OEE 범위 검증: 0 <= availability, performance, quality_rate <= 1
-- ================================================================
SELECT 'oee_daily range violation' AS rule_check,
       COUNT(*) AS violation_count
FROM oee_daily
WHERE availability < 0 OR availability > 1
   OR performance < 0  OR performance > 1
   OR quality_rate < 0 OR quality_rate > 1
   OR oee < 0          OR oee > 1;

-- ================================================================
-- 8.2.4  OEE 계산 정합성: oee ≈ availability * performance * quality_rate
-- ================================================================
SELECT 'oee_daily calculation mismatch' AS rule_check,
       COUNT(*) AS violation_count
FROM oee_daily
WHERE ABS(oee - (availability * performance * quality_rate)) > 0.01;

-- ================================================================
-- 8.2.5  inspection_details 판정 일관성: FAIL 항목이 있으면 inspection도 FAIL
-- ================================================================
SELECT 'inspection judgment inconsistency' AS rule_check,
       COUNT(*) AS violation_count
FROM inspections i
WHERE i.judgment = 'PASS'
  AND EXISTS (
    SELECT 1 FROM inspection_details d
    WHERE d.inspection_id = i.inspection_id
      AND d.judgment = 'FAIL'
  );

-- ================================================================
-- 8.2.6  설비 상태 전이 규칙: DOWN → RUNNING 직접 전이 금지
-- ================================================================
SELECT 'equip_status_log invalid transition' AS rule_check,
       COUNT(*) AS violation_count
FROM (
  SELECT equip_code,
         status,
         LAG(status) OVER (PARTITION BY equip_code ORDER BY changed_at) AS prev_status
  FROM equip_status_log
) t
WHERE t.prev_status = 'DOWN' AND t.status = 'RUNNING';

-- ================================================================
-- 8.2.7  CAPA 워크플로우 순서: action_type 순서 검증
-- ================================================================
SELECT 'capa_actions sequence violation' AS rule_check,
       COUNT(*) AS violation_count
FROM capa_actions ca1
JOIN capa_actions ca2 ON ca1.capa_id = ca2.capa_id
WHERE ca1.action_type = 'VERIFICATION'
  AND ca2.action_type = 'ROOT_CAUSE'
  AND ca1.performed_at < ca2.performed_at;  -- VERIFICATION이 ROOT_CAUSE보다 먼저

-- ================================================================
-- 8.2.8  sensor_data 물리적 범위 검증
-- ================================================================
SELECT 'sensor_data out of physical range' AS rule_check,
       COUNT(*) AS violation_count
FROM sensor_data
WHERE (sensor_type = 'TEMPERATURE' AND (value < -50 OR value > 500))
   OR (sensor_type = 'VIBRATION'   AND (value < 0   OR value > 50))
   OR (sensor_type = 'CURRENT'     AND (value < 0   OR value > 100))
   OR (sensor_type = 'PRESSURE'    AND (value < 0   OR value > 100))
   OR (sensor_type = 'HUMIDITY'    AND (value < 0   OR value > 100));

-- ================================================================
-- 8.2.9  erp_sync_log 레코드 정합성: success + failed = processed
-- ================================================================
SELECT 'erp_sync_log record count mismatch' AS rule_check,
       COUNT(*) AS violation_count
FROM erp_sync_log
WHERE records_success + records_failed != records_processed;

-- ================================================================
-- 8.2.10  recipes UNIQUE(recipe_code, version) + ACTIVE 중복 방지
-- ================================================================
SELECT 'recipes duplicate active version' AS rule_check,
       COUNT(*) AS violation_count
FROM (
  SELECT recipe_code, COUNT(*) AS active_count
  FROM recipes
  WHERE status = 'ACTIVE'
  GROUP BY recipe_code
  HAVING COUNT(*) > 1
) t;
```

### 8.3 볼륨 검증 쿼리

```sql
-- ================================================================
-- 환경별 기대 볼륨 대비 실제 건수 확인
-- ================================================================
SELECT
  'users'                  AS table_name, COUNT(*) AS actual_count FROM users
UNION ALL SELECT
  'user_permissions',      COUNT(*) FROM user_permissions
UNION ALL SELECT
  'items',                 COUNT(*) FROM items
UNION ALL SELECT
  'bom',                   COUNT(*) FROM bom
UNION ALL SELECT
  'processes',             COUNT(*) FROM processes
UNION ALL SELECT
  'equipments',            COUNT(*) FROM equipments
UNION ALL SELECT
  'routings',              COUNT(*) FROM routings
UNION ALL SELECT
  'equip_status_log',      COUNT(*) FROM equip_status_log
UNION ALL SELECT
  'production_plans',      COUNT(*) FROM production_plans
UNION ALL SELECT
  'work_orders',           COUNT(*) FROM work_orders
UNION ALL SELECT
  'work_results',          COUNT(*) FROM work_results
UNION ALL SELECT
  'quality_standards',     COUNT(*) FROM quality_standards
UNION ALL SELECT
  'inspections',           COUNT(*) FROM inspections
UNION ALL SELECT
  'inspection_details',    COUNT(*) FROM inspection_details
UNION ALL SELECT
  'defect_codes',          COUNT(*) FROM defect_codes
UNION ALL SELECT
  'inventory',             COUNT(*) FROM inventory
UNION ALL SELECT
  'inventory_transactions',COUNT(*) FROM inventory_transactions
UNION ALL SELECT
  'shipments',             COUNT(*) FROM shipments
UNION ALL SELECT
  'defect_history',        COUNT(*) FROM defect_history
UNION ALL SELECT
  'equip_sensors',         COUNT(*) FROM equip_sensors
UNION ALL SELECT
  'ai_forecasts',          COUNT(*) FROM ai_forecasts
UNION ALL SELECT
  'spc_rules',             COUNT(*) FROM spc_rules
UNION ALL SELECT
  'spc_violations',        COUNT(*) FROM spc_violations
UNION ALL SELECT
  'capa',                  COUNT(*) FROM capa
UNION ALL SELECT
  'capa_actions',          COUNT(*) FROM capa_actions
UNION ALL SELECT
  'oee_daily',             COUNT(*) FROM oee_daily
UNION ALL SELECT
  'notifications',         COUNT(*) FROM notifications
UNION ALL SELECT
  'notification_settings', COUNT(*) FROM notification_settings
UNION ALL SELECT
  'maintenance_plans',     COUNT(*) FROM maintenance_plans
UNION ALL SELECT
  'maintenance_orders',    COUNT(*) FROM maintenance_orders
UNION ALL SELECT
  'recipes',               COUNT(*) FROM recipes
UNION ALL SELECT
  'recipe_parameters',     COUNT(*) FROM recipe_parameters
UNION ALL SELECT
  'mqtt_config',           COUNT(*) FROM mqtt_config
UNION ALL SELECT
  'sensor_data',           COUNT(*) FROM sensor_data
UNION ALL SELECT
  'documents',             COUNT(*) FROM documents
UNION ALL SELECT
  'worker_skills',         COUNT(*) FROM worker_skills
UNION ALL SELECT
  'erp_sync_config',       COUNT(*) FROM erp_sync_config
UNION ALL SELECT
  'erp_sync_log',          COUNT(*) FROM erp_sync_log
UNION ALL SELECT
  'opcua_config',          COUNT(*) FROM opcua_config
UNION ALL SELECT
  'audit_trail',           COUNT(*) FROM audit_trail
ORDER BY table_name;
```

### 8.4 자동화 검증 실행

```bash
#!/bin/bash
# db/validate_seed.sh -- 시드 데이터 정합성 자동 검증

set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-mes_db}"
DB_USER="${DB_USER:-postgres}"

PASS=0
FAIL=0

run_check() {
  local label="$1"
  local query="$2"
  local result
  result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
           -t -A -c "$query" 2>/dev/null | tr -d '[:space:]')
  if [ "$result" = "0" ]; then
    echo "[PASS] $label"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $label -- violations: $result"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== DEXWEAVER MES v6.0 Data Validation ==="
echo ""

run_check "FK: user_permissions → users" \
  "SELECT COUNT(*) FROM user_permissions up LEFT JOIN users u ON up.user_id=u.user_id WHERE u.user_id IS NULL"

run_check "FK: bom → items (parent)" \
  "SELECT COUNT(*) FROM bom b LEFT JOIN items i ON b.parent_item=i.item_code WHERE i.item_code IS NULL"

run_check "FK: work_orders → equipments" \
  "SELECT COUNT(*) FROM work_orders wo LEFT JOIN equipments e ON wo.equip_code=e.equip_code WHERE e.equip_code IS NULL"

run_check "FK: sensor_data → equipments" \
  "SELECT COUNT(*) FROM sensor_data sd LEFT JOIN equipments e ON sd.equip_code=e.equip_code WHERE e.equip_code IS NULL"

run_check "BIZ: BOM no circular ref" \
  "SELECT COUNT(*) FROM bom b JOIN items p ON b.parent_item=p.item_code JOIN items c ON b.child_item=c.item_code WHERE p.category='RAW'"

run_check "BIZ: OEE range 0~1" \
  "SELECT COUNT(*) FROM oee_daily WHERE oee<0 OR oee>1 OR availability<0 OR availability>1"

run_check "BIZ: equip_status no DOWN→RUNNING" \
  "SELECT COUNT(*) FROM (SELECT status, LAG(status) OVER (PARTITION BY equip_code ORDER BY changed_at) AS prev FROM equip_status_log) t WHERE prev='DOWN' AND status='RUNNING'"

run_check "BIZ: sensor_data physical range" \
  "SELECT COUNT(*) FROM sensor_data WHERE (sensor_type='TEMPERATURE' AND (value<-50 OR value>500)) OR (sensor_type='VIBRATION' AND (value<0 OR value>50))"

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|:----:|:----:|:---------:|
| v1.0 | 2026-03-03 | 최초 작성. 40개 테이블 전체 생성 전략 수립 |